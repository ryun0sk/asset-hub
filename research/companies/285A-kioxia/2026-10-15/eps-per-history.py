"""Kioxia TTM and rolling-half-year annualized EPS/PER by information date.

Inputs are a dated snapshot. No network, API keys, or future earnings estimates.
EPS is an independent diluted TTM approximation, with quarter-equal share weights.
Run with --no-chart using standard Python, or with matplotlib for PNG/SVG outputs.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, timedelta
from pathlib import Path


BASE = Path(__file__).resolve().parent


def build_history():
    inputs = json.loads((BASE / 'eps-per-history-inputs.json').read_text())
    raw = inputs['fundamentals']
    phases = []
    for original in raw['phases']:
        phase = dict(original)
        annual = raw['inputs'][phase['annual']]
        ni = annual['netIncomeJPYMillion']
        shares = annual['dilutedWeightedSharesPreSplit']
        if phase['current']:
            current = raw['inputs'][phase['current']]
            prior = raw['inputs'][phase['prior']]
            ni += current['netIncomeJPYMillion'] - prior['netIncomeJPYMillion']
            shares += phase['weight'] * (current['dilutedWeightedSharesPreSplit']
                                         - prior['dilutedWeightedSharesPreSplit'])
        eps = ni * 1e6 / (shares * 3)
        assert abs(eps - phase['ttmDilutedEPSPostSplit']) < 1e-8
        phase.update(ttmNetIncomeJPYMillion=ni,
                     ttmDilutedWeightedSharesPreSplit=shares,
                     ttmDilutedEPSPostSplit=eps)
        phases.append(phase)

    f = raw['inputs']
    h1 = f['FY2026H1']
    q3 = f['FY2026Q3YTD']
    annual = f['FY2026']
    q1_prior = f['FY2026Q1']
    q1_new = f['FY2027Q1']
    q4_ni = annual['netIncomeJPYMillion'] - q3['netIncomeJPYMillion']
    q4_shares = annual['dilutedWeightedSharesPreSplit'] * 4 - q3['dilutedWeightedSharesPreSplit'] * 3
    half_year_inputs = [
        ('2025-04-01', '2025-09-30', h1['netIncomeJPYMillion'], h1['dilutedWeightedSharesPreSplit']),
        ('2025-07-01', '2025-12-31', q3['netIncomeJPYMillion'] - q1_prior['netIncomeJPYMillion'],
         (q3['dilutedWeightedSharesPreSplit'] * 3 - q1_prior['dilutedWeightedSharesPreSplit']) / 2),
        ('2025-10-01', '2026-03-31', annual['netIncomeJPYMillion'] - h1['netIncomeJPYMillion'],
         (annual['dilutedWeightedSharesPreSplit'] * 4 - h1['dilutedWeightedSharesPreSplit'] * 2) / 2),
        ('2026-01-01', '2026-06-30', q4_ni + q1_new['netIncomeJPYMillion'],
         (q4_shares + q1_new['dilutedWeightedSharesPreSplit']) / 2),
    ]
    for phase, (start, end, ni, shares) in zip(phases, half_year_inputs):
        half_eps = ni * 1e6 / (shares * 3)
        phase.update(halfYearStart=start, halfYearEnd=end, halfYearNetIncomeJPYMillion=ni,
                     halfYearDilutedWeightedSharesPreSplit=shares,
                     halfYearDilutedEPSJPY=half_eps,
                     halfYearAnnualizedDilutedEPSJPY=half_eps * 2)

    prices = inputs['prices']['rows']
    assert len({row['date'] for row in prices}) == len(prices)
    assert all(row['close'] > 0 for row in prices)
    rows = []
    for price in prices:
        if price['date'] < '2026-01-01':
            continue
        phase = max((p for p in phases if p['effectiveDate'] <= price['date']),
                    key=lambda p: p['effectiveDate'])
        assert phase['asOfReportDate'] < price['date']
        eps = phase['ttmDilutedEPSPostSplit']
        half_annual_eps = phase['halfYearAnnualizedDilutedEPSJPY']
        rows.append({'date': price['date'], 'closeJPY': price['close'],
                     'ttmDilutedEPSJPY': eps, 'trailingPER': price['close'] / eps,
                     'halfYearAnnualizedDilutedEPSJPY': half_annual_eps,
                     'halfYearAnnualizedPER': price['close'] / half_annual_eps,
                     'halfYearProfitPeriodStart': phase['halfYearStart'],
                     'halfYearProfitPeriodEnd': phase['halfYearEnd'],
                     'reportDate': phase['asOfReportDate'],
                     'profitPeriodStart': phase['trailingStart'],
                     'profitPeriodEnd': phase['trailingEnd']})
    month_ends = {}
    for row in rows:
        month_ends[row['date'][:7]] = row
    result = {'asOf': inputs['asOf'], 'definition': inputs['definition'],
              'priceSource': inputs['prices']['source'],
              'priceRetrievedAt': inputs['prices']['retrievedAt'],
              'sources': raw['sources'], 'methodology': raw['methodology'],
              'numeratorReview': raw['numeratorReview'],
              'phases': phases, 'firstTradingDay': rows[0],
              'monthEndsAndLatest': list(month_ends.values()), 'daily': rows,
              'externalCrossCheck': raw['externalCrossCheck']}
    result['halfYearMethodology'] = ('各時点で発表済みの直近2四半期のIFRS親会社帰属純利益を、'
        '四半期等分で再構成した希薄化平均株数で割り、2倍して年換算。'
        '会社公表の半年EPS・通期予想ではない。先の半年も同水準とみなす仮定を含む。')
    result['definition'] = ('当時公表済みの実績を使う希薄化後TTMと、直近6か月実績を2倍した年換算を併記。'
                            'いずれも独自再構成概算。予想利益は含まない。決算は翌営業日から反映。')
    f = raw['inputs']
    q4_ni = f['FY2026']['netIncomeJPYMillion'] - f['FY2026Q3YTD']['netIncomeJPYMillion']
    q4_diluted_shares = (f['FY2026']['dilutedWeightedSharesPreSplit'] * 4
                         - f['FY2026Q3YTD']['dilutedWeightedSharesPreSplit'] * 3)
    q1_ni = f['FY2027Q1']['netIncomeJPYMillion']
    q1_diluted_shares = f['FY2027Q1']['dilutedWeightedSharesPreSplit']
    half_year_eps = (q4_ni + q1_ni) * 1e6 / (((q4_diluted_shares + q1_diluted_shares) / 2) * 3)
    quarter_eps = q1_ni * 1e6 / (q1_diluted_shares * 3)
    result['recentAnnualizationComparison'] = {
        'priceJPY': 12880, 'priceDate': '2026-10-15',
        'basis': '希薄化後・独自再構成概算。半年/四半期の年換算は利益継続の仮定で、会社の通期予想ではない。',
        'halfYearPeriod': '2026-01-01 to 2026-06-30',
        'halfYearNetIncomeJPYMillion': q4_ni + q1_ni,
        'halfYearDilutedEPSJPY': half_year_eps,
        'halfYearAnnualizedDilutedEPSJPY': half_year_eps * 2,
        'halfYearAnnualizedPER': 12880 / (half_year_eps * 2),
        'quarterPeriod': '2026-04-01 to 2026-06-30',
        'quarterAnnualizedDilutedEPSJPY': quarter_eps * 4,
        'quarterAnnualizedPER': 12880 / (quarter_eps * 4),
    }
    assert q4_ni + q1_ni == 1249899
    assert 8.55 < result['recentAnnualizationComparison']['halfYearAnnualizedPER'] < 8.56
    assert abs(result['recentAnnualizationComparison']['halfYearAnnualizedDilutedEPSJPY']
               - rows[-1]['halfYearAnnualizedDilutedEPSJPY']) < 1e-8
    assert rows[-1]['date'] == '2026-10-15' and rows[-1]['closeJPY'] == 12880
    assert abs(rows[-1]['ttmDilutedEPSJPY'] - 832.23) < .02
    assert next(r for r in rows if r['date'] == '2026-07-31')['reportDate'] == '2026-05-15'
    assert next(r for r in rows if r['date'] == '2026-08-03')['reportDate'] == '2026-07-31'
    (BASE / 'eps-per-history.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    with (BASE / 'eps-per-history.csv').open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (BASE / 'eps-per-monthly.csv').open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows([rows[0]] + list(month_ends.values()))
    return result


def plot_history(result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.ticker import StrMethodFormatter

    font_path = Path('/Library/Fonts/Arial Unicode.ttf')
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=str(font_path)).get_name()
    plt.rcParams.update({'font.size': 11, 'axes.unicode_minus': False,
                         'svg.fonttype': 'path', 'axes.spines.top': False,
                         'axes.spines.right': False})
    rows = result['daily']
    dates = [date.fromisoformat(r['date']) for r in rows]
    eps = [r['ttmDilutedEPSJPY'] for r in rows]
    per = [r['trailingPER'] for r in rows]
    fig, axes = plt.subplots(2, 1, figsize=(12.6, 7.3), sharex=True)
    fig.patch.set_facecolor('#ffffff')
    blue, orange, grey = '#176b9c', '#b85516', '#606976'
    axes[0].step(dates, eps, where='post', color=blue, linewidth=2.5)
    axes[1].plot(dates, per, color=orange, linewidth=2)
    axes[0].set_ylabel('実績TTM EPS（円）')
    axes[1].set_ylabel('実績TTM PER（倍）')
    axes[0].set_ylim(0, 1000)
    axes[1].set_ylim(0, max(per) * 1.16)
    for ax in axes:
        ax.grid(axis='y', color='#e6e9ed', linewidth=.7)
        ax.spines['left'].set_color('#c4cbd3')
        ax.spines['bottom'].set_color('#c4cbd3')
        ax.set_axisbelow(True)
        ax.tick_params(length=0, pad=7)
        ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
    for phase in result['phases']:
        x = date.fromisoformat(phase['effectiveDate'])
        y = phase['ttmDilutedEPSPostSplit']
        label = x.strftime('%-m/%-d') + 'から 約' + f'{y:,.0f}' + '円'
        axes[0].annotate(label, xy=(x, y), xytext=(6, 16 if y < 700 else -28),
                         textcoords='offset points', fontsize=10, color=blue)
        if phase != result['phases'][0]:
            for ax in axes:
                ax.axvline(x, color='#aeb8c3', linewidth=.8, linestyle=(0, (4, 4)))
    last = rows[-1]
    axes[0].plot(dates[-1], eps[-1], 'o', color=blue, markersize=5)
    axes[1].plot(dates[-1], per[-1], 'o', color=orange, markersize=5)
    axes[1].annotate(f'10/15  約{per[-1]:.1f}倍', xy=(dates[-1], per[-1]),
                     xytext=(-105, 15), textcoords='offset points', color=orange,
                     fontsize=11, fontweight='bold')
    peak_index = max(range(len(per)), key=per.__getitem__)
    axes[1].annotate(dates[peak_index].strftime('%-m/%-d') + f' 約{per[peak_index]:.0f}倍',
                     xy=(dates[peak_index], per[peak_index]), xytext=(10, 10),
                     textcoords='offset points', color=grey, fontsize=10)
    axes[1].xaxis.set_major_locator(mdates.MonthLocator())
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%m月'))
    axes[1].set_xlim(dates[0] - timedelta(days=3), dates[-1] + timedelta(days=12))
    fig.suptitle('キオクシア：2026年の実績EPSとPERの推移', x=.08, ha='left',
                 fontsize=19, fontweight='bold', y=.97)
    fig.text(.08, .915, '当時発表済みの直近12か月実績を使用。予想EPS・四半期×4の年換算は含めない。',
             fontsize=11, color=grey)
    fig.text(.08, .048, 'EPSは希薄化後TTMの独自再構成概算。決算発表の翌営業日から更新。株価・EPSとも1対3分割後基準。',
             fontsize=9, color=grey)
    fig.text(.08, .022, '出所：キオクシア決算短信、Yahoo Finance日足。2026/10/15東証終値まで。',
             fontsize=9, color=grey)
    fig.subplots_adjust(left=.09, right=.96, top=.86, bottom=.12, hspace=.23)
    for suffix in ['png', 'svg']:
        fig.savefig(BASE / ('eps-per-history.' + suffix), dpi=180, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-chart', action='store_true')
    args = parser.parse_args()
    history = build_history()
    if not args.no_chart:
        plot_history(history)
    print(json.dumps({'latest': history['daily'][-1],
                      'monthEndsAndLatest': history['monthEndsAndLatest']}, ensure_ascii=False, indent=2))
