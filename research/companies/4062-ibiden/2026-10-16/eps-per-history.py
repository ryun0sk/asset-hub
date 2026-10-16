"""Ibiden actual diluted EPS/PER history, rebuilt from saved inputs only.

Published cumulative diluted EPS is split-adjusted, then added/subtracted.
This avoids inventing unpublished quarterly convertible-bond adjustments.
It is an approximation rather than a company-published twelve-month EPS:
weighted diluted shares and dilutive instruments can differ between periods.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def build():
    snapshot = json.loads((BASE / 'eps-per-history-inputs.json').read_text())
    facts = snapshot['fundamentals']
    inputs = facts['inputs']
    phases = []
    for source in facts['phases']:
        phase = dict(source)
        for output_key, expression_key in [
            ('ttmDilutedEPSJPY', 'ttmTerms'),
            ('halfYearAnnualizedDilutedEPSJPY', 'halfYearAnnualizedTerms'),
            ('ttmBasicEPSJPY', 'ttmTerms'),
            ('halfYearAnnualizedBasicEPSJPY', 'halfYearAnnualizedTerms'),
        ]:
            diluted = 'Diluted' in output_key
            key = 'reportedDilutedEPSJPY' if diluted else 'reportedBasicEPSJPY'
            phase[output_key] = sum(
                inputs[name][key] / inputs[name]['remainingSplitFactor'] * multiplier
                for name, multiplier in phase[expression_key]
            )
        phase['ttmNetIncomeJPYMillion'] = sum(
            inputs[name]['netIncomeJPYMillion'] * multiplier
            for name, multiplier in phase['ttmTerms']
        )
        phase['halfYearNetIncomeJPYMillion'] = sum(
            inputs[name]['netIncomeJPYMillion'] * multiplier / 2
            for name, multiplier in phase['halfYearAnnualizedTerms']
        )
        assert phase['ttmDilutedEPSJPY'] > 0
        assert phase['halfYearAnnualizedDilutedEPSJPY'] > 0
        assert phase['asOfReportDate'] < phase['effectiveDate']
        phases.append(phase)

    prices = snapshot['prices']['daily_prices']
    assert len({row['date'] for row in prices}) == len(prices)
    assert prices == sorted(prices, key=lambda row: row['date'])
    rows = []
    for price in prices:
        phase = max((p for p in phases if p['effectiveDate'] <= price['date']),
                    key=lambda p: p['effectiveDate'])
        eps = phase['ttmDilutedEPSJPY']
        half_eps = phase['halfYearAnnualizedDilutedEPSJPY']
        assert phase['asOfReportDate'] < price['date'] and price['close'] > 0
        rows.append(dict(
            date=price['date'], closeJPY=price['close'],
            ttmDilutedEPSJPY=eps, trailingPER=price['close'] / eps,
            halfYearAnnualizedDilutedEPSJPY=half_eps,
            halfYearAnnualizedPER=price['close'] / half_eps,
            profitPeriodStart=phase['trailingStart'], profitPeriodEnd=phase['trailingEnd'],
            halfYearProfitPeriodStart=phase['halfYearStart'],
            halfYearProfitPeriodEnd=phase['halfYearEnd'],
            reportDate=phase['asOfReportDate'], latestSourceDate=phase['asOfReportDate'],
        ))
    month_ends = {}
    for row in rows:
        month_ends[row['date'][:7]] = row
    monthly = [rows[0]] + list(month_ends.values())
    assert len(rows) == 190 and len(monthly) == 11
    assert rows[0]['date'] == '2026-01-05'
    assert rows[-1]['date'] == '2026-10-15' and rows[-1]['closeJPY'] == 9213
    assert abs(rows[-1]['ttmDilutedEPSJPY'] - 116.395) < 1e-9
    assert abs(rows[-1]['halfYearAnnualizedDilutedEPSJPY'] - 168.58) < 1e-9
    for release, effective in [('2026-02-03', '2026-02-04'),
                               ('2026-05-11', '2026-05-12'),
                               ('2026-08-04', '2026-08-05')]:
        before = next(row for row in rows if row['date'] == release)
        after = next(row for row in rows if row['date'] == effective)
        assert before['reportDate'] < release and after['reportDate'] == release
    result = dict(
        asOf=snapshot['asOf'], definition=snapshot['definition'], phases=phases,
        sources=facts['sources'], methodology=facts['methodology'],
        numeratorReview=facts['numeratorReview'], externalCrossCheck=facts['externalCrossCheck'],
        priceSource=snapshot['prices']['source_url'],
        priceRetrievedAt=snapshot['prices']['retrieved_at_utc'],
        priceChecks=snapshot['prices']['validation'],
        firstTradingDay=rows[0], monthEndsAndLatest=list(month_ends.values()), daily=rows,
    )
    (BASE / 'eps-per-history.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for filename, data in [('eps-per-history.csv', rows), ('eps-per-monthly.csv', monthly)]:
        with (BASE / filename).open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(data)
    return monthly


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))
