"""DISCO actual EPS/PER history using dated saved inputs, with no network.

TTM uses parent-attributable profit and quarter-weighted diluted denominators.
Rolling half-years are the latest two reported quarters, annualized by two.
Denominators are inferred from rounded public EPS; this is an approximation.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def build():
    snapshot = json.loads((BASE / 'eps-per-history-inputs.json').read_text())
    facts = snapshot['fundamentals']
    f = facts['inputs']
    half_terms = [
        [('FY2025H1', 1, 1)],
        [('FY2025Q3YTD', 1, 1.5), ('FY2025Q1', -1, -.5)],
        [('FY2025', 1, 2), ('FY2025H1', -1, -1)],
        [('FY2025', 1, 2), ('FY2025Q3YTD', -1, -1.5), ('FY2026Q1', 1, .5)],
    ]
    phases = []
    for original, terms in zip(facts['phases'], half_terms):
        p = dict(original)
        annual = f[p['annual']]
        ni, shares = annual['netIncomeJPYMillion'], annual['dilutedWeightedShares']
        eps_arithmetic = annual['dilutedEPSJPY']
        if p['current']:
            current, prior = f[p['current']], f[p['prior']]
            ni += current['netIncomeJPYMillion'] - prior['netIncomeJPYMillion']
            shares += p['weight'] * (current['dilutedWeightedShares'] - prior['dilutedWeightedShares'])
            eps_arithmetic += current['dilutedEPSJPY'] - prior['dilutedEPSJPY']
        eps = ni * 1e6 / shares
        half_ni = sum(f[key]['netIncomeJPYMillion'] * n for key, n, _ in terms)
        half_shares = sum(f[key]['dilutedWeightedShares'] * w for key, _, w in terms)
        half_eps = half_ni * 1e6 / half_shares * 2
        half_arithmetic = sum(f[key]['dilutedEPSJPY'] * n for key, n, _ in terms) * 2
        assert shares > 0 and half_shares > 0 and ni > 0 and half_ni > 0
        # An independent sum/difference of published EPS is close despite denominator changes.
        assert abs(eps-eps_arithmetic)/eps < .001
        assert abs(half_eps-half_arithmetic)/half_eps < .001
        p.update(ttmNetIncomeJPYMillion=ni, ttmDilutedWeightedShares=shares,
                 ttmDilutedEPSJPY=eps, halfYearNetIncomeJPYMillion=half_ni,
                 halfYearAnnualizedDilutedEPSJPY=half_eps, halfYearDilutedWeightedShares=half_shares,
                 publishedEPSArithmeticTTMJPY=eps_arithmetic,
                 publishedEPSArithmeticHalfYearAnnualizedJPY=half_arithmetic)
        phases.append(p)

    prices = snapshot['prices']['daily_prices']
    assert len({r['date'] for r in prices}) == len(prices)
    assert prices == sorted(prices, key=lambda r: r['date'])
    rows = []
    for price in prices:
        phase = max((p for p in phases if p['effectiveDate'] <= price['date']),
                    key=lambda p: p['effectiveDate'])
        assert phase['latestSourceDate'] < price['date']
        assert price['close'] > 0
        eps, half_eps = phase['ttmDilutedEPSJPY'], phase['halfYearAnnualizedDilutedEPSJPY']
        rows.append(dict(date=price['date'], closeJPY=price['close'],
                         ttmDilutedEPSJPY=eps, trailingPER=price['close'] / eps,
                         halfYearAnnualizedDilutedEPSJPY=half_eps,
                         halfYearAnnualizedPER=price['close'] / half_eps,
                         profitPeriodStart=phase['trailingStart'], profitPeriodEnd=phase['trailingEnd'],
                         halfYearProfitPeriodStart=phase['halfYearStart'],
                         halfYearProfitPeriodEnd=phase['halfYearEnd'],
                         reportDate=phase['asOfReportDate'], latestSourceDate=phase['latestSourceDate']))
    month_ends = {}
    for row in rows:
        month_ends[row['date'][:7]] = row
    monthly = [rows[0]] + list(month_ends.values())
    assert len(rows) == 190 and len(monthly) == 11
    assert rows[0]['date'] == '2026-01-05' and rows[0]['closeJPY'] == 51100
    assert rows[-1]['date'] == '2026-10-15' and rows[-1]['closeJPY'] == 53180
    for release, effective in [('2026-01-21','2026-01-22'),
                               ('2026-04-22','2026-04-23'),
                               ('2026-07-23','2026-07-24')]:
        before = next(r for r in rows if r['date'] == release)
        after = next(r for r in rows if r['date'] == effective)
        assert before['reportDate'] < release and after['reportDate'] == release
    result = dict(asOf=snapshot['asOf'], definition=snapshot['definition'], phases=phases,
                  sources=facts['sources'], methodology=facts['methodology'],
                  numeratorReview=facts['numeratorReview'], latestDisclosure=facts['latestDisclosure'],
                  priceSource=snapshot['prices']['source_url'], priceCorrections=snapshot['prices']['corrections'],
                  priceRetrievedAt=snapshot['prices']['retrieved_at_utc'],
                  firstTradingDay=rows[0], monthEndsAndLatest=list(month_ends.values()), daily=rows)
    (BASE / 'eps-per-history.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for filename, data in [('eps-per-history.csv', rows), ('eps-per-monthly.csv', monthly)]:
        with (BASE / filename).open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(data)
    return monthly


if __name__ == '__main__':
    for r in build():
        print(f"| {r['date']} | {r['closeJPY']:,.0f}円 | {r['ttmDilutedEPSJPY']:,.2f}円 | {r['trailingPER']:.1f}倍 | {r['halfYearAnnualizedDilutedEPSJPY']:,.2f}円 | {r['halfYearAnnualizedPER']:.1f}倍 |")
