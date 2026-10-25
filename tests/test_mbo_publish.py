"""Local-only dashboard exports: curated DTOs, safe files and demo opt-in."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
import json
import stat
import unittest

from backend.mbo import core
from backend.mbo.__main__ import demo
from backend.mbo.publish import export_dashboard
from backend.mbo_dashboard import MboDashboard, sanitize_bundle


class MboPublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.data_dir = self.root / 'source'
        demo(self.data_dir)
        self.output = self.root / 'output' / 'dashboard.json'

    def hashes(self):
        return {str(path.relative_to(self.data_dir)): sha256(path.read_bytes()).hexdigest()
                for path in self.data_dir.rglob('*') if path.is_file()}

    def test_real_frozen_history_exports_and_can_be_read_as_cloud_document(self):
        before = self.hashes()
        with patch('socket.create_connection', side_effect=AssertionError('No network')), \
                patch('backend.mbo.valuation.evaluate', side_effect=AssertionError('No calculation')):
            result = export_dashboard(self.data_dir, self.output, allow_demo=True)
        payload = json.loads(self.output.read_text())
        self.assertEqual(result['status'], 'exported')
        self.assertEqual(result['runs'], 2)
        self.assertEqual(payload, sanitize_bundle(payload))
        self.assertEqual(self.hashes(), before)
        doc = Mock()
        doc.read.return_value = payload, 1
        dashboard = MboDashboard(document=doc)
        with patch.object(dashboard, '_local_read', side_effect=AssertionError('No local reads')):
            shown = dashboard.response('/api/mbo/candidates', {})
        latest = core.read_snapshot(self.data_dir)
        self.assertEqual(shown['run_id'], latest['run_id'])
        self.assertEqual(shown['coverage'], latest['coverage'])
        self.assertEqual(shown['total'], 3)

    def test_keep_runs_selects_the_pinned_current_run_and_preserves_diff(self):
        export_dashboard(self.data_dir, self.output, keep_runs=1, allow_demo=True)
        payload = json.loads(self.output.read_text())
        latest = core.read_snapshot(self.data_dir)
        self.assertEqual([item['run_id'] for item in payload['runs']], [latest['run_id']])
        self.assertEqual(list(payload['snapshots']), [latest['run_id']])
        self.assertEqual(payload['snapshots'][latest['run_id']]['diff'], latest['diff'])

    def test_demo_requires_explicit_opt_in_without_changing_destination(self):
        self.output.parent.mkdir()
        self.output.write_text('PREVIOUS GOOD EXPORT')
        before = self.hashes()
        with self.assertRaisesRegex(ValueError, '--allow-demo'):
            export_dashboard(self.data_dir, self.output)
        self.assertEqual(self.output.read_text(), 'PREVIOUS GOOD EXPORT')
        self.assertEqual(self.hashes(), before)
        new_output = self.root / 'never-created' / 'dashboard.json'
        with self.assertRaises(ValueError):
            export_dashboard(self.data_dir, new_output)
        self.assertFalse(new_output.parent.exists())

    def test_non_demo_snapshot_exports_by_default(self):
        summary = deepcopy(core.read_runs(self.data_dir)['items'][0])
        summary['demo'] = False
        snapshot = deepcopy(core.read_snapshot(self.data_dir, summary['run_id']))
        snapshot['demo'] = False
        with patch.object(core, 'read_runs', return_value={'items': [summary]}), \
                patch.object(core, 'read_snapshot', return_value=snapshot):
            result = export_dashboard(self.data_dir, self.output)
        self.assertEqual(result['runs'], 1)
        self.assertFalse(json.loads(self.output.read_text())['runs'][0]['demo'])

    def test_export_projects_out_raw_paths_db_input_ids_and_failure_details(self):
        run = deepcopy(core.read_runs(self.data_dir)['items'][0])
        snapshot = deepcopy(core.read_snapshot(self.data_dir, run['run_id']))
        secret = '/private/DO-NOT-EXPORT'
        run.update(input_ids=[secret], input_hash=secret, manifest={'path': secret})
        snapshot.update(raw={'file': secret}, database=secret)
        snapshot['companies'][0].update(raw_relpath=secret, review_notes=[secret])
        snapshot['companies'][0]['facts'][0]['raw_path'] = secret
        snapshot['companies'][0]['evidence'][0]['raw_relpath'] = secret
        status = {'latest_success_run_id': run['run_id'], 'env': secret,
                  'last_attempt': {'status': 'failed', 'error': secret, 'path': secret}}
        with patch.object(core, 'read_runs', return_value={'items': [run]}), \
                patch.object(core, 'read_snapshot', return_value=snapshot), \
                patch.object(core, 'read_status', return_value=status):
            export_dashboard(self.data_dir, self.output, allow_demo=True)
        text = self.output.read_text()
        self.assertNotIn(secret, text)
        self.assertNotIn('raw_relpath', text)
        self.assertNotIn('input_ids', text)
        self.assertNotIn('input_hash', text)
        self.assertNotIn('review_notes', text)
        self.assertIn('更新に失敗', text)

    def test_output_is_atomic_owner_only_and_does_not_chmod_existing_parent(self):
        parent = self.output.parent
        parent.mkdir(mode=0o755)
        parent.chmod(0o755)
        self.output.write_text('old')
        self.output.chmod(0o644)
        export_dashboard(self.data_dir, self.output, allow_demo=True)
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(parent.stat().st_mode), 0o755)
        self.assertEqual(list(parent.iterdir()), [self.output])
        before = self.output.read_bytes()
        with patch('backend.mbo.publish.os.replace', side_effect=OSError('replace failed')):
            with self.assertRaises(OSError):
                export_dashboard(self.data_dir, self.output, allow_demo=True)
        self.assertEqual(self.output.read_bytes(), before)
        self.assertEqual(list(parent.iterdir()), [self.output])

    def test_symlinks_directories_and_source_database_or_history_are_rejected(self):
        target = self.root / 'private-target'
        target.write_text('PROTECT')
        link = self.root / 'symlink'
        link.symlink_to(target)
        directory = self.root / 'directory'
        directory.mkdir()
        link_dir = self.root / 'link-dir'
        link_dir.symlink_to(directory)
        latest = core.read_status(self.data_dir)['latest_success_run_id']
        destinations = [link, directory, link_dir / 'dashboard.json', self.data_dir / 'state.sqlite',
                        self.data_dir / 'published/current.json', self.data_dir / 'last_attempt.json',
                        self.data_dir / 'published' / latest / 'snapshot.json']
        before = self.hashes()
        for output in destinations:
            with self.subTest(output=output.name), self.assertRaises(ValueError):
                export_dashboard(self.data_dir, output, allow_demo=True)
        self.assertEqual(target.read_text(), 'PROTECT')
        self.assertEqual(self.hashes(), before)

    def test_empty_source_exports_empty_schema_without_initializing_source(self):
        empty = self.root / 'empty-source'
        result = export_dashboard(empty, self.output)
        self.assertEqual(result, {'status': 'exported', 'runs': 0, 'latest_run_id': None})
        self.assertEqual(json.loads(self.output.read_text()), sanitize_bundle({}))
        self.assertFalse(empty.exists())

    def test_bad_arguments_or_malformed_source_do_not_write(self):
        for keep in (0, -1, 1001, True, '52', 1.5):
            with self.subTest(keep=keep), self.assertRaises(ValueError):
                export_dashboard(self.data_dir, self.output, keep_runs=keep, allow_demo=True)
        with self.assertRaises(ValueError):
            export_dashboard(self.data_dir, self.output, allow_demo='yes')
        with patch.object(core, 'read_status', return_value={'latest_success_run_id': 'missing'}):
            with self.assertRaises(RuntimeError):
                export_dashboard(self.data_dir, self.output, allow_demo=True)
        self.assertFalse(self.output.parent.exists())

    def test_newer_in_progress_run_does_not_override_the_pinned_current_pointer(self):
        current = core.read_status(self.data_dir)['latest_success_run_id']
        summaries = core.read_runs(self.data_dir)['items']
        newer = deepcopy(summaries[0])
        newer['run_id'] = 'run-not-current-yet'
        with patch.object(core, 'read_runs', return_value={'items': [newer, *summaries]}), \
                patch.object(core, 'read_snapshot', wraps=core.read_snapshot) as read:
            export_dashboard(self.data_dir, self.output, keep_runs=1, allow_demo=True)
        read.assert_called_once_with(self.data_dir, current)
        self.assertEqual(json.loads(self.output.read_text())['latest_run_id'], current)


if __name__ == '__main__':
    unittest.main()
