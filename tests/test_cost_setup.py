import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

try:
    import requests
except ImportError:  # requirements.txt not installed (CI installs it)
    requests = None

from infra import setup_costs

PROJECT = 'asset-hub-test'
BASE = 'https://bigquery.googleapis.com/bigquery/v2/projects/billing-project/datasets/billing_export'
TABLE = 'gcp_billing_export_v1_01651C_879B71_5DFA29'
CONFIG = {'project': PROJECT, 'project_number': '123', 'account': 'owner@example.com', 'region': 'asia-northeast1',
          'service': 'asset-hub', 'allowed_emails': ['viewer@example.com'],
          'cost_control': {'currency': 'JPY', 'monthly_project_budget': 500, 'thresholds': [0.5, 0.8, 1.0], 'billing_account': ''},
          'cost_reporting': {'billing_table': 'billing-project.billing_export.' + TABLE, 'location': 'US',
                             'allow_pending_export': False, 'schedule': '0 1 * * *', 'time_zone': 'Asia/Tokyo'}}


def response(status, data=None):
    result = Mock(status_code=status)
    result.json.return_value = data
    if status >= 400:
        result.raise_for_status.side_effect = requests.HTTPError(response=result)
    return result


@unittest.skipUnless(requests, 'requests is not installed')
class SourceTest(unittest.TestCase):
    def session(self, *, table=404, enabled=True, location='US', exporter=True):
        session = Mock()
        dataset = {'location': location, 'datasetReference': {'projectId': PROJECT},
                   'access': [{'role': 'OWNER', 'userByEmail': 'billing-export-bigquery@system.gserviceaccount.com'}] if exporter else []}
        session.get.side_effect = [response(table), response(200, {'billingEnabled': enabled,
            'billingAccountName': 'billingAccounts/01651C-879B71-5DFA29'}), response(200, dataset)]
        return session

    def test_missing_table_is_rejected_by_default(self):
        session = self.session()
        with self.assertRaises(requests.HTTPError):
            setup_costs.verify_source(session, BASE, TABLE, PROJECT, 'US')
        self.assertEqual(session.get.call_count, 1)

    def test_explicit_pending_export_accepts_verified_billing_and_dataset(self):
        session = self.session()
        setup_costs.verify_source(session, BASE, TABLE, PROJECT, 'US', True)
        self.assertEqual(session.get.call_count, 3)

    def test_pending_export_rejects_wrong_source_or_incomplete_setup(self):
        for changes, table in [({}, 'unrelated_table'), ({'enabled': False}, TABLE),
                               ({'location': 'EU'}, TABLE), ({'exporter': False}, TABLE)]:
            with self.subTest(changes=changes, table=table):
                with self.assertRaises(ValueError):
                    setup_costs.verify_source(self.session(**changes), BASE, table, PROJECT, 'US', True)

    def test_permission_errors_are_not_treated_as_pending(self):
        session = self.session(table=403)
        with self.assertRaises(requests.HTTPError):
            setup_costs.verify_source(session, BASE, TABLE, PROJECT, 'US', True)
        self.assertEqual(session.get.call_count, 1)

    def test_existing_table_does_not_require_bootstrap_permissions(self):
        session = self.session(table=200)
        setup_costs.verify_source(session, BASE, TABLE, PROJECT, 'US', True)
        self.assertEqual(session.get.call_count, 1)


class PlanTest(unittest.TestCase):
    def plan(self, config):
        output = io.StringIO()
        with patch.object(setup_costs, 'load_config', return_value=config), \
                patch('subprocess.run', side_effect=AssertionError('dry-run must not call gcloud')), \
                patch('subprocess.check_output', side_effect=AssertionError('dry-run must not call gcloud')), \
                redirect_stdout(output):
            setup_costs.main([])
        return output.getvalue()

    def test_default_is_dry_run_printing_daily_schedule(self):
        text = self.plan(CONFIG)
        self.assertIn("gcloud scheduler jobs create http asset-cost-sync", text)
        self.assertIn("'--schedule=0 1 * * *' --time-zone=Asia/Tokyo", text)
        self.assertIn('--project=asset-hub-test --account=owner@example.com', text)
        self.assertIn('--threshold-rule=percent=0.8', text)

    def test_schedule_is_configurable(self):
        config = dict(CONFIG, cost_reporting=dict(CONFIG['cost_reporting'], schedule='0 2 * * 1'))
        self.assertIn("'--schedule=0 2 * * 1'", self.plan(config))

    def test_placeholder_config_still_plans_but_apply_refuses(self):
        placeholder = dict(CONFIG, project='TBD', project_number='TBD', account='TBD',
                           cost_reporting=dict(CONFIG['cost_reporting'], billing_table='TBD'))
        text = self.plan(placeholder)
        self.assertIn('注意', text)
        with patch('subprocess.run', side_effect=AssertionError('must not call gcloud')), redirect_stdout(io.StringIO()), \
                patch.object(setup_costs, 'load_config', return_value=placeholder):
            with self.assertRaises(SystemExit):
                setup_costs.main(['--apply'])

    def test_invalid_table_is_rejected(self):
        config = dict(CONFIG, cost_reporting=dict(CONFIG['cost_reporting'], billing_table='x` UNION'))
        with self.assertRaises(ValueError):
            self.plan(config)


if __name__ == '__main__':
    unittest.main()
