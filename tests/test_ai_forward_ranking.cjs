const test = require('node:test');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const path = require('node:path');
const fs = require('node:fs');
const ROOT = path.join(__dirname, '..');
const helpers = () => import(pathToFileURL(path.join(ROOT, 'web/ai-forward-ranking.js')).href);
const read = file => JSON.parse(fs.readFileSync(path.join(ROOT, file), 'utf8'));

function company(symbol, eps = 10, price = 100) {
  const row = e => ({eps_quote_currency: e, terminal_pe: 20, revenue_bn: 10, normal_net_income_bn: e / 10});
  return {symbol, name: symbol, financial_currency: 'USD', stages: ['test'],
    price: {close: price, date: '2026-10-16', currency: 'USD'},
    model_quality: 'screening', model_quality_label: '事業別試算・中低確度', method: '独自の事業別計算', risks: ['循環・回収'],
    sources: [{title: '公式資料', url: 'https://example.com/earnings', date: '2026-08-01'}],
    scenarios: {'2028': {weak: row(eps / 4), base: row(eps / 2), strong: row(eps)}, '2029': {weak: row(eps / 2), base: row(eps), strong: row(eps * 2)}}};
}
const fixture = companies => ({schema: 1, as_of: '2026-10-18 JST', price_date: '2026-10-16', companies, groups: [{id: 'test', name: '半導体テスト', symbols: companies.map(c => c.symbol)}]});

test('conditional price uses the full horizon and preserves zero/loss as unavailable', async () => {
  const {forwardValue} = await helpers();
  const c = company('NVDA', 14.73827, 214.13000488);
  c.scenarios['2029'].base.terminal_pe = 25;
  const result = forwardValue(c);
  assert.ok(Math.abs(result.value - 256.13) < .01);
  assert.ok(Math.abs(result.per - 14.53) < .01);
  assert.ok(forwardValue(c, {requiredReturn: .08}).value > result.value);
  assert.ok(forwardValue(c, {requiredReturn: .16}).value < result.value);
  for (const eps of [0, -3]) {
    const loss = forwardValue(company('loss', eps));
    assert.equal(loss.value, null);
    assert.equal(loss.per, null);
    assert.equal(loss.gap, null);
  }
});

test('ranking uses selected assumptions, handles unavailable values last, and keeps reference businesses out of ranks', async () => {
  const {filterForwardCompanies} = await helpers();
  const a = company('a', 10), b = company('b', 20), loss = company('loss', -2), ref = company('reference', 100);
  ref.rank_eligible = false;
  a.scenarios['2029'].weak.eps_quote_currency = 20;
  const data = fixture([a, b, loss, ref, a]);
  assert.deepEqual(filterForwardCompanies(data).map(c => c.symbol), ['b', 'a', 'loss', 'reference']);
  assert.deepEqual(filterForwardCompanies(data, {scenario: 'weak'}).map(c => c.symbol), ['a', 'b', 'loss', 'reference']);
  assert.deepEqual(data.companies.map(c => c.symbol), ['a', 'b', 'loss', 'reference', 'a']);
  assert.deepEqual(filterForwardCompanies(data, {query: ' Ａ ', group: 'test'}).map(c => c.symbol), ['a']);
  assert.equal(filterForwardCompanies(data, {quality: 'detailed'}).length, 0);
});

test('initial rendering keeps year/case/return controls and numeric column labels aligned', async () => {
  const {renderForwardRanking} = await helpers();
  const html = renderForwardRanking(fixture([company('a')]), {year: 2028, scenario: 'weak', requiredReturn: .16});
  for (const label of ['value="2028" selected', 'value="weak" selected', 'value="0.16" selected', '2028通常純利益', '現値÷2028 EPS', '16%条件の計算価格', '2028年・弱気ケース']) assert.ok(html.includes(label), label);
  assert.doesNotMatch(html, /順位は基準ケース|value="downside"|\bNaN\b|\bInfinity\b|undefined/);
});

test('display escapes text and attributes, rejects script URLs, and shows reference limits without a misleading gap', async () => {
  const {renderForwardRanking} = await helpers();
  const c = company('X" onmouseover="bad');
  c.name = '<img src=x onerror=bad>';
  c.sources = [{title: '<bad>', url: 'javascript:alert(1)'}];
  c.rank_eligible = false;
  c.key_condition = '残存会社のみ・分離株価値未評価';
  const html = renderForwardRanking(fixture([c]));
  assert.doesNotMatch(html, /<img|href="javascript:|data-forward-symbol="X" onmouseover=/);
  assert.match(html, /&lt;img/);
  assert.match(html, /比較対象外/);
  assert.match(html, /残存会社のみ・分離株価値未評価/);
});

test('saved comparison covers all 46 companies with six same-currency scenarios and reconciled financial identities', async () => {
  const {forwardValue, filterForwardCompanies, renderForwardRanking} = await helpers();
  const data = read('research/themes/ai-valuation-ranking/2026-10-18/ranking.json');
  const universe = read('research/themes/ai-supply-chain/2026-10-18/valuation.json').companies;
  assert.equal(data.companies.length, 46);
  assert.deepEqual(new Set(data.companies.map(c => c.symbol)), new Set(universe.map(c => c.symbol)));
  assert.equal(data.companies.filter(c => c.rank_eligible).length, 45);
  const seen = new Set();
  for (const c of data.companies) {
    assert.ok(!seen.has(c.symbol)); seen.add(c.symbol);
    assert.equal(c.price.date, '2026-10-16');
    assert.ok(c.sources.length > 0);
    for (const year of ['2028', '2029']) for (const scenario of ['weak', 'base', 'strong']) {
      const row = c.scenarios[year][scenario];
      assert.ok(row.diluted_shares_bn > 0);
      assert.equal(row.quote_currency, c.price.currency);
      const value = forwardValue(c, {year: Number(year), scenario});
      if (row.eps_quote_currency > 0) assert.ok(Math.abs(value.value - row.conditional_entry_price) < 1e-7 * Math.max(1, row.conditional_entry_price), c.symbol);
      else assert.equal(value.value, null);
    }
  }
  const sorted = filterForwardCompanies(data);
  assert.equal(sorted.at(-1).symbol, 'ETN');
  const gaps = sorted.filter(c => c.rank_eligible).map(c => forwardValue(c).gap).filter(v => v != null);
  assert.deepEqual(gaps, [...gaps].sort((a, b) => b - a));
  const html = renderForwardRanking(data);
  assert.equal((html.match(/data-forward-symbol=/g) || []).length, 46);
  assert.doesNotMatch(html, /\bNaN\b|\bInfinity\b|undefined/);
});
