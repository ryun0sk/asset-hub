"""Offline regression checks for the fixed 46-company current review."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'research/themes/ai-current-review/2026-11-06'


def load_builder():
    spec = importlib.util.spec_from_file_location('ai_current_review_builder', REVIEW / 'build_review.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CurrentReviewRegressionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        for filename in ('universe.json', 'prices.json'):
            shutil.copyfile(REVIEW / filename, self.base / filename)
        shutil.copytree(REVIEW / 'parts', self.base / 'parts')
        self.builder = load_builder()

    def build(self):
        with patch.object(self.builder, 'BASE', self.base), redirect_stdout(io.StringIO()):
            self.builder.main()

    def replace_input_rows(self, filename, transform):
        data = json.loads((REVIEW / filename).read_text())
        rows = data if filename == 'universe.json' else data['items']
        transform(rows)
        (self.base / filename).write_text(json.dumps(data), encoding='utf-8')

    def assert_rejected_before_output(self, filename):
        with self.assertRaisesRegex(ValueError, filename.replace('.', r'\.')):
            self.build()
        for filename in ('review.json', 'review.csv'):
            self.assertFalse((self.base / filename).exists(), 'invalid inputs must not publish a partial review')

    def test_saved_outputs_are_reproduced_without_network_access(self):
        self.build()
        for filename in ('review.json', 'review.csv'):
            self.assertEqual((self.base / filename).read_bytes(), (REVIEW / filename).read_bytes(), filename)
        companies = json.loads((self.base / 'review.json').read_text())['companies']
        self.assertEqual(len(companies), 46)
        self.assertEqual(len({company['symbol'] for company in companies}), 46)

    def test_duplicate_universe_symbols_are_rejected(self):
        for keep_row_count in (False, True):
            with self.subTest(keep_row_count=keep_row_count):
                def duplicate(rows):
                    if keep_row_count:
                        rows[-1] = rows[0]
                    else:
                        rows.append(rows[0])
                self.replace_input_rows('universe.json', duplicate)
                self.assert_rejected_before_output('universe.json')

    def test_duplicate_price_symbols_are_rejected(self):
        for keep_row_count in (False, True):
            with self.subTest(keep_row_count=keep_row_count):
                def duplicate(rows):
                    if keep_row_count:
                        rows[-1] = rows[0]
                    else:
                        rows.append(rows[0])
                self.replace_input_rows('prices.json', duplicate)
                self.assert_rejected_before_output('prices.json')

    def test_missing_universe_company_is_rejected(self):
        self.replace_input_rows('universe.json', lambda rows: rows.pop())
        self.assert_rejected_before_output('universe.json')

    def test_missing_price_company_is_rejected(self):
        self.replace_input_rows('prices.json', lambda rows: rows.pop())
        self.assert_rejected_before_output('prices.json')


if __name__ == '__main__':
    unittest.main()
