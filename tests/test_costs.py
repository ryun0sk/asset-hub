import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from backend.costs import cost_window, cost_query, parse_rows, read_costs, synchronize, cost_payload
from backend.storage import LocalDocument, Conflict

PROJECT = 'asset-hub-test'
TABLE = 'billing-project.billing_export.gcp_billing_export_v1_X'
NOW = datetime(2026, 9, 28, tzinfo=timezone.utc)
WINDOW = cost_window(NOW)
ROW = dict(date='2026-09-27', service_id='run', service='Cloud Run', currency='JPY', gross='12.35', credits='-10.01', exported_at='1790467200')


def snapshot():
    return parse_rows([ROW], WINDOW, NOW.isoformat(), PROJECT)


class CostsTest(unittest.TestCase):
    def setUp(self):
        patcher = patch.dict('os.environ', {'ASSET_PROJECT_ID': PROJECT})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_window_is_six_jst_calendar_months_including_current(self):
        self.assertEqual(WINDOW, {'start': '2026-04-01', 'end': '2026-10-01'})
        self.assertEqual(cost_window(datetime(2026, 12, 31, 15, tzinfo=timezone.utc)),
                         {'start': '2026-08-01', 'end': '2027-02-01'})

    def test_query_scopes_project_and_credits_without_multiplying_rows(self):
        sql = cost_query(TABLE)
        self.assertIn('project.id = @project', sql)
        self.assertIn('FROM UNNEST(credits)', sql)
        self.assertIn('_PARTITIONTIME', sql)
        for table in ['x', 'project.dataset.table` UNION SELECT *', 'other.table', 'TBD']:
            with self.assertRaises(ValueError):
                cost_query(table)

    def test_exact_amounts_and_missing_data(self):
        self.assertEqual(snapshot()['records'][0]['net'], 2.34)
        self.assertEqual(snapshot()['projectId'], PROJECT)
        empty = parse_rows([], WINDOW, NOW.isoformat(), PROJECT)
        self.assertEqual(empty['records'], [])
        self.assertIsNone(empty['currency'])
        self.assertIsNone(empty['latestUsageDate'])

    def test_invalid_or_mixed_rows_never_publish(self):
        for changes in [dict(gross='NaN'), dict(credits='Infinity'), dict(date='2026-09-31'),
                        dict(date='2026-10-01'), dict(exported_at=''), dict(currency='YEN!'), dict(service_id='')]:
            with self.assertRaises((ValueError, TypeError)):
                parse_rows([dict(ROW, **changes)], WINDOW, NOW.isoformat(), PROJECT)
        with self.assertRaises(ValueError):
            parse_rows([ROW, dict(ROW, currency='USD')], WINDOW, NOW.isoformat(), PROJECT)

    def test_query_poll_and_pagination_preserve_every_service(self):
        def response(data):
            result = Mock(); result.json.return_value = data
            return result
        fields = list(ROW)
        session = Mock()
        session.post.return_value = response({'jobComplete': False, 'jobReference': {'jobId': 'job-1', 'location': 'US'}})
        page = dict(jobComplete=True, schema={'fields': [{'name': k} for k in fields]}, rows=[{'f': [{'v': ROW[k]} for k in fields]}])
        session.get.side_effect = [response(dict(page, pageToken='next')), response(dict(page, rows=[{'f': [{'v': dict(ROW, service_id='storage')[k]} for k in fields]}]))]
        result = read_costs(TABLE, session=session, now=NOW)
        self.assertEqual(len(result['records']), 2)
        self.assertIn('/projects/' + PROJECT + '/queries', session.post.call_args.args[0])
        body = session.post.call_args.kwargs['json']
        self.assertEqual(body['maximumBytesBilled'], '100000000')
        self.assertEqual(body['queryParameters'][0]['parameterValue']['value'], PROJECT)
        self.assertEqual(session.get.call_args.kwargs['params']['pageToken'], 'next')

    def test_missing_project_never_queries(self):
        session = Mock()
        with patch.dict('os.environ', {'ASSET_PROJECT_ID': ''}):
            with self.assertRaises(ValueError):
                read_costs(TABLE, session=session, now=NOW)
        session.post.assert_not_called()

    def test_failed_sync_keeps_old_snapshot_and_marks_error(self):
        with tempfile.TemporaryDirectory() as directory:
            document = LocalDocument(Path(directory) / 'costs.json')
            old = dict(snapshot(), fetchedAt='2026-09-01T00:00:00+00:00')
            document.write({'snapshot': old}, 0)
            self.assertEqual(synchronize(document, 'table', read=Mock(side_effect=TimeoutError()), now=NOW), 'error')
            result = cost_payload(document)
            self.assertEqual(result['snapshot'], old)
            self.assertEqual(result['syncStatus']['status'], 'error')
            self.assertEqual(result['project'], PROJECT)

    def test_retry_cache_and_missing_configuration_do_not_query(self):
        with tempfile.TemporaryDirectory() as directory:
            document = LocalDocument(Path(directory) / 'costs.json')
            read = Mock(return_value=snapshot())
            self.assertEqual(synchronize(document, '', read=read, now=NOW), 'not_configured')
            self.assertIsNone(cost_payload(document)['snapshot'])
            read.assert_not_called()
            self.assertEqual(synchronize(document, 'table', read=read, now=NOW), 'ok')
            self.assertEqual(synchronize(document, 'table', read=read, now=NOW), 'cached')
            self.assertEqual(read.call_count, 1)
            # The next daily run must fetch again.
            self.assertEqual(synchronize(document, 'table', read=read, now=NOW + timedelta(days=1)), 'ok')
            self.assertEqual(read.call_count, 2)

    def test_empty_export_is_pending_not_zero(self):
        document = Mock(); document.read.return_value = ({}, 0)
        read = Mock(return_value=parse_rows([], WINDOW, NOW.isoformat(), PROJECT))
        self.assertEqual(synchronize(document, 'table', read=read, now=NOW), 'pending')
        self.assertEqual(document.write.call_args.args[0]['snapshot']['records'], [])

    def test_concurrent_newer_publication_is_not_overwritten(self):
        document = Mock(); document.read.return_value = ({}, 0)
        document.write.side_effect = Conflict()
        self.assertEqual(synchronize(document, 'table', read=Mock(return_value=snapshot()), now=NOW), 'superseded')

    def test_local_document_rejects_stale_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            document = LocalDocument(Path(directory) / 'costs.json')
            self.assertEqual(document.read(), ({}, 0))
            document.write({'a': 1}, 0)
            with self.assertRaises(Conflict):
                document.write({'a': 2}, 0)


class CostDisableTest(unittest.TestCase):
    def test_reenable_after_disable_fetches_and_restores_configured_status(self):
        with tempfile.TemporaryDirectory() as directory:
            document = LocalDocument(Path(directory) / 'costs.json')
            read = Mock(return_value=snapshot())
            self.assertEqual(synchronize(document, 'table', read=read, now=NOW), 'ok')
            self.assertEqual(synchronize(document, '', read=read, now=NOW + timedelta(minutes=1)), 'not_configured')
            self.assertEqual(synchronize(document, 'table', read=read, now=NOW + timedelta(minutes=2)), 'ok')
            self.assertEqual(read.call_count, 2)
            self.assertEqual(cost_payload(document)['syncStatus']['status'], 'ok')

    def test_clearing_configuration_ignores_recent_cache_and_preserves_history(self):
        document = Mock(); document.read.return_value = ({'snapshot': snapshot()}, 1)
        read = Mock()
        self.assertEqual(synchronize(document, '', read=read, now=NOW), 'not_configured')
        read.assert_not_called()
        state = document.write.call_args.args[0]
        self.assertEqual(state['snapshot'], snapshot())
        self.assertEqual(state['syncStatus']['status'], 'not_configured')

    def test_disable_pauses_schedule_clears_old_source_and_publishes_status(self):
        from infra.setup_costs import disable_reporting
        calls = []
        def run(*args, read=False):
            calls.append(args)
            if args[:3] == ('scheduler', 'jobs', 'list'):
                return [{'name': 'projects/p/locations/r/jobs/asset-cost-sync', 'state': 'ENABLED'}]
            if args[:3] == ('run', 'jobs', 'list'):
                return [{'metadata': {'name': 'asset-cost-sync'}}]
        disable_reporting(run, PROJECT, 'asia-northeast1', 'asset-cost-sync', 'image')
        self.assertEqual(calls[1][:3], ('scheduler', 'jobs', 'pause'))
        self.assertIn('--remove-env-vars=ASSET_COST_BILLING_TABLE', calls[3])
        self.assertEqual(calls[4][:3], ('run', 'jobs', 'execute'))

    def test_unconfigured_first_deploy_does_not_create_any_cost_job(self):
        from infra.setup_costs import disable_reporting
        run = Mock(return_value=[])
        disable_reporting(run, PROJECT, 'asia-northeast1', 'asset-cost-sync', 'image')
        self.assertEqual(run.call_count, 2)
        self.assertTrue(all(call.kwargs == {'read': True} for call in run.call_args_list))


class CostBudgetConfigTest(unittest.TestCase):
    def test_runtime_budget_is_exposed_without_private_config(self):
        document = Mock(); document.read.return_value = ({}, 1)
        with patch.dict('os.environ', {'ASSET_COST_PROJECT_BUDGET': '500', 'ASSET_COST_CURRENCY': 'JPY', 'ASSET_PROJECT_ID': PROJECT}):
            payload = cost_payload(document)
            self.assertEqual(payload['budget'], {'currency': 'JPY', 'projectBudget': 500})
            self.assertEqual(payload['syncStatus'], {'status': 'not_configured'})
            self.assertEqual(set(payload), {'project', 'budget', 'snapshot', 'syncStatus'})
        for value in ['', 'oops', 'NaN', 'Infinity', '-1', '0']:
            with self.subTest(value=value), patch.dict('os.environ', {'ASSET_COST_PROJECT_BUDGET': value}):
                self.assertIsNone(cost_payload(document)['budget']['projectBudget'])


if __name__ == '__main__':
    unittest.main()
