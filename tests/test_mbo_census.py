"""Acceptance checks for the reviewed historical census, independent of the UI."""
from collections import Counter
from contextlib import redirect_stdout
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch
from scripts import build_mbo_census as builder
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'research/themes/mbo-evaluation/2026-10-18/census-2021-2026'

class HistoricalCensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((FOLDER / 'census.json').read_text())
        cls.rows = cls.data['cases']

    def test_confirmed_population_has_unique_episodes_and_primary_reason_locations(self):
        self.assertGreaterEqual(len(self.rows), 100)
        self.assertEqual(len({r['case_id'] for r in self.rows}), len(self.rows))
        self.assertEqual(len({(r['code'], r['first_formal_mbo_announcement_date']) for r in self.rows}), len(self.rows))
        for r in self.rows:
            self.assertTrue('2021-01-01' <= r['first_formal_mbo_announcement_date'] <= self.data['as_of'])
            self.assertTrue(r['formal_date_source_ids'] and r['formal_date_locator'])
            self.assertTrue(r['public_motives'])
            for evidence in r['public_motives'] + r['observed_obstacles']:
                self.assertTrue(evidence['text'] and evidence['locator'] and evidence['source_ids'])
                for sid in evidence['source_ids']:
                    source = self.data['sources'][sid]
                    self.assertTrue(source['url'].startswith('https://'))
                    self.assertTrue(source.get('public_at') is None or source['public_at'] <= self.data['as_of'])

    def test_no_tob_transactions_and_delisting_only_evidence_never_invent_tob_results(self):
        equivalent = [r for r in self.rows if r['census']['scope_class'] == 'mbo_equivalent_no_tob']
        self.assertEqual({r['code'] for r in equivalent}, {'7338', '4349'})
        for r in equivalent:
            self.assertEqual(r['outcome']['mbo_tob_status'], 'not_applicable')
            self.assertNotIn('mbo_tob_result_date', r['outcome'])
        for r in self.rows:
            outcome = r['outcome']
            if outcome.get('result_kind') == 'delisting_observed' and r not in equivalent:
                self.assertEqual(outcome['mbo_tob_status'], 'unknown')
                self.assertNotIn('mbo_tob_result_date', outcome)
                self.assertEqual(outcome['completion_evidence'], 'exchange_delisting')
            if outcome.get('actual_delisting_date'):
                self.assertLessEqual(outcome['actual_delisting_date'], self.data['as_of'])
                self.assertTrue(outcome['delisting_source_ids'], r['name'])

    def test_retries_failures_and_report_boundaries_stay_separate(self):
        failures = [r for r in self.rows if r['census']['status'] == 'failed']
        self.assertEqual({r['code'] for r in failures}, {'3408', '7946', '3919', '3001', '7523', '4464'})
        for code in ['3408', '3919', '7523']:
            attempts = [r for r in self.rows if r['code'] == code]
            self.assertEqual(len(attempts), 2)
            self.assertEqual({r['census']['status'] for r in attempts}, {'failed', 'succeeded'})
        snow = next(r for r in self.rows if r['code'] == '7816')
        self.assertEqual(snow['first_official_disclosure_date'], '2024-02-16')
        self.assertEqual(snow['first_formal_mbo_announcement_date'], '2024-02-20')
        self.assertIn('インフォリッチ', next(r for r in self.rows if r['code'] == '9338')['aliases'])
        self.assertFalse(any(r['code'] == '3681' for r in self.rows))
        self.assertTrue(any(r['code'] == '3681' for r in self.data['references']))

    def test_counts_reconcile_with_explicit_scope_and_motive_frequency_denominator(self):
        expected = {2021: 17, 2022: 11, 2023: 17, 2024: 18, 2025: 31}
        for row in self.data['yearly']:
            if row['year'] in expected:
                self.assertEqual(row['tse_episodes'], expected[row['year']])
            self.assertEqual(row['episodes'], row['formal_mbo'] + row['equivalent_no_tob'])
            self.assertEqual(row['market_unconfirmed'], 0)
        counted = Counter(category for r in self.rows if r['census']['verification']['motive'] == 'verified'
                          for category in set(r['census']['motive_categories']))
        for category, amount in self.data['motive_counts'].items():
            self.assertEqual(amount, counted[category])

class CensusBuilderValidationTests(unittest.TestCase):
    def fixture(self, folder, **changes):
        row = {'episode_id': 'fictional-2026', 'code': '9999', 'name': '架空会社',
               'announcement_date': '2026-01-01', 'announcement_locator': '1頁',
               'announcement_source_ids': ['source-test'], 'result_date': '2026-02-01',
               'result_source_ids': ['source-test'], 'result_locator': '2頁',
               'outcome_status': 'succeeded', 'is_tse': True,
               'verification': {'announcement': 'verified', 'motive': 'verified', 'outcome': 'verified'},
               'sources': [{'source_id': 'source-test', 'url': 'https://example.com/fictional.pdf',
                            'public_at': '2026-01-01'}],
               'motives': [{'category': 'succession', 'text': '架空の承継説明',
                            'source_ids': ['source-test'], 'locator': '1頁'}], **changes}
        (folder / 'years-test.json').write_text(json.dumps({'episodes': [row]}))
        (folder / 'root-boundary-checks.json').write_text('{}')
        (folder.parent / 'cases-research.json').write_text('{"cases": [], "sources": {}}')
        (folder.parent / 'inforich-supplement.json').write_text(json.dumps({
            'case': {'code': '0000', 'first_formal_mbo_announcement_date': None}, 'sources': {}}))

    def build(self, **changes):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / 'census'
            folder.mkdir()
            (root / 'web').mkdir()
            self.fixture(folder, **changes)
            with patch.object(builder, 'ROOT', root), patch.object(builder, 'FOLDER', folder), redirect_stdout(StringIO()):
                builder.build()
            return json.loads((folder / 'census.json').read_text())

    def test_future_results_and_invalid_calendar_dates_are_not_exported(self):
        for change in ({'result_date': '2026-10-19'}, {'result_date': '2026-02-30'},
                       {'announcement_date': '2026-02-30'}, {'delisting_date': '2026-10-19'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.build(**change)

    def test_invalid_source_dates_cannot_be_used_to_classify_availability(self):
        sources = [{'source_id': 'source-test', 'url': 'https://example.com/fictional.pdf',
                    'public_at': '2026-02-30'}]
        with self.assertRaisesRegex(ValueError, 'source.public_at'):
            self.build(sources=sources)

    def test_future_delisting_plan_stays_a_plan(self):
        result = self.build(planned_delisting_date='2026-11-01')
        outcome = result['cases'][0]['outcome']
        self.assertEqual(outcome['planned_delisting_date'], '2026-11-01')
        self.assertNotIn('actual_delisting_date', outcome)


if __name__ == '__main__':
    unittest.main()
