import io
import json
import subprocess
import tempfile
from contextlib import redirect_stderr
import unittest
from pathlib import Path
from unittest.mock import patch

from infra import deploy
from infra.common import Gcloud, config_problems, load_config, placeholders, require_config

VALID = {'project': 'asset-hub-test', 'project_number': '123456', 'account': 'owner@example.com',
         'region': 'asia-northeast1', 'service': 'asset-hub', 'allowed_emails': ['viewer@example.com'],
         'cost_control': {'currency': 'JPY', 'monthly_project_budget': 500, 'thresholds': [0.5, 0.8, 1.0], 'billing_account': ''},
         'cost_reporting': {'billing_table': '', 'location': 'US', 'allow_pending_export': False,
                            'schedule': '0 1 * * *', 'time_zone': 'Asia/Tokyo'}}
PLACEHOLDER = dict(VALID, project='TBD', project_number='TBD', account='TBD', allowed_emails=[],
                   cost_reporting=dict(VALID['cost_reporting'], billing_table='TBD'))


class ConfigGuardTest(unittest.TestCase):
    def test_checked_in_config_keeps_fixed_settings(self):
        config = load_config()
        self.assertEqual(config['region'], 'asia-northeast1')
        self.assertEqual(config['service'], 'asset-hub')
        self.assertEqual(config['cost_control']['thresholds'], [0.5, 0.8, 1.0])

    def test_placeholder_config_is_refused(self):
        self.assertIn('config.project', placeholders(PLACEHOLDER))
        with self.assertRaises(SystemExit):
            require_config(PLACEHOLDER)

    def test_deploy_refuses_tbd_before_any_gcloud_call(self):
        for command in ['bootstrap', 'deploy', 'verify']:
            with self.subTest(command=command), patch('subprocess.run', side_effect=AssertionError('gcloud called')), \
                    patch.object(deploy, 'load_config', return_value=PLACEHOLDER):
                with self.assertRaises(SystemExit):
                    deploy.main([command])
        with self.assertRaises(SystemExit):
            deploy.main(['unknown'])

    def test_each_placeholder_or_missing_viewer_is_reported(self):
        self.assertEqual(config_problems(VALID), [])
        for changes in [{'project': 'TBD'}, {'project_number': 'tbd'}, {'account': 'TBD'}, {'allowed_emails': []},
                        {'allowed_emails': ['not-an-email']}, {'project_number': 'abc'},
                        {'cost_reporting': dict(VALID['cost_reporting'], billing_table='TBD')},
                        {'cost_reporting': dict(VALID['cost_reporting'], billing_table='bad table')}]:
            with self.subTest(changes=changes):
                self.assertTrue(config_problems(dict(VALID, **changes)))


class DeployPlanTest(unittest.TestCase):
    def test_service_is_private_behind_iap_and_small(self):
        args = deploy.deploy_args(VALID, 'env.json')
        for flag in ['--no-allow-unauthenticated', '--iap', '--memory=256Mi', '--max-instances=1', '--min=0',
                     '--service-account=asset-runtime@asset-hub-test.iam.gserviceaccount.com']:
            self.assertIn(flag, args)
        self.assertNotIn('--allow-unauthenticated', args)

    def test_iap_policy_and_env_follow_config(self):
        self.assertEqual(deploy.iap_policy(VALID), {'bindings': [
            {'role': 'roles/iap.httpsResourceAccessor', 'members': ['user:viewer@example.com']}]})
        env = deploy.service_env(VALID)
        self.assertEqual(env['ASSET_IAP_AUDIENCE'], '/projects/123456/locations/asia-northeast1/services/asset-hub')
        self.assertEqual(env['ASSET_ALLOWED_EMAILS'], 'viewer@example.com')
        self.assertEqual(env['ASSET_STATE_BUCKET'], 'asset-hub-test-asset-state')
        self.assertEqual(env['ASSET_PROJECT_ID'], 'asset-hub-test')

    def test_verify_rejects_public_invoker_and_extra_viewers(self):
        def gcloud(invoker, viewers):
            responses = {'describe': {'metadata': {'annotations': {'run.googleapis.com/iap-enabled': 'true'}},
                                      'status': {'url': 'https://x'}},
                         'get-iam-policy': None}
            class Fake:
                def run(self, *args, read=False):
                    if 'describe' in args:
                        return responses['describe']
                    if args[0] == 'iap':
                        return {'bindings': [{'role': 'roles/iap.httpsResourceAccessor', 'members': viewers}]}
                    return {'bindings': [{'role': 'roles/run.invoker', 'members': invoker}]}
            return Fake()
        ok = ['user:viewer@example.com']
        with patch('builtins.print'):
            deploy.verify(VALID, gcloud(['serviceAccount:iap'], ok))
        for invoker, viewers in [(['allUsers'], ok), (['allAuthenticatedUsers'], ok), ([], ok + ['user:other@example.com'])]:
            with self.subTest(invoker=invoker, viewers=viewers), self.assertRaises(AssertionError):
                deploy.verify(VALID, gcloud(invoker, viewers))

    def test_iam_bindings_retry_only_while_a_new_account_propagates(self):
        def result(code, stderr=''):
            return subprocess.CompletedProcess('gcloud', code, stderr=stderr)
        missing = result(1, 'Service account x does not exist.')
        with patch('subprocess.run', side_effect=[missing, missing, result(0)]) as run, redirect_stderr(io.StringIO()):
            Gcloud(VALID).run_retry('projects', 'add-iam-policy-binding', sleep=lambda _: None)
        self.assertEqual(run.call_count, 3)
        with patch('subprocess.run', return_value=missing), redirect_stderr(io.StringIO()), \
                self.assertRaises(subprocess.CalledProcessError):
            Gcloud(VALID).run_retry('x', attempts=2, sleep=lambda _: None)
        with patch('subprocess.run', return_value=result(1, 'PERMISSION_DENIED')) as run, redirect_stderr(io.StringIO()), \
                self.assertRaises(subprocess.CalledProcessError):
            Gcloud(VALID).run_retry('x', sleep=lambda _: self.fail('must not retry'))
        self.assertEqual(run.call_count, 1)

    def test_skip_costs_still_moves_the_cost_job_to_the_new_image(self):
        calls = []
        class Fake(Gcloud):
            def run(self, *args, read=False):
                calls.append(args)
            def succeeds(self, *args):
                return args[:3] == ('run', 'jobs', 'describe')
        deploy.deploy(VALID, Fake(VALID), ['--skip-costs'])
        updates = [c for c in calls if c[:3] == ('run', 'jobs', 'update')]
        self.assertEqual(len(updates), 1)
        self.assertIn('--image=asia-northeast1-docker.pkg.dev/asset-hub-test/asset-hub/app:current', updates[0])
        calls.clear()
        deploy.deploy(VALID, Fake(VALID), ['--skip-costs', '--existing-image'])
        self.assertFalse([c for c in calls if c[:3] == ('run', 'jobs', 'update')])

    def test_gcloud_is_pinned_to_project_and_account(self):
        command = Gcloud(VALID).command('run', 'services', 'list', read=True)
        self.assertEqual(command[-4:], ['--project=asset-hub-test', '--account=owner@example.com', '--quiet', '--format=json'])


class StagingTest(unittest.TestCase):
    def test_only_allowlisted_files_are_uploaded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'repo'
            files = ['backend/server.py', 'backend/notes.txt', 'web/index.html', 'web/app.js', 'web/.env',
                     'web/sub/x.js', 'research/catalog.json', 'research/themes/t/d/index.html',
                     'research/themes/t/d/working/raw.html', 'research/themes/t/d/qa/shot.png',
                     'research/themes/t/d/.DS_Store', 'research/themes/t/d/fetch.py', 'research/themes/t/d/a.pdf',
                     'data/private/costs.json', 'infra/config.json', '.env', 'Dockerfile', 'requirements.txt', '.dockerignore']
            for name in files:
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text('x')
            target = Path(directory) / 'stage'
            target.mkdir()
            staged = set(deploy.stage(root, target))
            self.assertEqual(staged, {'backend/server.py', 'web/index.html', 'web/app.js', 'research/catalog.json',
                                      'research/themes/t/d/index.html', 'research/themes/t/d/a.pdf',
                                      'Dockerfile', 'requirements.txt', '.dockerignore'})
            on_disk = {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}
            self.assertEqual(on_disk, staged)

    def test_real_repository_staging_excludes_working_material(self):
        from backend.paths import ROOT, research_files
        staged = list(research_files(ROOT / 'research'))
        self.assertTrue(staged)
        self.assertFalse([p for p in staged if '/working/' in '/' + p or '/qa/' in '/' + p or '/.' in '/' + p])

    def test_launch_configuration(self):
        from backend.paths import ROOT
        launch = json.loads((ROOT / '.claude/launch.json').read_text())
        self.assertEqual(launch['configurations'][0]['runtimeArgs'], ['-m', 'backend.server', '--port', '4330'])


if __name__ == '__main__':
    unittest.main()
