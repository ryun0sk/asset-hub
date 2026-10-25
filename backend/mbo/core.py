"""Immutable local imports, deterministic research runs, and frozen read models.

CSV values are manually transcribed facts, not automatic document extraction.
The source bytes and declared review status remain available for verification.
All monetary inputs are JPY (not millions of JPY). No HTTP/network clients.
"""
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import csv
import fcntl
import io
import json
import os
import re
import sqlite3
import stat
import uuid

from . import RULE_VERSION, SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[2]
JST = timezone(timedelta(hours=9))
DEFAULT_DATA_DIR = ROOT / 'data/private/mbo'
MAX_FILE = 32 * 1024 * 1024
MAX_ROWS = 50000
IDENTIFIER = re.compile(r'^[A-Za-z0-9_-]{1,100}$')
KINDS = ('documents', 'securities', 'facts', 'prices', 'events', 'scenarios', 'assessments', 'reviews')
CORRECTABLE = ('facts', 'prices', 'assessments', 'reviews')
MONEY = {'ebit', 'depreciation', 'capex', 'delta_nwc', 'excess_cash', 'debt',
         'noncontrolling_interest', 'operating_cfo', 'cash_and_equivalents',
         'revenue', 'investment_securities', 'cash_and_deposits'}
FLOW = {'ebit', 'depreciation', 'capex', 'delta_nwc', 'operating_cfo', 'revenue'}
LABELS = {'ebit': '営業利益', 'depreciation': '減価償却費', 'capex': '設備投資',
          'delta_nwc': '運転資本増加', 'excess_cash': '余剰現金', 'debt': '有利子負債',
          'noncontrolling_interest': '非支配持分', 'shares_diluted': '自己株控除後の希薄化株数',
          'owner_ratio': '確認済み経営陣・創業家保有比率', 'operating_cfo': '営業CF',
          'cash_and_equivalents': '現金及び現金同等物（実績）', 'revenue': '売上高',
          'investment_securities': '投資有価証券（基準DCFへ未加算）',
          'cash_and_deposits': '現金及び預金（現金同等物とは別）'}
QUALITY = {'verified', 'pending', 'conflicting', 'missing', 'not_applicable'}
FACT_KINDS = {'actual', 'company_forecast', 'external_forecast', 'own_scenario'}
EVENT_TYPES = {'mbo', 'parent_take_private', 'other_tob'}
EVENT_STATUS = {'reported', 'announced', 'ongoing', 'settled', 'withdrawn'}
SCENARIO_FIELDS = ('horizon_years', 'revenue_growth', 'tax_rate', 'wacc', 'terminal_growth',
                   'entry_debt_multiple', 'debt_interest', 'debt_amortization', 'exit_multiple',
                   'target_irr', 'fee_rate', 'rollover_ratio', 'minimum_cash')
HEADERS = {
    'documents': ['source_id', 'file', 'title', 'source_url', 'published_at'],
    'securities': ['code', 'name', 'exchange', 'security_type', 'as_of', 'source_id', 'included'],
    'facts': ['code', 'exchange', 'metric', 'value', 'unit', 'currency', 'period_start', 'period_end',
              'fact_kind', 'consolidation', 'share_basis', 'public_at', 'source_id', 'locator',
              'quality_status', 'missing_reason', 'supersedes', 'correction_reason'],
    'prices': ['code', 'exchange', 'value', 'currency', 'price_at', 'price_type', 'adjustment',
               'share_basis', 'public_at', 'source_id', 'locator', 'quality_status', 'supersedes', 'correction_reason'],
    'events': ['code', 'exchange', 'event_type', 'status', 'announced_at', 'public_at', 'source_id', 'locator'],
    'scenarios': ['code', 'exchange', 'name', 'as_of', *SCENARIO_FIELDS, 'note'],
    'assessments': ['code', 'exchange', 'dimension', 'factor_id', 'state', 'evidence_type',
                    'speaker', 'quote', 'interpretation', 'as_of', 'valid_until', 'public_at',
                    'source_id', 'locator', 'quality_status', 'reviewer', 'agreement_parties', 'agreement_terms', 'supersedes', 'correction_reason'],
    'reviews': ['code', 'exchange', 'state', 'reason', 'watch_trigger', 'as_of', 'next_review_at',
                'public_at', 'source_id', 'locator', 'quality_status', 'reviewer', 'basis_record_ids', 'supersedes', 'correction_reason'],
}


def now():
    return datetime.now(timezone.utc).isoformat()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode('utf-8')


def digest(value):
    return sha256(value).hexdigest()


def safe_id(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError('識別子は100文字以内の英数字・ハイフン・アンダースコアにしてください')
    return value


def instant(value, *, end_of_day=True):
    """Compare instants, not ISO strings; date-only availability is day's end JST."""
    if not isinstance(value, str):
        raise ValueError('ISO日付またはタイムゾーン付き日時が必要です')
    if len(value) == 10:
        return datetime.combine(date.fromisoformat(value), time.max if end_of_day else time.min, JST)
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('日時にはタイムゾーンが必要です')
    return parsed.astimezone(JST)


def iso(value, field):
    try:
        instant(value)
        return value
    except (ValueError, TypeError):
        raise ValueError(f'{field}: ISO日付またはタイムゾーン付き日時が必要です') from None


def day(value):
    return instant(value).date()


def numeric(value, field, positive=False, nonnegative=False):
    try:
        result = Decimal(value)
        if not result.is_finite() or abs(result) > Decimal('1e20') or result.as_tuple().exponent < -12:
            raise ValueError()
        if positive and result <= 0 or nonnegative and result < 0:
            raise ValueError()
        return format(result, 'f')
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError(f'{field}: 有限の数値と正負の条件を確認してください（桁区切りなし）') from None


def source_url(value):
    if not value:
        return None
    try:
        parts = urlsplit(value)
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
            raise ValueError()
        # Query/fragment may contain signed URLs, tokens or user tracking.
        return urlunsplit(('https', parts.netloc, parts.path, '', ''))
    except ValueError:
        raise ValueError('source_urlは認証情報を含まないHTTPS URLにしてください') from None


def reject_symlinks(path):
    path = Path(os.path.abspath(path))
    # macOS exposes these system-owned aliases. Do not resolve any arbitrary
    # ancestor symlink: user-created symlinks remain forbidden below the alias.
    for alias, target in (('/tmp', '/private/tmp'), ('/var', '/private/var')):
        alias_path = Path(alias)
        if (path == alias_path or alias_path in path.parents) and alias_path.is_symlink():
            declared_target = os.path.normpath(os.path.join(str(alias_path.parent), os.readlink(alias_path)))
            if declared_target == target:
                path = Path(target) / path.relative_to(alias_path)
            break
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('シンボリックリンクは取込・保存先に使えません')
    return path


def private_dir(path):
    path = reject_symlinks(path)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def atomic(path, content):
    path = Path(path)
    private_dir(path.parent)
    reject_symlinks(path)
    temporary = path.with_name('.tmp-' + uuid.uuid4().hex)
    try:
        with temporary.open('xb') as handle:
            os.chmod(temporary, 0o600)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def writer(data_dir):
    base = private_dir(data_dir)
    lock = reject_symlinks(base / '.writer.lock')
    previous_umask = os.umask(0o077)
    try:
        with lock.open('a') as handle:
            os.chmod(lock, 0o600)
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('別のMBO更新が実行中です') from None
            yield base
    finally:
        os.umask(previous_umask)


def connection(base, create=False):
    db = reject_symlinks(Path(base) / 'state.sqlite')
    if not create and not db.exists():
        raise FileNotFoundError('MBOデータが未初期化です')
    conn = sqlite3.connect(str(db) if create else db.as_uri() + '?mode=ro', uri=not create)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    if create:
        os.chmod(db, 0o600)
        conn.executescript('''
          CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS import_batch (
            import_id TEXT PRIMARY KEY, input_hash TEXT UNIQUE NOT NULL, observed_at TEXT NOT NULL,
            counts TEXT NOT NULL, demo INTEGER NOT NULL);
          CREATE TABLE IF NOT EXISTS record (
            record_id TEXT PRIMARY KEY, kind TEXT NOT NULL, import_id TEXT NOT NULL
            REFERENCES import_batch(import_id), payload TEXT NOT NULL);
          CREATE INDEX IF NOT EXISTS record_kind ON record(kind);
          CREATE TABLE IF NOT EXISTS run (
            run_id TEXT PRIMARY KEY, as_of TEXT NOT NULL, created_at TEXT NOT NULL,
            input_hash TEXT NOT NULL, summary TEXT NOT NULL);
        ''')
        existing = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        if existing and int(existing[0]) != SCHEMA_VERSION:
            conn.close()
            raise RuntimeError('対応していないDB版です')
        conn.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)', ('schema_version', str(SCHEMA_VERSION)))
        conn.commit()
    else:
        row = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        if not row or int(row[0]) != SCHEMA_VERSION:
            conn.close()
            raise RuntimeError('対応していないDB版です')
    return conn


def init(data_dir=DEFAULT_DATA_DIR):
    with writer(data_dir) as base:
        conn = connection(base, create=True)
        conn.close()
    return read_status(data_dir)


def records(conn, kind):
    return [json.loads(row[0]) for row in conn.execute('SELECT payload FROM record WHERE kind=? ORDER BY rowid', (kind,))]


def read_input(path, base=None):
    path = reject_symlinks(path)
    if base is not None:
        path.relative_to(reject_symlinks(base))
    if not path.exists():
        raise FileNotFoundError('入力ファイルがありません')
    if not path.is_file() or path.stat().st_size > MAX_FILE:
        raise ValueError('入力は32MiB以下の通常ファイルにしてください')
    return path.read_bytes()


def csv_rows(path, encoding):
    data = read_input(path)
    try:
        reader = csv.DictReader(io.StringIO(data.decode(encoding), newline=''))
        headers = reader.fieldnames
        if not headers or len(headers) != len(set(headers)):
            raise ValueError('CSVヘッダーが空または重複しています')
        rows = []
        for i, row in enumerate(reader, 2):
            if i > MAX_ROWS + 1:
                raise ValueError('CSV行数の上限は50000行です')
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f'{i}行: 列数がヘッダーと一致しません')
            rows.append((i, {k: v.strip() for k, v in row.items()}))
        return data, rows
    except UnicodeError:
        raise ValueError('CSV文字コードを確認してください（UTF-8 BOM対応、または--encoding cp932）') from None
    except csv.Error:
        raise ValueError(f'{Path(path).name}: CSVの形式・セルの長さを確認してください') from None


def required(row, *fields):
    for field in fields:
        if not row.get(field):
            raise ValueError(f'{field}が必要です')


def security_key(row):
    required(row, 'code')
    safe_id(row['code'])
    row['exchange'] = row.get('exchange') or 'TSE'
    safe_id(row['exchange'])
    return row['exchange'] + ':' + row['code']


def validate_corrections(prepared, conn):
    """Corrections append a single successor to an existing immutable record."""
    old = {kind: records(conn, kind) if conn else [] for kind in CORRECTABLE}
    by_id = {r['record_id']: (kind, r) for kind, rows in old.items() for r in rows}
    replaced = {r['supersedes'] for rows in old.values() for r in rows if r.get('supersedes')}
    batch_targets = set()
    for kind in CORRECTABLE:
        for line, row in enumerate(prepared[kind], 2):
            target = row.get('supersedes')
            if not target:
                if row.get('correction_reason'):
                    raise ValueError(f'{kind}.csv {line}行: correction_reasonにはsupersedesが必要です')
                continue
            safe_id(target)
            required(row, 'correction_reason')
            prior = by_id.get(target)
            if prior is None:
                raise ValueError(f'{kind}.csv {line}行: supersedesの既存record_idが見つかりません')
            prior_kind, previous = prior
            if prior_kind != kind or previous['security_id'] != row['security_id']:
                raise ValueError(f'{kind}.csv {line}行: 別種別・別銘柄のrecordは訂正できません')
            if kind == 'facts':
                if (previous['metric'] != row['metric']
                        or day(previous['period_end']) != day(row['period_end'])):
                    raise ValueError(f'{kind}.csv {line}行: 訂正は同じmetric・period_endに限ります')
            elif kind == 'prices' and instant(previous['price_at']) != instant(row['price_at']):
                raise ValueError(f'{kind}.csv {line}行: 訂正は同じprice_atに限ります')
            elif kind in ('assessments', 'reviews'):
                if day(previous['as_of']) != day(row['as_of']) or (kind == 'assessments' and previous['factor_id'] != row['factor_id']):
                    raise ValueError(f'{kind}.csv {line}行: 訂正は同じas_of・論点に限ります')
            if target in replaced or target in batch_targets:
                raise ValueError(f'{kind}.csv {line}行: 既に訂正済みです。最新訂正record_idを指定してください（分岐訂正不可）')
            batch_targets.add(target)


def active_records(rows):
    """Call only after availability filtering; future corrections cannot hide old values."""
    superseded = {r['supersedes'] for r in rows if r.get('supersedes')}
    return [r for r in rows if r['record_id'] not in superseded]


def import_bundle(directory, data_dir=DEFAULT_DATA_DIR, *, dry_run=False, encoding='utf-8-sig', demo=False):
    """Validate a complete batch before any DB mutation. Unknown values never become zero."""
    directory = reject_symlinks(directory)
    if not directory.is_dir():
        raise ValueError('CSV取込フォルダがありません')
    if encoding not in ('utf-8-sig', 'utf-8', 'cp932'):
        raise ValueError('対応文字コードはUTF-8とCP932です')
    with writer(data_dir) as base:
        db_exists = (base / 'state.sqlite').exists()
        conn = connection(base, create=False) if db_exists else None
        try:
            old_docs = records(conn, 'documents') if conn else []
            old_secs = records(conn, 'securities') if conn else []
            stored_demo = conn.execute("SELECT value FROM metadata WHERE key='demo'").fetchone() if conn else None
            if stored_demo and bool(int(stored_demo[0])) != demo:
                raise ValueError('デモと実データは別の保存先にしてください')
            parsed, hashes = {}, {}
            for kind in KINDS:
                path = directory / (kind + '.csv')
                if path.exists() or path.is_symlink():
                    content, rows = csv_rows(path, encoding)
                    parsed[kind] = rows
                    hashes[kind + '.csv'] = digest(content)
            if not parsed or not any(rows for rows in parsed.values()):
                raise ValueError('取込対象のCSV行がありません')
            stamp = now()
            prepared = {kind: [] for kind in KINDS}
            raw = {}
            errors = []
            docs = {r['source_id']: r for r in old_docs}
            secs = {r['key']: r for r in old_secs}
            for kind in KINDS:
                for line, initial in parsed.get(kind, []):
                    row = dict(initial)
                    try:
                        # Bound all user text before it reaches the browser or logs.
                        if any(len(v) > 2000 or '\x00' in v for v in row.values()):
                            raise ValueError('セルは2000文字以内、NULなしにしてください')
                        if kind == 'documents':
                            required(row, 'source_id', 'title', 'published_at')
                            safe_id(row['source_id'])
                            iso(row['published_at'], 'published_at')
                            row['source_url'] = source_url(row.get('source_url', ''))
                            relative = row.pop('file', '')
                            row.update(document_id='doc-' + uuid.uuid4().hex, sha256=None, raw_relpath=None, filename=None)
                            if relative:
                                path = directory / relative
                                if '..' in Path(relative).parts or Path(relative).is_absolute():
                                    raise ValueError('原本fileは取込フォルダ内の相対パスにしてください')
                                if path.suffix.lower() not in {'.pdf', '.csv', '.xml', '.xbrl', '.html', '.txt'}:
                                    raise ValueError('原本はPDF/CSV/XML/XBRL/HTML/TXTのみ。ZIP展開は行いません')
                                content = read_input(path, directory)
                                sha = digest(content)
                                row.update(sha256=sha, raw_relpath=f'raw/{sha}/original{path.suffix.lower()}', filename=path.name)
                                raw[row['raw_relpath']] = content
                                hashes[relative] = sha
                            old = docs.get(row['source_id'])
                            if old:
                                comparable = ('sha256', 'title', 'published_at', 'source_url')
                                if any(row.get(k) != old.get(k) for k in comparable):
                                    raise ValueError('同じsource_idの出所を変更できません。訂正版には新しいsource_idを付けてください')
                                row = dict(old)
                            docs[row['source_id']] = row
                        elif kind == 'securities':
                            required(row, 'name', 'security_type', 'as_of', 'source_id')
                            row['key'] = security_key(row)
                            iso(row['as_of'], 'as_of')
                            if row['security_type'] != 'common_stock':
                                raise ValueError('初版は普通株common_stockのみ対応しています')
                            if row.get('included', 'true') not in ('true', 'false', ''):
                                raise ValueError('includedはtrue/falseです')
                            row['included'] = row.get('included') != 'false'
                            row['security_id'] = secs.get(row['key'], {}).get('security_id', 'sec-' + uuid.uuid4().hex)
                            secs[row['key']] = row
                        else:
                            row['key'] = security_key(row)
                            if row['key'] not in secs:
                                raise ValueError('銘柄が未登録です。先にsecurities.csvへ追加してください')
                            row['security_id'] = secs[row['key']]['security_id']
                            if kind == 'scenarios':
                                required(row, 'name', 'as_of', *SCENARIO_FIELDS)
                                if row['name'] not in ('bear', 'base', 'bull'):
                                    raise ValueError('シナリオ名はbear/base/bullです')
                                iso(row['as_of'], 'as_of')
                                for field in SCENARIO_FIELDS:
                                    row[field] = numeric(row[field], field)
                                years = Decimal(row['horizon_years'])
                                if years != years.to_integral_value() or not 1 <= years <= 30:
                                    raise ValueError('horizon_yearsは1〜30の整数です')
                                row['horizon_years'] = int(years)
                                # Full parameter validation also occurs in the calculator.
                            else:
                                required(row, 'source_id', 'public_at', 'locator')
                                iso(row['public_at'], 'public_at')
                                status = row.get('quality_status') or 'pending'
                                if status not in QUALITY:
                                    raise ValueError('quality_statusが不正です')
                                row['quality_status'] = status
                                if kind == 'facts':
                                    required(row, 'metric', 'unit', 'period_end', 'fact_kind', 'consolidation')
                                    if row['metric'] not in LABELS or row['fact_kind'] not in FACT_KINDS:
                                        raise ValueError('metric/fact_kindが対応範囲外です')
                                    iso(row['period_end'], 'period_end')
                                    if row['consolidation'] not in ('consolidated', 'standalone'):
                                        raise ValueError('連結/単体を明記してください')
                                    metric = row['metric']
                                    if metric in FLOW:
                                        required(row, 'period_start')
                                        iso(row['period_start'], 'period_start')
                                        duration = (day(row['period_end']) - day(row['period_start'])).days
                                        if duration < 330 or duration > 380:
                                            raise ValueError('初版のCF計算は通期330〜380日だけ対応しています')
                                    if metric in MONEY and (row.get('currency') != 'JPY' or row['unit'] != 'JPY'):
                                        raise ValueError('金額は円単位のJPYにそろえてください（百万円は換算）')
                                    if metric == 'shares_diluted' and row['unit'] != 'shares' or metric == 'owner_ratio' and row['unit'] != 'ratio':
                                        raise ValueError('株数はshares、保有比率はratioです')
                                    value = row.get('value', '')
                                    if value:
                                        row['value'] = numeric(value, metric, positive=metric == 'shares_diluted',
                                                               nonnegative=metric not in {'ebit', 'delta_nwc', 'operating_cfo'})
                                        if metric in MONEY | {'shares_diluted'} and Decimal(row['value']) != Decimal(row['value']).to_integral_value():
                                            raise ValueError('円・株数は整数単位で入力してください')
                                        if metric == 'owner_ratio' and Decimal(row['value']) > 1:
                                            raise ValueError('保有比率は0〜1です')
                                    else:
                                        required(row, 'missing_reason')
                                        row['value'] = None
                                        row['quality_status'] = 'missing'
                                    if metric == 'shares_diluted' and not row.get('share_basis'):
                                        row['quality_status'] = 'pending'
                                        row['missing_reason'] = 'missing_basis'
                                elif kind == 'prices':
                                    required(row, 'value', 'currency', 'price_at', 'price_type', 'adjustment')
                                    row['value'] = numeric(row['value'], '株価', positive=True)
                                    iso(row['price_at'], 'price_at')
                                    if row['currency'] != 'JPY' or row['price_type'] not in ('close', 'reference') or row['adjustment'] != 'unadjusted':
                                        raise ValueError('初版はJPYのclose/reference・未調整価格unadjustedのみ対応です')
                                    if not row.get('share_basis'):
                                        row['quality_status'] = 'pending'
                                elif kind == 'events':
                                    required(row, 'event_type', 'status', 'announced_at')
                                    if row['event_type'] not in EVENT_TYPES or row['status'] not in EVENT_STATUS:
                                        raise ValueError('event_type/statusが不正です')
                                    iso(row['announced_at'], 'announced_at')
                                elif kind in ('assessments', 'reviews'):
                                    from .assessment import validate_assessment, validate_review
                                    required(row, 'state', 'as_of', 'reviewer')
                                    iso(row['as_of'], 'as_of')
                                    if kind == 'assessments':
                                        required(row, 'dimension', 'factor_id', 'evidence_type', 'speaker', 'interpretation', 'valid_until')
                                        iso(row['valid_until'], 'valid_until')
                                        validate_assessment(row)
                                    else:
                                        required(row, 'reason', 'next_review_at')
                                        iso(row['next_review_at'], 'next_review_at')
                                        validate_review(row)
                        if kind not in ('documents', 'scenarios'):
                            doc = docs.get(row['source_id'])
                            if doc is None:
                                raise ValueError('source_idに対応するdocuments.csvの行がありません')
                            row['document_id'] = doc['document_id']
                            if kind == 'securities':
                                row['public_at'] = doc['published_at']
                            if day(row['public_at']) < day(doc['published_at']):
                                raise ValueError('public_atを原本の公表日より前にできません')
                            if (len(row['public_at']) > 10 and len(doc['published_at']) > 10
                                    and instant(row['public_at']) < instant(doc['published_at'])):
                                raise ValueError('public_atを原本の公表時刻より前にできません')
                            if not doc.get('sha256') and row.get('quality_status') == 'verified':
                                row['quality_status'] = 'pending'
                                row['missing_reason'] = 'missing_source_bytes'
                        row['observed_at'] = stamp
                        row['ready_at'] = stamp
                        # Do not allow arbitrary CSV columns into the read API.
                        allowed = set(HEADERS[kind]) | {'key', 'security_id', 'document_id', 'sha256', 'raw_relpath',
                                  'filename', 'observed_at', 'ready_at', 'missing_reason', 'public_at'}
                        row = {k: v for k, v in row.items() if k in allowed}
                        prepared[kind].append(row)
                    except (ValueError, OSError) as exc:
                        errors.append(f'{kind}.csv {line}行: {exc}')
            if errors:
                raise ValueError('\n'.join(errors[:30]))
            input_hash = digest(encode({'files': hashes, 'mapping_version': 1, 'demo': demo}))
            counts = {k: len(v) for k, v in prepared.items()}
            if conn and conn.execute('SELECT 1 FROM import_batch WHERE input_hash=?', (input_hash,)).fetchone():
                return {'status': 'duplicate', 'input_hash': input_hash, 'counts': counts}
            validate_corrections(prepared, conn)
            if dry_run:
                return {'status': 'preview', 'input_hash': input_hash, 'counts': counts, 'errors': []}
            if conn is not None:
                conn.close()
            conn = connection(base, create=True)
            import_id = 'imp-' + uuid.uuid4().hex
            for relative, content in raw.items():
                path = base / relative
                if path.exists():
                    if digest(read_input(path)) != digest(content):
                        raise RuntimeError('保存済み原本のハッシュが一致しません')
                else:
                    atomic(path, content)
            with conn:
                conn.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)', ('demo', str(int(demo))))
                conn.execute('INSERT INTO import_batch VALUES (?,?,?,?,?)', (import_id, input_hash, stamp, json.dumps(counts), int(demo)))
                for kind, rows in prepared.items():
                    for row in rows:
                        rid = 'rec-' + uuid.uuid4().hex
                        row['record_id'] = rid
                        conn.execute('INSERT INTO record VALUES (?,?,?,?)', (rid, kind, import_id, encode(row).decode()))
            manifest = {'schema_version': 1, 'import_id': import_id, 'input_hash': input_hash,
                        'files': hashes, 'observed_at': stamp, 'counts': counts, 'demo': demo}
            atomic(base / 'imports' / import_id / 'manifest.json', encode(manifest))
            return {'status': 'imported', **manifest}
        finally:
            if conn:
                conn.close()


def record_time(row):
    public = row.get('public_at') or row.get('as_of') or row.get('published_at')
    first = instant(public)
    return first, instant(row['observed_at']) if row.get('observed_at') else first


def latest(rows, key):
    selected = {}
    for row in rows:
        grouping = key(row)
        if grouping not in selected or record_time(row) >= record_time(selected[grouping]):
            selected[grouping] = row
    return list(selected.values())


def visible(row, as_of):
    cutoff = instant(as_of)
    # Never backdate actual acquisition/review. Historical frozen runs are the
    # reference for what was known then; later imports cannot recreate that state.
    timestamps = [row.get('public_at', row.get('as_of', row.get('published_at'))),
                  row.get('observed_at'), row.get('ready_at')]
    return all(value is None or instant(value) <= cutoff for value in timestamps)


def _fact_set(rows, as_of):
    """Actual operating facts; an explicit analyst surplus-cash bridge is separate.

    Excess cash is not an accounting line. It can use a reviewed own_scenario
    anchored to the same balance-sheet date/scope. Explicit share roll-forwards
    remain estimates and preserve their reported anchor. Operating forecasts
    never replace historical cash-flow inputs.
    """
    available = [r for r in rows if r['fact_kind'] == 'actual'
                 and day(r['period_end']) <= day(as_of) and visible(r, as_of)]
    if not available:
        return {}, []
    # Choose a financial statement's period, not a newer ownership/stock-count-only update.
    anchor = [r for r in available if r['metric'] == 'ebit'] or [r for r in available if r['metric'] in MONEY] or available
    period = max(day(r['period_end']) for r in anchor)
    scope = 'consolidated' if any(r['consolidation'] == 'consolidated' and day(r['period_end']) == period for r in anchor) else 'standalone'
    balance_metrics = ('cash_and_equivalents', 'debt', 'noncontrolling_interest', 'excess_cash')
    balances = [r for r in available if r['metric'] in balance_metrics and r['consolidation'] == scope]
    balance_period = max((day(r['period_end']) for r in balances), default=period)
    point_metrics = ('shares_diluted', 'owner_ratio', *balance_metrics)
    selected = latest([r for r in available if day(r['period_end']) == period
                       and r['consolidation'] == scope and r['metric'] not in point_metrics], lambda r: r['metric'])
    # Share count and ownership describe a point in time, not an annual flow.
    # A later issuance/repurchase must not be discarded because EBIT is annual.
    for metric in point_metrics:
        candidates = [r for r in available if r['metric'] == metric
                      and (metric not in balance_metrics or
                           (r['consolidation'] == scope and day(r['period_end']) == balance_period))]
        if candidates:
            selected.append(max(candidates, key=lambda r: (day(r['period_end']), *record_time(r))))
    # Preserve the analyst classification rather than calling all cash surplus
    # or misclassifying an operating reserve as a reported company fact.
    if not any(r['metric'] == 'excess_cash' for r in selected):
        adjustments = [r for r in rows if r['metric'] == 'excess_cash'
                       and r['fact_kind'] == 'own_scenario'
                       and day(r['period_end']) == balance_period
                       and r['consolidation'] == scope and visible(r, as_of)]
        if adjustments:
            selected.append(max(adjustments, key=record_time))
    # An explicitly reviewed roll-forward may reflect announced treasury-share
    # changes after the last report. Keep it labelled as an estimate.
    reported_shares = [r for r in selected if r['metric'] == 'shares_diluted']
    share_date = max((day(r['period_end']) for r in reported_shares), default=period)
    share_adjustments = [r for r in rows if r['metric'] == 'shares_diluted'
                         and r['fact_kind'] == 'own_scenario'
                         and share_date <= day(r['period_end']) <= day(as_of) and visible(r, as_of)]
    if share_adjustments:
        adjustment = max(share_adjustments, key=lambda r: (day(r['period_end']), *record_time(r)))
        if not reported_shares or not any(r['quality_status'] == 'verified' for r in reported_shares):
            adjustment = {**adjustment, 'quality_status': 'pending', 'missing_reason': '推計の起点となる実績株数が未確認'}
        selected.append(adjustment)
    result = {}
    for original in selected:
        row = dict(original)
        row_period = day(row['period_end'])
        peers = [r for r in [*available, *[a for a in rows if a['fact_kind'] == 'own_scenario' and visible(a, as_of)]]
                 if r['metric'] == row['metric'] and r['fact_kind'] == row['fact_kind'] and day(r['period_end']) == row_period
                 and (r['metric'] in ('shares_diluted', 'owner_ratio') or r['consolidation'] == scope)
                 and instant(r['public_at']) == instant(row['public_at']) and r['quality_status'] == 'verified']
        signatures = {(Decimal(r['value']) if r['value'] is not None else None,
                       r.get('unit'), r.get('currency'), r.get('share_basis') if r['metric'] == 'shares_diluted' else None)
                      for r in peers}
        if len(signatures) > 1:
            row.update(quality_status='conflicting', missing_reason='同時点の資料に値の衝突')
        if (day(as_of) - row_period).days > 548:
            row.update(quality_status='pending', missing_reason='財務基準日が548日超前')
        # FCFF components must cover the same fiscal year.
        if row['metric'] in FLOW:
            starts = {day(r['period_start']) for r in selected if r['metric'] in FLOW}
            if len(starts) > 1:
                row.update(quality_status='pending', missing_reason='会計期間不一致')
        result[row['metric']] = row
    return result, selected


def identify(company):
    return {k: company[k] for k in ('security_id', 'code', 'name')}


def compare(previous, companies):
    before = {c['security_id']: c for c in (previous or {}).get('companies', []) if c['status'] != 'event'}
    after = {c['security_id']: c for c in companies if c['status'] != 'event'}
    changes = []
    for sid in after.keys() & before.keys():
        old, new = before[sid], after[sid]
        messages = []
        for key, label in [('price', '株価・価格日'), ('valuation', '価値・シナリオ'), ('missing', '不足情報'),
                           ('priority', '旧ルールの参考値'), ('mbo_assessment', 'MBOの論点・作業判断'),
                           ('reasons', '候補の根拠'), ('facts', '確認した財務値')]:
            if old.get(key) != new.get(key):
                messages.append(label + 'が変化')
        if messages:
            changes.append({**identify(new), 'changes': messages})
    added = [identify(after[sid]) for sid in after.keys() - before.keys()]
    removed = [identify(before[sid]) for sid in before.keys() - after.keys()]
    return {'previous_run_id': (previous or {}).get('run_id'), 'added': sorted(added, key=lambda r: r['code']),
            'removed': sorted(removed, key=lambda r: r['code']), 'changed': sorted(changes, key=lambda r: r['code']),
            'summary': f'候補追加{len(added)}件・候補から移動{len(removed)}件・変化{len(changes)}件'}


def build(as_of, data_dir=DEFAULT_DATA_DIR):
    from .valuation import evaluate
    from .assessment import evaluate_assessment
    iso(as_of, 'as_of')
    if len(as_of) != 10 or day(as_of) > day(now()):
        raise ValueError('as_ofは今日以前の日付にしてください')
    with writer(data_dir) as base:
        attempt = {'status': 'running', 'as_of': as_of, 'started_at': now()}
        atomic(base / 'last_attempt.json', encode(attempt))
        conn = None
        try:
            if not (base / 'state.sqlite').exists():
                raise FileNotFoundError('MBOデータが未初期化です')
            conn = connection(base, create=True)
            all_rows = {kind: records(conn, kind) for kind in KINDS}
            rows = {kind: [r for r in entries if visible(r, as_of)] for kind, entries in all_rows.items()}
            input_rows = rows
            rows = {kind: active_records(entries) if kind in CORRECTABLE else entries
                    for kind, entries in rows.items()}
            # Membership is effective on as_of. An older dated list imported
            # from a newer publication must not undo a later inclusion/removal.
            security_rows = sorted((r for r in rows['securities'] if day(r['as_of']) <= day(as_of)),
                                   key=lambda r: (instant(r['as_of']), *record_time(r)))
            securities = list({r['security_id']: r for r in security_rows}.values())
            securities = [r for r in securities if r['included']]
            docs = {r['document_id']: r for r in rows['documents']}
            for doc in docs.values():
                if doc.get('raw_relpath'):
                    if digest(read_input(base / doc['raw_relpath'])) != doc['sha256']:
                        raise RuntimeError('原本が変更されています。更新を停止しました')
            previous = read_snapshot(base) if (base / 'published/current.json').exists() else None
            if previous and as_of < previous['as_of']:
                raise ValueError('最新runより古い日付へcurrentを巻き戻せません。履歴は既存runを選んでください')
            demo_row = conn.execute("SELECT value FROM metadata WHERE key='demo'").fetchone()
            demo = bool(demo_row and int(demo_row[0]))
            companies, events = [], []
            for sec in securities:
                sid = sec['security_id']
                source_facts = [r for r in rows['facts'] if r['security_id'] == sid]
                facts, selected_facts = _fact_set(source_facts, as_of)
                reported_shares = [r for r in selected_facts if r['metric'] == 'shares_diluted' and r['fact_kind'] == 'actual'] \
                    if facts.get('shares_diluted', {}).get('fact_kind') == 'own_scenario' else []
                prices = [r for r in rows['prices'] if r['security_id'] == sid and day(r['price_at']) <= day(as_of)]
                price = max(prices, key=lambda r: (instant(r['price_at']), *record_time(r)), default=None)
                if price:
                    peers = [r for r in prices if instant(r['price_at']) == instant(price['price_at'])
                             and instant(r['public_at']) == instant(price['public_at']) and r['quality_status'] == 'verified']
                    if len({(Decimal(r['value']), r.get('share_basis'), r['currency']) for r in peers}) > 1:
                        price = {**price, 'quality_status': 'conflicting', 'missing_reason': '同時点の価格・株式基準に衝突'}
                selected_scenarios = latest([r for r in rows['scenarios'] if r['security_id'] == sid], lambda r: r['name'])
                event_history = [r for r in rows['events'] if r['security_id'] == sid]
                company_events = latest(event_history, lambda r: r['event_type'])
                event_rows = [{**identify(sec), **{k: r[k] for k in ('event_type', 'status', 'announced_at', 'source_id')}} for r in company_events]
                events.extend(event_rows)
                valuation = evaluate(facts, selected_scenarios, price, as_of)
                assessments = [r for r in rows['assessments'] if r['security_id'] == sid]
                reviews = [r for r in rows['reviews'] if r['security_id'] == sid]
                mbo_assessment = evaluate_assessment(facts, valuation, assessments, reviews, event_history, as_of)
                reasons, missing, priority = [], [], 0
                def value(metric):
                    fact = facts.get(metric)
                    return Decimal(fact['value']) if fact and fact['quality_status'] == 'verified' and fact['value'] is not None else None
                owner = value('owner_ratio')
                if owner is not None and owner >= Decimal('.2'):
                    priority += 2
                    reasons.append('確認済み経営陣・創業家保有比率20%以上（構造条件）')
                cfo, capex = value('operating_cfo'), value('capex')
                if cfo is not None and capex is not None and cfo - capex > 0:
                    priority += 1
                    reasons.append('営業CF−設備投資が正（探索用の代理指標）')
                cash, debt = value('excess_cash'), value('debt')
                if cash is not None and debt is not None and cash > debt:
                    priority += 1
                    reasons.append('余剰現金が有利子負債を上回る' +
                                   ('（運転必要額を控除した独自仮定）' if facts['excess_cash']['fact_kind'] == 'own_scenario' else '（確認済み入力）'))
                for scenario in selected_scenarios:
                    if scenario['name'] == 'base' and scenario.get('note'):
                        reasons.append('調査メモ：' + scenario['note'])
                for metric in ('ebit', 'depreciation', 'capex', 'delta_nwc', 'excess_cash', 'debt', 'noncontrolling_interest', 'shares_diluted', 'owner_ratio'):
                    fact = facts.get(metric)
                    if fact is None or fact.get('quality_status') != 'verified' or fact.get('value') is None:
                        missing.append(LABELS[metric] + '：' + (fact or {}).get('missing_reason', '未取込・未確認'))
                if not price:
                    missing.append('株価未入力：割安率は未計算')
                for group in (valuation['standalone'], valuation['discount_to_base'], valuation['lbo']):
                    missing.extend(group.get('reasons', []))
                discount = valuation['discount_to_base']
                if discount['status'] == 'ok' and Decimal(discount['value']) > 0:
                    reasons.append('基本シナリオの単独継続価値を株価が下回る（独自仮定）')
                if not reasons:
                    reasons.append('登録済み・調査待ち。根拠の追加により選別する')
                has_event = bool(event_rows)  # Withdrawn transactions remain in event research, not new discoveries.
                status = 'event' if has_event else ('ready' if discount['status'] == 'ok' else 'pending')
                used = [*facts.values(), *reported_shares, *([price] if price else []), *company_events, *assessments, *reviews, sec]
                evidence = []
                seen = set()
                for item in used:
                    doc = docs.get(item.get('document_id'))
                    key = (item.get('document_id'), item.get('locator', ''))
                    if doc and key not in seen:
                        seen.add(key)
                        evidence.append({k: doc.get(k) for k in ('document_id', 'source_id', 'title', 'filename', 'source_url', 'published_at', 'sha256')}
                                        | {'locator': item.get('locator', '銘柄一覧'), 'quality_status': item.get('quality_status', 'pending')})
                fact_dtos = []
                for r in [*facts.values(), *reported_shares]:
                    fact_dtos.append({k: r.get(k) for k in ('record_id', 'metric', 'value', 'unit', 'currency', 'period_start', 'period_end', 'fact_kind',
                                      'consolidation', 'share_basis', 'public_at', 'observed_at', 'ready_at', 'quality_status', 'source_id', 'locator', 'missing_reason', 'supersedes', 'correction_reason')}
                                     | {'label': LABELS[r['metric']]})
                price_dto = {k: price.get(k) for k in ('record_id', 'value', 'currency', 'price_at', 'price_type', 'adjustment', 'share_basis', 'quality_status', 'source_id', 'supersedes', 'correction_reason')} if price else None
                companies.append({**identify(sec), 'exchange': sec['exchange'], 'status': status, 'priority': priority,
                                  'reasons': reasons, 'missing': list(dict.fromkeys(missing)), 'facts': fact_dtos, 'price': price_dto,
                                  'mbo_assessment': mbo_assessment,
                                  'valuation': valuation, 'evidence': evidence, 'events': event_rows, 'review_notes': [], 'is_new': False})
            run_id = 'run-' + as_of + '-' + uuid.uuid4().hex[:12]
            diff = compare(previous, companies)
            new_ids = {r['security_id'] for r in diff['added']}
            for company in companies:
                company['is_new'] = company['security_id'] in new_ids
            coverage = {'universe': len(companies), 'prices': sum(c['price'] is not None for c in companies),
                        'valued': sum(c['valuation']['discount_to_base']['status'] == 'ok' for c in companies),
                        'pending': sum(c['status'] == 'pending' for c in companies), 'events': sum(c['status'] == 'event' for c in companies)}
            input_ids = sorted(r['record_id'] for entries in input_rows.values() for r in entries)
            input_hash = digest(encode({'ids': input_ids, 'rule_version': RULE_VERSION, 'as_of': as_of}))
            created = now()
            snapshot = {'schema_version': 1, 'run_id': run_id, 'as_of': as_of, 'created_at': created,
                        'demo': demo, 'source_scope': 'imported_universe', 'coverage': coverage, 'companies': companies,
                        'events': events, 'diff': diff, 'rule_version': RULE_VERSION,
                        'retrospective': day(as_of) < day(created), 'network_mode': 'offline', 'paid_provider_requests': 0}
            run_summary = {k: snapshot[k] for k in ('schema_version', 'run_id', 'as_of', 'created_at', 'demo', 'coverage', 'rule_version', 'retrospective')}
            run_summary.update(status='success', input_hash=input_hash)
            snapshot_bytes = encode(snapshot)
            if len(snapshot_bytes) > MAX_FILE:
                raise ValueError('表示結果が32MiBを超えました。対象集合を小さく分けてください')
            # Result and input IDs are immutable. The only replaced published file is current.json.
            atomic(base / 'runs' / run_id / 'manifest.json', encode({**run_summary, 'input_ids': input_ids, 'network_mode': 'offline', 'paid_provider_requests': 0}))
            atomic(base / 'published' / run_id / 'snapshot.json', snapshot_bytes)
            with conn:
                conn.execute('INSERT INTO run VALUES (?,?,?,?,?)', (run_id, as_of, created, input_hash, encode(run_summary).decode()))
            atomic(base / 'published/current.json', encode({'run_id': run_id}))
            atomic(base / 'last_attempt.json', encode({**attempt, 'status': 'success', 'run_id': run_id, 'finished_at': now()}))
            return run_summary | {'diff': diff}
        except Exception:
            atomic(base / 'last_attempt.json', encode({**attempt, 'status': 'failed', 'finished_at': now(),
                                                     'error': '更新に失敗しました。最後の成功結果を保持しています。CLIで入力を確認してください。'}))
            raise
        finally:
            if conn:
                conn.close()


def load_json(path):
    content = read_input(path)
    return json.loads(content, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('有限でないJSON値')))


def read_status(data_dir=DEFAULT_DATA_DIR):
    base = reject_symlinks(data_dir)
    pointer = load_json(base / 'published/current.json') if (base / 'published/current.json').exists() else {}
    attempt = load_json(base / 'last_attempt.json') if (base / 'last_attempt.json').exists() else None
    return {'schema_version': 1, 'mode': 'mbo-local', 'offline': True,
            'storage_state': 'ready' if pointer else 'empty', 'latest_success_run_id': pointer.get('run_id'), 'last_attempt': attempt,
            'edinet': {'configured': 'unknown', 'collection_enabled': False},
            'features': {'file_import_cli': True, 'http_write': False, 'llm': False, 'cloud': False}}


def read_snapshot(data_dir=DEFAULT_DATA_DIR, run_id=None):
    base = reject_symlinks(data_dir)
    if run_id in (None, 'latest'):
        run_id = load_json(base / 'published/current.json')['run_id']
    safe_id(run_id)
    payload = load_json(base / 'published' / run_id / 'snapshot.json')
    if payload.get('schema_version') != 1:
        raise RuntimeError('対応していない公開データ版です')
    return payload


def read_runs(data_dir=DEFAULT_DATA_DIR):
    base = reject_symlinks(data_dir)
    if not (base / 'state.sqlite').exists():
        return {'schema_version': 1, 'items': [], 'total': 0}
    conn = connection(base)
    try:
        result = [json.loads(row[0]) for row in conn.execute('SELECT summary FROM run ORDER BY created_at DESC')]
        # A DB entry alone cannot expose an incomplete publication.
        result = [r for r in result if (base / 'published' / r['run_id'] / 'snapshot.json').is_file()]
        return {'schema_version': 1, 'items': result, 'total': len(result)}
    finally:
        conn.close()


def locate(document_id, data_dir=DEFAULT_DATA_DIR):
    safe_id(document_id)
    base = reject_symlinks(data_dir)
    conn = connection(base)
    try:
        document = next((r for r in records(conn, 'documents') if r['document_id'] == document_id), None)
        if not document or not document.get('raw_relpath'):
            raise FileNotFoundError('原本が未保存です')
        path = base / document['raw_relpath']
        if digest(read_input(path)) != document['sha256']:
            raise RuntimeError('原本ハッシュが一致しません')
        return str(path)
    finally:
        conn.close()


def backup(destination, data_dir=DEFAULT_DATA_DIR):
    with writer(data_dir) as base:
        destination = reject_symlinks(destination)
        if destination == base or base in destination.parents:
            raise ValueError('バックアップ先はデータ保存先の外に指定してください')
        destination = private_dir(destination)
        if list(destination.iterdir()):
            raise ValueError('バックアップ先には空の新規フォルダを指定してください')
        source = connection(base)
        target_path = destination / 'state.sqlite'
        target = sqlite3.connect(target_path)
        try:
            os.chmod(target_path, 0o600)
            source.backup(target)
        finally:
            target.close()
            source.close()
        hashes = {'state.sqlite': digest(read_input(target_path))}
        for folder in ('raw', 'imports', 'runs', 'published'):
            for path in sorted((base / folder).rglob('*')):
                if path.is_file():
                    content = read_input(path)
                    relative = path.relative_to(base)
                    atomic(destination / relative, content)
                    hashes[str(relative)] = digest(content)
        atomic(destination / 'backup-manifest.json', encode({'created_at': now(), 'schema_version': 1, 'sha256': hashes}))
        return {'status': 'backed_up', 'files': len(hashes)}
