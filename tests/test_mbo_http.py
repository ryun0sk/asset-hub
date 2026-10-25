import copy
from decimal import Decimal
import hashlib
import http.client
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from backend.mbo.http import API_CSP, MBO_CSP, MboServer


def frozen_snapshot():
    def company(identifier, name, state, priority, value):
        return {'security_id': identifier, 'code': identifier, 'name': name,
                'exchange': 'TSE', 'status': state, 'priority': priority,
                'reasons': [], 'missing': [], 'facts': [], 'evidence': [],
                'price': None, 'events': [], 'is_new': False,
                'valuation': {'discount_to_base': {
                    'status': 'ok' if value is not None else 'pending', 'value': value}}}
    return {
        'schema_version': 1, 'run_id': 'run-001', 'as_of': '2026-10-18', 'demo': True,
        'source_scope': 'imported_universe',
        'coverage': {'universe': 4, 'prices': 2, 'valued': 2, 'pending': 1, 'events': 1},
        'companies': [company('1001', 'Alpha', 'ready', 5, '0.30'),
                      company('1002', 'Beta', 'ready', 10, '-0.10'),
                      company('1003', 'Gamma', 'pending', 1, None),
                      company('1004', 'Announced', 'event', 99, '0.90')],
        'events': [{'security_id': '1004', 'event_type': 'mbo', 'status': 'announced'}],
        'diff': {'previous_run_id': None, 'added': [], 'removed': [], 'changed': [], 'summary': {}},
    }


class MboHTTPTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.web = self.root / 'web'
        self.web.mkdir()
        for name, content in {
            'mbo.html': '<!doctype html><title>MBO</title>',
            'mbo-app.js': 'console.log("MBO")', 'mbo.css': 'body{}',
            'mbo-cases.js': 'export const cases = true;',
            'mbo-case-data.js': 'export const snapshot = {};',
            'mbo-census.js': 'export const census = true;',
            'mbo-census-data.js': 'export const censusData = {};',
            'tokens.css': ':root{}', 'favicon.svg': '<svg/>',
            'app.js': 'PRIVATE EXISTING APP', 'assets.js': 'PRIVATE ASSETS',
            'index.html': 'PRIVATE EXISTING SHELL', 'notes.json': 'PRIVATE NOTES',
        }.items():
            (self.web / name).write_text(content, encoding='utf-8')
        self.data_dir = self.root / 'never-created'
        self.snapshot = frozen_snapshot()
        self.original = copy.deepcopy(self.snapshot)
        self.patches = [patch('backend.mbo.http.read_status'),
                        patch('backend.mbo.http.read_runs'),
                        patch('backend.mbo.http.read_snapshot')]
        self.status, self.runs, self.read = [item.start() for item in self.patches]
        self.status.return_value = {'schema_version': 1, 'mode': 'mbo-local',
                                    'offline': True, 'storage_state': 'empty',
                                    'latest_success_run_id': None}
        self.runs.return_value = {'schema_version': 1, 'items': [
            {'run_id': 'run-001'}, {'run_id': 'run-002'}], 'total': 2}
        def read(data_dir, run_id=None):
            if run_id not in (None, 'run-001'):
                raise FileNotFoundError('/private/DO_NOT_DISCLOSE')
            return self.snapshot
        self.read.side_effect = read
        self.server = MboServer(('127.0.0.1', 0), data_dir=self.data_dir, web_dir=self.web)
        self.port = self.server.server_port
        self.thread = threading.Thread(
            target=lambda: self.server.serve_forever(poll_interval=0.01), daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def request(self, path='/', method='GET', host='default', headers=()):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        connection.putrequest(method, path, skip_host=True)
        if host == 'default':
            host = f'127.0.0.1:{self.port}'
        if host is not None:
            connection.putheader('Host', host)
        for name, value in headers:
            connection.putheader(name, value)
        connection.endheaders()
        response = connection.getresponse()
        body = response.read()
        connection.close()
        return response, body

    def api(self, path, **kwargs):
        response, body = self.request(path, **kwargs)
        return response, json.loads(body) if body else None

    def test_empty_status_does_not_create_storage_or_request_other_data(self):
        response, data = self.api('/api/mbo/status')
        self.assertEqual(response.status, 200)
        self.assertEqual(data['storage_state'], 'empty')
        self.assertFalse(self.data_dir.exists())
        self.status.assert_called_once_with(self.data_dir)
        self.runs.assert_not_called()
        self.read.assert_not_called()

    def test_headers_and_head_are_read_only(self):
        response, body = self.request('/api/mbo/status')
        self.assertEqual(response.getheader('Content-Type'), 'application/json; charset=utf-8')
        self.assertEqual(response.getheader('Content-Security-Policy'), API_CSP)
        self.assertEqual(response.getheader('Cache-Control'), 'no-store')
        self.assertEqual(response.getheader('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.getheader('Referrer-Policy'), 'no-referrer')
        self.assertIsNone(response.getheader('Access-Control-Allow-Origin'))
        self.assertEqual(len(response.getheader('X-Request-ID')), 32)
        head, head_body = self.request('/api/mbo/status', method='HEAD')
        self.assertEqual(head.status, 200)
        self.assertEqual(head_body, b'')
        self.assertEqual(int(head.getheader('Content-Length')), len(body))

    def test_only_fixed_mbo_assets_are_served(self):
        for path in ('/', '/mbo.html', '/mbo-app.js', '/mbo-cases.js', '/mbo-case-data.js',
                     '/mbo-census.js', '/mbo-census-data.js',
                     '/mbo.css', '/tokens.css', '/favicon.svg'):
            with self.subTest(path=path):
                response, body = self.request(path)
                self.assertEqual(response.status, 200)
                self.assertEqual(response.getheader('Content-Security-Policy'), MBO_CSP)
                self.assertNotIn("'unsafe-inline'", MBO_CSP)
                head, head_body = self.request(path, method='HEAD')
                self.assertEqual(head_body, b'')
                self.assertEqual(int(head.getheader('Content-Length')), len(body))
        for path in ('/app.js', '/index.html', '/assets.js', '/notes.json', '/api/assets',
                     '/api/costs', '/api/catalog', '/research/report.md', '/data/private/state.sqlite',
                     '/../secret.txt', '/%2e%2e/secret.txt', '/api/mbo/raw/file.pdf',
                     '/web/mbo.html', '/sub/../mbo.html'):
            with self.subTest(path=path):
                response, body = self.request(path)
                self.assertEqual(response.status, 404)
                self.assertNotIn(b'PRIVATE', body)

    def test_missing_or_symlinked_allowlisted_asset_is_not_served(self):
        (self.web / 'favicon.svg').unlink()
        self.assertEqual(self.request('/favicon.svg')[0].status, 404)
        secret = self.root / 'secret.txt'
        secret.write_text('PRIVATE RAW DATA')
        (self.web / 'mbo.css').unlink()
        (self.web / 'mbo.css').symlink_to(secret)
        response, body = self.request('/mbo.css')
        self.assertEqual(response.status, 404)
        self.assertNotIn(b'PRIVATE', body)

    def test_host_must_be_unique_loopback_with_actual_port(self):
        for host in (None, 'localhost', '127.0.0.1', 'localhost:1', 'evil.example:4331',
                     f'127.0.0.1:{self.port}.evil.example', f'localhost:{self.port}@evil.example',
                     f'[::1]:{self.port}'):
            with self.subTest(host=host):
                self.assertEqual(self.request('/api/mbo/status', host=host)[0].status, 403)
        self.assertEqual(self.request('/api/mbo/status', headers=[
            ('Host', f'127.0.0.1:{self.port}')])[0].status, 403)
        self.status.assert_not_called()
        self.assertEqual(self.request('/api/mbo/status', host=f'localhost:{self.port}')[0].status, 200)

    def test_origin_and_fetch_metadata_reject_cross_origin_requests(self):
        for headers in ([('Origin', 'https://evil.example')], [('Origin', 'null')],
                        [('Origin', f'http://127.0.0.1:{self.port + 1}')],
                        [('Origin', f'https://127.0.0.1:{self.port}')],
                        [('Sec-Fetch-Site', 'cross-site')], [('Sec-Fetch-Site', 'same-site')],
                        [('Origin', f'http://127.0.0.1:{self.port}'),
                         ('Origin', f'http://127.0.0.1:{self.port}')]):
            with self.subTest(headers=headers):
                self.assertEqual(self.request('/api/mbo/status', headers=headers)[0].status, 403)
        self.status.assert_not_called()
        good = [('Origin', f'http://127.0.0.1:{self.port}'), ('Sec-Fetch-Site', 'same-origin')]
        self.assertEqual(self.request('/api/mbo/status', headers=good)[0].status, 200)

    def test_write_and_unknown_methods_are_405_without_core_access(self):
        for method in ('POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'TRACE', 'CONNECT', 'PROPFIND'):
            with self.subTest(method=method):
                response, body = self.request('/api/mbo/status', method=method)
                self.assertEqual(response.status, 405)
                self.assertEqual(response.getheader('Allow'), 'GET, HEAD')
                self.assertEqual(json.loads(body)['error']['code'], 'method_not_allowed')
        self.status.assert_not_called()
        self.read.assert_not_called()
        self.assertFalse(self.data_dir.exists())

    def test_candidates_sort_and_filter_without_mutating_frozen_snapshot(self):
        response, data = self.api('/api/mbo/candidates')
        self.assertEqual(response.status, 200)
        self.assertEqual(data['run_id'], 'run-001')
        self.assertEqual(data['source_scope'], 'imported_universe')
        self.assertEqual([item['code'] for item in data['items']], ['1002', '1001', '1003'])
        self.assertEqual(data['total'], 3)
        self.assertEqual(data['coverage']['universe'], 4)
        _, discounted = self.api('/api/mbo/candidates?sort=discount')
        self.assertEqual([item['code'] for item in discounted['items']], ['1001', '1002', '1003'])
        _, filtered = self.api('/api/mbo/candidates?status=ready&q=alpha')
        self.assertEqual([item['code'] for item in filtered['items']], ['1001'])
        _, pending = self.api('/api/mbo/candidates?status=pending')
        self.assertEqual([item['code'] for item in pending['items']], ['1003'])
        _, events = self.api('/api/mbo/candidates?status=event')
        self.assertEqual(events['items'], [])
        self.assertEqual(self.snapshot, self.original)

    def test_pagination_and_decimal_strings(self):
        self.snapshot['companies'][0]['valuation']['discount_to_base']['value'] = Decimal('0.3000')
        _, data = self.api('/api/mbo/candidates?sort=name&limit=1&offset=0')
        self.assertEqual(data['items'][0]['code'], '1001')
        self.assertEqual(data['items'][0]['valuation']['discount_to_base']['value'], '0.3000')
        self.assertEqual((data['limit'], data['offset'], data['total']), (1, 0, 3))
        _, data = self.api('/api/mbo/candidates?offset=9999')
        self.assertEqual(data['items'], [])
        _, runs = self.api('/api/mbo/runs?limit=1&offset=1')
        self.assertEqual(runs['items'], [{'run_id': 'run-002'}])
        self.assertEqual(runs['total'], 2)

    def test_company_and_events_keep_concrete_run_identity(self):
        self.snapshot['retrospective'] = True
        self.snapshot['network_mode'] = 'offline'
        response, company = self.api('/api/mbo/companies/1001?run_id=run-001')
        self.assertEqual(response.status, 200)
        self.assertEqual(company['company']['name'], 'Alpha')
        self.assertEqual(company['run_id'], 'run-001')
        self.assertTrue(company['retrospective'])
        self.assertEqual(company['network_mode'], 'offline')
        self.read.assert_called_with(self.data_dir, 'run-001')
        _, events = self.api('/api/mbo/events?run_id=latest&limit=1')
        self.assertEqual(events['items'], self.snapshot['events'])
        self.assertEqual(events['run_id'], 'run-001')
        self.read.assert_called_with(self.data_dir, None)
        self.assertEqual(self.api('/api/mbo/companies/missing')[0].status, 404)
        self.assertEqual(self.api('/api/mbo/candidates?run_id=missing')[0].status, 404)

    def test_invalid_queries_are_rejected_before_reading_core(self):
        paths = ['/api/mbo/candidates?run_id=../../private',
                 '/api/mbo/candidates?run_id=', '/api/mbo/candidates?run_id=%2fsecret',
                 '/api/mbo/candidates?run_id=' + 'a' * 101,
                 '/api/mbo/candidates?limit=201', '/api/mbo/candidates?limit=0',
                 '/api/mbo/candidates?offset=-1', '/api/mbo/candidates?offset=1.5',
                 '/api/mbo/candidates?status=verified', '/api/mbo/candidates?sort=random',
                 '/api/mbo/candidates?q=' + 'a' * 101,
                 '/api/mbo/candidates?limit=1&limit=2',
                 '/api/mbo/candidates?filename=secret', '/api/mbo/companies/%2e%2e',
                 '/api/mbo/status?run_id=latest', '/api/mbo/events?offset=-1']
        for path in paths:
            with self.subTest(path=path):
                response, data = self.api(path)
                self.assertEqual(response.status, 400)
                self.assertEqual(data['error']['code'], 'invalid_request')
        self.status.assert_not_called()
        self.read.assert_not_called()

    def test_data_failures_do_not_disclose_exception_text_or_paths(self):
        for error in (ValueError('/private/path SECRET'), RuntimeError('API_KEY=SECRET'),
                      OSError('internal SQL /private/path SECRET')):
            with self.subTest(error=type(error).__name__):
                self.read.side_effect = error
                response, body = self.request('/api/mbo/candidates')
                self.assertEqual(response.status, 503)
                payload = json.loads(body)
                self.assertTrue(payload['error']['retryable'])
                self.assertEqual(payload['error']['code'], 'unavailable')
                self.assertNotIn(b'SECRET', body)
                self.assertNotIn(b'/private/', body)
                self.assertEqual(payload['request_id'], response.getheader('X-Request-ID'))

    def test_specific_run_cannot_silently_resolve_to_another_snapshot(self):
        self.read.side_effect = None
        self.read.return_value = self.snapshot
        self.assertEqual(self.api('/api/mbo/candidates?run_id=run-other')[0].status, 503)

    def test_real_core_empty_readers_do_not_initialize_storage(self):
        from backend.mbo import core
        self.server.data_dir = self.data_dir.resolve()
        self.status.side_effect = core.read_status
        self.runs.side_effect = core.read_runs
        _, status = self.api('/api/mbo/status')
        _, runs = self.api('/api/mbo/runs')
        self.assertEqual(status['storage_state'], 'empty')
        self.assertEqual(runs['items'], [])
        self.assertFalse(self.data_dir.exists())

    def test_real_core_frozen_readers_preserve_files_and_run_identity(self):
        from backend.mbo import core
        base = self.data_dir.resolve()
        core.init(base)
        (base / 'published' / 'run-001').mkdir(parents=True)
        (base / 'published' / 'run-001' / 'snapshot.json').write_text(json.dumps(self.snapshot))
        (base / 'published' / 'current.json').write_text(json.dumps({'run_id': 'run-001'}))
        summary = {'schema_version': 1, 'run_id': 'run-001', 'as_of': '2026-10-18',
                   'demo': True, 'coverage': self.snapshot['coverage'], 'status': 'success'}
        connection = core.connection(base, create=True)
        try:
            connection.execute('INSERT INTO run VALUES (?,?,?,?,?)',
                               ('run-001', '2026-10-18', '2026-10-18', 'test-input', json.dumps(summary)))
            connection.commit()
        finally:
            connection.close()
        def hashes():
            return {str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in base.rglob('*') if p.is_file()}
        before = hashes()
        self.server.data_dir = base
        self.status.side_effect = core.read_status
        self.runs.side_effect = core.read_runs
        self.read.side_effect = core.read_snapshot
        _, status = self.api('/api/mbo/status')
        _, runs = self.api('/api/mbo/runs')
        _, candidates = self.api('/api/mbo/candidates?sort=discount')
        _, company = self.api('/api/mbo/companies/1001?run_id=run-001')
        _, events = self.api('/api/mbo/events?run_id=run-001')
        self.assertEqual(status['latest_success_run_id'], 'run-001')
        self.assertEqual(runs['total'], 1)
        self.assertEqual(candidates['total'], 3)
        self.assertEqual(company['company']['name'], 'Alpha')
        self.assertEqual(events['total'], 1)
        self.assertEqual(self.api('/api/mbo/candidates?run_id=missing')[0].status, 404)
        self.assertEqual(hashes(), before)


class MboStartupTest(unittest.TestCase):
    def test_cloud_marker_including_empty_value_rejects_startup(self):
        for marker in ('asset-hub', ''):
            with self.subTest(marker=marker), patch.dict(os.environ, {'K_SERVICE': marker}):
                with self.assertRaisesRegex(RuntimeError, 'Cloud'):
                    MboServer(('127.0.0.1', 0))

    def test_non_loopback_bind_is_rejected(self):
        for host in ('0.0.0.0', 'localhost', '::1', '192.168.1.2'):
            with self.subTest(host=host):
                with self.assertRaisesRegex(ValueError, 'loopback'):
                    MboServer((host, 0))


if __name__ == '__main__':
    unittest.main()
