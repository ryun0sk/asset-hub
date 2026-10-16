"""Dated Advantest actual diluted EPS/PER history; saved inputs only, no network.

TTM uses annual plus current YTD minus prior YTD profit and quarter-weighted
diluted denominators. Rolling half-years use the latest two reported quarters.
Some denominators are inferred; the post-CB numerator adjustment is unpublished.
This is an independent approximation, not company-published TTM or guidance.
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
        if p['current']:
            current, prior = f[p['current']], f[p['prior']]
            ni += current['netIncomeJPYMillion'] - prior['netIncomeJPYMillion']
            shares += p['weight'] * (current['dilutedWeightedShares'] - prior['dilutedWeightedShares'])
        eps = ni * 1e6 / shares
        half_ni = sum(f[key]['netIncomeJPYMillion'] * n for key, n, _ in terms)
        half_shares = sum(f[key]['dilutedWeightedShares'] * w for key, _, w in terms)
        half_eps = half_ni * 1e6 / half_shares * 2
        assert abs(eps - p['ttmDilutedEPSJPY']) < 1e-8
        assert half_ni == p['halfYearNetIncomeJPYMillion']
        assert abs(half_eps - p['halfYearAnnualizedDilutedEPSJPY']) < 1e-8
        p.update(ttmNetIncomeJPYMillion=ni, ttmDilutedWeightedShares=shares,
                 ttmDilutedEPSJPY=eps, halfYearAnnualizedDilutedEPSJPY=half_eps,
                 halfYearDilutedWeightedShares=half_shares)
        # Exact H1 denominators were disclosed after the earnings release.
        p['latestSourceDate'] = '2025-11-13' if not phases else p['asOfReportDate']
        phases.append(p)

    rows = []
    prices = snapshot['prices']['daily_prices']
    assert len({r['date'] for r in prices}) == len(prices)
    assert prices == sorted(prices, key=lambda r: r['date'])
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
    assert rows[-1]['date'] == '2026-10-15' and rows[-1]['closeJPY'] == 34340
    assert abs(rows[-1]['ttmDilutedEPSJPY'] - 630.24) < .02
    for release, effective in [('2026-01-28', '2026-01-29'),
                               ('2026-04-27', '2026-04-28'),
                               ('2026-07-29', '2026-07-30')]:
        before = next(r for r in rows if r['date'] == release)
        after = next(r for r in rows if r['date'] == effective)
        assert before['reportDate'] < release and after['reportDate'] == release
    result = dict(asOf=snapshot['asOf'], definition=snapshot['definition'], phases=phases,
                  sources=facts['sources'], methodology=facts['methodology'],
                  numeratorReview=facts['numeratorReview'], priceSource=snapshot['prices']['source_url'],
                  priceRetrievedAt=snapshot['prices']['retrieved_at_utc'],
                  externalCrossCheck=facts['externalCrossCheck'],
                  firstTradingDay=rows[0], monthEndsAndLatest=list(month_ends.values()), daily=rows)
    (BASE / 'eps-per-history.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for filename, data in [('eps-per-history.csv', rows), ('eps-per-monthly.csv', monthly)]:
        with (BASE / filename).open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(data)
    return monthly


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))
