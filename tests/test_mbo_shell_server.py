"""MBO uses the Asset Hub auth boundary and does not bypass it."""
import json
from unittest.mock import Mock

from tests.test_server import ServerTest


class MboShellServerTest(ServerTest):
    def setUp(self):
        super().setUp()
        self.server.mbo_dashboard = Mock()
        self.server.mbo_dashboard.response.return_value = {'schema_version': 1, 'mode': 'mbo-dashboard'}

    def test_same_origin_api_get_head_and_no_writes(self):
        response, body = self.request('/api/mbo/status')
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(body)['mode'], 'mbo-dashboard')
        self.assertEqual(response.getheader('Cache-Control'), 'no-store')
        self.assertIsNone(response.getheader('Access-Control-Allow-Origin'))
        response, body = self.request('/api/mbo/status', method='HEAD')
        self.assertEqual(response.status, 200)
        self.assertEqual(body, b'')
        self.assertEqual(self.request('/api/mbo/status', method='POST')[0].status, 405)

    def test_query_errors_unknown_runs_and_storage_failure_are_separate(self):
        for exception, code in [(ValueError('secret'), 400), (FileNotFoundError('/private/secret'), 404),
                                (RuntimeError('token secret'), 503)]:
            self.server.mbo_dashboard.response.side_effect = exception
            response, body = self.request('/api/mbo/candidates?run_id=x')
            self.assertEqual(response.status, code)
            self.assertNotIn(b'secret', body)
            self.assertIn('request_id', json.loads(body))

    def test_duplicate_query_and_cross_origin_rejected_before_reading(self):
        for path, headers, code in [('/api/mbo/runs?limit=1&limit=2', {}, 400),
                                    ('/api/mbo/status', {'Origin': 'https://foreign.example'}, 403),
                                    ('/api/mbo/status', {'Sec-Fetch-Site': 'cross-site'}, 403)]:
            self.server.mbo_dashboard.response.reset_mock()
            response, _ = self.request(path, headers=headers)
            self.assertEqual(response.status, code)
            self.server.mbo_dashboard.response.assert_not_called()

    def test_other_features_still_use_their_existing_readers(self):
        for path in ('/api/catalog', '/api/assets', '/api/costs', '/'):
            self.assertEqual(self.request(path)[0].status, 200)
        self.server.mbo_dashboard.response.assert_not_called()


class MboCloudShellServerTest(MboShellServerTest):
    cloud = True

    def test_iap_rejection_happens_before_any_mbo_read(self):
        self.server.verify.side_effect = PermissionError()
        response, _ = self.request('/api/mbo/status')
        self.assertEqual(response.status, 403)
        self.server.mbo_dashboard.response.assert_not_called()
