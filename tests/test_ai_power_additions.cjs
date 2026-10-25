const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const ROOT = path.join(__dirname, '..');
const CURRENT = 'research/themes/ai-supply-chain/2026-10-18/';
const PREVIOUS = 'research/themes/ai-supply-chain/2026-10-03/';
const MONTHLY = 'research/themes/ai-actual-valuation/2026-10-18/';
const read = relative => JSON.parse(fs.readFileSync(path.join(ROOT, relative), 'utf8'));
const prices = read(CURRENT + 'prices.json');
const fundamentals = read(CURRENT + 'fundamentals.json');
const valuation = read(CURRENT + 'valuation.json');
const catalog = read(CURRENT + 'catalog.json');
const actual = read(MONTHLY + 'valuation-history.json');
const daily = read(MONTHLY + 'addition-daily.json');
const additions = ['7011.T', 'GEV', 'ENR.DE'];
const find = (data, symbol) => {
  const company = data.companies.find(item => item.symbol === symbol);
  assert.ok(company, symbol + ': company exists');
  return company;
};
const near = (value, expected, label, tolerance = 1e-8) => {
  assert.ok(Number.isFinite(value), label + ': finite number');
  assert.ok(Math.abs(value - expected) <= tolerance, `${label}: ${value} != ${expected}`);
};
const helpers = () => import(pathToFileURL(path.join(ROOT, 'web/ai-actual-valuations.js')).href);
const format = value => value.toLocaleString('ja-JP', {minimumFractionDigits: 2, maximumFractionDigits: 2});

test('power-generation additions appear once across the 46-company catalog and data sets', () => {
  const listed = [...new Set(catalog.groups.flatMap(group => group.symbols))].sort();
  assert.equal(listed.length, 46);
  for (const data of [prices, fundamentals, valuation]) {
    const symbols = data.companies.map(company => company.symbol);
    assert.equal(symbols.length, 46);
    assert.equal(new Set(symbols).size, 46, 'no duplicate company');
    assert.deepEqual([...symbols].sort(), listed);
  }
  const generation = catalog.groups.filter(group => group.id === 'generation');
  assert.equal(generation.length, 1);
  assert.deepEqual([...generation[0].symbols].sort(), [...additions].sort());
  const edges = catalog.edges;
  assert.ok(edges.some(([from, to]) => from === 'cloud' && to === 'generation'));
  assert.ok(edges.some(([from, to]) => from === 'generation' && to === 'power'));
});

test('all saved company records for the original 43 companies are preserved exactly', () => {
  for (const [filename, current] of [['prices.json', prices], ['fundamentals.json', fundamentals], ['valuation.json', valuation]]) {
    const previous = read(PREVIOUS + filename);
    assert.equal(previous.companies.length, 43);
    for (const company of previous.companies) {
      assert.deepEqual(find(current, company.symbol), company, `${filename}: ${company.symbol} remains unchanged`);
    }
    assert.deepEqual(current.companies.filter(company => !previous.companies.some(old => old.symbol === company.symbol)).map(company => company.symbol).sort(), [...additions].sort());
  }
});

test('the four existing monthly histories and their accounting adjustments remain unchanged', () => {
  const previous = read('research/themes/ai-actual-valuation/2026-10-16/valuation-history.json');
  assert.equal(previous.companies.length, 4);
  assert.equal(actual.companies.length, 7);
  assert.equal(new Set(actual.companies.map(company => company.symbol)).size, 7);
  for (const company of previous.companies) {
    assert.deepEqual(find(actual, company.symbol), company, `${company.symbol}: monthly rows, sources and adjustments`);
  }
});

test('latest P/E values use local closing prices and the documented actual EPS bases', () => {
  const expected = {
    '7011.T': {currency: 'JPY', close: 3796, ttm: 118.6, half: 152.24},
    GEV: {currency: 'USD', close: 921.200012, ttm: 34.94, half: 39.82},
    'ENR.DE': {currency: 'EUR', close: 134.979996, ttm: 3.11, half: 4.28},
  };
  for (const symbol of additions) {
    const input = expected[symbol], company = find(valuation, symbol), snapshot = company.snapshot;
    const history = find(actual, symbol), latest = history.monthly.at(-1);
    const price = find(prices, symbol).rows.at(-1);
    assert.equal(company.priceCurrency, input.currency);
    assert.equal(company.epsCurrency, input.currency);
    assert.equal(history.currency, input.currency);
    assert.equal(snapshot.date, '2026-10-16');
    assert.equal(latest.date, snapshot.date);
    near(snapshot.close, input.close, symbol + ': quoted close');
    near(snapshot.close, price.close, symbol + ': close matches price source');
    near(snapshot.ttmEps, input.ttm, symbol + ': actual TTM EPS');
    near(snapshot.ttmEpsPriceCurrency, input.ttm, symbol + ': no FX substitution');
    near(snapshot.pe, input.close / input.ttm, symbol + ': valuation P/E');
    near(latest.close, input.close, symbol + ': monthly close');
    near(latest.ttmDilutedEPS, input.ttm, symbol + ': monthly TTM EPS');
    near(latest.halfYearAnnualizedDilutedEPS, input.half, symbol + ': six-month annualized EPS');
    near(latest.trailingPER, input.close / input.ttm, symbol + ': monthly TTM P/E');
    near(latest.halfYearAnnualizedPER, input.close / input.half, symbol + ': monthly annualized P/E');
  }
});

test('company forecasts remain separate from diluted actuals and missing estimates stay null', () => {
  const mhi = find(valuation, '7011.T');
  near(mhi.companyForecast.eps, 113.09, 'MHI company forecast EPS');
  assert.equal(mhi.companyForecast.periodEnd, '2027-03-31');
  assert.match(mhi.companyForecast.label, /基本/);
  assert.match(mhi.companyForecastNote, /基本.*113\.09/);
  assert.match(find(actual, '7011.T').basis, /希薄化後/);
  near(mhi.companyForecast.pe, mhi.snapshot.close / 113.09, 'forecast P/E uses its own basic EPS');
  for (const symbol of additions) assert.equal(find(valuation, symbol).analyst, null, symbol + ': no invented analyst estimate');
  for (const symbol of ['GEV', 'ENR.DE']) assert.equal(find(valuation, symbol).companyForecast, null, symbol + ': no invented company EPS');
  const gev = find(valuation, 'GEV');
  const notes = gev.snapshot.notes.join('\n');
  assert.match(notes, /Prolec/);
  assert.match(notes, /再評価益/);
  assert.match(notes, /税便益|税効果/);
  assert.match(notes, /2026Q1|2026年1〜3月/);
  assert.match(notes, /2025Q4|2025年10〜12月/);
  near(gev.quarterly.find(row => row.periodEnd === '2026-03-31').eps, 17.44, 'GEV revaluation quarter');
  near(gev.quarterly.find(row => row.periodEnd === '2025-12-31').eps, 13.39, 'GEV tax-benefit quarter');
});

test('daily records change EPS only on the first eligible local trading date', () => {
  const boundaries = [
    {symbol: 'GEV', before: '2026-04-21', after: '2026-04-22', old: 17.8, next: 34.33, halfOld: 30.06, halfNext: 61.66},
    {symbol: 'ENR.DE', before: '2026-08-04', after: '2026-08-05', old: 2.55, next: 3.11, halfOld: 3.32, halfNext: 4.28},
    {symbol: '7011.T', before: '2026-08-03', after: '2026-08-04', old: 98.84, next: 118.6, halfOld: 129.28, halfNext: 152.24},
  ];
  for (const boundary of boundaries) {
    const rows = daily[boundary.symbol].daily;
    const before = rows.find(row => row.date === boundary.before);
    const after = rows.find(row => row.date === boundary.after);
    assert.ok(before && after, boundary.symbol + ': both boundary dates exist');
    near(before.ttmDilutedEPS, boundary.old, boundary.symbol + ': previous-close EPS');
    near(after.ttmDilutedEPS, boundary.next, boundary.symbol + ': release-day EPS');
    near(before.halfYearAnnualizedDilutedEPS, boundary.halfOld, boundary.symbol + ': previous half-year EPS');
    near(after.halfYearAnnualizedDilutedEPS, boundary.halfNext, boundary.symbol + ': updated half-year EPS');
    assert.ok(before.knownFrom < boundary.after);
    assert.equal(after.knownFrom, boundary.after);
    assert.ok(before.profitPeriodEnd < after.profitPeriodEnd);
    near(before.trailingPER, before.close / boundary.old, boundary.symbol + ': pre-release P/E');
    near(after.trailingPER, after.close / boundary.next, boundary.symbol + ': post-release P/E');
  }
});

test('every added daily and monthly observation uses public data and preserves the market close', () => {
  for (const symbol of additions) {
    const company = find(valuation, symbol), history = find(actual, symbol);
    const quotes = new Map(find(prices, symbol).rows.map(row => [row.date, row.close]));
    const rows = daily[symbol].daily;
    assert.ok(rows.length > 180, symbol + ': full year-to-date history');
    for (const row of rows) {
      assert.ok(row.knownFrom <= row.date, symbol + ' ' + row.date + ': no future known date');
      assert.ok(row.reportDate <= row.knownFrom, symbol + ' ' + row.date + ': report precedes eligibility');
      const available = company.ttmSeries.filter(point => point.knownFrom <= row.date).sort((a, b) => b.periodEnd.localeCompare(a.periodEnd))[0];
      assert.ok(available, symbol + ' ' + row.date + ': eligible financial report');
      assert.equal(row.profitPeriodEnd, available.periodEnd);
      near(row.ttmDilutedEPS, available.eps, symbol + ' ' + row.date + ': eligible EPS');
      near(row.close, quotes.get(row.date), symbol + ' ' + row.date + ': unconverted close');
    }
    for (const row of history.monthly) {
      assert.deepEqual(row, rows.find(point => point.date === row.date), symbol + ' ' + row.date + ': monthly is an actual daily observation');
      assert.equal(Object.hasOwn(row, 'closeJPY'), false, 'new rows use currency-neutral fields');
      assert.equal(Object.hasOwn(row, 'ttmDilutedEPSJPY'), false);
    }
    assert.equal(history.monthly[0].date.slice(0, 7), '2026-01');
    assert.equal(history.monthly.at(-1).date, '2026-10-16');
  }
});

test('the live monthly path loads seven companies and renders each currency from neutral fields', async () => {
  const {ACTUAL_VALUATION_PATH, validActualValuations, renderActualCompany} = await helpers();
  assert.equal(ACTUAL_VALUATION_PATH, MONTHLY + 'valuation-history.json');
  assert.equal(validActualValuations(actual), true);
  const units = {'7011.T': '円', GEV: '米ドル', 'ENR.DE': 'ユーロ'};
  for (const symbol of additions) {
    const company = structuredClone(find(actual, symbol));
    // Different legacy aliases make an accidental fallback observable.
    for (const row of company.monthly) Object.assign(row, {closeJPY: 987654321, ttmDilutedEPSJPY: 987654322, halfYearAnnualizedDilutedEPSJPY: 987654323});
    const html = renderActualCompany(company);
    const headings = html.match(/<thead>([\s\S]*?)<\/thead>/)?.[1];
    assert.ok(headings);
    assert.ok(headings.includes(`株価（${units[symbol]}）`));
    assert.ok(headings.includes(`EPS（${units[symbol]}）`));
    if (company.currency !== 'JPY') assert.doesNotMatch(headings, /円|JPY/);
    assert.doesNotMatch(html, /987,654,32[123]|NaN|Infinity|undefined/);
    const rendered = [...html.matchAll(/<th scope="row">([^<]+)<\/th>((?:<td>[^<]*<\/td>)+)/g)];
    assert.equal(rendered.length, company.monthly.length);
    for (const [index, row] of company.monthly.entries()) {
      const cells = [...rendered[index][2].matchAll(/<td>([^<]*)<\/td>/g)].map(match => match[1]);
      assert.equal(rendered[index][1], row.date);
      assert.equal(cells[0], format(row.close));
      assert.equal(cells[1], format(row.ttmDilutedEPS));
      assert.equal(cells[3], format(row.halfYearAnnualizedDilutedEPS));
    }
  }
});

test('official annual and quarterly EPS remain available as separate graph inputs', () => {
  for (const symbol of additions) {
    const company = find(valuation, symbol), fund = find(fundamentals, symbol), input = read(company.sourcePath);
    assert.ok(company.quarterly.length >= 10, symbol + ': quarterly chart history');
    assert.ok(company.annual.length >= 2, symbol + ': annual chart history');
    assert.deepEqual(company.quarterly, input.quarterly);
    assert.deepEqual(company.annual, input.annual);
    assert.deepEqual(fund.quarterlyRows, input.quarterly);
    assert.deepEqual(fund.rows, input.annual);
    for (const row of [...fund.rows, ...fund.quarterlyRows]) {
      assert.match(row.periodEnd, /^\d{4}-\d{2}-\d{2}$/);
      assert.ok(Number.isFinite(row.eps));
      assert.match(row.source, /^https:\/\//);
      assert.ok(row.periodEnd < row.publishedDate && row.publishedDate <= row.knownFrom);
    }
    assert.equal(company.quarterly.at(-1).periodEnd, '2026-06-30');
  }
  near(find(fundamentals, 'ENR.DE').rows.at(-1).eps, 1.60, 'ENR official annual EPS is not replaced by quarterly sum');
  near(find(fundamentals, 'GEV').rows.at(-1).eps, 17.69, 'GEV official annual EPS is not replaced by quarterly sum');
});
