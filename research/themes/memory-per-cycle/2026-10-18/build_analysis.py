"""Reproduce the dated valuation comparison; no network or price updates."""
import hashlib
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
KIO_PATH = Path('research/companies/285A-kioxia/2026-10-15/eps-per-history.json')
SAVED_PATH = Path('research/themes/ai-supply-chain/2026-10-18/valuation.json')


def main():
    history = json.loads((ROOT / KIO_PATH).read_text())
    saved = json.loads((ROOT / SAVED_PATH).read_text())
    daily = history['daily']
    rows = {row['date']: row for row in daily}
    companies = {company['symbol']: company for company in saved['companies']}
    for row in daily:
        assert math.isclose(row['trailingPER'], row['closeJPY'] / row['ttmDilutedEPSJPY'])
    dates = ['2026-01-05', '2026-03-31', '2026-04-30', '2026-05-13',
             '2026-05-15', '2026-05-18', '2026-06-22', '2026-07-31',
             '2026-08-03', '2026-10-02', '2026-10-15']
    points = [{key: rows[day][key] for key in ['date', 'closeJPY', 'ttmDilutedEPSJPY',
                                              'trailingPER', 'reportDate']} for day in dates]
    peak = max(daily, key=lambda row: row['trailingPER'])
    assert peak['date'] == '2026-05-13'
    intervals = []
    for start, end in [('2026-01-05', '2026-05-13'), ('2026-03-31', '2026-04-30'),
                       ('2026-05-15', '2026-05-18'), ('2026-07-31', '2026-08-03'),
                       ('2026-05-13', '2026-10-15'), ('2026-10-02', '2026-10-15')]:
        a, b = rows[start], rows[end]
        price = b['closeJPY'] / a['closeJPY']
        eps = b['ttmDilutedEPSJPY'] / a['ttmDilutedEPSJPY']
        multiple = b['trailingPER'] / a['trailingPER']
        assert math.isclose(price / eps, multiple)
        intervals.append({'start': start, 'end': end, 'priceFactor': price,
                          'epsFactor': eps, 'perFactor': multiple,
                          'priceChangePct': (price - 1) * 100,
                          'epsChangePct': (eps - 1) * 100,
                          'perChangePct': (multiple - 1) * 100})
    known = [row for row in companies['285A.T']['ttmSeries'] if row['knownFrom'] <= peak['date']]
    old_eps = max(known, key=lambda row: row['knownFrom'])['eps']
    old_peak_per = peak['closeJPY'] / old_eps
    sk_price = 1262000
    sk_fy25_basic_eps, sk_h125_basic_eps, sk_h126_basic_eps = 62044, 21890, 189546
    sk_ttm_basic_approx = sk_fy25_basic_eps - sk_h125_basic_eps + sk_h126_basic_eps
    sk_forecast_adjusted_eps = 355218.90
    kio_price, kio_forecast_eps = 12880, 3443
    q2_dividend_income, q2_fair_value_gain = 10.027945, 53.237425
    result = {
        'researchDateJST': '2026-10-18', 'stockPriceAsOf': '2026-10-15',
        'pricePolicy': 'Reuse dated saved prices; not current quotes or new consensus.',
        'inputHashes': {str(path): hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                        for path in [KIO_PATH, SAVED_PATH]},
        'kioxiaReconstructedDilutedTTM': {'points': points, 'intervals': intervals},
        'kioxiaSavedChartAudit': {
            'date': peak['date'], 'closeJPY': peak['closeJPY'],
            'savedEPSJPY': old_eps, 'savedPER': old_peak_per,
            'reconstructedEPSJPY': peak['ttmDilutedEPSJPY'],
            'reconstructedPER': peak['trailingPER'],
            'savedOverstatementPct': (old_peak_per / peak['trailingPER'] - 1) * 100,
            'explanation': 'Saved TTM lacks the 2025-12 quarter; update timing also uses period-end+45 days.'},
        'skHynixAtSavedOct15Price': {
            'currency': 'KRW', 'price': sk_price, 'fy2025CompanyBasicEPS': sk_fy25_basic_eps,
            'priorHalfYearBasicEPS': sk_h125_basic_eps, 'currentHalfYearBasicEPS': sk_h126_basic_eps,
            'ttmCompanyBasicEPSApprox': sk_ttm_basic_approx,
            'fy2025CompanyBasicPER': sk_price / sk_fy25_basic_eps,
            'ttmCompanyBasicPERApprox': sk_price / sk_ttm_basic_approx,
            'savedGraphTTMEPS': companies['000660.KS']['snapshot']['ttmEps'],
            'savedGraphEPSAppliedToOct15PER': sk_price / companies['000660.KS']['snapshot']['ttmEps'],
            'previouslyRetrievedFY2026AdjustedForecastEPS': sk_forecast_adjusted_eps,
            'forecastPER': sk_price / sk_forecast_adjusted_eps,
            'methodNote': 'Basic EPS differences are approximate when weighted shares change. Forecast adjustments not reconciled.'},
        'skQ2FinancialIncomeTrillionKRW': {
            'dividendIncome': q2_dividend_income, 'financialAssetFairValueGain': q2_fair_value_gain,
            'sumPretaxIncomeItems': q2_dividend_income + q2_fair_value_gain,
            'operatingProfit': 60.542608, 'pretaxProfit': 122.708355,
            'parentAttributableProfit': 93.820236,
            'note': 'Not a tax-adjusted exclusion from net profit; not all attributed to Kioxia.'},
        'kioxiaFixedPriceForecastSensitivity': [
            {'profitFractionOfSavedForecast': fraction, 'priceJPY': kio_price,
             'epsJPY': kio_forecast_eps * fraction,
             'per': kio_price / (kio_forecast_eps * fraction)}
            for fraction in [1, .5, .25]],
        'sources': {
            'skReportedEPSAndFinancialIncome': 'https://www.sec.gov/Archives/edgar/data/2120882/000119312526354777/d147827d6k.htm',
            'skForecastDefinition': 'https://stockanalysis.com/quote/krx/000660/forecast/',
            'savedPricesAndForecasts': 'research/companies/285A-kioxia/2026-10-15/per-analysis.md',
            'kioxiaOriginalReportSources': history['sources']},
    }
    (BASE / 'analysis-calculations.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'peakPER': peak['trailingPER'], 'skTTMApproxPER': sk_price / sk_ttm_basic_approx,
                      'kioxiaLatestSavedPER': daily[-1]['trailingPER'], 'verifiedIntervals': len(intervals)}, indent=2))


if __name__ == '__main__':
    main()
