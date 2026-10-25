"""Recompute 46-company conditional earnings and valuation comparison offline.

Money and diluted ordinary shares use billions. Future values are independent
scenarios, not observed values, guidance, consensus, or a probability forecast.
All financial identities are checked against the saved specialist inputs.
"""
import copy
import csv
from datetime import date
import hashlib
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
OLD = ROOT / 'research/themes/ai-forward-valuation/2026-10-18'
CASES = ('weak', 'base', 'strong')


def read(path):
    return json.loads(path.read_text())


def check(actual, expected, label):
    assert abs(actual - expected) <= 1e-7 * max(1, abs(actual), abs(expected)), (label, actual, expected)


def currency_factor(financial, quote, prices):
    if financial == quote:
        return 1
    if financial == 'USD' and quote in ('TWD', 'HKD', 'KRW', 'JPY'):
        symbol = {'TWD': 'TWD=X', 'HKD': 'HKD=X', 'KRW': 'KRW=X', 'JPY': 'JPY=X'}[quote]
        return prices[symbol]['last']['close']
    if financial == 'EUR' and quote == 'USD':
        return prices['EURUSD=X']['last']['close']
    raise ValueError(('Unsupported currency bridge', financial, quote))


def add_value(row, company, price, rate=0.12):
    out = dict(row)
    eps, pe = row['eps_quote_currency'], company['terminal_pe'][row['case']]
    years = (date(row['year'], 12, 31) - date.fromisoformat(price['last']['date'])).days / 365.25
    value = eps * pe / (1 + rate) ** years if eps > 0 else None
    out.update(terminal_pe=pe, price=price['last']['close'], price_date=price['last']['date'],
               quote_currency=price['currency'], financial_currency=company['financial_currency'],
               discount_years=years, required_return=rate,
               forward_scenario_pe=price['last']['close'] / eps if eps > 0 else None,
               conditional_entry_price=value,
               entry_price_gap_pct=(value / price['last']['close'] - 1) * 100 if value is not None else None,
               terminal_price=eps * pe if eps > 0 else None,
               rank_eligible=company.get('rank_eligible', True))
    out['return_sensitivity'] = {str(r): eps * pe / (1 + r) ** years if eps > 0 else None for r in (0.08, 0.12, 0.16)}
    out['pe_sensitivity'] = {str(f): value * f if value is not None else None for f in (0.75, 1, 1.25)}
    return out


def detailed_eight(prices):
    spec = importlib.util.spec_from_file_location('previous_eight', OLD / 'build_model.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    notes, macro = read(BASE / 'inputs/detailed-eight-notes.json'), read(OLD / 'macro.json')
    result = {}
    for row in module.build_rows():
        symbol = '2330.TW' if row['symbol'] == 'TSM' else row['symbol']
        if symbol not in result:
            note = notes[symbol]
            result[symbol] = dict(symbol=symbol, financial_currency=row['financial_currency'],
                quote_currency=prices[symbol]['currency'], method=note['method'], risks=note['risks'],
                key_condition=note['key_condition'], model_quality='detailed', model_quality_label='詳細モデル・独自仮定',
                terminal_pe=macro['valuation']['terminal_pe'][row['symbol']],
                sources=[{'title': '会社決算・説明資料', 'url': note['url'], 'date': note['date'], 'status': '実績・会社見通し'}],
                source_input='research/themes/ai-forward-valuation/2026-10-18/', rows=[], rank_eligible=True,
                basis_note='先の8社詳細モデルを保存入力から再計算。将来値はすべて独自仮定。確認範囲の詳しさは予測確率を意味しない。')
        converted = dict(row, symbol=symbol)
        if symbol == '2330.TW':
            converted['eps_quote_currency'] = row['eps_financial_currency'] * currency_factor('USD', 'TWD', prices)
            converted['ordinary_shares_per_quoted_unit'] = 1
            result[symbol]['basis_note'] += '' if len(result[symbol]['rows']) else ' 今回は台湾普通株2330.TW。旧表のADR EPS÷5×USD/TWDで換算し、ADRの株価プレミアムを持ち込まない。'
        elif symbol == 'ASML':
            converted['eps_quote_currency'] = row['eps_financial_currency'] * currency_factor('EUR', 'USD', prices)
        result[symbol]['rows'].append(converted)
    assert len(result) == 8
    return result


def sources_for(company):
    out, seen = [], set()
    for fact in company.get('anchor_facts', []):
        urls = fact.get('sourceURLs', fact.get('source_urls', fact.get('sources', [])))
        if isinstance(urls, str):
            urls = [urls]
        if fact.get('url'):
            urls = [*urls, fact['url']]
        for item in urls:
            url = item.get('url') if isinstance(item, dict) else item
            if not url or url in seen:
                continue
            seen.add(url)
            out.append({'title': (item.get('title') if isinstance(item, dict) else None) or fact.get('title') or '一次資料',
                        'url': url, 'date': fact.get('date', ''), 'status': fact.get('scope', '実績・会社見通し')})
    return out


def recompute(company, row, prices):
    segments = row['segments']
    revenue, operating = 0, 0
    for segment in segments:
        rev = segment['market_or_revenue_anchor_bn'] * segment['growth_factor'] * segment.get('share_factor', 1)
        check(rev, segment['revenue_bn'], (company['symbol'], row['year'], row['case'], segment['name']))
        revenue += rev
        operating += rev * segment['operating_margin']
    operating -= row.get('unallocated_cost_bn', 0)
    pretax = operating + row['net_finance_bn'] + row.get('other_normal_nonoperating_bn', 0)
    tax = max(pretax, 0) * row['tax_rate']
    ni = pretax - tax - row.get('minority_bn', 0) - row.get('preferred_dividends_bn', 0)
    eps = ni / row['diluted_shares_bn'] * currency_factor(company['financial_currency'], company['quote_currency'], prices)
    for label, value in [('revenue_bn', revenue), ('operating_income_bn', operating), ('normal_net_income_bn', ni), ('eps_quote_currency', eps)]:
        check(value, row[label], (company['symbol'], row['year'], row['case'], label))
    return dict(row, revenue_bn=revenue, operating_income_bn=operating, normal_net_income_bn=ni,
                eps_quote_currency=eps, symbol=company['symbol'])


def newer_companies(prices):
    result = {}
    for name in ('japan', 'compute', 'infrastructure'):
        path = BASE / 'inputs' / (name + '.json')
        data = read(path)
        for source in data['companies']:
            company = copy.deepcopy(source)
            symbol = company['symbol']
            assert symbol not in result
            assert company['quote_currency'] == prices[symbol]['currency'], (symbol, company['quote_currency'])
            if isinstance(company['risks'], str):
                company['risks'] = [company['risks']]
            company['sources'] = sources_for(company)
            assert company['sources'], ('No primary source', symbol)
            company['model_quality_raw'] = company.get('model_quality', '中低')
            limited = str(company['model_quality_raw']).startswith('C_') or company['model_quality_raw'] == 'low'
            company['model_quality'] = 'limited' if limited else 'screening'
            company['model_quality_label'] = '限定的な試算・低確度' if limited else '事業別試算・中低確度'
            company['source_input'] = path.relative_to(ROOT).as_posix()
            company['basis_note'] = ' '.join(str(f.get('facts', f.get('scope', ''))) for f in company.get('anchor_facts', []))
            if company.get('share_basis'):
                company['basis_note'] += ' 株数・換算基準：' + company['share_basis']
            company['key_condition'] = company.get('key_condition') or company['risks'][0]
            company['rank_eligible'] = symbol != 'ETN'
            if symbol == 'ETN':
                company['key_condition'] = '参考：残存ETNのみ。Mobility分離株価値を未評価のため順位比較対象外。'
                company['valuation_note'] = '現在株価はMobility分離前の権利を含む。残存会社の将来EPSだけの計算価格には下方バイアスがあり、他社との割安順位から除外する。'
            if symbol == 'WAF.DE':
                company['key_condition'] = '強い市況回復仮定。新工場償却を吸収する採算改善が必要。'
                company['risks'].append('基準2029売上1.870bnEUR・EBIT14%は、償却をH1年率0.4776bnで維持するとEBITDA率約39.5%が必要。EBITDA30%/35%ならEPS約0.79/2.50EURで、基準4.05EURより低い。独自感応度。')
            company['rows'] = [recompute(company, row, prices) for row in company['rows']]
            result[symbol] = company
    assert len(result) == 38
    return result


def money(value, currency, digits=2):
    if value is None:
        return '算出不能'
    return f'{value:,.{0 if currency in ("JPY", "KRW") else digits}f} {currency}'


def ranking_gap(company):
    gap = company['scenarios']['2029']['base']['entry_price_gap_pct']
    return gap if gap is not None else float('-inf')


def markdown_tables(companies):
    eligible = [c for c in companies if c['rank_eligible']]
    eligible.sort(key=ranking_gap, reverse=True)
    eligible += [c for c in companies if not c['rank_eligible']]
    lines = ['|順|企業|10/16株価|2028→2029通常純利益（bn）|2028→2029 EPS|現値÷29EPS|29想定PER|12%条件価格|現値比余地|',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    ranges = ['|企業|2029EPS：弱／基準／強|2029計算価格：弱／基準／強|', '|---|---:|---:|']
    for i, c in enumerate(eligible, 1):
        a, b = c['scenarios']['2028']['base'], c['scenarios']['2029']['base']
        currency = c['price']['currency']
        rank = i if c['rank_eligible'] and b['entry_price_gap_pct'] is not None else '参考' if not c['rank_eligible'] else '—'
        gap = f'{b["entry_price_gap_pct"]:+.0f}%' if c['rank_eligible'] and b['entry_price_gap_pct'] is not None else '比較対象外' if not c['rank_eligible'] else '算出不能'
        pe = f'{b["forward_scenario_pe"]:.1f}倍' if b['forward_scenario_pe'] is not None else '算出不能'
        lines.append(f'|{rank}|{c["name"]} ({c["symbol"]})|{money(c["price"]["close"],currency)}|{a["normal_net_income_bn"]:,.2f}→{b["normal_net_income_bn"]:,.2f} {c["financial_currency"]}|{money(a["eps_quote_currency"],currency)}→{money(b["eps_quote_currency"],currency)}|{pe}|{b["terminal_pe"]}倍|{money(b["conditional_entry_price"],currency)}|{gap}|')
        eps = '／'.join(money(c['scenarios']['2029'][s]['eps_quote_currency'],currency) for s in CASES)
        values = '／'.join(money(c['scenarios']['2029'][s]['conditional_entry_price'],currency) for s in CASES)
        ranges.append(f'|{c["name"]}|{eps}|{values}|')
    return '\n'.join(lines), '\n'.join(ranges)


def build():
    quotes = read(BASE / 'prices.json')
    prices = {p['symbol']: p for p in quotes['items']}
    chain = read(ROOT / 'research/themes/ai-supply-chain/2026-10-18/catalog.json')
    universe = read(ROOT / 'research/themes/ai-supply-chain/2026-10-18/valuation.json')['companies']
    models = detailed_eight(prices)
    models.update(newer_companies(prices))
    assert set(models) == {c['symbol'] for c in universe} and len(models) == 46
    companies, rows = [], []
    for entry in universe:
        symbol = entry['symbol']
        company = models[symbol]
        assert prices[symbol]['last']['date'] == '2026-10-16'
        company.update(name=entry['name'], stages=[g['id'] for g in chain['groups'] if symbol in g['symbols']],
            price={'close': prices[symbol]['last']['close'], 'date': '2026-10-16', 'currency': prices[symbol]['currency'], 'url': prices[symbol]['history_url']})
        raw_rows = company.pop('rows')
        assert {(r['year'],r['case']) for r in raw_rows} == {(y,c) for y in (2028,2029) for c in CASES}
        company['scenarios'] = {str(y): {} for y in (2028,2029)}
        for row in raw_rows:
            row = add_value(row, company, prices[symbol])
            company['scenarios'][str(row['year'])][row['case']] = row
            rows.append(row)
        for year in ('2028','2029'):
            values = [company['scenarios'][year][c]['eps_quote_currency'] for c in CASES]
            assert values == sorted(values), (symbol, year, 'scenario order', values)
        companies.append(company)
    assert len(rows) == 276
    data = {'schema':1, 'as_of':'2026-10-18 JST', 'price_date':'2026-10-16', 'required_return':0.12,
            'revision':'2026-10-18 Taiwan CB follow-up; initial published version retained in revisions/initial-published',
            'scenario_type':'independent conditional assumptions; no probabilities; not company guidance or consensus',
            'money_units':'billions of financial_currency; EPS is per quoted ordinary share in quote_currency',
            'ranking_definition':'EPS * terminal PE discounted at 12% / current price - 1; dividends/tax/FX changes excluded',
            'rank_eligible_count':45, 'reference_count':1, 'groups':chain['groups'], 'companies':companies}
    (BASE/'ranking.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (BASE/'results.json').write_text(json.dumps({'as_of':data['as_of'],'rows':rows},ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    fields = ['symbol','year','case','financial_currency','quote_currency','price','price_date','revenue_bn','operating_income_bn',
              'normal_net_income_bn','diluted_shares_bn','eps_quote_currency','forward_scenario_pe','terminal_pe','terminal_price',
              'conditional_entry_price','entry_price_gap_pct','rank_eligible']
    with (BASE/'results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    paths = [BASE/'prices.json',*(BASE/'inputs').glob('*.json'),OLD/'build_model.py',OLD/'macro.json',*(OLD/'inputs').glob('*.json')]
    manifest = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    (BASE/'input-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    table, ranges = markdown_tables(companies)
    template = (BASE/'report-template.md').read_text()
    details=[]
    for c in companies:
        src='、'.join(f'[{s["title"]} {s["date"]}]({s["url"]})' for s in c['sources'])
        details += [f'### {c["name"]}（{c["symbol"]}）', '', str(c['method']), '',
                    '**成立条件・反証：** '+' '.join(c['risks']), '', c.get('valuation_note',''), '', src, '']
    (BASE/'report.md').write_text(template.replace('{{BASE_TABLE}}',table).replace('{{RANGE_TABLE}}',ranges).replace('{{COMPANY_DETAILS}}','\n'.join(details)))
    print(f'Recomputed {len(companies)} companies / {len(rows)} scenarios; 45 comparable + ETN reference.')
    ranked=sorted((c for c in companies if c['rank_eligible']), key=ranking_gap, reverse=True)
    for c in ranked[:12]:
        row=c['scenarios']['2029']['base']
        print(c['symbol'], 'EPS',round(row['eps_quote_currency'],3),'gap',round(row['entry_price_gap_pct'],1))


if __name__ == '__main__':
    build()
