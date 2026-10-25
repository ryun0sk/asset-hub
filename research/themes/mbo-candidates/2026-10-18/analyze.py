"""Save the frozen result and independently check the flat base DCF identity."""
from pathlib import Path
from decimal import Decimal as D, localcontext
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from backend.mbo import core


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', default=str(ROOT / 'data/private/mbo'))
    args = parser.parse_args()
    folder = Path(__file__).parent
    inputs = json.loads((folder / 'research-inputs.json').read_text())
    snapshot = core.read_snapshot(args.data_dir)
    by_code = {c['code']: c for c in snapshot['companies']}
    checks = []
    with localcontext() as context:
        context.prec = 48
        for c in snapshot['companies']:
            base = next(s for s in c['valuation']['standalone']['scenarios'] if s['name'] == 'base')
            if base['status'] != 'ok':
                continue
            def fact(metric):
                rows = [r for r in c['facts'] if r['metric'] == metric]
                own = [r for r in rows if r['fact_kind'] == 'own_scenario']
                return D((own or rows)[0]['value'])
            fcf = fact('ebit') * D('.70') + fact('depreciation') - max(fact('capex'), fact('depreciation')) - max(fact('delta_nwc'), D(0))
            equity = fcf / D('.10') + fact('excess_cash') - fact('debt') - fact('noncontrolling_interest')
            independent = equity / fact('shares_diluted')
            assert abs(independent - D(base['value_per_share'])) < D('1e-30')
            checks.append({'code': c['code'], 'base_fcff_jpy': str(fcf),
                           'independent_equity_jpy': str(equity),
                           'independent_value_per_share_jpy': str(independent), 'passed': True})
        ten = by_code['5945']
        base = next(s for s in ten['valuation']['standalone']['scenarios'] if s['name'] == 'base')
        holdings = next(r for r in inputs['financial_review']['5945']['facts'] if r['metric'] == 'investment_securities')
        shares = D(next(r['value'] for r in ten['facts'] if r['metric'] == 'shares_diluted' and r['fact_kind'] == 'own_scenario'))
        asset_cases = []
        for recovery in (D('.50'), D('.70'), D('.90')):
            added = D(holdings['value']) * recovery
            equity = D(base['equity_value']) + added
            value = equity / shares
            market = D(ten['price']['value'])
            asset_cases.append({'recovery_assumption': str(recovery), 'additional_asset_value_jpy': str(added),
                                'value_per_share_jpy': str(value), 'discount_to_value': str(1-market/value),
                                'upside_from_price': str(value/market-1),
                                'headroom_before_additional_capex_pv_jpy': str(equity-market*shares)})
    result = {'schema_version': 1, 'as_of': snapshot['as_of'], 'run_id': snapshot['run_id'],
              'created_at': snapshot['created_at'], 'rule_version': snapshot['rule_version'],
              'research_input_sha256': hashlib.sha256((folder / 'research-inputs.json').read_bytes()).hexdigest(),
              'screened': 23, 'deep_researched': 6, 'coverage': snapshot['coverage'],
              'conclusion': '明確な割安MBO候補の確証なし。年次BSによる保守的参考DCF2社は保存価格を下回る。',
              'valuation_scope': '参考DCFは通期BS一式。最新中間BSを使った現行企業価値の確定ではない。金融資産の全額・買収プレミアムを加算していない。',
              'assumptions': {'bear': {'growth': '-0.02', 'wacc': '0.12', 'terminal_growth': '0'},
                              'base': {'growth': '0', 'wacc': '0.10', 'terminal_growth': '0'},
                              'bull': {'growth': '0.02', 'wacc': '0.08', 'terminal_growth': '0.01'},
                              'years': 5, 'tax': '0.30', 'forward_nwc': 'max(実績trade-NWC,0)',
                              'forward_capex': 'max(実績capex,減価償却)',
                              'rates_are_fixed_analyst_sensitivities': True},
              'independent_checks': checks, 'tenryu_additional_asset_sensitivity': {
                  'reported_investment_securities_jpy': holdings['value'], 'source_id': holdings['source_id'],
                  'basis': '2026/3末。会社の換金計画ではない。帳簿の50/70/90%を税・価格・換金費用等の一括控除後回収額とする独自感応度。建替え追加投資・将来損失は未控除。',
                  'cases': asset_cases},
              'companies': [{k: c[k] for k in ('code', 'name', 'status', 'priority', 'reasons', 'missing', 'facts', 'price', 'valuation', 'evidence')} for c in snapshot['companies']],
              'events': snapshot['events'],
              'excluded': [c for c in inputs['universe_review']['companies'] if not c['included']],
              'sources': inputs['public_sources']}
    (folder / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'run_id': snapshot['run_id'], 'coverage': snapshot['coverage'],
                      'independent_base_checks': len(checks), 'tenryu_asset_cases': asset_cases}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
