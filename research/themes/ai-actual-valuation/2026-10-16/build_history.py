"""Assemble four dated actual EPS/PER histories for Asset Hub, without network.

The source company snapshots remain unchanged. This file validates and combines
saved actual histories and explicitly adjusted estimates, without forecasts.
"""
from __future__ import annotations

import csv
import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
COMPANIES = [
    dict(code='285A', name='キオクシア', symbol='285A.T', folder='285A-kioxia/2026-10-15',
         report='per-analysis.md', basis='希薄化後EPS・利益と期間平均株数から再構成した概算',
         splitBasis='2026/10/1の1対3分割後',
         notes=['TTMは利益・希薄化分母を四半期等分で再構成した独自概算。会社公表TTMではありません。',
                '半年年換算は2026年1〜6月の利益継続を仮定します。高いNAND価格が続く保証はありません。']),
    dict(code='6857', name='アドバンテスト', symbol='6857.T', folder='6857-advantest/2026-10-15',
         report='report.md', basis='希薄化後EPS・利益と期間平均分母から再構成した概算',
         splitBasis='2023/10/1の1対4分割後。2026年の分割なし',
         notes=['四半期の希薄化分母は公表EPSから逆算。CB発行後の分子調整は非開示のため、ゼロ仮定の有効分母を使う独自概算です。',
                '2026年1〜3月と4〜6月には戦略投資の評価益が含まれます。本業だけの持続利益とは区別してください。']),
    dict(code='4062', name='イビデン', symbol='4062.T', folder='4062-ibiden/2026-10-16',
         report='report.md', basis='希薄化後EPS・会社公表累計EPSの差引による概算',
         splitBasis='2026/1/1・10/1の各1対2分割後へ統一',
         notes=['四半期CBの希薄化分子・分母が非開示のため、公表希薄化後EPSを分割調整し差引した独自近似です。期間平均株数の変化等で会社正式TTMとは異なります。',
                '実績系列の最新TTM・半年は豊田自動織機株式の売却益491.44億円（税引前）を含みます。半年年換算は本業だけの利益水準ではありません。']),
    dict(code='6146', name='ディスコ', symbol='6146.T', folder='6146-disco/2026-10-16',
         report='report.md', basis='希薄化後EPS・利益と期間平均分母から再構成した概算',
         splitBasis='2023/4/1の1対3分割後。2026年の分割なし',
         notes=['希薄化分母を丸め済み公表EPSから逆算する独自概算です。通期・半期の分子調整ゼロを確認し、四半期非開示部分はゼロと仮定します。',
                '最新公表実績は2026年4〜6月。次回決算は10/22予定で、未発表の7〜9月利益は含めません。']),
]


def fmt(value, digits=2):
    step = Decimal('1').scaleb(-digits)
    return f"{Decimal(str(value)).quantize(step, rounding=ROUND_HALF_UP):,.{digits}f}"


def build():
    companies, combined, sources = [], [], []
    date_reference = None
    for metadata in COMPANIES:
        source = ROOT / 'research/companies' / metadata['folder'] / 'eps-per-history.json'
        raw_bytes = source.read_bytes()
        history = json.loads(raw_bytes)
        daily = history['daily']
        assert len(daily) == 190
        dates = [row['date'] for row in daily]
        assert dates == sorted(set(dates))
        assert dates[0] == '2026-01-05' and dates[-1] == '2026-10-15'
        if date_reference is None:
            date_reference = dates
        assert dates == date_reference
        month_ends = {}
        for row in daily:
            assert row['reportDate'] < row['date']
            if row.get('latestSourceDate'):
                assert row['latestSourceDate'] < row['date']
            assert row['closeJPY'] > 0
            for eps_key, per_key in [('ttmDilutedEPSJPY', 'trailingPER'),
                                     ('halfYearAnnualizedDilutedEPSJPY', 'halfYearAnnualizedPER')]:
                assert row[eps_key] > 0
                assert abs(row['closeJPY'] / row[eps_key] - row[per_key]) < 1e-8
            month_ends[row['date'][:7]] = row
        monthly = [daily[0]] + list(month_ends.values())
        assert len(monthly) == 11
        company = {k: v for k, v in metadata.items() if k not in ('folder', 'report')}
        company.update(reportPath=f"research/companies/{metadata['folder']}/{metadata['report']}",
                       sourcePath=source.relative_to(ROOT).as_posix(),
                       sourceSHA256=hashlib.sha256(raw_bytes).hexdigest(), monthly=monthly)
        companies.append(company)
        sources.append(dict(path=company['sourcePath'], sha256=company['sourceSHA256']))
        for row in monthly:
            combined.append(dict(code=company['code'], company=company['name'], profitBasis='実績', basis=company['basis'], **row))
        if company['code'] == '4062':
            adjustment_source = source.parent / 'ex-stock-gain.json'
            adjustment_bytes = adjustment_source.read_bytes()
            adjustment = json.loads(adjustment_bytes)
            assert adjustment['sourceHistory'] == dict(path=company['sourcePath'], sha256=company['sourceSHA256'])
            assert len(adjustment['monthly']) == 11
            for actual, adjusted in zip(monthly, adjustment['monthly']):
                assert actual['date'] == adjusted['date'] and actual['closeJPY'] == adjusted['closeJPY']
                for eps_key, per_key in [('ttmDilutedEPSJPY', 'trailingPER'),
                                         ('halfYearAnnualizedDilutedEPSJPY', 'halfYearAnnualizedPER')]:
                    assert 0 < adjusted[eps_key] <= actual[eps_key]
                    assert abs(adjusted['closeJPY'] / adjusted[eps_key] - adjusted[per_key]) < 1e-8
            company['exStockGain'] = {k: adjustment[k] for k in ('label', 'basis', 'notes', 'monthly', 'assumedTaxRate', 'reportPath')}
            company['exStockGain']['sourcePath'] = adjustment_source.relative_to(ROOT).as_posix()
            company['exStockGain']['sourceSHA256'] = hashlib.sha256(adjustment_bytes).hexdigest()
            sources.append(dict(path=company['exStockGain']['sourcePath'], sha256=company['exStockGain']['sourceSHA256']))
            for row in adjustment['monthly']:
                combined.append(dict(code=company['code'], company=company['name'], profitBasis=adjustment['label'], basis=adjustment['basis'], **row))
    payload = dict(asOf='2026-10-15', dataAsOf='2026-10-16',
                   definition='当時発表済み実績のTTMと、直近2四半期実績を2倍した半年年換算。円・株式分割調整後。いずれも独自再構成概算で、予想利益を含まない。',
                   companies=companies, sources=sources)
    (BASE / 'valuation-history.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    fields = list(dict.fromkeys(key for row in combined for key in row))
    with (BASE / 'valuation-history.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(combined)
    text = ['# AI関連4銘柄の実績EPS・PER推移', '',
            '株価は2026年10月15日東証終値まで、資料確認・編集は10月16日。TTMは直近12か月、半年年換算は直近2四半期の実績を2倍。各時点で公表済みの決算のみを使用する。円・分割調整後。', '',
            '**4社とも希薄化後の独自概算。イビデンはCB詳細が未開示のため公表累計EPS差分、他3社は利益と期間平均分母の再構成を基本とする。いずれも会社公表TTM・会社予想ではない。**', '',
            'Asset Hubの「AI関連銘柄・サプライチェーン → PERの推移」に、4社の比較と銘柄切替の月次表を表示する。「EPS・PER」一覧の上部にも入口がある。', '',
            '## 10月15日の比較', '',
            '| 会社 | 株価 | TTM EPS | TTM PER | 半年年換算EPS | 半年年換算PER |',
            '|---|---:|---:|---:|---:|---:|']
    for c in companies:
        r = c['monthly'][-1]
        text.append(f"| {c['name']} | {fmt(r['closeJPY'])}円 | {fmt(r['ttmDilutedEPSJPY'])}円 | {fmt(r['trailingPER'],1)}倍 | {fmt(r['halfYearAnnualizedDilutedEPSJPY'])}円 | {fmt(r['halfYearAnnualizedPER'],1)}倍 |")
        if c.get('exStockGain'):
            r = c['exStockGain']['monthly'][-1]
            text.append(f"| {c['name']}・豊田自動織機売却益除外（税率29.9%仮定） | {fmt(r['closeJPY'])}円 | {fmt(r['ttmDilutedEPSJPY'])}円 | {fmt(r['trailingPER'],1)}倍 | {fmt(r['halfYearAnnualizedDilutedEPSJPY'])}円 | {fmt(r['halfYearAnnualizedPER'],1)}倍 |")
    for c in companies:
        text += ['', f"## {c['name']}の月次表", '',
                 f"{c['basis']}。{c['splitBasis']}。", '',
                 '| 時点 | 株価 | TTM EPS | TTM PER | 半年年換算EPS | 半年年換算PER |',
                 '|---|---:|---:|---:|---:|---:|']
        for r in c['monthly']:
            text.append(f"| {r['date']} | {fmt(r['closeJPY'])}円 | {fmt(r['ttmDilutedEPSJPY'])}円 | {fmt(r['trailingPER'],1)}倍 | {fmt(r['halfYearAnnualizedDilutedEPSJPY'])}円 | {fmt(r['halfYearAnnualizedPER'],1)}倍 |")
        text += ['', *[f'- {note}' for note in c['notes']], '',
                 f"[計算方法・一次資料](../../../companies/{c['reportPath'].split('research/companies/')[1]})。"]
        if c.get('exStockGain'):
            adjustment = c['exStockGain']
            text += ['', f"### {adjustment['label']}", '', adjustment['basis'], '',
                     '| 時点 | 株価 | TTM EPS | TTM PER | 半年年換算EPS | 半年年換算PER |',
                     '|---|---:|---:|---:|---:|---:|']
            for r in adjustment['monthly']:
                text.append(f"| {r['date']} | {fmt(r['closeJPY'])}円 | {fmt(r['ttmDilutedEPSJPY'])}円 | {fmt(r['trailingPER'],1)}倍 | {fmt(r['halfYearAnnualizedDilutedEPSJPY'])}円 | {fmt(r['halfYearAnnualizedPER'],1)}倍 |")
            text += ['', *[f'- {note}' for note in adjustment['notes']], '',
                     '[除外方法・税率感応度・一次資料](../../../companies/4062-ibiden/2026-10-16/ex-stock-gain.md)。']
    text += ['', '## 保存と再現', '',
             '[表示用JSON](valuation-history.json) · [実績44行＋除外推計11行のCSV](valuation-history.csv) · [組合せスクリプト](build_history.py)。', '',
             '各社の入力・計算コード・日次結果は会社別レポートから参照。組合せスクリプトは外部通信を行わず、過去の会社別スナップショットを変更しない。株価補完・分母推計・一時利益等の限界も各社資料へ記録した。', '',
             'EPSの金額自体を企業規模・優劣の順位へ使わない。半年年換算は利益継続の仮定を含み、季節性や一時利益で大きく変わる。PERの差だけで割安・割高を断定しない。', '']
    (BASE / 'report.md').write_text('\n'.join(text))
    return payload


if __name__ == '__main__':
    payload = build()
    print(json.dumps({'companies': len(payload['companies']), 'monthlyRows': 44,
                      'latest': [{'name': c['name'], **c['monthly'][-1]} for c in payload['companies']]},
                     ensure_ascii=False, indent=2))
