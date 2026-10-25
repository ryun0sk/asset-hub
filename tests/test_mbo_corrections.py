"""Append-only corrections over fictional hand-entered financial records."""

from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import csv
import json
import unittest

from backend.mbo import core


class MboCorrectionsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data = self.root / 'state'
        self.today = date.today()
        self.first = self.today - timedelta(days=7)
        self.period = self.today - timedelta(days=30)
        self.counter = 0
        self.initial_fact = {
            'code': 'FAKE1', 'exchange': 'DEMO', 'metric': 'ebit', 'value': '100',
            'unit': 'JPY', 'currency': 'JPY', 'period_start': (self.period - timedelta(days=364)).isoformat(),
            'period_end': self.period.isoformat(), 'fact_kind': 'actual', 'consolidation': 'consolidated',
            'share_basis': '', 'public_at': self.first.isoformat(), 'source_id': 'source1',
            'locator': '架空の表1', 'quality_status': 'verified', 'missing_reason': '',
        }
        self.initial_price = {
            'code': 'FAKE1', 'exchange': 'DEMO', 'value': '10', 'currency': 'JPY',
            'price_at': self.first.isoformat(), 'price_type': 'close', 'adjustment': 'unadjusted',
            'share_basis': 'fictional-basis', 'public_at': self.first.isoformat(),
            'source_id': 'source1', 'locator': '架空の株価表', 'quality_status': 'verified',
        }
        initial = self.bundle(
            documents=[{'source_id': 'source1', 'file': 'fictional.txt', 'title': '架空の原本',
                        'source_url': '', 'published_at': self.first.isoformat()}],
            securities=[{'code': code, 'exchange': 'DEMO', 'name': '架空' + code,
                         'security_type': 'common_stock', 'as_of': self.first.isoformat(),
                         'source_id': 'source1', 'included': 'true'} for code in ('FAKE1', 'FAKE2')],
            facts=[self.initial_fact], prices=[self.initial_price],
        )
        (initial / 'fictional.txt').write_text('仮想数値のみ。実在企業ではありません。', encoding='utf-8')
        self.import_at(initial, self.first)
        self.original_id = self.stored('facts')[0]['record_id']
        self.original_price_id = self.stored('prices')[0]['record_id']

    def bundle(self, **kinds):
        self.counter += 1
        directory = self.root / f'bundle-{self.counter}'
        directory.mkdir()
        for kind, rows in kinds.items():
            with (directory / (kind + '.csv')).open('w', encoding='utf-8', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=core.HEADERS[kind])
                writer.writeheader()
                writer.writerows(rows)
        return directory

    def import_at(self, directory, day, **kwargs):
        with patch.object(core, 'now', return_value=day.isoformat() + 'T12:00:00+09:00'):
            return core.import_bundle(directory, self.data, **kwargs)

    def stored(self, kind):
        conn = core.connection(self.data)
        try:
            return core.records(conn, kind)
        finally:
            conn.close()

    def corrected(self, **changes):
        return dict(self.initial_fact, value='200', supersedes=self.original_id,
                    correction_reason='架空原本との照合による誤転記訂正', **changes)

    def read_company(self, run):
        snapshot = core.read_snapshot(self.data, run['run_id'])
        return next(row for row in snapshot['companies'] if row['code'] == 'FAKE1')

    def test_append_only_correction_and_idempotent_reimport(self):
        before = self.stored('facts')[0]
        directory = self.bundle(facts=[self.corrected()])
        result = self.import_at(directory, self.today)
        self.assertEqual(result['status'], 'imported')
        after = self.stored('facts')
        self.assertEqual(after[0], before)
        self.assertEqual(after[-1]['supersedes'], self.original_id)
        self.assertEqual(after[-1]['value'], '200')
        self.assertEqual(self.import_at(directory, self.today)['status'], 'duplicate')
        self.assertEqual(len(self.stored('facts')), 2)
        run = core.build(self.today.isoformat(), self.data)
        dto = self.read_company(run)['facts'][0]
        self.assertEqual(dto['record_id'], after[-1]['record_id'])
        self.assertEqual(dto['correction_reason'], after[-1]['correction_reason'])
        manifest = json.loads((self.data / 'runs' / run['run_id'] / 'manifest.json').read_text())
        self.assertIn(self.original_id, manifest['input_ids'])
        self.assertIn(after[-1]['record_id'], manifest['input_ids'])

    def test_future_correction_does_not_rewrite_past_or_hide_old_value(self):
        old_run = core.build(self.first.isoformat(), self.data)
        frozen = self.data / 'published' / old_run['run_id'] / 'snapshot.json'
        original_bytes = frozen.read_bytes()
        self.import_at(self.bundle(facts=[self.corrected()]), self.today)
        replay = core.build(self.first.isoformat(), self.data)
        self.assertEqual(self.read_company(replay)['facts'][0]['value'], '100')
        current = core.build(self.today.isoformat(), self.data)
        self.assertEqual(self.read_company(current)['facts'][0]['value'], '200')
        self.assertEqual(frozen.read_bytes(), original_bytes)

    def test_explicit_correction_resolves_same_time_conflicting_values(self):
        wrong = dict(self.initial_fact, value='999')
        self.import_at(self.bundle(facts=[wrong]), self.first)
        conflict_run = core.build(self.first.isoformat(), self.data)
        self.assertEqual(self.read_company(conflict_run)['facts'][0]['quality_status'], 'conflicting')
        wrong_id = self.stored('facts')[-1]['record_id']
        corrected = dict(self.initial_fact, supersedes=wrong_id, correction_reason='原本の100へ訂正')
        self.import_at(self.bundle(facts=[corrected]), self.today)
        run = core.build(self.today.isoformat(), self.data)
        fact = self.read_company(run)['facts'][0]
        self.assertEqual(fact['quality_status'], 'verified')
        self.assertEqual(fact['value'], '100')
        self.assertEqual(len(self.stored('facts')), 3)

    def test_rejects_unknown_id_missing_reason_wrong_company_metric_or_period(self):
        changes = [
            {'supersedes': 'rec-unknown'}, {'correction_reason': ''}, {'code': 'FAKE2'},
            {'metric': 'capex'}, {'period_end': (self.period + timedelta(days=1)).isoformat()},
            {'supersedes': self.original_price_id},
        ]
        for change in changes:
            with self.subTest(change=change):
                row = self.corrected()
                row.update(change)
                with self.assertRaises(ValueError):
                    self.import_at(self.bundle(facts=[row]), self.today)
                self.assertEqual(len(self.stored('facts')), 1)

    def test_branch_rejected_and_latest_successor_can_be_corrected(self):
        first_correction = self.bundle(facts=[self.corrected()])
        self.import_at(first_correction, self.today)
        correction_id = self.stored('facts')[-1]['record_id']
        branch = self.corrected()
        branch['value'] = '300'
        with self.assertRaisesRegex(ValueError, '最新訂正record_id'):
            self.import_at(self.bundle(facts=[branch]), self.today)
        self.assertEqual(len(self.stored('facts')), 2)
        branch['supersedes'] = correction_id
        self.import_at(self.bundle(facts=[branch]), self.today)
        self.assertEqual(len(self.stored('facts')), 3)
        self.assertEqual(core.active_records(self.stored('facts'))[0]['value'], '300')

    def test_two_successors_in_one_batch_rejects_entire_batch(self):
        one, two = self.corrected(), self.corrected()
        two['value'] = '300'
        with self.assertRaisesRegex(ValueError, '分岐訂正不可'):
            self.import_at(self.bundle(facts=[one, two]), self.today)
        self.assertEqual(len(self.stored('facts')), 1)

    def test_price_correction_preserves_price_date_and_history(self):
        row = dict(self.initial_price, value='11', supersedes=self.original_price_id,
                   correction_reason='架空の終値を原本に合わせ訂正')
        invalid = dict(row, price_at=(self.first + timedelta(days=1)).isoformat())
        with self.assertRaisesRegex(ValueError, 'price_at'):
            self.import_at(self.bundle(prices=[invalid]), self.today)
        self.import_at(self.bundle(prices=[row]), self.today)
        history = self.stored('prices')
        self.assertEqual([r['value'] for r in history], ['10', '11'])
        run = core.build(self.today.isoformat(), self.data)
        self.assertEqual(self.read_company(run)['price']['value'], '11')
        self.assertEqual(self.read_company(run)['price']['record_id'], history[-1]['record_id'])

    def test_dry_run_validates_without_saving_or_consuming_target(self):
        bundle = self.bundle(facts=[self.corrected()])
        self.assertEqual(self.import_at(bundle, self.today, dry_run=True)['status'], 'preview')
        self.assertEqual(len(self.stored('facts')), 1)
        self.assertEqual(self.import_at(bundle, self.today)['status'], 'imported')

    def test_reason_without_target_is_not_silently_an_unrelated_new_value(self):
        row = dict(self.initial_fact, correction_reason='訂正のつもり')
        with self.assertRaisesRegex(ValueError, 'supersedes'):
            self.import_at(self.bundle(facts=[row]), self.today)


if __name__ == '__main__':
    unittest.main()
