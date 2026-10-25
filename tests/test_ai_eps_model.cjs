const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const ROOT = path.join(__dirname, '..');
const helpers = () => import(pathToFileURL(path.join(ROOT, 'web/ai-eps-model.js')).href);
const row = (periodEnd, knownFrom, eps) => ({periodEnd, knownFrom, eps});
const at = (result, date) => result.points.find(point => point.date === date);
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} ≈ ${expected}`);

test('EPS events use the public date inclusively and never backfill later releases', async () => {
  const {buildEpsSeries} = await helpers();
  const company = {ttmSeries: [
    row('2025-09-30', '2025-11-01', 10),
    row('2025-12-31', '2026-02-05', 20),
    row('2026-03-31', '2026-05-10', 30),
  ]};
  const result = buildEpsSeries(company, {start: '2026-02-04', end: '2026-02-06'});
  assert.deepEqual(result.points.map(point => [point.date, point.eps]), [
    ['2026-02-04', 10], ['2026-02-05', 20], ['2026-02-06', 20],
  ]);
  assert.deepEqual(at(result, '2026-02-05'), {
    date: '2026-02-05', x: Date.UTC(2026, 1, 5), eps: 20,
    periodEnd: '2025-12-31', knownFrom: '2026-02-05',
  });
  assert.equal(result.startEPS, 10);
  assert.equal(result.endEPS, 20);
  assert.equal(result.baseEPS, 10);
  assert.equal(result.changePercent, 100);
  assert.deepEqual(result.indexPoints.map(point => point.eps), [100, 200, 200]);
  assert.ok(!result.points.some(point => point.date === '2026-05-10'));
});

test('the newest period wins even when an older period is released later, without mutating input', async () => {
  const {buildEpsSeries} = await helpers();
  const company = {ttmSeries: [
    row('2025-12-31', '2026-02-01', 30),
    row('2025-09-30', '2026-02-04', 99),
    row('2025-12-31', '2026-02-05', 35),
  ]};
  const before = structuredClone(company);
  Object.freeze(company.ttmSeries);
  for (const point of company.ttmSeries) Object.freeze(point);
  Object.freeze(company);
  const result = buildEpsSeries(company, {start: '2026-02-01', end: '2026-02-06'});
  assert.deepEqual(result.points.map(point => point.eps), [30, 30, 35, 35]);
  assert.deepEqual(company, before);
});

test('zero and negative EPS remain plotted, including negative indexed values', async () => {
  const {buildEpsSeries} = await helpers();
  const company = {ttmSeries: [
    row('2025-06-30', '2025-08-01', 10),
    row('2025-09-30', '2025-11-01', 0),
    row('2025-12-31', '2026-02-01', -5),
  ]};
  const result = buildEpsSeries(company, {start: '2025-10-01', end: '2026-02-02'});
  assert.deepEqual(result.points.map(point => point.eps), [10, 0, -5, -5]);
  assert.deepEqual(result.indexPoints.map(point => point.eps), [100, 0, -50, -50]);
  assert.equal(result.changePercent, -150);
  for (const start of ['2025-11-01', '2026-02-01']) {
    const unindexed = buildEpsSeries(company, {start, end: '2026-02-02'});
    assert.equal(unindexed.baseEPS, null);
    assert.equal(unindexed.indexPoints, null);
    assert.equal(unindexed.changePercent, null);
  }
});

test('missing start EPS does not acquire a later index base', async () => {
  const {buildEpsSeries} = await helpers();
  const result = buildEpsSeries({ttmSeries: [row('2025-12-31', '2026-02-05', 20)]}, {
    start: '2026-02-04', end: '2026-02-06',
  });
  assert.deepEqual(result.points[0], {date: '2026-02-04', x: Date.UTC(2026, 1, 4), eps: null, periodEnd: null, knownFrom: null});
  assert.equal(result.endEPS, 20);
  assert.equal(result.baseEPS, null);
  assert.equal(result.indexPoints, null);
  assert.equal(result.changePercent, null);
});

test('EPS expires the day after the maximum age and never falls back to an older period', async () => {
  const {buildEpsSeries} = await helpers();
  const company = {ttmSeries: [row('2025-12-30', '2025-12-30', 5), row('2025-12-31', '2025-12-31', 10)]};
  const result = buildEpsSeries(company, {start: '2026-01-09', end: '2026-01-12', maxAgeDays: 10});
  assert.equal(at(result, '2026-01-10').eps, 10, 'age exactly 10 days remains usable');
  assert.equal(at(result, '2026-01-11').eps, null, 'age 11 days is stale');
  assert.equal(result.endEPS, null);
  assert.equal(result.changePercent, null);
  assert.deepEqual(result.indexPoints.map(point => point.eps), [100, 100, null, null]);
  assert.equal(at(result, '2026-01-11').periodEnd, '2025-12-31');
});

test('UTC leap-day arithmetic, a one-day range, and the default 550-day age are stable', async () => {
  const {buildEpsSeries} = await helpers();
  const leap = buildEpsSeries({ttmSeries: [row('2024-02-28', '2024-02-28', 3)]}, {
    start: '2024-02-29', end: '2024-03-01', maxAgeDays: 1,
  });
  assert.deepEqual(leap.points.map(point => [point.x, point.eps]), [[Date.UTC(2024, 1, 29), 3], [Date.UTC(2024, 2, 1), null]]);
  const single = buildEpsSeries({ttmSeries: [row('2025-01-01', '2025-01-01', 2)]}, {start: '2025-01-01', end: '2025-01-01'});
  assert.equal(single.points.length, 1);
  assert.equal(single.changePercent, 0);
  const period = Date.UTC(2025, 0, 1), iso = days => new Date(period + days * 86400000).toISOString().slice(0, 10);
  const expires = buildEpsSeries({ttmSeries: [row('2025-01-01', '2025-01-01', 2)]}, {start: iso(550), end: iso(551)});
  assert.deepEqual(expires.points.map(point => point.eps), [2, null]);
});

test('empty, invalid-date, and nonfinite EPS data fail safely', async () => {
  const {buildEpsSeries} = await helpers();
  for (const company of [null, {}, {ttmSeries: []}, {ttmSeries: [row('2026-02-30', '2026-03-01', 5)]}]) {
    const result = buildEpsSeries(company, {start: '2026-03-01', end: '2026-03-02'});
    assert.deepEqual(result.points.map(point => point.eps), [null, null]);
    assert.equal(result.baseEPS, null);
  }
  for (const options of [{}, {start: '2026-02-30', end: '2026-03-02'}, {start: '2026-03-02', end: '2026-03-01'}]) {
    assert.deepEqual(buildEpsSeries({}, options), {points: [], startEPS: null, endEPS: null, baseEPS: null, indexPoints: null, changePercent: null});
  }
  for (const eps of [null, NaN, Infinity, '20']) {
    const result = buildEpsSeries({ttmSeries: [row('2025-12-31', '2026-02-01', eps)]}, {start: '2026-02-01', end: '2026-02-02'});
    assert.equal(result.endEPS, null);
  }
});

test('saved split-adjusted EPS stays in native EPS currency with documented release boundaries', async () => {
  const {buildEpsSeries} = await helpers();
  const saved = JSON.parse(fs.readFileSync(path.join(ROOT, 'research/themes/ai-supply-chain/2026-10-18/valuation.json'), 'utf8'));
  const companies = saved.companies;
  const expected = {'285A.T': 833.49666667, '7011.T': 118.6, GEV: 34.94, 'ENR.DE': 3.11, ASML: 25.41};
  for (const [symbol, eps] of Object.entries(expected)) {
    const company = companies.find(item => item.symbol === symbol), before = structuredClone(company);
    const result = buildEpsSeries(company, {start: '2026-01-01', end: '2026-10-16', maxAgeDays: saved.method.maxAgeDays});
    near(result.endEPS, eps);
    assert.deepEqual(company, before);
    for (const point of result.points.filter(point => point.eps != null)) {
      assert.ok(point.knownFrom <= point.date, `${symbol} never uses an unpublished result`);
      assert.ok((point.x - Date.parse(point.periodEnd + 'T00:00:00Z')) / 86400000 <= saved.method.maxAgeDays);
    }
  }
  const asml = companies.find(company => company.symbol === 'ASML');
  assert.equal(asml.epsCurrency, 'EUR');
  assert.equal(asml.priceCurrency, 'USD');
  assert.equal(buildEpsSeries(asml, {start: '2026-10-01', end: '2026-10-16', maxAgeDays: saved.method.maxAgeDays}).endEPS, 25.41, 'no price-currency FX conversion');
  const enr = companies.find(company => company.symbol === 'ENR.DE');
  const boundary = buildEpsSeries(enr, {start: '2025-11-13', end: '2025-11-14', maxAgeDays: saved.method.maxAgeDays});
  assert.equal(boundary.startEPS, 1.08);
  assert.equal(boundary.endEPS, 1.61);
});
