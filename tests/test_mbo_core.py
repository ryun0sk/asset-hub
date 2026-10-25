"""Integration checks for an offline weekly workflow, using only fictional companies."""
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import csv
import json
import contextlib
import io
import os
import sqlite3
import unittest

from backend.mbo import core
from backend.mbo.__main__ import demo, templates, write_csv
from backend.paths import shell_assets


class MboCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.base = Path(self.temp.name) / 'private'
        self.result = demo(self.base)
        self.snapshot = core.read_snapshot(self.base)

    def tearDown(self):
        self.temp.cleanup()

    def update(self, kind, rows):
        directory = Path(self.temp.name) / ('update-' + str(len(list(Path(self.temp.name).iterdir()))))
        directory.mkdir()
        write_csv(directory / (kind + '.csv'), rows, core.HEADERS[kind])
        return directory

    def original_rows(self, kind):
        with (self.base / 'demo-input-initial' / (kind + '.csv')).open(encoding='utf-8-sig', newline='') as handle:
            return list(csv.DictReader(handle))

    def count(self):
        conn = core.connection(self.base)
        try:
            return conn.execute('SELECT COUNT(*) FROM record').fetchone()[0]
        finally:
            conn.close()

    def test_full_offline_flow_events_missing_price_dcf_lbo_and_diff(self):
        self.assertEqual(self.snapshot['coverage'], {'universe': 4, 'prices': 3, 'valued': 3, 'pending': 1, 'events': 1})
        self.assertEqual(len(core.read_runs(self.base)['items']), 2)
        by_code = {r['code']: r for r in self.snapshot['companies']}
        self.assertEqual(by_code['DEMO1']['valuation']['lbo']['status'], 'ok')
        self.assertEqual(by_code['DEMO2']['valuation']['standalone']['status'], 'ok')
        self.assertIsNone(by_code['DEMO2']['valuation']['discount_to_base']['value'])
        self.assertEqual(by_code['DEMO3']['status'], 'event')
        self.assertEqual(self.snapshot['diff']['removed'][0]['code'], 'DEMO3')
        self.assertEqual(self.snapshot['network_mode'], 'offline')
        self.assertEqual(self.snapshot['paid_provider_requests'], 0)
        content = json.dumps(self.snapshot)
        self.assertNotIn(str(self.base), content)
        self.assertNotIn('raw_relpath', content)
        self.assertNotIn('api_key', content)

    def test_duplicate_batch_is_idempotent_and_preview_does_not_write_records(self):
        count = self.count()
        self.assertEqual(core.import_bundle(self.base / 'demo-input-initial', self.base, demo=True)['status'], 'duplicate')
        rows = self.original_rows('prices')
        rows[0]['value'] = '601'
        directory = self.update('prices', rows)
        self.assertEqual(core.import_bundle(directory, self.base, demo=True, dry_run=True)['status'], 'preview')
        self.assertEqual(self.count(), count)

    def test_invalid_second_row_rejects_entire_batch(self):
        count = self.count()
        rows = self.original_rows('facts')[:2]
        rows[0]['value'] = '1200000001'
        rows[1]['value'] = 'NaN'
        with self.assertRaisesRegex(ValueError, 'facts.csv 3行'):
            core.import_bundle(self.update('facts', rows), self.base, demo=True)
        self.assertEqual(self.count(), count)

    def test_conflicting_same_time_fact_blocks_valuation(self):
        row = self.original_rows('facts')[0]
        row['value'] = '1234567890'
        core.import_bundle(self.update('facts', [row]), self.base, demo=True)
        core.build(date.today().isoformat(), self.base)
        company = core.read_snapshot(self.base)['companies'][0]
        self.assertEqual(company['valuation']['standalone']['status'], 'pending')
        self.assertEqual(next(f for f in company['facts'] if f['metric'] == 'ebit')['quality_status'], 'conflicting')

    def test_future_prices_and_inputs_do_not_leak_to_past(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        # The real observation date is today even for an older public report.
        self.assertFalse(core.visible({'public_at': '2020-01-01', 'observed_at': core.now()}, yesterday))
        self.assertFalse(core.visible({'as_of': '2020-01-01', 'observed_at': core.now()}, yesterday))
        with self.assertRaisesRegex(ValueError, '巻き戻せません'):
            core.build(yesterday, self.base)
        self.assertEqual(core.read_status(self.base)['latest_success_run_id'], self.snapshot['run_id'])

    def test_conflicting_price_is_pending_until_explicit_correction(self):
        with (self.base / 'demo-input-update/prices.csv').open(encoding='utf-8-sig', newline='') as handle:
            row = next(csv.DictReader(handle))
        row['value'] = '631'
        core.import_bundle(self.update('prices', [row]), self.base, demo=True)
        core.build(date.today().isoformat(), self.base)
        company = core.read_snapshot(self.base)['companies'][0]
        self.assertEqual(company['price']['quality_status'], 'conflicting')
        self.assertIsNone(company['valuation']['discount_to_base']['value'])

    def test_equivalent_price_decimal_notation_does_not_create_conflict(self):
        with (self.base / 'demo-input-update/prices.csv').open(encoding='utf-8-sig', newline='') as handle:
            row = next(csv.DictReader(handle))
        row['value'] += '.00'
        core.import_bundle(self.update('prices', [row]), self.base, demo=True)
        core.build(date.today().isoformat(), self.base)
        company = core.read_snapshot(self.base)['companies'][0]
        self.assertEqual(company['price']['quality_status'], 'verified')
        self.assertEqual(company['valuation']['discount_to_base']['status'], 'ok')

    def test_newer_effective_membership_wins_over_later_publication_of_old_list(self):
        row = self.original_rows('securities')[0]
        removal = dict(row, included='false', as_of=date.today().isoformat())
        old_list = dict(row, included='true', source_id='demo-update')
        core.import_bundle(self.update('securities', [removal, old_list]), self.base, demo=True)
        core.build(date.today().isoformat(), self.base)
        self.assertNotIn('DEMO1', [c['code'] for c in core.read_snapshot(self.base)['companies']])

    def test_failed_build_keeps_last_good_snapshot_and_records_failure(self):
        doc = next(p for p in (self.base / 'raw').rglob('*.txt'))
        doc.write_text('changed', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, '原本が変更'):
            core.build(date.today().isoformat(), self.base)
        status = core.read_status(self.base)
        self.assertEqual(status['last_attempt']['status'], 'failed')
        self.assertEqual(status['latest_success_run_id'], self.snapshot['run_id'])
        self.assertEqual(core.read_snapshot(self.base), self.snapshot)

    def test_original_snapshot_is_immutable_after_next_run(self):
        old = self.base / 'published' / self.snapshot['run_id'] / 'snapshot.json'
        digest_before = core.digest(old.read_bytes())
        core.build(date.today().isoformat(), self.base)
        self.assertEqual(core.digest(old.read_bytes()), digest_before)
        self.assertEqual(core.read_snapshot(self.base, self.snapshot['run_id']), self.snapshot)

    def test_missing_source_bytes_downgrades_verified_to_pending(self):
        folder = Path(self.temp.name) / 'no-bytes'
        folder.mkdir()
        write_csv(folder / 'documents.csv', [{'source_id': 'unverified', 'file': '', 'title': '原本未保存',
                  'source_url': 'https://example.com/report?token=redacted', 'published_at': date.today().isoformat()}], core.HEADERS['documents'])
        row = self.original_rows('prices')[0]
        row.update(source_id='unverified', public_at=date.today().isoformat(), price_at=date.today().isoformat())
        write_csv(folder / 'prices.csv', [row], core.HEADERS['prices'])
        core.import_bundle(folder, self.base, demo=True)
        core.build(date.today().isoformat(), self.base)
        company = core.read_snapshot(self.base)['companies'][0]
        self.assertEqual(company['price']['quality_status'], 'pending')
        self.assertIsNone(company['valuation']['discount_to_base']['value'])
        source = next(e for e in company['evidence'] if e['source_id'] == 'unverified')
        self.assertEqual(source['source_url'], 'https://example.com/report')

    def test_locate_verifies_hash_backup_copies_database_and_evidence(self):
        document = self.snapshot['companies'][0]['evidence'][0]
        path = Path(core.locate(document['document_id'], self.base))
        self.assertEqual(core.digest(path.read_bytes()), document['sha256'])
        target = Path(self.temp.name) / 'backup'
        result = core.backup(target, self.base)
        self.assertGreater(result['files'], 5)
        conn = core.connection(target)
        self.assertEqual(conn.execute('SELECT COUNT(*) FROM run').fetchone()[0], 2)
        conn.close()
        self.assertEqual(core.read_snapshot(target), self.snapshot)

    def test_backup_cannot_write_into_source_database_or_raw_tree(self):
        before = {str(p.relative_to(self.base)): core.digest(p.read_bytes())
                  for p in self.base.rglob('*') if p.is_file()}
        for target in (self.base, self.base / 'backup', self.base / 'raw' / 'backup'):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, '保存先の外'):
                core.backup(target, self.base)
        after = {str(p.relative_to(self.base)): core.digest(p.read_bytes())
                 for p in self.base.rglob('*') if p.is_file()}
        self.assertEqual(after, before)

    def test_private_files_and_directories_have_owner_only_permissions(self):
        for path in self.base.rglob('*'):
            if path.name.startswith('demo-input'):
                continue
            mode = path.stat().st_mode & 0o777
            self.assertEqual(mode & 0o077, 0, str(path))

    def test_demo_and_real_data_cannot_be_combined(self):
        with self.assertRaisesRegex(ValueError, '別の保存先'):
            core.import_bundle(self.base / 'demo-input-initial', self.base)


class MboEmptyAndSecurityTests(unittest.TestCase):
    def test_mbo_entry_never_initializes_cloud_assets_or_billing_and_ignores_port_env(self):
        from backend.server import main
        with patch.dict(os.environ, {'PORT': 'invalid', 'ASSET_STATE_BUCKET': 'unused'}, clear=True):
            with patch.dict('sys.modules', {'backend.assets': None, 'backend.costs': None, 'backend.cloud': None}):
                with patch('sys.argv', ['server', '--mode', 'mbo-local']):
                    with patch('backend.mbo.http.serve') as serve:
                        main()
                        self.assertEqual(serve.call_args.kwargs['port'], 4331)
        with patch.dict(os.environ, {'K_SERVICE': ''}, clear=True):
            with patch('sys.argv', ['server', '--mode', 'mbo-local']):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    main()

    def test_complete_demo_pipeline_never_needs_a_network_socket(self):
        with TemporaryDirectory() as temp:
            with patch('socket.socket', side_effect=AssertionError('network forbidden')):
                result = demo(Path(temp) / 'offline')
                self.assertTrue(result['fictional'])
                self.assertEqual(result['current']['coverage']['valued'], 3)

    def test_reads_do_not_create_storage_and_templates_work_without_network(self):
        with TemporaryDirectory() as temp:
            base = Path(temp) / 'absent'
            with patch('socket.create_connection', side_effect=AssertionError('network forbidden')):
                self.assertEqual(core.read_status(base)['storage_state'], 'empty')
                self.assertEqual(core.read_runs(base)['total'], 0)
                self.assertFalse(base.exists())
                templates(Path(temp) / 'templates')
                core.init(base)
                self.assertEqual(core.read_status(base)['storage_state'], 'empty')

    def test_input_symlink_and_raw_traversal_rejected(self):
        with TemporaryDirectory() as temp:
            base = Path(temp)
            outside = base / 'secret.txt'
            outside.write_text('do not ingest')
            bundle = base / 'bundle'
            bundle.mkdir()
            (bundle / 'linked.txt').symlink_to(outside)
            for file in ('../secret.txt', str(outside), 'linked.txt'):
                write_csv(bundle / 'documents.csv', [{'source_id': 'x', 'file': file, 'title': 'x',
                          'source_url': '', 'published_at': date.today().isoformat()}], core.HEADERS['documents'])
                with self.assertRaises(ValueError):
                    core.import_bundle(bundle, base / 'data')
            self.assertFalse((base / 'data/state.sqlite').exists())

    def test_oversized_csv_cell_returns_validation_error_without_traceback(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp) / 'input'
            directory.mkdir()
            (directory / 'documents.csv').write_text('source_id,title,published_at\nx,' + 'x' * 200000 + ',2026-01-01\n')
            with self.assertRaisesRegex(ValueError, 'documents.csv: CSV'):
                core.import_bundle(directory, Path(temp) / 'data')

    def test_mbo_assets_excluded_from_dashboard_and_cloud_staging(self):
        assets = shell_assets(core.ROOT / 'web')
        for name in ('mbo.html', 'mbo.css'):
            self.assertNotIn('/' + name, assets)
        self.assertIn('/mbo-app.js', assets)


if __name__ == '__main__':
    unittest.main()
