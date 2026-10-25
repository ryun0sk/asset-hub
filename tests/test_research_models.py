"""Offline regression checks for dated research model arithmetic and attribution."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_model():
    path = ROOT / 'research/themes/ai-valuation-ranking/2026-10-18/build_model.py'
    spec = importlib.util.spec_from_file_location('dated_ranking_model', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RankingModelRegressionTests(unittest.TestCase):
    def test_string_source_url_is_preserved_when_another_source_is_present(self):
        model = load_model()
        sources = model.sources_for({'anchor_facts': [{
            'sourceURLs': 'https://example.com/first', 'url': 'https://example.com/second'}]})
        self.assertEqual([source['url'] for source in sources],
                         ['https://example.com/first', 'https://example.com/second'])

    def test_zero_gap_sorts_above_a_negative_gap_and_missing_value(self):
        model = load_model()
        def company(gap):
            return {'scenarios': {'2029': {'base': {'entry_price_gap_pct': gap}}}}
        values = [company(-1), company(None), company(0), company(10)]
        ordered = sorted(values, key=model.ranking_gap, reverse=True)
        self.assertEqual([row['scenarios']['2029']['base']['entry_price_gap_pct'] for row in ordered],
                         [10, 0, -1, None])


if __name__ == '__main__':
    unittest.main()
