"""Remove only the Toyota Industries stock-sale gain from saved Ibiden EPS.

This is a conditional estimate, not reported or fully normalized earnings.
Use the same FY2026 annual EPS term as the original cumulative-EPS method;
retain all other gains/losses and the original convertible-bond adjustment.
"""
from __future__ import annotations

import csv
import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
D = lambda value: Decimal(str(value))


def fmt(value, digits=2):
    if value is None:
        return '算出不能'
    return f"{D(value).quantize(Decimal('1').scaleb(-digits), rounding=ROUND_HALF_UP):,.{digits}f}"


def build():
    inputs = json.loads((BASE / 'ex-stock-gain-inputs.json').read_text())
    source_path = ROOT / inputs['sourceHistory']['path']
    raw = source_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == inputs['sourceHistory']['sha256']
    history = json.loads(raw)
    saved_facts = json.loads((BASE / 'eps-per-history-inputs.json').read_text())['fundamentals']
    shares = inputs['denominator']
    assert shares['basicWeightedShares'] == saved_facts['inputs']['FY2026_Mar']['basicWeightedShares']
    assert shares['potentialShares'] == saved_facts['numeratorReview']['FY2026_Mar']['ordinaryShareIncreaseThousands'] * 1000
    denominator = D(shares['basicWeightedShares'] + shares['potentialShares']) * D(shares['remainingSplitFactor'])
    assert denominator == 589655250
    gross_gain = D(inputs['gain']['pretaxJPYMillion']) * 1000000
    assert gross_gain == D(saved_facts['numeratorReview']['extraordinaryItems']['ToyotaIndustriesTOBGainJPYMillion']) * 1000000
    central_rate = D(inputs['tax']['assumedRate'])
    gain_after_tax = gross_gain * (1 - central_rate)
    annual_gain_eps = gain_after_tax / denominator
    phases = history['phases']

    def adjust(row, rate):
        phase = max((p for p in phases if p['effectiveDate'] <= row['date']), key=lambda p: p['effectiveDate'])
        ttm_coefficient = sum(coef for name, coef in phase['ttmTerms'] if name == 'FY2026_Mar')
        half_coefficient = sum(coef for name, coef in phase['halfYearAnnualizedTerms'] if name == 'FY2026_Mar')
        assert ttm_coefficient in (0, 1) and half_coefficient in (0, 2)
        amount = gross_gain * (1 - D(rate)) / denominator
        ttm_eps = D(row['ttmDilutedEPSJPY']) - amount * ttm_coefficient
        half_eps = D(row['halfYearAnnualizedDilutedEPSJPY']) - amount * half_coefficient
        if ttm_coefficient:
            assert row['date'] >= inputs['effectiveDate']
            assert row['profitPeriodStart'] <= inputs['gain']['periodStart'] <= inputs['gain']['periodEnd'] <= row['profitPeriodEnd']
        if half_coefficient:
            assert row['halfYearProfitPeriodStart'] <= inputs['gain']['periodStart'] <= inputs['gain']['periodEnd'] <= row['halfYearProfitPeriodEnd']
        return dict(row, ttmDilutedEPSJPY=float(ttm_eps),
                    trailingPER=float(D(row['closeJPY']) / ttm_eps) if ttm_eps > 0 else None,
                    halfYearAnnualizedDilutedEPSJPY=float(half_eps),
                    halfYearAnnualizedPER=float(D(row['closeJPY']) / half_eps) if half_eps > 0 else None,
                    ttmGainEPSAdjustmentJPY=float(amount * ttm_coefficient),
                    halfYearAnnualizedGainEPSAdjustmentJPY=float(amount * half_coefficient),
                    adjustmentApplied=bool(ttm_coefficient or half_coefficient))

    daily = [adjust(row, central_rate) for row in history['daily']]
    month_ends = {}
    for row in daily:
        month_ends[row['date'][:7]] = row
    monthly = [daily[0]] + list(month_ends.values())
    assert len(daily) == 190 and len(monthly) == 11
    assert all(a['date'] == b['date'] and a['closeJPY'] == b['closeJPY'] for a, b in zip(daily, history['daily']))
    before = next(row for row in daily if row['date'] == '2026-05-11')
    after = next(row for row in daily if row['date'] == '2026-05-12')
    assert not before['adjustmentApplied'] and after['adjustmentApplied']
    assert abs(daily[-1]['ttmDilutedEPSJPY'] - 57.97112604992493) < 1e-8
    assert abs(daily[-1]['halfYearAnnualizedDilutedEPSJPY'] - 51.73225209984985) < 1e-8
    sensitivity = [dict(assumedTaxRate=float(rate), **adjust(history['daily'][-1], rate))
                   for rate in inputs['tax']['sensitivityRates']]
    result = dict(asOf=history['asOf'], dataAsOf='2026-10-16',
                  label='豊田自動織機株式売却益を除く（推計）',
                  basis='税引前491.44億円に税率29.9%を仮定。税引後寄与344.50億円を除外し、元の実績EPSと同じ通期項で再構成。',
                  notes=[
                      '豊田自動織機株式の売却益491.44億円だけを除く独自推計です。売却固有の税引後額は非開示のため、法定実効税率29.9%を仮定します。',
                      '他の株式売却益・減損損失・その他の損益は残ります。「本業だけのEPS」「正常利益」ではありません。',
                      '売却益を含む通期実績の公表後（5/12から）のみ調整し、年初〜4月の月次値は実績と同じです。',
                      '税率25〜35%なら10/15のTTM PERは約148〜171倍、半年年換算PERは約153〜211倍。税率は売却固有の実績税率ではありません。',
                  ],
                  sourceHistory=inputs['sourceHistory'], inputPath=(BASE / 'ex-stock-gain-inputs.json').relative_to(ROOT).as_posix(),
                  reportPath=(BASE / 'ex-stock-gain.md').relative_to(ROOT).as_posix(),
                  estimatedAfterTaxGainJPYMillion=float(gain_after_tax / 1000000),
                  dilutedDenominatorShares=int(denominator), annualEPSAdjustmentJPY=float(annual_gain_eps),
                  assumedTaxRate=float(central_rate), companyCrossCheck=inputs['companyCrossCheck'],
                  sources=inputs['sources'], sensitivity=sensitivity, daily=daily, monthly=monthly)
    (BASE / 'ex-stock-gain.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for name, rows in [('ex-stock-gain-daily.csv', daily), ('ex-stock-gain-monthly.csv', monthly)]:
        with (BASE / name).open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    last = history['daily'][-1]
    adjusted = daily[-1]
    lines = ['# イビデン｜豊田自動織機株式売却益を除いたEPS・PER（推計）', '',
             '2026年10月16日作成。株価は10月15日終値9,213円、2026年10月1日分割後の円基準で固定。', '',
             '**売却益を除くとTTM EPSは57.97円・PER158.9倍、直近半年年換算EPSは51.73円・PER178.1倍。** 税率29.9%を仮定した独自推計であり、会社公表の調整後EPSではない。', '',
             '## 実績との比較', '',
             '| 利益基準 | TTM EPS | TTM PER | 半年年換算EPS | 半年年換算PER |',
             '|---|---:|---:|---:|---:|']
    for label, row in [('実績（売却益を含む）', last), ('豊田自動織機売却益除外・税率29.9%仮定', adjusted)]:
        lines.append(f"| {label} | {fmt(row['ttmDilutedEPSJPY'])}円 | {fmt(row['trailingPER'],1)}倍 | {fmt(row['halfYearAnnualizedDilutedEPSJPY'])}円 | {fmt(row['halfYearAnnualizedPER'],1)}倍 |")
    lines += ['', '利益期間はTTMが2025年7月〜2026年6月、半年が2026年1〜6月。半年年換算は直近半年の利益を2倍する参考値であり、将来予想ではない。', '',
              '## 除外対象と税引後額', '',
              '対象は2026年1〜3月期の豊田自動織機株式売却益491.44億円のみ。売却代金569.178億円ではなく、損益計上した売却益を使う。[3月24日会社開示](https://www2.jpx.co.jp/disc/40620/140120260324587882.pdf)', '',
              '売却固有の税引後利益・税額は確認できないため、売却年度の法定実効税率29.9%を仮定する。前年有報でも29.9%が既に開示されており、6月の新情報を過去の税率へ遡及適用したものではない。連結全体・単体全体の実際負担税率を売却固有の税率とみなさない。[第172期有報・PDF100/121ページ](https://disclosure2dl.edinet-fsa.go.jp/searchdocument/pdf/S100VXHK.pdf)、[第173期有報・PDF127ページ](https://disclosure2dl.edinet-fsa.go.jp/searchdocument/pdf/S100YC4B.pdf)', '',
              '会社は政策投資株全体について「税引後換算345億円」を開示しており、今回のToyota単独推計344.50億円と近い。ただし会社値は対象範囲と丸めが異なるため、Toyota単独の確定額には置き換えない。[5月12日説明資料・Page#4](https://www.ibiden.co.jp/ir/items/kessannsetsumeiFY2025.pdf)', '',
              '## 再構成の方法', '',
              '元の実績は会社公表の希薄化後累計EPSを差引した概算。その方法を保ち、2026年3月期の通期EPS項から売却益の推定寄与を除く。四半期CB調整や半年固有の希薄化株数は新たに仮定しない。', '',
              '```text',
              '希薄化分母 = (通期基本期中平均279,243,625株 + 潜在株式15,584,000株) × 10月分割2',
              '            = 589,655,250株',
              f'推定税引後売却益 = 49,144百万円 × (1 − 29.9%) = {fmt(gain_after_tax / 1000000,3)}百万円',
              f'通期EPS控除額 = 推定税引後売却益 ÷ 希薄化分母 = {fmt(annual_gain_eps,6)}円',
              f'TTM EPS = 116.395 − {fmt(annual_gain_eps,6)} = {fmt(adjusted["ttmDilutedEPSJPY"],6)}円',
              f'半年年換算EPS = 168.58 − 2 × {fmt(annual_gain_eps,6)} = {fmt(adjusted["halfYearAnnualizedDilutedEPSJPY"],6)}円',
              'PER = 株価9,213円 ÷ 各EPS', '```', '',
              '分母は2026年3月期短信の期中平均株式数と普通株式増加数による。潜在株式は千株単位の公表値のため分母も概算。CB分子調整△350百万円は元の実績EPS内に残す。[通期短信・PDF2ページと18ページ（添付16ページ）](https://www2.jpx.co.jp/disc/40620/140120260505517290.pdf)', '',
              '## 除外後の月次推移', '',
              '| 時点 | 株価 | TTM EPS | TTM PER | 半年年換算EPS | 半年年換算PER |',
              '|---|---:|---:|---:|---:|---:|']
    for row in monthly:
        lines.append(f"| {row['date']} | {fmt(row['closeJPY'])}円 | {fmt(row['ttmDilutedEPSJPY'])}円 | {fmt(row['trailingPER'],1)}倍 | {fmt(row['halfYearAnnualizedDilutedEPSJPY'])}円 | {fmt(row['halfYearAnnualizedPER'],1)}倍 |")
    lines += ['', '5月12日から通期実績と売却益控除を反映する。3月24日に売却益の事前開示はあるが、未発表の通期利益は当日実績EPSへ取り込まない。過去株価と利益の分割基準は元系列のまま維持する。', '',
              '## 税率の感応度（10月15日）', '',
              '| 仮定税率 | TTM EPS | TTM PER | 半年年換算EPS | 半年年換算PER |',
              '|---|---:|---:|---:|---:|']
    for row in sensitivity:
        lines.append(f"| {fmt(row['assumedTaxRate']*100,1)}% | {fmt(row['ttmDilutedEPSJPY'])}円 | {fmt(row['trailingPER'],1)}倍 | {fmt(row['halfYearAnnualizedDilutedEPSJPY'])}円 | {fmt(row['halfYearAnnualizedPER'],1)}倍 |")
    lines += ['', '## 解釈と限界', '',
              '除外後は一時利益込みの実績よりPERが大きく上がる。イビデンを評価するには今後の利益成長が必要になるが、この機械的な調整だけで成長率や適正株価を決めることはできない。', '',
              '他の株式売却益、減損損失、補助金、為替等は残す。損失の戻入れや全社税率の置換は行っておらず、完全な正常利益・本業利益ではない。会社開示の政策株売却益345億円や全投資有価証券売却益494.48億円の一律控除とは対象が異なる。', '',
              '[実績表](report.md) · [入力・出典](ex-stock-gain-inputs.json) · [月次CSV](ex-stock-gain-monthly.csv) · [計算結果](ex-stock-gain.json)', '',
              '再計算コードはローカルの`ex-stock-gain.py`（本番配信対象外）。`python3 research/companies/4062-ibiden/2026-10-16/ex-stock-gain.py`で保存済み資料から再現する。元の実績JSON/CSVは変更しない。', '']
    (BASE / 'ex-stock-gain.md').write_text('\n'.join(lines))
    return result


if __name__ == '__main__':
    result = build()
    print(json.dumps({'monthlyRows': len(result['monthly']), 'latest': result['monthly'][-1],
                      'sensitivity': result['sensitivity']}, ensure_ascii=False, indent=2))
