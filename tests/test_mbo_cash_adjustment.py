"""Analyst cash adjustments remain distinct from reported operating facts."""
import unittest
from backend.mbo.core import _fact_set
from backend.mbo.valuation import evaluate
from tests.test_mbo_valuation import inputs


def row(metric, kind='actual', value='100', **changes):
    return dict(metric=metric, fact_kind=kind, value=value, unit='JPY', currency='JPY',
                quality_status='verified', consolidation='standalone',
                period_start='2025-04-01', period_end='2026-03-31',
                public_at='2026-05-15', **changes)


class CashAdjustmentTest(unittest.TestCase):
    def test_only_explicit_cash_adjustment_enters_and_classification_survives(self):
        facts, _ = _fact_set([row('ebit'), row('excess_cash', 'own_scenario', '70'),
                              row('ebit', 'own_scenario', '900'),
                              row('delta_nwc', 'company_forecast', '0')], '2026-10-18')
        self.assertEqual(facts['ebit']['value'], '100')
        self.assertNotIn('delta_nwc', facts)
        self.assertEqual(facts['excess_cash']['fact_kind'], 'own_scenario')
        self.assertEqual(facts['excess_cash']['value'], '70')

    def test_cash_must_match_scope_period_availability_and_conflicts_block(self):
        anchor = row('ebit')
        for change in ({'consolidation': 'consolidated'}, {'period_end': '2025-03-31'},
                       {'public_at': '2026-10-19'}, {'fact_kind': 'company_forecast'}):
            adjustment = row('excess_cash', 'own_scenario') | change
            self.assertNotIn('excess_cash', _fact_set([anchor, adjustment], '2026-10-18')[0])
        facts, _ = _fact_set([anchor, row('excess_cash', 'own_scenario', '70'),
                              row('excess_cash', 'own_scenario', '71')], '2026-10-18')
        self.assertEqual(facts['excess_cash']['quality_status'], 'conflicting')

    def test_reported_cash_never_becomes_surplus_automatically_and_policy_is_visible(self):
        facts, _ = _fact_set([row('ebit'), row('cash_and_equivalents', value='1000')], '2026-10-18')
        self.assertNotIn('excess_cash', facts)
        facts, scenarios, price = inputs()
        facts['excess_cash']['fact_kind'] = 'own_scenario'
        facts['excess_cash']['period_end'] = '2026-03-31'
        facts['cash_and_equivalents'] = row('cash_and_equivalents', value='500')
        result = evaluate(facts, scenarios, price, '2026-10-18')
        self.assertIn('会社実績ではなく', result['standalone']['scenarios'][1]['assumptions']['equity_bridge'])

    def test_latest_balance_sheet_does_not_mix_consolidation_or_replace_annual_operations(self):
        rows = [row('ebit'), row('debt', value='10'), row('cash_and_equivalents', value='500'),
                row('debt', value='20') | {'period_end': '2026-06-30', 'public_at': '2026-08-10'},
                row('debt', value='80') | {'period_end': '2026-09-30', 'public_at': '2026-10-10', 'consolidation': 'consolidated'},
                row('cash_and_equivalents', value='400') | {'period_end': '2026-06-30', 'public_at': '2026-08-10'}]
        facts, _ = _fact_set(rows, '2026-10-18')
        self.assertEqual(facts['ebit']['period_end'], '2026-03-31')
        self.assertEqual(facts['debt']['value'], '20')
        self.assertEqual(facts['cash_and_equivalents']['value'], '400')
        self.assertNotIn('noncontrolling_interest', facts)

    def test_mixed_bridge_dates_and_cash_overclaim_are_blocked(self):
        facts, scenarios, price = inputs()
        for key in ('excess_cash', 'debt', 'noncontrolling_interest'):
            facts[key]['period_end'] = '2026-03-31'
        facts['debt']['period_end'] = '2026-06-30'
        self.assertEqual(evaluate(facts, scenarios, price, '2026-10-18')['discount_to_base']['status'], 'pending')
        facts['debt']['period_end'] = '2026-03-31'
        facts['excess_cash']['fact_kind'] = 'own_scenario'
        facts['cash_and_equivalents'] = row('cash_and_equivalents', value='90')
        self.assertEqual(evaluate(facts, scenarios, price, '2026-10-18')['standalone']['status'], 'pending')
        facts['cash_and_equivalents']['value'] = '100'
        self.assertEqual(evaluate(facts, scenarios, price, '2026-10-18')['standalone']['status'], 'ok')
        facts['ebit']['fact_kind'] = 'own_scenario'
        self.assertEqual(evaluate(facts, scenarios, price, '2026-10-18')['standalone']['status'], 'pending')

    def test_working_capital_release_is_not_repeated_in_dcf_or_lbo(self):
        facts, scenarios, price = inputs()
        baseline = evaluate(facts, scenarios, price, '2026-10-18')
        facts['delta_nwc']['value'] = '-200'
        released = evaluate(facts, scenarios, price, '2026-10-18')
        self.assertEqual(facts['delta_nwc']['value'], '-200')
        self.assertEqual(released['standalone'], baseline['standalone'])
        self.assertEqual(released['lbo'], baseline['lbo'])

    def test_forward_capex_floor_preserves_reported_low_investment(self):
        facts, scenarios, price = inputs()
        baseline = evaluate(facts, scenarios, price, '2026-10-18')
        facts['capex']['value'] = '50'
        lower = evaluate(facts, scenarios, price, '2026-10-18')
        self.assertEqual(facts['capex']['value'], '50')
        self.assertEqual(lower['standalone'], baseline['standalone'])
        self.assertEqual(lower['lbo'], baseline['lbo'])

    def test_explicit_share_rollforward_keeps_original_report_and_estimate_classification(self):
        reported = row('shares_diluted', value='100') | {'unit': 'shares', 'share_basis': 'current'}
        estimated = reported | {'value': '105', 'fact_kind': 'own_scenario',
                                'period_end': '2026-08-07', 'public_at': '2026-10-18'}
        facts, selected = _fact_set([row('ebit'), reported, estimated], '2026-10-18')
        self.assertEqual(facts['shares_diluted']['fact_kind'], 'own_scenario')
        self.assertEqual(facts['shares_diluted']['value'], '105')
        self.assertIn(reported, selected)
        facts, scenarios, price = inputs()
        facts['shares_diluted']['fact_kind'] = 'own_scenario'
        self.assertEqual(evaluate(facts, scenarios, price, '2026-10-18')['standalone']['status'], 'ok')


if __name__ == '__main__':
    unittest.main()
