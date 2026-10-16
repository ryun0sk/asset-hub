const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const ROOT = path.join(__dirname, '..');
const read = file => JSON.parse(fs.readFileSync(path.join(ROOT, file), 'utf8'));
const base = 'research/themes/ai-supply-chain/2026-10-03/';
const valuation = read(base + 'valuation.json');
const chain = read(base + 'catalog.json');
const catalog = read('research/catalog.json');
const entry = catalog.groups.flatMap(group => group.entries).find(item => item.id === 'ai-supply-chain-2026-10-03');
const helpers = () => import(pathToFileURL(path.join(ROOT, 'web/ai-valuations.js')).href);
const symbols = companies => companies.map(company => company.symbol);
const closeTo = (actual, expected, label) => assert.ok(Math.abs(actual - expected) < 0.00001, label);

test('saved valuation contains all 43 listed companies with consistent currency and PER bases', () => {
  const listed = [...new Set(chain.groups.flatMap(group => group.symbols))];
  assert.equal(valuation.companies.length, 43);
  assert.equal(new Set(symbols(valuation.companies)).size, 43);
  assert.deepEqual(symbols(valuation.companies).sort(), listed.sort());
  for (const company of valuation.companies) {
    const snapshot = company.snapshot;
    assert.ok(snapshot.close > 0, company.symbol);
    assert.ok(snapshot.date === '2026-10-02' || (company.symbol === 'WAF.DE' && snapshot.date === '2026-10-01'));
    const converted = company.epsCurrency === company.priceCurrency ? snapshot.ttmEps : snapshot.ttmEps * snapshot.fxRate;
    closeTo(snapshot.ttmEpsPriceCurrency, converted, company.symbol + ' FX');
    if (snapshot.ttmEpsPriceCurrency > 0) closeTo(snapshot.pe, snapshot.close / snapshot.ttmEpsPriceCurrency, company.symbol + ' actual PER');
    else assert.equal(snapshot.pe, null, company.symbol + ' loss PER');
    if (company.companyForecast) closeTo(company.companyForecast.pe, snapshot.close / company.companyForecast.eps, company.symbol + ' company PER');
    for (const period of ['0y', '+1y']) {
      const forecast = company.analyst?.periods?.[period];
      if (forecast?.avgPriceCurrency > 0) closeTo(forecast.pe, snapshot.close / forecast.avgPriceCurrency, company.symbol + ' analyst PER');
    }
  }
  assert.deepEqual(valuation.companies.filter(company => company.snapshot.status === 'loss').map(company => company.symbol), ['3436.T', 'WAF.DE', 'LITE']);
  assert.equal(valuation.companies.filter(company => company.analyst).length, 18);
  assert.equal(valuation.companies.filter(company => company.companyForecast).length, 5);
});

test('all-company filtering searches names, codes and roles, with no repeated companies', async () => {
  const {filterAiCompanies} = await helpers();
  const options = {query: '', group: '', sort: 'order'};
  assert.deepEqual(filterAiCompanies(valuation.companies, chain.groups, options), valuation.companies);
  assert.deepEqual(symbols(filterAiCompanies([...valuation.companies, valuation.companies[0]], chain.groups, options)), symbols(valuation.companies));
  assert.deepEqual(symbols(filterAiCompanies(valuation.companies, chain.groups, {...options, query: '  nVdA  '})), ['NVDA']);
  assert.deepEqual(symbols(filterAiCompanies(valuation.companies, chain.groups, {...options, query: 'キオクシアHD'})), ['285A.T']);
  assert.deepEqual(symbols(filterAiCompanies(valuation.companies, chain.groups, {...options, query: 'gemini'})), ['GOOGL']);
  const server = chain.groups.find(group => group.id === 'server');
  assert.deepEqual(new Set(symbols(filterAiCompanies(valuation.companies, chain.groups, {...options, group: server.id}))), new Set(server.symbols));
  assert.deepEqual(symbols(filterAiCompanies(valuation.companies, chain.groups, {...options, group: 'server', query: 'nvda'})), ['NVDA']);
  assert.deepEqual(filterAiCompanies(valuation.companies, chain.groups, {...options, query: '存在しない会社'}), []);
});

test('each PER sort uses its own saved field, is stable, and leaves unavailable values last', async () => {
  const {filterAiCompanies} = await helpers();
  const fixture = [
    {symbol: 'missing', name: 'missing', snapshot: {pe: null}},
    {symbol: 'a', name: 'a', snapshot: {pe: 20}, analyst: {periods: {'0y': {pe: 6}, '+1y': {pe: 3}}}},
    {symbol: 'b', name: 'b', snapshot: {pe: 10}, analyst: {periods: {'0y': {pe: 2}, '+1y': {pe: 9}}}},
    {symbol: 'tie', name: 'tie', snapshot: {pe: 10}, analyst: {periods: {'0y': {pe: 2}, '+1y': {pe: 9}}}},
    {symbol: 'invalid', name: 'invalid', snapshot: {pe: -5}, analyst: {periods: {'0y': {pe: 0}, '+1y': {pe: Infinity}}}},
  ];
  const before = symbols(fixture);
  const sorted = sort => symbols(filterAiCompanies(fixture, [], {query: '', group: '', sort}));
  assert.deepEqual(sorted('actual'), ['b', 'tie', 'a', 'missing', 'invalid']);
  assert.deepEqual(sorted('current'), ['b', 'tie', 'a', 'missing', 'invalid']);
  assert.deepEqual(sorted('next'), ['a', 'b', 'tie', 'missing', 'invalid']);
  assert.deepEqual(symbols(fixture), before, 'sorting preserves the input order');
});

test('all-company table includes losses, missing forecasts, valuation dates and currency notes', async () => {
  const {renderAiValuations} = await helpers();
  const html = renderAiValuations(valuation, chain);
  const tbody = html.match(/<tbody\b[^>]*data-ai-rows[^>]*>([\s\S]*?)<\/tbody>/)?.[1];
  assert.ok(tbody, 'all-company table body');
  assert.equal((tbody.match(/<tr\b/g) || []).length, 43);
  for (const company of valuation.companies) {
    const rows = [...tbody.matchAll(/<tr\b[^>]*data-symbol="([^"]+)"[^>]*>([\s\S]*?)<\/tr>/g)].filter(row => row[1] === company.symbol);
    assert.equal(rows.length, 1, company.symbol + ' appears once');
    if (company.snapshot.status === 'loss') assert.match(rows[0][2], /赤字・算出不能/);
    if (!company.analyst) assert.match(rows[0][2], /取得なし/);
  }
  for (const label of ['実績', '会社予想', '外部予想', '2026-10-02', '2026-10-04', 'USD', 'EUR', 'HKD', 'TTMが1四半期遅れ']) assert.ok(html.includes(label), label);
  const row = symbol => [...tbody.matchAll(/<tr\b[^>]*data-symbol="([^"]+)"[^>]*>([\s\S]*?)<\/tr>/g)].find(match => match[1] === symbol)[2];
  for (const label of ['19,300.00', '833.50', '23.2倍', '3,489.09', '5.5倍']) assert.ok(row('285A.T').includes(label), 'Kioxia ' + label);
  for (const label of ['28.61', '25.41', '43.17', '38.34', 'USD', 'EUR']) assert.ok(row('ASML').includes(label), 'ASML currency conversion ' + label);
  for (const label of ['1.09', '0.1391', 'HKD', 'USD']) assert.ok(row('0992.HK').includes(label), 'Lenovo currency conversion ' + label);
  assert.doesNotMatch(html, /\bNaN\b|\bInfinity\b|undefined/);
});

test('renderer escapes company, notes, group and data-attribute text', async () => {
  const {renderAiValuations} = await helpers();
  const unsafe = '<img src=x onerror="alert(1)"> & test';
  const company = structuredClone(valuation.companies[0]);
  company.name = unsafe;
  company.symbol = 'X" onmouseover="alert(1)';
  company.snapshot.notes = [unsafe];
  company.companyForecast.label = unsafe;
  const html = renderAiValuations({...valuation, companies: [company]}, {groups: [{id: 'unsafe', name: unsafe, symbols: [company.symbol], roles: {[company.symbol]: unsafe}}]});
  assert.doesNotMatch(html, /<img|data-symbol="X" onmouseover=/);
  assert.match(html, /&lt;img/);
  assert.match(html, /&amp; test/);
  assert.match(html, /data-symbol="X(?:&quot;|&#34;|&#x22;)/);
});

test('supplement is limited to the current AI supply-chain EPS/PER HTML view', async () => {
  const {isAiValuationView} = await helpers();
  const fund = entry.items.find(item => item.view === 'fund');
  assert.equal(isAiValuationView(entry, fund, false), true);
  assert.equal(isAiValuationView(entry, fund, true), false);
  for (const item of entry.items.filter(item => item !== fund)) assert.equal(isAiValuationView(entry, item, false), false);
  assert.equal(isAiValuationView({...entry, kind: 'company'}, fund, false), false);
  assert.equal(isAiValuationView({...entry, slug: 'photonics'}, fund, false), false);
  assert.equal(isAiValuationView(entry, {...fund, type: 'md'}, false), false);
  assert.equal(isAiValuationView(entry, {...fund, path: 'research/../outside/index.html'}, false), false);
  assert.equal(isAiValuationView(null, null, false), false);
});
