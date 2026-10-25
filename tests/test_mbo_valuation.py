"""All companies, numbers, financing terms and prices here are fictional."""

import copy
import json
import unittest
from decimal import Decimal as D, localcontext

from backend.mbo.valuation import evaluate


def inputs():
    values = {
        'ebit': '1000', 'depreciation': '200', 'capex': '200',
        'delta_nwc': '0', 'excess_cash': '100', 'debt': '300',
        'noncontrolling_interest': '0', 'shares_diluted': '100',
    }
    facts = {key: {'value': value, 'quality_status': 'verified', 'currency': 'JPY',
                   'unit': 'shares' if key == 'shares_diluted' else 'JPY'}
             for key, value in values.items()}
    facts['shares_diluted']['share_basis'] = '2026-10-01'
    params = {
        'horizon_years': 5, 'revenue_growth': '0', 'tax_rate': '0.3',
        'wacc': '0.1', 'terminal_growth': '0', 'entry_debt_multiple': '2',
        'debt_interest': '0.04', 'debt_amortization': '0.1',
        'exit_multiple': '6', 'target_irr': '0.2', 'fee_rate': '0.02',
        'rollover_ratio': '0', 'minimum_cash': '0',
    }
    scenarios = [dict(params, name=name) for name in ('bear', 'base', 'bull')]
    price = {'value': '50', 'currency': 'JPY', 'price_at': '2026-10-17',
             'share_basis': '2026-10-01', 'quality_status': 'verified'}
    return facts, scenarios, price


def calculate(facts=None, scenarios=None, price=None):
    default_facts, default_scenarios, default_price = inputs()
    return evaluate(facts if facts is not None else default_facts,
                    scenarios if scenarios is not None else default_scenarios,
                    price if price is not None else default_price, '2026-10-18')


class MboValuationTest(unittest.TestCase):
    def assertDecimalClose(self, actual, expected, tolerance='0.00000001'):
        self.assertLessEqual(abs(D(actual) - D(expected)), D(tolerance))

    def test_constant_fcff_perpetuity_and_equity_bridge(self):
        result = calculate()
        self.assertEqual(result['standalone']['status'], 'ok')
        for row in result['standalone']['scenarios']:
            # 700 recurring FCFF / 10%; equity = 7000 + 100 - 300.
            self.assertDecimalClose(row['enterprise_value'], '7000')
            self.assertDecimalClose(row['equity_value'], '6800')
            self.assertDecimalClose(row['value_per_share'], '68')
            self.assertEqual(row['yearly'][0]['fcff'], '700')
        self.assertDecimalClose(result['discount_to_base']['value'], D(1) - D(50) / D(68))

    def test_no_cash_double_counting(self):
        facts, scenarios, price = inputs()
        original = evaluate(facts, scenarios, price, '2026-10-18')
        facts['excess_cash']['value'] = '200'
        changed = evaluate(facts, scenarios, price, '2026-10-18')
        base = lambda result: D(result['standalone']['scenarios'][1]['equity_value'])
        self.assertDecimalClose(base(changed) - base(original), '100')

    def test_nonpositive_residual_equity_has_no_share_value_or_discount(self):
        for debt, expected_equity in [('2900', '0'), ('3000', '-100')]:
            with self.subTest(debt=debt):
                facts, scenarios, price = inputs()
                facts['debt']['value'] = debt
                # Constant FCFF 700 / 25% = EV 2800; + cash 100 - debt.
                # 1 / 1.25 is terminating, so the zero boundary is exact.
                for scenario in scenarios:
                    scenario['wacc'] = '0.25'
                result = evaluate(facts, scenarios, price, '2026-10-18')
                self.assertEqual(result['standalone']['status'], 'pending')
                for row in result['standalone']['scenarios']:
                    self.assertEqual(row['status'], 'infeasible')
                    self.assertIsNone(row['value_per_share'])
                    self.assertEqual(D(row['enterprise_value']), D('2800'))
                    self.assertEqual(D(row['equity_value']), D(expected_equity))
                    self.assertEqual(len(row['yearly']), 5)
                    self.assertEqual(row['yearly'][0]['fcff'], '700')
                    self.assertIn('残余株主価値', row['reasons'][0])
                self.assertEqual(result['discount_to_base']['status'], 'pending')
                self.assertIsNone(result['discount_to_base']['value'])
                self.assertIn('残余株主価値', result['discount_to_base']['reasons'][0])
                # The independently financed LBO remains unaffected by DCF WACC.
                for scenario in scenarios:
                    scenario['wacc'] = '0.1'
                positive_dcf = evaluate(facts, scenarios, price, '2026-10-18')
                self.assertEqual(positive_dcf['standalone']['status'], 'ok')
                for key in ('status', 'max_price_per_share', 'yearly', 'financing', 'reasons'):
                    self.assertEqual(result['lbo'].get(key), positive_dcf['lbo'].get(key))

    def test_missing_fact_not_zero_and_unverified_not_accepted(self):
        for mutation in ('missing', 'null', 'unverified', 'float'):
            with self.subTest(mutation=mutation):
                facts, scenarios, price = inputs()
                if mutation == 'missing':
                    del facts['delta_nwc']
                elif mutation == 'null':
                    facts['delta_nwc']['value'] = None
                elif mutation == 'unverified':
                    facts['delta_nwc']['quality_status'] = 'pending'
                else:
                    facts['delta_nwc']['value'] = 0.0
                result = evaluate(facts, scenarios, price, '2026-10-18')
                self.assertEqual(result['standalone']['status'], 'pending')
                self.assertIsNone(result['standalone']['scenarios'][1]['value_per_share'])
                self.assertEqual(result['lbo']['status'], 'pending')

    def test_invalid_fact_objects_remain_pending_instead_of_crashing(self):
        # CSV/JSON adapters may leave an entire field null, not just its value.
        for metric in ('ebit', 'depreciation', 'capex', 'delta_nwc', 'excess_cash',
                       'debt', 'noncontrolling_interest', 'shares_diluted'):
            for bad in (None, [], '100', 0):
                with self.subTest(metric=metric, bad=bad):
                    facts, scenarios, price = inputs()
                    facts[metric] = bad
                    result = evaluate(facts, scenarios, price, '2026-10-18')
                    self.assertEqual(result['standalone']['status'], 'pending')
                    self.assertEqual(result['lbo']['status'], 'pending')
                    self.assertEqual(result['discount_to_base']['status'], 'pending')
                    json.dumps(result, allow_nan=False)

    def test_invalid_discount_growth_shares_units_and_currency(self):
        for field, value in [('wacc', '0'), ('terminal_growth', '0.1'),
                             ('tax_rate', '1.2'), ('rollover_ratio', '1'),
                             ('revenue_growth', '-1'), ('minimum_cash', '0.5')]:
            with self.subTest(field=field):
                facts, scenarios, price = inputs()
                scenarios[1][field] = value
                result = evaluate(facts, scenarios, price, '2026-10-18')
                self.assertEqual(result['standalone']['scenarios'][1]['status'], 'pending')
        for metric, field, value in [('shares_diluted', 'value', '0'),
                                     ('shares_diluted', 'value', '-1'),
                                     ('ebit', 'unit', 'million JPY'),
                                     ('debt', 'currency', 'USD')]:
            with self.subTest(metric=metric, field=field):
                facts, scenarios, price = inputs()
                facts[metric][field] = value
                self.assertEqual(evaluate(facts, scenarios, price, '2026-10-18')['standalone']['status'], 'pending')

    def test_missing_and_duplicate_scenarios_remain_pending(self):
        facts, scenarios, price = inputs()
        del scenarios[1]['fee_rate']
        result = evaluate(facts, scenarios[:2], price, '2026-10-18')
        self.assertEqual(result['standalone']['scenarios'][1]['status'], 'pending')
        self.assertEqual(result['standalone']['scenarios'][2]['status'], 'pending')
        facts, scenarios, price = inputs()
        scenarios.append(dict(scenarios[1]))
        self.assertEqual(evaluate(facts, scenarios, price, '2026-10-18')['lbo']['status'], 'pending')

    def test_price_validation_only_blocks_discount(self):
        bad_prices = [None, {'value': '-1'}, {'value': '0'}, {'currency': 'USD'},
                      {'share_basis': 'different'}, {'price_at': '2026-10-19'},
                      {'price_at': '2026-10-03'}, {'price_at': 'bad'},
                      {'quality_status': 'pending'}]
        for change in bad_prices:
            with self.subTest(change=change):
                facts, scenarios, price = inputs()
                price = None if change is None else dict(price, **change)
                result = evaluate(facts, scenarios, price, '2026-10-18')
                self.assertEqual(result['standalone']['status'], 'ok')
                self.assertEqual(result['discount_to_base']['status'], 'pending')
                self.assertIsNone(result['discount_to_base']['value'])
        facts, scenarios, price = inputs()
        price['price_at'] = '2026-10-04'
        self.assertEqual(evaluate(facts, scenarios, price, '2026-10-18')['discount_to_base']['status'], 'ok')

    def test_future_facts_and_intraday_ready_time_are_blocked(self):
        for field in ('public_at', 'observed_at', 'ready_at', 'period_end'):
            facts, scenarios, price = inputs()
            facts['ebit'][field] = '2026-10-19'
            result = evaluate(facts, scenarios, price, '2026-10-18')
            self.assertEqual(result['standalone']['status'], 'pending')
        facts, scenarios, price = inputs()
        facts['ebit']['ready_at'] = '2026-10-18T13:01:00+09:00'
        self.assertEqual(evaluate(facts, scenarios, price, '2026-10-18T13:00:00+09:00')['standalone']['status'], 'pending')

    def test_lbo_sources_uses_and_analytical_target_price(self):
        result = calculate()['lbo']
        self.assertEqual(result['status'], 'ok')
        finance = result['financing']
        self.assertDecimalClose(finance['total_sources'], finance['total_uses'])
        self.assertEqual(finance['new_debt'], '2400')
        self.assertEqual(finance['existing_debt_refinanced'], '300')
        self.assertEqual(result['yearly'][0]['interest'], '96')
        self.assertEqual(result['yearly'][0]['repayment'], '240')
        self.assertDecimalClose(result['yearly'][0]['closing_cash'], '392.8')
        # Last-year debt 1200; cash sums five operating CFs less interest,
        # cash tax and scheduled repayment. Solve independently of bisection.
        cash = sum(D('1000') - D('2400') * (1 - D('0.1') * year) * D('0.04')
                   - (D('1000') - D('2400') * (1 - D('0.1') * year) * D('0.04')) * D('0.3')
                   - D('240') for year in range(5))
        exit_equity = D('7200') - D('1200') + cash
        maximum = (exit_equity / D('1.2') ** 5 - D('300') + D('2400') + D('100')) / D('1.02')
        self.assertDecimalClose(result['max_price_per_share'], maximum / 100)
        self.assertDecimalClose(finance['sponsor_npv_at_target_irr'], '0')

    def test_rollover_follows_contributions_and_does_not_create_value(self):
        facts, scenarios, price = inputs()
        original = evaluate(facts, scenarios, price, '2026-10-18')['lbo']
        scenarios[1]['rollover_ratio'] = '0.25'
        result = evaluate(facts, scenarios, price, '2026-10-18')['lbo']
        self.assertEqual(result['status'], 'ok')
        self.assertDecimalClose(result['max_price_per_share'], original['max_price_per_share'])
        finance = result['financing']
        self.assertDecimalClose(finance['total_sources'], finance['total_uses'])
        self.assertDecimalClose(D(finance['rollover_equity']), D(finance['purchase_equity_value']) * D('0.25'))
        self.assertNotEqual(D(finance['sponsor_ownership']), D('0.75'))
        self.assertDecimalClose(finance['sponsor_npv_at_target_irr'], '0')

    def test_cash_reserve_funded_once_returned_once(self):
        facts, scenarios, price = inputs()
        original = evaluate(facts, scenarios, price, '2026-10-18')['lbo']
        scenarios[1]['minimum_cash'] = '100'
        result = evaluate(facts, scenarios, price, '2026-10-18')['lbo']
        self.assertEqual(result['status'], 'ok')
        self.assertDecimalClose(D(result['yearly'][-1]['closing_cash']) - D(original['yearly'][-1]['closing_cash']), '100')
        # Retained idle capital is a real funding cost, not free acquisition cash.
        self.assertLess(D(result['max_price_per_share']), D(original['max_price_per_share']))

    def test_lbo_cannot_fund_mandatory_repayment(self):
        facts, scenarios, price = inputs()
        scenarios[1]['debt_amortization'] = '1'
        result = evaluate(facts, scenarios, price, '2026-10-18')
        self.assertEqual(result['standalone']['status'], 'ok')
        self.assertEqual(result['lbo']['status'], 'infeasible')
        self.assertIsNone(result['lbo']['max_price_per_share'])

    def test_minority_interest_is_not_silently_allocated_to_lbo_sponsor(self):
        facts, scenarios, price = inputs()
        facts['noncontrolling_interest']['value'] = '100'
        result = evaluate(facts, scenarios, price, '2026-10-18')
        self.assertDecimalClose(result['standalone']['scenarios'][1]['equity_value'], '6700')
        self.assertEqual(result['lbo']['status'], 'pending')

    def test_screening_proxy_does_not_replace_fcff(self):
        facts, scenarios, price = inputs()
        facts['operating_cfo'] = {'value': '999999', 'quality_status': 'verified', 'unit': 'JPY', 'currency': 'JPY'}
        facts['owner_ratio'] = {'value': '0.99', 'quality_status': 'verified', 'unit': 'ratio'}
        result = evaluate(facts, scenarios, price, '2026-10-18')
        self.assertDecimalClose(result['standalone']['scenarios'][1]['value_per_share'], '68')
        self.assertNotIn('mbo_probability', json.dumps(result))

    def test_deterministic_json_and_no_input_or_decimal_context_mutation(self):
        facts, scenarios, price = inputs()
        before = copy.deepcopy((facts, scenarios, price))
        with localcontext() as ctx:
            ctx.prec = 9
            first = evaluate(facts, scenarios, price, '2026-10-18')
            self.assertEqual(ctx.prec, 9)
        second = evaluate(facts, scenarios, price, '2026-10-18')
        self.assertEqual(first, second)
        self.assertEqual((facts, scenarios, price), before)
        json.dumps(first, allow_nan=False)

    def test_nonfinite_and_extreme_numbers_are_pending(self):
        for value in ('NaN', 'Infinity', '1e100', '1e-10000000'):
            with self.subTest(value=value):
                facts, scenarios, price = inputs()
                scenarios[1]['wacc'] = value
                result = evaluate(facts, scenarios, price, '2026-10-18')
                self.assertEqual(result['standalone']['scenarios'][1]['status'], 'pending')


if __name__ == '__main__':
    unittest.main()
