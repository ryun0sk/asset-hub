import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock

from backend.paths import resolve_research, research_files, shell_assets
from backend.server import API_CSP, RESEARCH_HTML_CSP, SHELL_CSP, DashboardServer, Handler

SHELL = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-src 'self'; "
         "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


def tree(base):
    files = {
        'secret.txt': 'outside',
        'web/index.html': '<!doctype html><title>shell</title>',
        'web/app.js': 'console.log(1)',
        'web/styles.css': 'body{}',
        'web/.hidden.js': 'no',
        'web/notes.md': 'no',
        'web/sub/nested.js': 'no',
        'research/catalog.json': '{"items": []}',
        'research/themes/a/2026-09-05/index.html': '<script>1</script>',
        'research/themes/a/2026-09-05/report.md': '# report',
        'research/themes/a/2026-09-05/model.mjs': 'export {}',
        'research/themes/a/2026-09-05/data.json': '{}',
        'research/themes/a/2026-09-05/doc.pdf': '%PDF-1.4',
        'research/themes/a/2026-09-05/chart.svg': '<svg/>',
        'research/themes/a/2026-09-05/build.py': 'print()',
        'research/themes/a/2026-09-05/verify.cjs': '1',
        'research/themes/a/2026-09-05/working/raw.md': 'private',
        'research/themes/a/2026-09-05/qa/check.png': 'private',
        'research/themes/a/2026-09-05/.notes.md': 'hidden',
        'research/.hidden/x.md': 'hidden',
    }
    for name, content in files.items():
        path = Path(base) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    research = Path(base) / 'research'
    try:
        (research / 'escape.md').symlink_to(Path(base) / 'secret.txt')
        (research / 'alias').symlink_to(research / 'themes/a/2026-09-05/working')
    except OSError:
        pass
    return Path(base)


class PathAllowlistTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = tree(self.temp.name)
        self.research = self.root / 'research'

    def tearDown(self):
        self.temp.cleanup()

    def found(self, path):
        result = resolve_research(self.research, path)
        return result and result[1]

    def test_allowed_research_files_and_types(self):
        base = '/research/themes/a/2026-09-05/'
        self.assertEqual(self.found(base + 'index.html'), 'text/html; charset=utf-8')
        self.assertEqual(self.found(base + 'report.md'), 'text/plain; charset=utf-8')
        self.assertEqual(self.found(base + 'model.mjs'), 'text/plain; charset=utf-8')
        self.assertEqual(self.found(base + 'doc.pdf'), 'application/pdf')
        self.assertEqual(self.found('/research/themes/a/2026-09-05/report%2Emd'), 'text/plain; charset=utf-8')

    def test_traversal_hidden_and_working_paths_are_rejected(self):
        for path in ['/research/../secret.txt', '/research/%2e%2e/secret.txt', '/research/themes/../../secret.txt',
                     '/research/themes/a/2026-09-05/..%2f..%2f..%2f..%2fsecret.txt', '/research/%2Fetc%2Fpasswd',
                     '/research//themes/a/2026-09-05/report.md', '/research/themes/a/2026-09-05/working/raw.md',
                     '/research/themes/a/2026-09-05/Working/raw.md', '/research/themes/a/2026-09-05/qa/check.png',
                     '/research/themes/a/2026-09-05/.notes.md', '/research/.hidden/x.md',
                     '/research/themes/a/2026-09-05/build.py', '/research/themes/a/2026-09-05/verify.cjs',
                     '/research/themes/a/2026-09-05/', '/research/themes', '/research/', '/research/x%ff.md',
                     '/research/themes/a/2026-09-05/report.md%00.md', '/research/escape.md', '/research/alias/raw.md']:
            with self.subTest(path=path):
                self.assertIsNone(resolve_research(self.research, path))

    def test_shell_assets_are_top_level_allowlisted_files(self):
        assets = shell_assets(self.root / 'web')
        self.assertEqual(set(assets), {'/', '/index.html', '/app.js', '/styles.css'})

    def test_image_staging_list_matches_served_files(self):
        staged = set(research_files(self.research))
        self.assertIn('themes/a/2026-09-05/report.md', staged)
        self.assertIn('catalog.json', staged)
        self.assertFalse({p for p in staged if 'working' in p or 'qa/' in p or '/.' in p or p.endswith(('.py', '.cjs'))})
        self.assertNotIn('escape.md', staged)


class ServerTest(unittest.TestCase):
    cloud = False

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = tree(self.temp.name)
        self.server = DashboardServer(('127.0.0.1', 0), Handler).configure(
            self.cloud, web_dir=self.root / 'web', research_dir=self.root / 'research')
        self.server.cost_document = Mock()
        self.server.cost_document.read.return_value = ({'snapshot': None, 'syncStatus': {'status': 'pending'}}, 1)
        self.server.asset_document = Mock()
        self.server.asset_document.read.return_value = (
            {'state': {'version': 1, 'accounts': [], 'snapshots': [], 'latestDate': None}, 'pushedAt': '2026-10-04T01:00:00+00:00'}, 1)
        self.server.verify = Mock(return_value='viewer@example.com')
        self.server.audience = 'aud'
        self.server.allowed = frozenset({'viewer@example.com'})
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.temp.cleanup()

    def request(self, path, method='GET', host='localhost', headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_address[1], timeout=5)
        connection.putrequest(method, path, skip_host=True)
        connection.putheader('Host', host)
        for name, value in (headers or {}).items():
            connection.putheader(name, value)
        connection.endheaders()
        response = connection.getresponse()
        body = response.read()
        connection.close()
        return response, body


class LocalServerTest(ServerTest):
    def test_shell_routes_get_strict_csp(self):
        for path in ['/', '/index.html', '/app.js', '/styles.css']:
            with self.subTest(path=path):
                response, _ = self.request(path)
                self.assertEqual(response.status, 200)
                self.assertEqual(response.getheader('Content-Security-Policy'), SHELL)
                self.assertEqual(response.getheader('X-Content-Type-Options'), 'nosniff')
                self.assertEqual(response.getheader('Referrer-Policy'), 'no-referrer')
                self.assertEqual(response.getheader('Cache-Control'), 'private, no-cache')
                self.assertTrue(response.getheader('ETag'))
        self.assertEqual(SHELL_CSP, SHELL)

    def test_unlisted_shell_files_are_not_served(self):
        for path in ['/.hidden.js', '/notes.md', '/sub/nested.js', '/../secret.txt', '/backend/server.py', '/infra/config.json']:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0].status, 404)

    def test_research_html_gets_relaxed_frameable_csp(self):
        response, body = self.request('/research/themes/a/2026-09-05/index.html?tab=x')
        self.assertEqual(response.status, 200)
        self.assertEqual(body, b'<script>1</script>')
        csp = response.getheader('Content-Security-Policy')
        self.assertEqual(csp, RESEARCH_HTML_CSP)
        self.assertIn("frame-ancestors 'self'", csp)
        self.assertIn("'unsafe-inline'", csp)
        self.assertIn('https://cdn.jsdelivr.net', csp)
        self.assertNotIn("'unsafe-eval'", csp)

    def test_research_files_types_and_headers(self):
        response, body = self.request('/research/themes/a/2026-09-05/report.md')
        self.assertEqual((response.status, body), (200, b'# report'))
        self.assertEqual(response.getheader('Content-Type'), 'text/plain; charset=utf-8')
        self.assertEqual(response.getheader('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.getheader('Cache-Control'), 'private, no-cache')
        self.assertIn('sandbox', response.getheader('Content-Security-Policy'))
        response, _ = self.request('/research/themes/a/2026-09-05/doc.pdf')
        self.assertEqual(response.getheader('Content-Type'), 'application/pdf')
        self.assertNotIn('sandbox', response.getheader('Content-Security-Policy'))

    def test_research_rejections_over_http(self):
        for path in ['/research/../secret.txt', '/research/%2e%2e/secret.txt',
                     '/research/themes/a/2026-09-05/working/raw.md', '/research/themes/a/2026-09-05/.notes.md',
                     '/research/themes/a/2026-09-05/build.py']:
            with self.subTest(path=path):
                response, body = self.request(path)
                self.assertEqual(response.status, 404)
                self.assertNotIn(b'private', body)
                self.assertNotIn(b'outside', body)

    def test_catalog_and_missing_catalog(self):
        response, body = self.request('/api/catalog')
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(body), {'items': []})
        self.assertEqual(response.getheader('Content-Security-Policy'), API_CSP)
        (self.root / 'research/catalog.json').unlink()
        response, body = self.request('/api/catalog')
        self.assertEqual(response.status, 404)
        self.assertIn('error', json.loads(body))

    def test_costs_payload_and_storage_failure(self):
        response, body = self.request('/api/costs')
        self.assertEqual(response.status, 200)
        self.assertEqual(set(json.loads(body)), {'project', 'budget', 'snapshot', 'syncStatus'})
        self.assertEqual(response.getheader('Cache-Control'), 'no-store')
        self.server._cost_cache = (0.0, None)
        self.server.cost_document.read.side_effect = RuntimeError('private billing error')
        response, body = self.request('/api/costs')
        self.assertEqual(response.status, 503)
        self.assertNotIn(b'private', body)

    def test_cost_snapshot_is_reused_within_a_minute(self):
        for _ in range(3):
            self.assertEqual(self.request('/api/costs')[0].status, 200)
        self.server.cost_document.read.assert_called_once()

    def test_assets_payload_and_storage_failure(self):
        response, body = self.request('/api/assets')
        self.assertEqual(response.status, 200)
        payload = json.loads(body)
        self.assertEqual(set(payload), {'state', 'status'})
        self.assertEqual(payload['status'], {'status': 'ok', 'pushedAt': '2026-10-04T01:00:00+00:00'})
        self.assertEqual(payload['state']['version'], 1)
        self.assertEqual(response.getheader('Cache-Control'), 'no-store')
        self.assertEqual(response.getheader('Content-Security-Policy'), API_CSP)
        self.assertEqual(response.getheader('Content-Type'), 'application/json; charset=utf-8')
        self.server._asset_cache = (0.0, None)
        self.server.asset_document.read.side_effect = RuntimeError('private balance error')
        response, body = self.request('/api/assets')
        self.assertEqual(response.status, 503)
        self.assertNotIn(b'private', body)
        self.assertNotIn(b'balance', body)
        self.assertEqual(json.loads(body), {'error': '資産データを読み込めませんでした。'})
        self.assertEqual(response.getheader('Content-Security-Policy'), API_CSP)
        self.assertEqual(self.request('/api/assets', method='HEAD')[1], b'')

    def test_asset_state_is_reused_within_a_minute(self):
        for _ in range(3):
            self.assertEqual(self.request('/api/assets')[0].status, 200)
        self.server.asset_document.read.assert_called_once()
        self.server.cost_document.read.assert_not_called()

    def test_static_files_revalidate_with_etag(self):
        path = '/research/themes/a/2026-09-05/index.html'
        response, _ = self.request(path)
        tag = response.getheader('ETag')
        response, body = self.request(path, headers={'If-None-Match': tag})
        self.assertEqual((response.status, body), (304, b''))
        self.assertEqual(response.getheader('ETag'), tag)
        (self.root / 'research/themes/a/2026-09-05/index.html').write_text('<script>changed</script>')
        response, body = self.request(path, headers={'If-None-Match': tag})
        self.assertEqual((response.status, body), (200, b'<script>changed</script>'))

    def test_head_has_headers_without_body(self):
        response, body = self.request('/', method='HEAD')
        self.assertEqual((response.status, body), (200, b''))
        self.assertEqual(response.getheader('Content-Security-Policy'), SHELL)

    def test_only_get_and_head(self):
        for method in ['POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']:
            with self.subTest(method=method):
                response, _ = self.request('/api/costs', method=method)
                self.assertEqual(response.status, 405)
                self.assertEqual(response.getheader('Allow'), 'GET, HEAD')

    def test_local_mode_requires_loopback_host(self):
        for host in ['localhost:4330', '127.0.0.1', '127.0.0.1:4330']:
            self.assertEqual(self.request('/', host=host)[0].status, 200)
        for host in ['evil.example', 'evil.example:4330', '[::1]:4330', '', 'localhost.evil.example']:
            with self.subTest(host=host):
                self.assertEqual(self.request('/', host=host)[0].status, 403)
        self.server.verify.assert_not_called()


class CloudServerTest(ServerTest):
    cloud = True

    def test_every_route_requires_iap_assertion(self):
        self.server.verify.side_effect = PermissionError()
        for path in ['/', '/app.js', '/api/catalog', '/api/costs', '/api/assets', '/research/themes/a/2026-09-05/index.html',
                     '/missing']:
            with self.subTest(path=path):
                response, body = self.request(path, host='asset-hub.example')
                self.assertEqual(response.status, 403)
                self.assertNotIn(b'shell', body)
                self.assertNotIn(b'items', body)
                self.assertNotIn(b'pushedAt', body)
        self.assertEqual(self.request('/api/costs', method='POST', host='x')[0].status, 403)
        self.assertEqual(self.request('/api/assets', method='POST', host='x')[0].status, 403)
        self.server.cost_document.read.assert_not_called()
        self.server.asset_document.read.assert_not_called()

    def test_valid_assertion_is_checked_against_audience_and_viewers(self):
        response, _ = self.request('/api/catalog', host='asset-hub.example',
                                   headers={'X-Goog-IAP-JWT-Assertion': 'signed'})
        self.assertEqual(response.status, 200)
        self.server.verify.assert_called_once_with('signed', 'aud', frozenset({'viewer@example.com'}))

    def test_cloud_shell_assets_are_fixed_at_startup(self):
        (self.root / 'web/late.js').write_text('late')
        self.assertEqual(self.request('/late.js', host='x')[0].status, 404)


if __name__ == '__main__':
    unittest.main()
