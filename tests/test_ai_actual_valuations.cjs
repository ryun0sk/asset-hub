const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const helpers = () => import(pathToFileURL(path.join(__dirname, '..', 'web/ai-actual-valuations.js')).href);

function data() {
  return {
    asOf: '2026-10-15', dataAsOf: '2026-10-16',
    companies: ['285A', '6857', '4062', '6146'].map((code, index) => ({
      code, symbol: `${code}.T`, name: ['キオクシア', 'アドバンテスト', 'イビデン', 'ディスコ'][index],
      basis: index === 2 ? '基本EPS' : '希薄化後EPSの再構成概算', splitBasis: '2026-10-15の株式数基準',
      reportPath: `research/companies/${code}-example/2026-10-16/report.md`,
      monthly: [
        {date: '2026-01-05', closeJPY: 10000, ttmDilutedEPSJPY: 100, trailingPER: 100, halfYearAnnualizedDilutedEPSJPY: 200, halfYearAnnualizedPER: 50, profitPeriodStart: '2024-10-01', profitPeriodEnd: '2025-09-30', halfYearProfitPeriodStart: '2025-04-01', halfYearProfitPeriodEnd: '2025-09-30', reportDate: '2025-11-01'},
        {date: '2026-10-15', closeJPY: 12000, ttmDilutedEPSJPY: 500, trailingPER: 24, halfYearAnnualizedDilutedEPSJPY: 800, halfYearAnnualizedPER: 15, profitPeriodStart: '2025-07-01', profitPeriodEnd: '2026-06-30', halfYearProfitPeriodStart: '2026-01-01', halfYearProfitPeriodEnd: '2026-06-30', reportDate: '2026-07-31'},
      ], notes: ['半年の年換算は会社予想ではない'],
    })),
  };
}

function withExStockGain() {
  const fixture = data(), company = fixture.companies[2];
  company.exStockGain = {
    label: '株式売却益を除く（推計）', basis: '公表された税引前売却益を仮定税率で税引後に補正する推計',
    reportPath: 'research/companies/4062-example/2026-10-16/ex-stock-gain.md',
    notes: ['適用税率は仮定で、実際の売却益課税額とは一致しない'],
    monthly: company.monthly.map((row, index) => index === 0 ? {...row} : {...row, ttmDilutedEPSJPY: 300, trailingPER: 40, halfYearAnnualizedDilutedEPSJPY: 400, halfYearAnnualizedPER: 30}),
  };
  return fixture;
}

test('monthly table preserves historical bases, dates and fundamental definitions across four companies', async () => {
  const {renderActualValuations, validActualValuations} = await helpers();
  const fixture = data();
  assert.equal(validActualValuations(fixture), true);
  const html = renderActualValuations(fixture, '4062.T');
  for (const label of ['キオクシア', 'アドバンテスト', 'イビデン', 'ディスコ', '2026-10-15', '2026-10-16', '会社予想ではありません', '基本EPS', '2026-01-01〜2026-06-30', '2024-10-01〜2025-09-30', '24.0倍', '15.0倍', '2026-10-03保存版']) assert.ok(html.includes(label), label);
  assert.match(html, /<option value="4062\.T" selected>/);
  assert.equal((html.match(/<option\b/g) || []).length, 4);
  assert.match(html, /href="\/research\/companies\/4062-example\/2026-10-16\/report.md"/);
  assert.doesNotMatch(html, /NaN|Infinity|undefined/);
  assert.equal(validActualValuations({companies: []}), false);
  fixture.companies[0].monthly[0].closeJPY = null;
  assert.equal(validActualValuations(fixture), false);
});

test('picker follows supported selected companies and retains a meaningful fallback', async () => {
  const {actualCompanyForSelection} = await helpers();
  const {companies} = data();
  assert.equal(actualCompanyForSelection(companies, ['SNDK', '6146.T']).code, '6146');
  assert.equal(actualCompanyForSelection(companies, ['285A.T', '6857.T'], '6857.T').code, '6857');
  assert.equal(actualCompanyForSelection(companies, ['285A.T'], '6146.T').code, '285A');
  assert.equal(actualCompanyForSelection(companies, ['NVDA']), null);
  assert.equal(actualCompanyForSelection(companies), null);
});

test('monthly renderer escapes imported labels and never links unsafe paths or invents missing PER', async () => {
  const {renderActualCompany} = await helpers();
  const company = data().companies[0];
  company.name = '<img src=x onerror="alert(1)"> & company';
  company.reportPath = 'javascript:alert(1)';
  company.notes = ['<script>alert(1)</script>'];
  company.monthly[1].trailingPER = null;
  company.monthly[1].halfYearAnnualizedPER = -2;
  company.monthly[1].ttmDilutedEPSJPY = null;
  const html = renderActualCompany(company);
  assert.match(html, /&lt;img/);
  assert.match(html, /&lt;script&gt;/);
  assert.doesNotMatch(html, /<img|<script|javascript:|NaN|Infinity|undefined/);
  assert.equal((html.match(/算出不能/g) || []).length, 2);
});

test('stock-gain estimate is visible in the comparison and selectable without replacing reported history', async () => {
  const {validActualValuations, renderActualValuations, renderActualCompany} = await helpers();
  const fixture = withExStockGain(), company = fixture.companies[2];
  assert.equal(validActualValuations(fixture), true);
  const overview = renderActualValuations(fixture);
  assert.equal((overview.match(/data-actual-symbol=/g) || []).length, 5);
  assert.match(overview, /data-actual-symbol="4062\.T" data-actual-profit-basis="exStockGain" aria-pressed="false">イビデン：株式売却益を除く（推計）/);
  assert.match(overview, /<td>40\.0倍<\/td><td>30\.0倍<\/td>/);
  const reported = renderActualCompany(company);
  assert.match(reported, /<option value="reported" selected>実績/);
  assert.match(reported, /<td>500\.00<\/td><td>24\.0倍<\/td><td>800\.00<\/td><td>15\.0倍<\/td>/);
  assert.doesNotMatch(reported, /適用税率は仮定/);
  const adjusted = renderActualCompany(company, 'exStockGain');
  assert.match(adjusted, /<option value="exStockGain" selected>株式売却益を除く（推計）/);
  assert.ok(adjusted.includes(company.exStockGain.basis));
  assert.ok(adjusted.includes(company.exStockGain.notes[0]));
  assert.ok(adjusted.includes(company.notes[0]), 'existing accounting notes remain visible');
  assert.match(reported, /href="\/research\/companies\/4062-example\/2026-10-16\/report.md"/);
  assert.match(adjusted, /href="\/research\/companies\/4062-example\/2026-10-16\/ex-stock-gain.md"/);
  assert.match(adjusted, /<td>100\.00<\/td><td>100\.0倍<\/td><td>200\.00<\/td><td>50\.0倍<\/td>/, 'earlier unaffected row is preserved');
  assert.match(adjusted, /<td>300\.00<\/td><td>40\.0倍<\/td><td>400\.00<\/td><td>30\.0倍<\/td>/);
  const unsupported = renderActualCompany(fixture.companies[0], 'exStockGain');
  assert.doesNotMatch(unsupported, /data-actual-basis|株式売却益/);
  assert.match(unsupported, /実績EPS・PER月次推移/);
  company.exStockGain.monthly[0].date = '2026-01-06';
  assert.equal(validActualValuations(fixture), false, 'adjusted dates must align with reported history');
});

test('estimate labels and notes are escaped, and a nonpositive estimate EPS cannot show a positive PER', async () => {
  const {renderActualValuations, renderActualCompany} = await helpers();
  const fixture = withExStockGain(), company = fixture.companies[2];
  company.exStockGain.label = '<img src=x onerror="alert(1)">（推計）';
  company.exStockGain.basis = '<script>basis</script>';
  company.exStockGain.notes = ['<img src=x>'];
  company.exStockGain.reportPath = 'javascript:alert(1)';
  company.exStockGain.monthly[1].ttmDilutedEPSJPY = -3;
  company.exStockGain.monthly[1].halfYearAnnualizedDilutedEPSJPY = 0;
  const html = renderActualCompany(company, 'exStockGain');
  assert.match(html, /&lt;img/);
  assert.match(html, /&lt;script&gt;basis&lt;\/script&gt;/);
  assert.doesNotMatch(html, /<img|<script|javascript:|NaN|Infinity|undefined/);
  assert.equal((html.match(/算出不能/g) || []).length, 2);
  const overview = renderActualValuations(fixture);
  assert.doesNotMatch(overview, /<img|<script/);
  assert.equal((overview.match(/算出不能/g) || []).length, 2);
});

test('failed fetch exposes retry and cleanup prevents late results from changing the page', async () => {
  const {mountActualValuationHistory} = await helpers();
  const before = global.fetch;
  const listeners = new Map();
  const doc = {
    querySelectorAll: () => [],
    addEventListener: (name, listener) => listeners.set(name, listener),
    removeEventListener: (name, listener) => { if (listeners.get(name) === listener) listeners.delete(name); },
  };
  const host = {innerHTML: '', isConnected: true, contains: () => true};
  try {
    global.fetch = async () => ({ok: false});
    const cleanup = mountActualValuationHistory(host, doc);
    await new Promise(resolve => setImmediate(resolve));
    assert.match(host.innerHTML, /role="alert"/);
    assert.match(host.innerHTML, /data-actual-retry/);
    let complete;
    global.fetch = () => new Promise(resolve => { complete = resolve; });
    const retry = {closest: selector => selector === '[data-actual-retry]' ? retry : null};
    listeners.get('click')({target: retry});
    assert.match(host.innerHTML, /読み込んでいます/);
    cleanup();
    complete({ok: true, json: async () => data()});
    await new Promise(resolve => setImmediate(resolve));
    assert.match(host.innerHTML, /読み込んでいます/);
    assert.equal(listeners.size, 0);
  } finally { global.fetch = before; }
});

test('mounted monthly table follows stage and checkbox selections and offers its own four-company picker', async () => {
  const {mountActualValuationHistory} = await helpers();
  const before = global.fetch;
  const listeners = new Map(), select = {value: ''}, monthly = {innerHTML: ''};
  let symbols = ['285A.T', 'SNDK'];
  const buttons = data().companies.map(company => ({dataset: {actualSymbol: company.symbol}, setAttribute: () => {}}));
  const doc = {
    querySelectorAll: () => symbols.map(value => ({value})),
    addEventListener: (name, listener) => listeners.set(name, listener),
    removeEventListener: (name, listener) => { if (listeners.get(name) === listener) listeners.delete(name); },
  };
  const host = {
    innerHTML: '', isConnected: true, contains: () => true,
    querySelector: selector => selector === '[data-actual-company]' ? select : monthly,
    querySelectorAll: () => buttons,
  };
  try {
    global.fetch = async () => ({ok: true, json: async () => data()});
    const cleanup = mountActualValuationHistory(host, doc);
    await new Promise(resolve => setImmediate(resolve));
    assert.match(host.innerHTML, /<option value="285A\.T" selected>/);
    const chain = {closest: selector => selector === '[data-chain]' ? chain : null};
    symbols = ['4062.T'];
    listeners.get('click')({target: chain});
    assert.equal(select.value, '4062.T');
    assert.match(monthly.innerHTML, /イビデン/);
    const checkbox = {value: '6146.T', matches: selector => selector === '#fund-choices input'};
    symbols = ['4062.T', '6146.T'];
    listeners.get('change')({target: checkbox});
    assert.equal(select.value, '6146.T');
    assert.match(monthly.innerHTML, /ディスコ/);
    symbols = ['NVDA'];
    listeners.get('click')({target: chain});
    assert.equal(select.value, '6146.T', 'unsupported source selections retain the monthly comparison');
    const ownSelect = {value: '6857.T', matches: selector => selector === '[data-actual-company]'};
    listeners.get('change')({target: ownSelect});
    assert.equal(select.value, '6857.T');
    assert.match(monthly.innerHTML, /アドバンテスト/);
    const button = {dataset: {actualSymbol: '285A.T'}, closest: selector => selector === '[data-actual-symbol]' ? button : null};
    listeners.get('click')({target: button});
    assert.equal(select.value, '285A.T');
    cleanup();
    assert.equal(listeners.size, 0);
  } finally { global.fetch = before; }
});

test('mounted profit-basis control and comparison buttons synchronize, while company changes reset to actuals', async () => {
  const {mountActualValuationHistory} = await helpers();
  const before = global.fetch, fixture = withExStockGain(), listeners = new Map();
  const select = {value: ''}, monthly = {innerHTML: ''};
  const buttons = fixture.companies.flatMap(company => ['reported', ...(company.exStockGain ? ['exStockGain'] : [])].map(basis => ({
    dataset: {actualSymbol: company.symbol, actualProfitBasis: basis},
    setAttribute(name, value) { this[name] = value; },
  })));
  const doc = {
    querySelectorAll: () => [],
    addEventListener: (name, listener) => listeners.set(name, listener),
    removeEventListener: (name, listener) => { if (listeners.get(name) === listener) listeners.delete(name); },
  };
  const host = {
    innerHTML: '', isConnected: true, contains: () => true,
    querySelector: selector => selector === '[data-actual-company]' ? select : monthly,
    querySelectorAll: () => buttons,
  };
  const click = (symbol, basis) => {
    const button = buttons.find(item => item.dataset.actualSymbol === symbol && item.dataset.actualProfitBasis === basis);
    button.closest = selector => selector === '[data-actual-symbol]' ? button : null;
    listeners.get('click')({target: button});
    return button;
  };
  const changeBasis = value => listeners.get('change')({target: {value, matches: selector => selector === '[data-actual-basis]'}});
  try {
    global.fetch = async () => ({ok: true, json: async () => fixture});
    const cleanup = mountActualValuationHistory(host, doc);
    await new Promise(resolve => setImmediate(resolve));
    assert.match(host.innerHTML, /<option value="285A\.T" selected>/);
    const adjustedButton = click('4062.T', 'exStockGain');
    assert.equal(select.value, '4062.T');
    assert.equal(adjustedButton['aria-pressed'], 'true');
    assert.match(monthly.innerHTML, /<option value="exStockGain" selected>/);
    assert.match(monthly.innerHTML, /40\.0倍/);
    changeBasis('reported');
    assert.equal(adjustedButton['aria-pressed'], 'false');
    assert.match(monthly.innerHTML, /<option value="reported" selected>/);
    changeBasis('exStockGain');
    assert.equal(adjustedButton['aria-pressed'], 'true');
    const actualButton = click('4062.T', 'reported');
    assert.equal(actualButton['aria-pressed'], 'true');
    assert.equal(adjustedButton['aria-pressed'], 'false');
    assert.match(monthly.innerHTML, /<option value="reported" selected>/);
    changeBasis('exStockGain');
    const otherSelect = {value: '6146.T', matches: selector => selector === '[data-actual-company]'};
    listeners.get('change')({target: otherSelect});
    assert.equal(select.value, '6146.T');
    assert.doesNotMatch(monthly.innerHTML, /data-actual-basis|株式売却益/);
    otherSelect.value = '4062.T';
    listeners.get('change')({target: otherSelect});
    assert.match(monthly.innerHTML, /<option value="reported" selected>/, 'returning to the company begins with reported actuals');
    cleanup();
    assert.equal(listeners.size, 0);
  } finally { global.fetch = before; }
});

test('saved four-company research renders all 44 monthly rows without losing dates, notes or numeric precision', async () => {
  const {ACTUAL_VALUATION_PATH, validActualValuations, renderActualValuations, renderActualCompany, actualCompanyForSelection} = await helpers();
  const saved = JSON.parse(fs.readFileSync(path.join(__dirname, '..', ACTUAL_VALUATION_PATH), 'utf8'));
  assert.equal(validActualValuations(saved), true);
  assert.deepEqual(saved.companies.map(company => company.code), ['285A', '6857', '4062', '6146']);
  const format = (value, digits) => value.toLocaleString('ja-JP', {minimumFractionDigits: digits, maximumFractionDigits: digits});
  for (const company of saved.companies) {
    assert.equal(company.monthly.length, 11, company.code);
    assert.equal(company.monthly.at(-1).date, saved.asOf, company.code);
    assert.equal(actualCompanyForSelection(saved.companies, [company.symbol]).code, company.code);
    const html = renderActualCompany(company);
    const rows = [...html.matchAll(/<tr\b[^>]*><th scope="row">([^<]+)<\/th>([\s\S]*?)<\/tr>/g)];
    assert.equal(rows.length, 11, `${company.code}: monthly row count`);
    assert.match(html, /class="ai-actual-notes" open/, 'important accounting notes are initially visible');
    assert.ok(html.includes(company.basis), `${company.code}: EPS basis`);
    assert.ok(fs.existsSync(path.join(__dirname, '..', company.reportPath)), `${company.code}: report link exists`);
    company.monthly.forEach((point, index) => {
      assert.equal(rows[index][1], point.date);
      const cells = [...rows[index][2].matchAll(/<td>([^<]*)<\/td>/g)].map(match => match[1]);
      assert.deepEqual(cells, [format(point.closeJPY, 2), format(point.ttmDilutedEPSJPY, 2), `${format(point.trailingPER, 1)}倍`, format(point.halfYearAnnualizedDilutedEPSJPY, 2), `${format(point.halfYearAnnualizedPER, 1)}倍`], `${company.code} ${point.date}: all five numeric columns`);
      assert.ok(point.reportDate <= point.date, `${company.code}: published financial results only`);
    });
    const overview = renderActualValuations(saved, company.symbol);
    assert.match(overview, new RegExp(`<option value="${company.symbol.replace('.', '\\.')}" selected>`));
    assert.doesNotMatch(overview, /NaN|Infinity|undefined/);
  }
});

test('saved stock-gain estimate preserves all reported histories, renders 11 estimated rows and respects the release boundary', async () => {
  const {ACTUAL_VALUATION_PATH, validActualValuations, renderActualValuations, renderActualCompany} = await helpers();
  const read = relative => JSON.parse(fs.readFileSync(path.join(__dirname, '..', relative), 'utf8'));
  const saved = read(ACTUAL_VALUATION_PATH), company = saved.companies.find(item => item.code === '4062');
  const close = (actual, expected, label) => assert.ok(Math.abs(actual - expected) < 1e-9, label);
  assert.equal(validActualValuations(saved), true);
  const metrics = ['closeJPY', 'ttmDilutedEPSJPY', 'trailingPER', 'halfYearAnnualizedDilutedEPSJPY', 'halfYearAnnualizedPER'];
  for (const item of saved.companies) {
    const raw = read(item.sourcePath);
    for (const row of item.monthly) {
      const source = raw.daily.find(point => point.date === row.date);
      assert.ok(source, `${item.code} ${row.date}: original actual exists`);
      for (const key of metrics) close(row[key], source[key], `${item.code} ${row.date}: ${key} preserves original actual`);
    }
    if (item !== company) assert.equal(item.exStockGain, undefined, `${item.code}: no unrelated adjustment`);
  }
  const adjusted = company.exStockGain, source = read(adjusted.sourcePath), raw = read(company.sourcePath);
  assert.equal(adjusted.monthly.length, 11);
  const last = adjusted.monthly.at(-1);
  close(last.ttmDilutedEPSJPY, 57.97112604992493, 'latest estimate TTM EPS');
  close(last.trailingPER, 158.92394417292726, 'latest estimate TTM PER');
  close(last.halfYearAnnualizedDilutedEPSJPY, 51.73225209984985, 'latest estimate half-year annualized EPS');
  close(last.halfYearAnnualizedPER, 178.0900623119545, 'latest estimate half-year annualized PER');
  assert.equal(last.date, '2026-10-15');
  const html = renderActualCompany(company, 'exStockGain');
  const rows = [...html.matchAll(/<tr\b[^>]*><th scope="row">([^<]+)<\/th>([\s\S]*?)<\/tr>/g)];
  assert.equal(rows.length, 11);
  const format = (value, digits) => value.toLocaleString('ja-JP', {minimumFractionDigits: digits, maximumFractionDigits: digits});
  adjusted.monthly.forEach((row, index) => {
    const original = company.monthly[index], estimate = source.monthly.find(point => point.date === row.date);
    assert.equal(rows[index][1], row.date);
    const cells = [...rows[index][2].matchAll(/<td>([^<]*)<\/td>/g)].map(match => match[1]);
    assert.deepEqual(cells, [format(row.closeJPY, 2), format(row.ttmDilutedEPSJPY, 2), `${format(row.trailingPER, 1)}倍`, format(row.halfYearAnnualizedDilutedEPSJPY, 2), `${format(row.halfYearAnnualizedPER, 1)}倍`]);
    for (const key of metrics) close(row[key], estimate[key], `${row.date}: saved estimate source matches ${key}`);
    assert.equal(row.closeJPY, original.closeJPY, 'adjustment preserves the same stock price');
    assert.ok(row.reportDate < row.date, 'no same-day after-close results used');
    if (row.date < '2026-05-12') {
      for (const key of metrics) close(row[key], original[key], `${row.date}: unavailable annual result is not anticipated`);
      assert.equal(row.adjustmentApplied, false);
    } else {
      close(original.ttmDilutedEPSJPY - row.ttmDilutedEPSJPY, source.annualEPSAdjustmentJPY, `${row.date}: annual gain removed once from TTM`);
      close(original.halfYearAnnualizedDilutedEPSJPY - row.halfYearAnnualizedDilutedEPSJPY, source.annualEPSAdjustmentJPY * 2, `${row.date}: six-month gain removed before annualizing`);
    }
  });
  const before = source.daily.find(row => row.date === '2026-05-11');
  const after = source.daily.find(row => row.date === '2026-05-12');
  const rawBefore = raw.daily.find(row => row.date === before.date), rawAfter = raw.daily.find(row => row.date === after.date);
  assert.equal(before.adjustmentApplied, false);
  assert.equal(before.reportDate, '2026-02-03', '5/11 trading close predates the annual release');
  assert.equal(after.adjustmentApplied, true);
  assert.equal(after.reportDate, '2026-05-11', '5/12 is the first trading day that can use the annual release');
  close(before.ttmDilutedEPSJPY, rawBefore.ttmDilutedEPSJPY, 'release-day close stays unadjusted');
  close(rawAfter.ttmDilutedEPSJPY - after.ttmDilutedEPSJPY, source.annualEPSAdjustmentJPY, 'next trading day uses the adjusted annual result');
  assert.ok(html.includes('href="/' + adjusted.reportPath + '"'), 'estimate view links its dedicated method report');
  assert.ok(fs.existsSync(path.join(__dirname, '..', adjusted.reportPath)));
  const overview = renderActualValuations(saved);
  assert.match(overview, /<td>158\.9倍<\/td><td>178\.1倍<\/td>/, 'estimate is visible even when another company is selected');
  assert.match(overview, /<td>79\.2倍<\/td><td>54\.7倍<\/td>/, 'reported Ibiden comparison remains available');
});
