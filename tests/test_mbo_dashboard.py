"""Read-only local/cloud MBO browsing, using fictional data only."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
import json
import subprocess
import sys
import unittest

from backend.mbo_dashboard import MboDashboard, QueryError, UNAVAILABLE, sanitize_bundle


def frozen():
    def company(identifier, name, state, priority, discount):
        return {'security_id': identifier, 'code': identifier, 'name': name,
                'exchange': 'TSE', 'status': state, 'priority': priority,
                'reasons': ['確認済みの条件'], 'missing': [], 'is_new': False,
                'facts': [], 'price': None, 'evidence': [], 'events': [],
                'valuation': {'discount_to_base': {
                    'status': 'ok' if discount is not None else 'pending', 'value': discount,
                    'reasons': []}, 'standalone': {'status': 'pending', 'scenarios': []},
                    'lbo': {'status': 'pending', 'max_price_per_share': None, 'reasons': []}}}
    return {'schema_version': 1, 'run_id': 'run-001', 'as_of': '2026-10-18',
            'created_at': '2026-10-18T12:00:00+09:00', 'demo': True,
            'source_scope': 'imported_universe', 'rule_version': 'mbo-1', 'retrospective': False,
            'coverage': {'universe': 4, 'prices': 2, 'valued': 2, 'pending': 1, 'events': 1},
            'companies': [company('sec-a', 'Alpha', 'ready', 5, '.30'),
                          company('sec-b', 'Beta', 'ready', 10, '-.10'),
                          company('sec-c', 'Gamma', 'pending', 1, None),
                          company('sec-d', 'Deal', 'event', 99, '.90')],
            'events': [{'security_id': 'sec-d', 'code': '1234', 'name': 'Deal',
                        'event_type': 'mbo', 'status': 'withdrawn',
                        'announced_at': '2026-10-01', 'source_id': 'source-a'}],
            'diff': {'previous_run_id': None, 'added': [], 'removed': [], 'changed': [], 'summary': '初回'}}


def cloud_payload(snapshot=None):
    snapshot = snapshot or frozen()
    summary = {key: deepcopy(snapshot[key]) for key in (
        'schema_version', 'run_id', 'as_of', 'created_at', 'demo', 'coverage', 'rule_version', 'retrospective')}
    summary['status'] = 'success'
    return {'schema_version': 1, 'runs': [summary], 'snapshots': {'run-001': snapshot},
            'latest_run_id': 'run-001', 'last_attempt': None}


class MboDashboardCloudTests(unittest.TestCase):
    def setUp(self):
        self.payload = cloud_payload()
        self.document = Mock()
        self.document.read.return_value = self.payload, 123
        self.dashboard = MboDashboard(Path('/must-never-read-local'), document=self.document)
        self.local = patch.object(self.dashboard, '_local_read', side_effect=AssertionError('local read'))
        self.local_read = self.local.start()
        self.addCleanup(self.local.stop)

    def test_cloud_status_and_latest_run_and_read_only_document(self):
        status = self.dashboard.response('/api/mbo/status', {})
        self.assertEqual(status['mode'], 'mbo-dashboard')
        self.assertFalse(status['offline'])
        self.assertFalse(status['features']['http_write'])
        self.assertFalse(status['features']['file_import_cli'])
        self.assertTrue(status['features']['cloud'])
        candidates = self.dashboard.response('/api/mbo/candidates', {})
        self.assertEqual(candidates['run_id'], 'run-001')
        self.assertEqual(candidates['total'], 3)
        self.assertEqual(candidates['source_scope'], 'imported_universe')
        self.document.read.assert_called_once_with()
        self.document.write.assert_not_called()
        self.local_read.assert_not_called()

    def test_selection_is_stable_paged_and_excludes_all_announced_events(self):
        page = self.dashboard.response('/api/mbo/candidates', {'limit': '1', 'offset': '1'})
        self.assertEqual(page['total'], 3)
        self.assertEqual(page['items'][0]['security_id'], 'sec-a')
        for order, expected in [('priority', ['sec-b', 'sec-a', 'sec-c']),
                                ('discount', ['sec-a', 'sec-b', 'sec-c']),
                                ('name', ['sec-a', 'sec-b', 'sec-c'])]:
            with self.subTest(order=order):
                response = self.dashboard.response('/api/mbo/candidates', {'sort': order})
                self.assertEqual([x['security_id'] for x in response['items']], expected)
        self.assertEqual(self.dashboard.response('/api/mbo/candidates', {'q': 'ALPHA'})['total'], 1)
        self.assertEqual(self.dashboard.response('/api/mbo/candidates', {'status': 'pending'})['total'], 1)
        self.assertEqual(self.dashboard.response('/api/mbo/candidates', {'status': 'event'})['total'], 0)
        events = self.dashboard.response('/api/mbo/events', {'run_id': 'run-001'})
        self.assertEqual(events['items'][0]['status'], 'withdrawn')
        self.assertEqual(self.dashboard.response('/api/mbo/events', {'offset': '50'})['items'], [])

    def test_known_nested_fields_only_and_failure_detail_is_replaced(self):
        secret = '/private/SECRET-token-and-env'
        self.payload.update(raw={'path': secret}, env={'API_KEY': secret})
        self.payload['runs'][0].update(input_ids=[secret], raw_relpath=secret, input_hash=secret)
        self.payload['last_attempt'] = {'status': 'failed', 'as_of': '2026-10-18',
                                        'error': secret, 'traceback': secret, 'env': secret, 'raw_relpath': secret}
        snapshot = self.payload['snapshots']['run-001']
        snapshot.update(raw=secret, metadata={'path': secret})
        snapshot['diff']['path'] = secret
        snapshot['coverage']['raw'] = secret
        snapshot['events'][0]['raw'] = secret
        company = snapshot['companies'][0]
        company.update(raw=secret, review_notes=[secret], env=secret)
        company['facts'] = [{'metric': 'ebit', 'value': '123', 'label': 'EBIT', 'raw': secret}]
        company['evidence'] = [{'document_id': 'doc-a', 'title': '確認済み資料', 'raw_relpath': secret,
                                'filename': secret, 'source_url': 'https://example.com/doc?token=SECRET-token-and-env#SECRET-token-and-env'}]
        company['valuation']['lbo'].update(
            raw=secret, assumptions={'wacc': '0.1', 'env': secret},
            financing={'new_debt': '100', 'path': secret},
            yearly=[{'year': 1, 'ebit': '30', 'raw': secret}])
        responses = [self.dashboard.response('/api/mbo/' + path, {})
                     for path in ('status', 'runs', 'candidates', 'events', 'companies/sec-a')]
        result = json.dumps(responses, ensure_ascii=False)
        self.assertNotIn('SECRET-token-and-env', result)
        self.assertNotIn('raw_relpath', result)
        self.assertNotIn('input_hash', result)
        self.assertNotIn('review_notes', result)
        shown = responses[-1]['company']
        self.assertEqual(shown['facts'][0]['value'], '123')
        self.assertEqual(shown['valuation']['lbo']['financing'], {'new_debt': '100'})
        self.assertEqual(shown['evidence'][0]['source_url'], 'https://example.com/doc')
        self.assertIn('更新に失敗', responses[0]['last_attempt']['error'])

    def test_output_mutation_cannot_change_cached_snapshot_or_document(self):
        before = deepcopy(self.payload)
        first = self.dashboard.response('/api/mbo/companies/sec-a', {})
        first['company']['name'] = 'modified'
        first['company']['valuation']['discount_to_base']['value'] = '9999'
        again = self.dashboard.response('/api/mbo/companies/sec-a', {})
        self.assertEqual(again['company']['name'], 'Alpha')
        self.assertEqual(again['company']['valuation']['discount_to_base']['value'], '0.30')
        self.assertEqual(self.payload, before)

    def test_missing_price_remains_missing_without_computing_a_discount(self):
        row = self.dashboard.response('/api/mbo/companies/sec-c', {})['company']
        self.assertIsNone(row['price'])
        self.assertIsNone(row['valuation']['discount_to_base']['value'])
        self.assertEqual(row['valuation']['discount_to_base']['status'], 'pending')

    def test_infeasible_lbo_and_dcf_scenarios_are_displayable_with_null_prices(self):
        company = self.payload['snapshots']['run-001']['companies'][0]
        company['valuation']['lbo'] = {'status': 'infeasible', 'max_price_per_share': None,
                                      'reasons': ['目標IRRを満たす正の買収価格がない'], 'yearly': []}
        company['valuation']['standalone'] = {
            'status': 'infeasible', 'scenarios': [
                {'name': 'bear', 'status': 'infeasible', 'enterprise_value': '100',
                 'equity_value': '-10', 'value_per_share': None, 'reasons': ['株主残余が0以下']},
                {'name': 'base', 'status': 'infeasible', 'enterprise_value': '100',
                 'equity_value': '0', 'value_per_share': None, 'reasons': ['株主残余が0以下']}]}
        company['valuation']['discount_to_base'] = {'status': 'pending', 'value': None}
        shown = self.dashboard.response('/api/mbo/companies/sec-a', {})['company']['valuation']
        self.assertEqual(shown, company['valuation'])
        self.assertIsNone(shown['lbo']['max_price_per_share'])
        self.assertTrue(all(s['value_per_share'] is None for s in shown['standalone']['scenarios']))

    def test_public_bundle_sanitizer_is_pure_idempotent_and_explicitly_versioned(self):
        original = deepcopy(self.payload)
        result = sanitize_bundle(self.payload)
        self.assertEqual(result['schema_version'], 1)
        self.assertEqual(sanitize_bundle(result), result)
        result['snapshots']['run-001']['companies'][0]['name'] = 'changed'
        self.assertEqual(self.payload, original)
        self.assertEqual(sanitize_bundle({}), {'schema_version': 1, 'runs': [], 'snapshots': {},
                                             'latest_run_id': None, 'last_attempt': None})

    def test_cache_is_sixty_seconds_and_refresh_failure_is_generic(self):
        with patch('backend.mbo_dashboard.monotonic', return_value=100):
            self.dashboard.response('/api/mbo/status', {})
        with patch('backend.mbo_dashboard.monotonic', return_value=159.99):
            self.dashboard.response('/api/mbo/runs', {})
        self.assertEqual(self.document.read.call_count, 1)
        with patch('backend.mbo_dashboard.monotonic', return_value=160):
            self.dashboard.response('/api/mbo/status', {})
        self.assertEqual(self.document.read.call_count, 2)
        self.document.read.side_effect = OSError('/private/SECRET bucket token=SECRET')
        with patch('backend.mbo_dashboard.monotonic', return_value=221):
            with self.assertRaises(RuntimeError) as raised:
                self.dashboard.response('/api/mbo/status', {})
        self.assertEqual(str(raised.exception), UNAVAILABLE)
        self.assertTrue(raised.exception.__suppress_context__)

    def test_parallel_reads_share_a_single_document_fetch(self):
        with ThreadPoolExecutor(max_workers=12) as workers:
            results = list(workers.map(lambda _: self.dashboard.response('/api/mbo/candidates', {}), range(40)))
        self.assertTrue(all(result['run_id'] == 'run-001' for result in results))
        self.document.read.assert_called_once()

    def test_empty_cloud_document_is_cached_empty_status_not_local_fallback(self):
        self.document.read.return_value = {}, 0
        self.assertEqual(self.dashboard.response('/api/mbo/status', {})['storage_state'], 'empty')
        self.assertEqual(self.dashboard.response('/api/mbo/runs', {})['total'], 0)
        with self.assertRaises(FileNotFoundError):
            self.dashboard.response('/api/mbo/candidates', {})
        self.local_read.assert_not_called()
        self.document.read.assert_called_once()

    def test_bad_queries_fail_before_any_storage_access(self):
        cases = [('status', {'run_id': 'run-001'}), ('runs', {'limit': '201'}),
                 ('runs', {'limit': '0'}), ('runs', {'limit': True}),
                 ('runs', {'offset': '-1'}), ('runs', {'offset': '１'}),
                 ('runs', {'offset': '99999999999'}), ('candidates', {'q': 'x' * 101}),
                 ('candidates', {'sort': 'probability'}), ('candidates', {'status': 'unknown'}),
                 ('candidates', {'run_id': '../private'}), ('events', {'q': 'secret'}),
                 ('companies/../file', {}), ('companies/sec-a', {'offset': '0'})]
        for path, query in cases:
            with self.subTest(path=path, query=query), self.assertRaises(ValueError):
                self.dashboard.response('/api/mbo/' + path, query)
        self.document.read.assert_not_called()
        self.local_read.assert_not_called()

    def test_missing_run_company_or_endpoint_is_not_found(self):
        for path, query in [('candidates', {'run_id': 'unknown'}), ('companies/sec-unknown', {}),
                            ('raw', {}), ('companies', {})]:
            with self.subTest(path=path), self.assertRaises(FileNotFoundError):
                self.dashboard.response('/api/mbo/' + path, query)

    def test_invalid_cloud_shapes_and_mismatched_frozen_ids_fail_closed(self):
        malformed = []
        for change in (
            lambda p: p.update(schema_version=2),
            lambda p: p.update(schema_version=True),
            lambda p: p.update(latest_run_id='unknown'),
            lambda p: p['runs'][0].update(as_of='2026-10-17'),
            lambda p: p['runs'].clear(),
            lambda p: p['snapshots']['run-001'].update(run_id='run-other'),
            lambda p: p['snapshots']['run-001'].update(schema_version=2),
            lambda p: p['snapshots']['run-001'].update(schema_version=True),
            lambda p: p['snapshots']['run-001']['companies'].append(deepcopy(p['snapshots']['run-001']['companies'][0])),
            lambda p: p['snapshots']['run-001']['companies'][0].update(priority='Infinity'),
            lambda p: p['snapshots']['run-001']['companies'][0]['valuation']['discount_to_base'].update(value='NaN'),
            lambda p: p['snapshots']['run-001']['companies'][0].update(name={'raw': 'private'}),
        ):
            payload = cloud_payload()
            change(payload)
            malformed.append(payload)
        malformed.extend([[], {'schema_version': 1, 'runs': 'raw'},
                          {'schema_version': 1, 'snapshots': []}])
        for payload in malformed:
            with self.subTest(payload_type=type(payload).__name__):
                doc = Mock()
                doc.read.return_value = payload, 1
                dashboard = MboDashboard(document=doc)
                with self.assertRaisesRegex(RuntimeError, UNAVAILABLE):
                    dashboard.response('/api/mbo/status', {})

    def test_import_and_cloud_use_do_not_import_mbo_core_or_cloud_clients(self):
        source = '''
import sys
from backend.mbo_dashboard import MboDashboard
class Document:
    def read(self): return {}, 0
MboDashboard(document=Document()).response('/api/mbo/status', {})
assert 'backend.mbo' not in sys.modules
assert 'backend.mbo.core' not in sys.modules
assert 'google.auth' not in sys.modules
assert 'sqlite3' not in sys.modules
'''
        result = subprocess.run([sys.executable, '-c', source], cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


class MboDashboardLocalTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def hashes(self, root):
        return {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest()
                for path in root.rglob('*') if path.is_file()}

    def test_empty_local_does_not_initialize_directory_or_database(self):
        data_dir = self.root / 'never-created'
        dashboard = MboDashboard(data_dir)
        result = dashboard.response('/api/mbo/status', {})
        self.assertEqual(result['mode'], 'mbo-dashboard')
        self.assertTrue(result['offline'])
        self.assertEqual(result['storage_state'], 'empty')
        self.assertEqual(dashboard.response('/api/mbo/runs', {})['items'], [])
        with self.assertRaises(FileNotFoundError):
            dashboard.response('/api/mbo/candidates', {})
        self.assertFalse(data_dir.exists())

    def test_real_core_published_results_are_frozen_and_all_reads_leave_hashes_unchanged(self):
        from backend.mbo import core
        from backend.mbo.__main__ import demo
        data_dir = self.root / 'demo'
        demo(data_dir)
        dashboard = MboDashboard(data_dir)
        runs = core.read_runs(data_dir)['items']
        before = self.hashes(data_dir)
        with patch('backend.mbo.valuation.evaluate', side_effect=AssertionError('No calculation on GET')):
            for summary in runs:
                query = {'run_id': summary['run_id']}
                published = core.read_snapshot(data_dir, summary['run_id'])
                candidates = dashboard.response('/api/mbo/candidates', query)
                self.assertEqual(candidates['run_id'], summary['run_id'])
                self.assertEqual(candidates['coverage'], published['coverage'])
                expected = [c for c in published['companies'] if c['status'] != 'event']
                self.assertEqual(candidates['total'], len(expected))
                for company in published['companies']:
                    shown = dashboard.response('/api/mbo/companies/' + company['security_id'], query)['company']
                    self.assertEqual(shown['valuation'], company['valuation'])
                    self.assertEqual(shown['facts'], company['facts'])
                    self.assertEqual(shown['price'], company['price'])
                self.assertEqual(dashboard.response('/api/mbo/events', query)['items'], published['events'])
            first = dashboard.response('/api/mbo/runs', {'limit': '1', 'offset': '0'})
            second = dashboard.response('/api/mbo/runs', {'limit': '1', 'offset': '1'})
            self.assertEqual(first['total'], 2)
            self.assertNotEqual(first['items'][0]['run_id'], second['items'][0]['run_id'])
        self.assertEqual(self.hashes(data_dir), before)

    def test_local_internal_failure_is_generic_and_status_attempt_is_sanitized(self):
        dashboard = MboDashboard(self.root)
        with patch('backend.mbo.core.read_status', side_effect=ValueError('/private/SECRET')):
            with self.assertRaisesRegex(RuntimeError, UNAVAILABLE):
                dashboard.response('/api/mbo/status', {})
        with patch('backend.mbo.core.read_status', return_value={
                'latest_success_run_id': None, 'env': 'SECRET',
                'last_attempt': {'status': 'failed', 'error': '/private/SECRET', 'path': '/private/SECRET'}}):
            result = dashboard.response('/api/mbo/status', {})
        self.assertNotIn('SECRET', json.dumps(result))
        self.assertIn('更新に失敗', result['last_attempt']['error'])

    def test_decimal_values_are_json_safe_strings_and_pending_discount_is_never_invented(self):
        snapshot = frozen()
        snapshot['companies'][0]['valuation']['discount_to_base']['value'] = Decimal('.30')
        snapshot['companies'][2]['valuation']['discount_to_base']['value'] = Decimal('99')
        dashboard = MboDashboard(self.root)
        with patch('backend.mbo.core.read_snapshot', return_value=snapshot):
            shown = dashboard.response('/api/mbo/candidates', {})
        by_id = {x['security_id']: x for x in shown['items']}
        self.assertEqual(by_id['sec-a']['valuation']['discount_to_base']['value'], '0.30')
        self.assertIsNone(by_id['sec-c']['valuation']['discount_to_base']['value'])
        json.dumps(shown, allow_nan=False)


if __name__ == '__main__':
    unittest.main()
