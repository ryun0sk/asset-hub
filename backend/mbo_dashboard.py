"""Read-only MBO dashboard DTOs, without cloud or collection dependencies.

``document`` is an already configured read-only document whose ``read()``
returns ``(payload, generation)``. Only the local path lazily imports MBO core.
The cloud document contains curated runs and frozen snapshots, never a DB copy.
"""
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from threading import RLock
from time import monotonic
from urllib.parse import urlsplit, urlunsplit
import json
import re


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / 'data' / 'private' / 'mbo'
IDENTIFIER = re.compile(r'[A-Za-z0-9_-]{1,100}\Z')
INTEGER = re.compile(r'[0-9]{1,10}\Z')
MAX_DOCUMENT_BYTES = 32 * 1024 * 1024
CACHE_SECONDS = 60
UNAVAILABLE = 'MBOデータを読み込めませんでした。'


class QueryError(ValueError):
    """A public query error, distinct from malformed stored data."""


def _decimal_value(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return number if number.is_finite() else None


def _priority(company):
    assessment = company.get('mbo_assessment')
    if assessment:
        # Work queue only. Coverage and the retired four-point score are not
        # MBO suitability, and cannot promote an information-rich company.
        return Decimal({'monitor': 3, 'research': 2, 'awaiting': 1, 'deferred': 0}.get(
            assessment.get('workflow', {}).get('state'), 0))
    return _decimal_value(company.get('priority')) or Decimal(0)


def _discount(company):
    value = company.get('valuation', {}).get('discount_to_base', {})
    return _decimal_value(value.get('value')) if value.get('status') == 'ok' else None


def query_response(path, query, *, status_reader, runs_reader, snapshot_reader):
    """Select a page from already trusted DTOs; shared with loopback HTTP.

    Readers take no arguments except ``snapshot_reader(run_id_or_None)``.
    This function neither reads storage nor mutates any reader result.
    """
    if (not isinstance(path, str) or not isinstance(query, dict) or len(query) > 12
            or any(not isinstance(k, str) or not isinstance(v, str) for k, v in query.items())):
        raise QueryError('指定された条件を確認してください。')

    def allowed(*keys):
        if set(query) - set(keys):
            raise QueryError('指定された条件を確認してください。')

    def page():
        raw_limit, raw_offset = query.get('limit', '50'), query.get('offset', '0')
        if not INTEGER.fullmatch(raw_limit) or not INTEGER.fullmatch(raw_offset):
            raise QueryError('指定された条件を確認してください。')
        limit, offset = int(raw_limit), int(raw_offset)
        if not 1 <= limit <= 200:
            raise QueryError('指定された条件を確認してください。')
        return limit, offset

    def snapshot():
        requested = query.get('run_id', 'latest')
        if not IDENTIFIER.fullmatch(requested):
            raise QueryError('指定された条件を確認してください。')
        resolved = None if requested == 'latest' else requested
        value = snapshot_reader(resolved)
        actual = value.get('run_id')
        if (not isinstance(actual, str) or not IDENTIFIER.fullmatch(actual)
                or actual == 'latest' or (resolved is not None and actual != resolved)):
            raise RuntimeError(UNAVAILABLE)
        return value

    def meta(value):
        result = {'schema_version': value.get('schema_version', 1), 'run_id': value['run_id'],
                  'as_of': value.get('as_of'), 'demo': value.get('demo', False),
                  'source_scope': value.get('source_scope', 'imported_universe')}
        for key in ('created_at', 'rule_version', 'retrospective', 'network_mode', 'paid_provider_requests'):
            if key in value:
                result[key] = value[key]
        return result

    if path == '/api/mbo/status':
        allowed()
        return status_reader()
    if path == '/api/mbo/runs':
        allowed('limit', 'offset')
        limit, offset = page()
        runs = runs_reader()
        items = runs['items']
        return {'schema_version': runs.get('schema_version', 1), 'items': items[offset:offset + limit],
                'total': len(items), 'limit': limit, 'offset': offset}
    if path == '/api/mbo/candidates':
        allowed('run_id', 'q', 'status', 'sort', 'limit', 'offset')
        limit, offset = page()
        search, state, order = query.get('q', ''), query.get('status', 'all'), query.get('sort', 'priority')
        if (len(search) > 100 or state not in {'all', 'ready', 'pending', 'event'}
                or order not in {'priority', 'discount', 'name'}):
            raise QueryError('指定された条件を確認してください。')
        value = snapshot()
        search = search.casefold()
        items = [company for company in value['companies']
                 if company.get('status') != 'event'
                 and (state == 'all' or company.get('status') == state)
                 and (not search or any(search in str(company.get(key, '')).casefold()
                                        for key in ('name', 'code', 'security_id')))]

        def stable(company):
            return str(company.get('name', '')).casefold(), company['security_id']

        if order == 'name':
            items.sort(key=stable)
        elif order == 'discount':
            def discount_key(company):
                discount = _discount(company)
                return (discount is None, -discount if discount is not None else Decimal(0),
                        -_priority(company), *stable(company))
            items.sort(key=discount_key)
        else:
            items.sort(key=lambda company: (-_priority(company), *stable(company)))
        return {**meta(value), 'coverage': value.get('coverage', {}),
                'items': items[offset:offset + limit], 'total': len(items),
                'limit': limit, 'offset': offset, 'diff': value.get('diff', {})}
    if path.startswith('/api/mbo/companies/'):
        allowed('run_id')
        security_id = path[len('/api/mbo/companies/'):]
        if not IDENTIFIER.fullmatch(security_id):
            raise QueryError('指定された条件を確認してください。')
        value = snapshot()
        company = next((item for item in value['companies'] if item['security_id'] == security_id), None)
        if company is None:
            raise FileNotFoundError('対象のデータがありません。')
        return {**meta(value), 'company': company}
    if path == '/api/mbo/events':
        allowed('run_id', 'limit', 'offset')
        limit, offset = page()
        value = snapshot()
        items = value.get('events', [])
        return {**meta(value), 'coverage': value.get('coverage', {}),
                'items': items[offset:offset + limit], 'total': len(items),
                'limit': limit, 'offset': offset, 'diff': value.get('diff', {})}
    raise FileNotFoundError('対象のデータがありません。')


# The following projections are deliberately allowlists at every nesting level.
def _text(value):
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > 8000:
        raise RuntimeError(UNAVAILABLE)
    return value


def _id(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value) or value == 'latest':
        raise RuntimeError(UNAVAILABLE)
    return value


def _optional_id(value):
    return None if value is None else _id(value)


def _bool(value):
    if not isinstance(value, bool):
        raise RuntimeError(UNAVAILABLE)
    return value


def _int(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10**10:
        raise RuntimeError(UNAVAILABLE)
    return value


def _number(value):
    if value is None:
        return None
    if (not isinstance(value, (str, int, float, Decimal)) or isinstance(value, bool)
            or len(str(value)) > 1000):
        raise RuntimeError(UNAVAILABLE)
    number = _decimal_value(value)
    if number is None or abs(number.adjusted()) > 1000:
        raise RuntimeError(UNAVAILABLE)
    return format(number, 'f')


def _rank(value):
    number = _decimal_value(value)
    if isinstance(value, bool) or number is None or abs(number) > 10**9:
        raise RuntimeError(UNAVAILABLE)
    return int(number) if number == number.to_integral_value() else float(number)


def _moment(value):
    if value in (None, ''):
        return value
    _text(value)
    try:
        if len(value) == 10:
            date.fromisoformat(value)
        else:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise RuntimeError(UNAVAILABLE) from None
    return value


def _enum(*values):
    def check(value):
        if not any(type(value) is type(allowed) and value == allowed for allowed in values):
            raise RuntimeError(UNAVAILABLE)
        return value
    return check


def _list(convert, maximum=50000):
    def check(value):
        if not isinstance(value, list) or len(value) > maximum:
            raise RuntimeError(UNAVAILABLE)
        return [convert(item) for item in value]
    return check


def _object(value, fields):
    if not isinstance(value, dict):
        raise RuntimeError(UNAVAILABLE)
    return {key: convert(value[key]) for key, convert in fields.items() if key in value}


def _fields(keys, convert=_text):
    return {key: convert for key in keys.split()}


def _url(value):
    if not value:
        return None
    _text(value)
    try:
        parts = urlsplit(value)
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
            return None
        return urlunsplit(('https', parts.netloc, parts.path, '', ''))
    except ValueError:
        return None


def _filename(value):
    value = _text(value)
    return value if value and '/' not in value and '\\' not in value else None


def _coverage(value):
    return _object(value, _fields('universe prices valued pending events', _int))


def _identity(value):
    result = _object(value, {'security_id': _id, 'code': _text, 'name': _text})
    if 'security_id' not in result:
        raise RuntimeError(UNAVAILABLE)
    return result


def _event(value):
    result = _identity(value)
    result.update(_object(value, {**_fields('event_type status source_id'), 'announced_at': _moment}))
    return result


def _diff(value):
    def changed(item):
        return {**_identity(item), **_object(item, {'changes': _list(_text, 500)})}
    return _object(value, {'previous_run_id': _optional_id, 'added': _list(_identity),
                           'removed': _list(_identity), 'changed': _list(changed), 'summary': _text})


PARAMETERS = ('revenue_growth tax_rate wacc terminal_growth entry_debt_multiple debt_interest '
              'debt_amortization exit_multiple target_irr rollover_ratio fee_rate minimum_cash')
POLICIES = ('scenario cash_policy debt_amortization_basis financing lease_policy minimum_cash_policy '
            'rollover_policy tax_policy fee_basis equity_bridge fcf_basis growth_basis')
YEARLY = ('capex cash_before_repayment closing_cash closing_debt delta_nwc depreciation ebit interest '
          'opening_debt repayment taxes fcff present_value')
FINANCING = ('additional_cash_reserve excess_cash_used existing_debt_refinanced exit_enterprise_value '
             'exit_equity_value fees new_debt purchase_equity_value rollover_equity sponsor_equity '
             'sponsor_exit_proceeds sponsor_npv_at_target_irr sponsor_ownership total_sources total_uses')


def _assumptions(value):
    return _object(value, {**_fields(PARAMETERS, _number), **_fields(POLICIES), 'horizon_years': _int})


def _valuation_group(value):
    return _object(value, {'status': _enum('ok', 'pending', 'infeasible'), 'name': _text,
                           **_fields('value value_per_share enterprise_value equity_value max_price_per_share', _number),
                           'reasons': _list(_text, 500), 'assumptions': _assumptions,
                           'financing': lambda x: _object(x, _fields(FINANCING, _number)),
                           'yearly': _list(lambda x: _object(x, {**_fields(YEARLY, _number), 'year': _int}), 100)})


def _valuation(value):
    result = _object(value, {
        'standalone': lambda x: _object(x, {'status': _enum('ok', 'pending', 'infeasible'),
                                            'scenarios': _list(_valuation_group, 20)}),
        'discount_to_base': _valuation_group, 'lbo': _valuation_group})
    discount = result.get('discount_to_base', {})
    if discount.get('status') in {'pending', 'infeasible'}:
        discount['value'] = None
    if discount.get('status') == 'ok' and discount.get('value') is None:
        raise RuntimeError(UNAVAILABLE)
    return result


def _mbo_assessment(value):
    states = _enum('supported', 'contradicted', 'unknown', 'conflicting', 'not_applicable')
    return _object(value, {
        'version': _enum('mbo-evidence-1', 'mbo-evidence-2'), 'validation_status': _enum('hypothesis_not_calibrated'),
        'workflow': lambda x: _object(x, {
            'state': _enum('awaiting', 'research', 'monitor', 'deferred', 'event'),
            **_fields('label reason watch_trigger reviewer'), 'next_review_at': _moment,
            'basis_record_ids': _list(_id, 50)}),
        'axes': _list(lambda x: _object(x, {
            'id': _enum('ownership', 'motive', 'execution', 'obstacles'), **_fields('label note'), 'state': states,
            'factors': _list(lambda y: _object(y, {**_fields('factor_id label criterion'), 'state': states}), 100),
            'evidence': _list(lambda y: _object(y, {
                **_fields('record_id factor_id label quote interpretation source_id document_id locator '
                          'quality_status reviewer speaker agreement_parties agreement_terms supersedes correction_reason exclusion_reason'),
                'state': states, 'evidence_type': _enum('public_fact', 'analyst_hypothesis', 'own_scenario', 'post_announcement'),
                'usable_for_candidate': _bool,
                **_fields('public_at observed_at ready_at as_of valid_until', _moment)}), 2000)}), 4),
        'information': lambda x: _object(x, {**_fields('verified_count hypothesis_count unresolved_count', _int),
                                            'coverage_label': _text}),
        'financial_context': _list(_text, 100), 'cautions': _list(_text, 100)})


def _company(value):
    result = _identity(value)
    result.update(_object(value, {
        **_fields('exchange'), 'status': _enum('ready', 'pending', 'event'), 'priority': _rank,
        'reasons': _list(_text, 500), 'missing': _list(_text, 500), 'is_new': _bool,
        'facts': _list(lambda x: _object(x, {
            **_fields('record_id metric label unit currency fact_kind consolidation share_basis quality_status '
                      'source_id locator missing_reason supersedes correction_reason'), 'value': _number,
            **_fields('period_start period_end public_at observed_at ready_at', _moment)}), 2000),
        'price': lambda x: None if x is None else _object(x, {
            **_fields('record_id currency price_type adjustment share_basis quality_status source_id supersedes correction_reason'),
            'value': _number, 'price_at': _moment}),
        'valuation': _valuation, 'events': _list(_event, 2000),
        'mbo_assessment': _mbo_assessment,
        'evidence': _list(lambda x: _object(x, {
            **_fields('document_id source_id title sha256 locator quality_status'),
            'filename': _filename, 'source_url': _url, 'published_at': _moment}), 2000)}))
    if result.get('status') is None:
        raise RuntimeError(UNAVAILABLE)
    return result


def _meta(value):
    result = _object(value, {'schema_version': _enum(1), 'run_id': _id, 'as_of': _moment,
                             'created_at': _moment, 'demo': _bool, 'coverage': _coverage,
                             'rule_version': _text, 'retrospective': _bool})
    if result.get('schema_version') != 1 or not result.get('run_id'):
        raise RuntimeError(UNAVAILABLE)
    return result


def _run(value):
    result = _meta(value)
    result['status'] = _enum('success')(value.get('status'))
    # Input hashes, manifests and IDs are not needed to browse the result.
    return result


def _snapshot(value):
    result = _meta(value)
    result.update(_object(value, {'companies': _list(_company), 'events': _list(_event), 'diff': _diff}))
    if 'companies' not in result or len({c['security_id'] for c in result['companies']}) != len(result['companies']):
        raise RuntimeError(UNAVAILABLE)
    result.update(_object(value, {'source_scope': _enum('imported_universe'),
                                   'network_mode': _enum('offline'), 'paid_provider_requests': _enum(0)}))
    result.setdefault('source_scope', 'imported_universe')
    return result


def _attempt(value):
    if value is None:
        return None
    result = _object(value, {'status': _enum('running', 'success', 'failed', 'error'),
                             'run_id': _optional_id, 'as_of': _moment,
                             **_fields('started_at finished_at', _moment)})
    if result.get('status') in {'failed', 'error'}:
        result['error'] = '更新に失敗しました。最後の成功結果を保持しています。'
    return result


def sanitize_bundle(payload) -> dict:
    """Validate and project a curated dashboard bundle, with no I/O or imports.

    Both local export and cloud reads use this exact public boundary. Extra
    fields are discarded recursively; malformed known fields fail closed.
    An absent object (``{}``) becomes the explicit empty schema-v1 bundle.
    """
    try:
        if not isinstance(payload, dict):
            raise RuntimeError(UNAVAILABLE)
        if len(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()) > MAX_DOCUMENT_BYTES:
            raise RuntimeError(UNAVAILABLE)
        if not payload:
            return {'schema_version': 1, 'runs': [], 'snapshots': {},
                    'latest_run_id': None, 'last_attempt': None}
        if type(payload.get('schema_version')) is not int or payload['schema_version'] != 1:
            raise RuntimeError(UNAVAILABLE)
        runs = _list(_run, 1000)(payload.get('runs', []))
        source = payload.get('snapshots', {})
        if not isinstance(source, dict) or len(source) > 1000:
            raise RuntimeError(UNAVAILABLE)
        snapshots = {_id(key): _snapshot(value) for key, value in source.items()}
        if any(key != value['run_id'] for key, value in snapshots.items()):
            raise RuntimeError(UNAVAILABLE)
        run_ids = [run['run_id'] for run in runs]
        if len(set(run_ids)) != len(run_ids) or set(run_ids) != set(snapshots):
            raise RuntimeError(UNAVAILABLE)
        for run in runs:
            frozen = snapshots[run['run_id']]
            if any(key in frozen and run[key] != frozen[key] for key in run if key != 'status'):
                raise RuntimeError(UNAVAILABLE)
        latest = _optional_id(payload.get('latest_run_id'))
        if latest is not None and latest not in run_ids:
            raise RuntimeError(UNAVAILABLE)
        return {'schema_version': 1, 'runs': runs, 'snapshots': snapshots,
                'latest_run_id': latest, 'last_attempt': _attempt(payload.get('last_attempt'))}
    except Exception:
        raise RuntimeError(UNAVAILABLE) from None


class MboDashboard:
    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR, document=None):
        self.data_dir = Path(data_dir)
        self.document = document
        self._lock = RLock()
        self._cached = None
        self._cached_at = 0

    def _local_read(self, name, *args):
        try:
            from .mbo import core
            return getattr(core, name)(self.data_dir, *args)
        except FileNotFoundError:
            if name == 'read_snapshot':
                raise FileNotFoundError('対象のデータがありません。') from None
            raise RuntimeError(UNAVAILABLE) from None
        except Exception:
            raise RuntimeError(UNAVAILABLE) from None

    def _cloud(self):
        with self._lock:
            if self._cached is not None and monotonic() - self._cached_at < CACHE_SECONDS:
                return self._cached
            try:
                payload, _generation = self.document.read()
                result = sanitize_bundle(payload)
            except Exception:
                raise RuntimeError(UNAVAILABLE) from None
            self._cached, self._cached_at = result, monotonic()
            return result

    def _status(self):
        cloud = self.document is not None
        if cloud:
            value = self._cloud()
            latest, attempt = value['latest_run_id'], value['last_attempt']
        else:
            value = self._local_read('read_status')
            latest, attempt = _optional_id(value.get('latest_success_run_id')), _attempt(value.get('last_attempt'))
        return {'schema_version': 1, 'mode': 'mbo-dashboard', 'offline': not cloud,
                'storage_state': 'ready' if latest else 'empty', 'latest_success_run_id': latest,
                'last_attempt': attempt, 'edinet': {'configured': 'unknown', 'collection_enabled': False},
                'features': {'file_import_cli': not cloud, 'http_write': False, 'llm': False, 'cloud': cloud}}

    def _runs(self):
        items = self._cloud()['runs'] if self.document is not None else _list(_run, 1000)(self._local_read('read_runs')['items'])
        return {'schema_version': 1, 'items': items, 'total': len(items)}

    def _snapshot(self, run_id):
        if self.document is None:
            return _snapshot(self._local_read('read_snapshot', run_id))
        value = self._cloud()
        resolved = value['latest_run_id'] if run_id is None else run_id
        if resolved not in value['snapshots']:
            raise FileNotFoundError('対象のデータがありません。')
        return value['snapshots'][resolved]

    def response(self, path: str, query: dict) -> dict:
        """Return only sanitized DTOs; never write or calculate on a read."""
        try:
            return deepcopy(query_response(path, query, status_reader=self._status,
                                           runs_reader=self._runs, snapshot_reader=self._snapshot))
        except QueryError:
            raise
        except FileNotFoundError:
            raise FileNotFoundError('対象のデータがありません。') from None
        except Exception:
            raise RuntimeError(UNAVAILABLE) from None
