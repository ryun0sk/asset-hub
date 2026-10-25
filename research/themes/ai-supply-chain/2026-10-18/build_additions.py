"""Add power-generation companies without revising the 43-company snapshot.

Offline, reproducible build from the preserved 2026-10-03 inputs, the three
official EPS input files, and addition-prices.json. No estimates are invented.
"""
from copy import deepcopy
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import statistics

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[3]
PREVIOUS = BASE.parent / '2026-10-03'
ACTUAL_PREVIOUS = REPO / 'research/themes/ai-actual-valuation/2026-10-16'
ACTUAL = REPO / 'research/themes/ai-actual-valuation/2026-10-18'
INPUTS = [
    'research/companies/7011-mitsubishi-heavy-industries/2026-10-18/eps-inputs.json',
    'research/companies/GEV-ge-vernova/2026-10-18/eps-inputs.json',
    'research/companies/ENR-siemens-energy/2026-10-18/eps-inputs.json',
]
DISPLAY_NOTES = {
    '7011.T': [
        '会社全体の希薄化後EPS。ガスタービン部門単独の利益ではなく、非継続事業・固定資産売却等の一時損益を含む。',
        '累計EPSの差引による四半期EPSと、その4期合計によるTTM概算。期間平均株数・希薄化・丸めの影響を含む。',
        '会社予想113.09円は2027年3月期の基本EPS。実績の希薄化後EPSとは基準が異なる。',
        '半年年換算は直近2四半期の実績合計を2倍した参考値で、会社予想ではない。',
    ],
    'GEV': [
        'US GAAP希薄化後の四半期EPS合算によるTTM概算。株数変化・丸め等で公式通期や半期EPSと小差がある。',
        '2025年10〜12月の税便益約29億ドルと、2026年1〜3月のProlec再評価益39.92億ドル（税前）を含み、実績PERを押し下げている。',
        '半年年換算は一時利益も2倍にする参考値。持続利益や将来予想を示すものではない。',
        '2024年4〜6月にはSteam Power事業一部売却の利益も含む。会社・外部の通期EPS予想は今回未取得。',
    ],
    'ENR.DE': [
        'IFRS希薄化後の四半期EPS合算によるTTM概算。2025年9月期は四半期合算1.61ユーロ、公式通期1.60ユーロと小差がある。',
        '資産売却・インド事業分離の利益や風力事業の品質費用等を含む全社実績。調整後EPSや持続利益とは異なる。',
        '年度末は9月30日。会社の全社純利益見通しには非支配持分を含むため、単純に株数で割って会社予想EPSにしていない。',
        '半年年換算は直近2四半期実績の2倍で、会社予想ではない。会社・外部の通期EPS予想は今回未取得。',
    ],
}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')


def fingerprint(path):
    return {'path': path.relative_to(REPO).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def period_start(end, months):
    d = date.fromisoformat(end) + timedelta(days=1)
    y, m = divmod(d.year * 12 + d.month - 1 - months, 12)
    return date(y, m + 1, d.day).isoformat()


def earnings_series(data):
    quarters = sorted(data['quarterly'], key=lambda r: r['periodEnd'])
    series = {}
    for i in range(3, len(quarters)):
        group = quarters[i-3:i+1]
        if any(not 70 <= (date.fromisoformat(b['periodEnd']) - date.fromisoformat(a['periodEnd'])).days <= 100
               for a, b in zip(group, group[1:])):
            continue
        end = group[-1]['periodEnd']
        series[end] = {
            'periodEnd': end, 'eps': round(sum(q['eps'] for q in group), 8),
            'knownFrom': max(q['knownFrom'] for q in group),
            'publishedDate': max(q['publishedDate'] for q in group),
            'source': 'official-quarterly-sum',
            'profitPeriodStart': period_start(end, 12),
            'halfYearAnnualizedEps': round(sum(q['eps'] for q in group[-2:]) * 2, 8),
            'halfYearProfitPeriodStart': period_start(end, 6),
        }
    for row in data.get('annual', []):
        if row['periodEnd'] in series:
            # Use annual EPS when no explicit company-specific TTM is supplied.
            series[row['periodEnd']].update(eps=row['eps'], knownFrom=row['knownFrom'],
                                          publishedDate=row['publishedDate'], source='official-annual')
    for row in data.get('ttm', []):
        old = series.get(row['periodEnd'], {})
        series[row['periodEnd']] = {**old, **row,
            'profitPeriodStart': row.get('profitPeriodStart', period_start(row['periodEnd'], 12))}
    return sorted(series.values(), key=lambda r: (r['knownFrom'], r['periodEnd']))


def known(series, day):
    options = [r for r in series if r['knownFrom'] <= day and
               (date.fromisoformat(day) - date.fromisoformat(r['periodEnd'])).days <= 460]
    return max(options, key=lambda r: r['periodEnd']) if options else None


def quantile(values, q):
    p = (len(values) - 1) * q
    i = int(p)
    return values[i] + (values[min(i + 1, len(values) - 1)] - values[i]) * (p - i)


def actual_row(price, ttm):
    eps = ttm['eps'] if ttm else None
    half = ttm.get('halfYearAnnualizedEps') if ttm else None
    return {'date': price['date'], 'close': price['close'], 'ttmDilutedEPS': eps,
            'trailingPER': price['close'] / eps if eps and eps > 0 else None,
            'halfYearAnnualizedDilutedEPS': half,
            'halfYearAnnualizedPER': price['close'] / half if half and half > 0 else None,
            'profitPeriodStart': ttm.get('profitPeriodStart') if ttm else None,
            'profitPeriodEnd': ttm['periodEnd'] if ttm else None,
            'halfYearProfitPeriodStart': ttm.get('halfYearProfitPeriodStart') if ttm else None,
            'halfYearProfitPeriodEnd': ttm['periodEnd'] if ttm else None,
            'reportDate': ttm.get('publishedDate') if ttm else None,
            'knownFrom': ttm['knownFrom'] if ttm else None}


def company_values(data, prices):
    series, rows = earnings_series(data), prices['rows']
    warning = '税便益・Prolec再評価益を含む' if data['symbol'] == 'GEV' else None
    notes = DISPLAY_NOTES[data['symbol']]
    pes = [p['close'] / t['eps'] if (t := known(series, p['date'])) and t['eps'] > 0 else None for p in rows]
    valid = sorted(p for p in pes if p is not None)
    start = next((i for i, p in enumerate(pes) if p is not None), None)
    ttm, last = known(series, rows[-1]['date']), rows[-1]
    assert ttm, data['symbol'] + ': no latest TTM'
    forecast = deepcopy(data.get('companyForecast'))
    if forecast:
        forecast.update(pe=last['close'] / forecast['eps'] if forecast['eps'] > 0 else None,
                        label='会社公表の基本EPS予想')
    next_earnings = data.get('nextEarnings')
    value = {
        'symbol': data['symbol'], 'name': data['name'], 'priceCurrency': data['currency'], 'epsCurrency': data['currency'],
        'ttmSeries': series,
        'pe': {'from': rows[start]['date'] if start is not None else None,
               'values': [round(v, 4) if v is not None else None for v in pes[start:]] if start is not None else []},
        'peStats': {'days': len(valid), 'from': rows[start]['date'],
                    'to': next(p['date'] for p, v in reversed(list(zip(rows, pes))) if v is not None),
                    'median': statistics.median(valid), 'p10': quantile(valid, .1), 'p90': quantile(valid, .9),
                    'min': valid[0], 'max': valid[-1]} if valid else None,
        'snapshot': {'date': last['date'], 'close': last['close'], 'status': 'ok' if ttm['eps'] > 0 else 'loss',
                     'ttmEps': ttm['eps'], 'ttmPeriodEnd': ttm['periodEnd'], 'ttmKnownFrom': ttm['knownFrom'],
                     'ttmSource': ttm['source'], 'ttmEpsPriceCurrency': ttm['eps'], 'fxRate': None,
                     'pe': last['close'] / ttm['eps'] if ttm['eps'] > 0 else None, 'notes': notes, 'warning': warning},
        'analyst': data.get('analyst'), 'companyForecast': forecast,
        'companyForecastNote': ('通期EPS会社予想は未確認（売上・利益率等の見通しを開示）'
                                if data['symbol'] in ('GEV', 'ENR.DE') else data.get('companyForecastNote', '通期EPS会社予想は未取得')),
        'nextEarnings': {**next_earnings, 'status': 'confirmed', 'time': next_earnings.get('time', '時刻は出典参照'),
                         'event': next_earnings.get('event', '決算')} if next_earnings else {'status': 'unconfirmed'},
        'quarterly': data['quarterly'], 'annual': data['annual'], 'decompositionPresets': {},
        'sourcePath': data['_inputPath'], 'reportPath': data['_inputPath'].replace('eps-inputs.json', 'report.md'), 'warning': warning,
    }
    daily = [actual_row(p, known(series, p['date'])) for p in rows if p['date'] >= '2026-01-01']
    months = {r['date'][:7]: r for r in daily}
    monthly = [daily[0]] + list(months.values())
    monthly = list({r['date']: r for r in monthly}.values())
    actual = {'symbol': data['symbol'], 'code': data['code'], 'name': data['name'], 'currency': data['currency'],
              'basis': data['basis'], 'splitBasis': data['splitBasis'], 'notes': notes,
              'reportPath': value['reportPath'], 'sourcePath': value['sourcePath'],
              'sourceSHA256': hashlib.sha256((REPO / data['_inputPath']).read_bytes()).hexdigest(), 'monthly': monthly, 'warning': warning}
    return value, actual, daily


def main():
    prices, fund, valuation, catalog = [read(PREVIOUS / (f + '.json')) for f in ['prices', 'fundamentals', 'valuation', 'catalog']]
    additions = read(BASE / 'addition-prices.json')
    actual = read(ACTUAL_PREVIOUS / 'valuation-history.json')
    actual.update(asOf='2026-10-16', dataAsOf='2026-10-18', chartAsOf='2026-10-18',
                  definition='各市場の現地通貨・株式分割調整後。各時点で公表済みの実績EPS。既存4社は10/15、追加3社は10/16終値まで。')
    files = [PREVIOUS / (f + '.json') for f in ['prices', 'fundamentals', 'valuation', 'catalog']]
    files.append(BASE / 'addition-prices.json')
    daily_output = {}
    for path in INPUTS:
        data = read(REPO / path)
        data['_inputPath'] = path
        price = next(p for p in additions['companies'] if p['symbol'] == data['symbol'])
        value, monthly, daily = company_values(data, price)
        prices['companies'].append(price)
        valuation['companies'].append(value)
        actual['companies'].append(monthly)
        daily_output[data['symbol']] = {'currency': data['currency'], 'daily': daily}
        fund['companies'].append({
            'symbol': data['symbol'], 'name': data['name'], 'priceCurrency': data['currency'], 'epsCurrency': data['currency'],
            'epsBasis': 'diluted', 'quarterlyEpsBasis': 'diluted', 'ttmEpsBasis': 'diluted-quarterly-sum',
            'source': path, 'retrievedAt': '2026-10-18', 'rows': data['annual'], 'quarterlyRows': data['quarterly'],
            'ttmRows': value['ttmSeries'], 'adjustments': [], 'trailingPeRows': [], 'forwardPeRows': [],
        })
        files.append(REPO / path)
    group = {'id': 'generation', 'name': '発電・ガスタービン', 'short': 'AI向け電力をつくる',
             'symbols': ['7011.T', 'GEV', 'ENR.DE'], 'row': 2, 'product': 'ガスタービン・発電設備・保守',
             'purpose': '電力会社やデータセンターへ安定した発電能力を供給する',
             'note': 'AI以外の電力需要も含む。受注・生産枠予約・売上は異なる。GEVの実績EPSには税効果・Prolec再評価益が含まれる。',
             'roles': {'7011.T': '三菱重工／大型ガスタービン・GTCC', 'GEV': 'GE Vernova／ガスタービン・送配電',
                       'ENR.DE': 'Siemens Energy／ガスタービン・送電網'}}
    catalog['groups'].insert(next(i for i, g in enumerate(catalog['groups']) if g['id'] == 'power'), group)
    catalog['edges'].extend([
        ['cloud', 'generation', '発電設備・長期電力供給', '電力会社経由や自家発電で必要な電力を確保する'],
        ['generation', 'power', '発電した電力', '系統・変圧器・配電設備を通じて需要家へ届ける'],
    ])
    date_note = '既存43社は2026-10-02までの保存値、追加3社は2026-10-16終値。各行に基準日を表示。'
    prices.update(end='2026-10-16', snapshotNote=date_note)
    fund.update(end='2026-10-16', snapshotNote=date_note)
    valuation.update(asOf='2026-10-16', snapshotNote=date_note, generatedBy=fingerprint(Path(__file__))['path'],
                     inputs=[fingerprint(p) for p in files])
    valuation['method']['ttm'] += ' 追加3社は公式公表日・公表時刻に基づく既知日と、各社資料に明記した公式四半期EPSの合算によるTTM概算。公式通期EPSは通期実績配列に別記し、四半期合算との差を注記。'
    for filename, payload in [('prices.json', prices), ('fundamentals.json', fund), ('valuation.json', valuation), ('catalog.json', catalog)]:
        write(BASE / filename, payload)
    write(ACTUAL / 'valuation-history.json', actual)
    write(ACTUAL / 'addition-daily.json', daily_output)
    import csv
    with (ACTUAL / 'valuation-history.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['symbol', 'name', 'currency', 'profitBasis', 'date', 'close', 'ttmDilutedEPS',
                                                   'trailingPER', 'halfYearAnnualizedDilutedEPS', 'halfYearAnnualizedPER'])
        writer.writeheader()
        for company in actual['companies']:
            for basis, dataset in [('reported', company), ('exStockGain', company.get('exStockGain'))]:
                if not dataset:
                    continue
                for row in dataset['monthly']:
                    writer.writerow({'symbol': company['symbol'], 'name': company['name'], 'currency': company.get('currency', 'JPY'),
                                     'profitBasis': basis, 'date': row['date'], 'close': row.get('close', row.get('closeJPY')),
                                     'ttmDilutedEPS': row.get('ttmDilutedEPS', row.get('ttmDilutedEPSJPY')), 'trailingPER': row['trailingPER'],
                                     'halfYearAnnualizedDilutedEPS': row.get('halfYearAnnualizedDilutedEPS', row.get('halfYearAnnualizedDilutedEPSJPY')),
                                     'halfYearAnnualizedPER': row['halfYearAnnualizedPER']})
    print('Built 46-company valuation and 7-company monthly EPS/PER inputs')


if __name__ == '__main__':
    main()
