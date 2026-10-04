const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const ROOT = path.join(__dirname, '..');
const web = name => pathToFileURL(path.join(ROOT, 'web', name)).href;
const FIXTURES = path.join(__dirname, 'fixtures', 'assets');
const readJson = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const catalog = readJson(path.join(ROOT, 'research', 'catalog.json'));

// The same document backend.assets build_state produces: accounts list, snapshots by date ascending.
function buildState() {
  const accounts = readJson(path.join(FIXTURES, 'accounts.json')).accounts;
  const snapshots = fs.readdirSync(path.join(FIXTURES, 'snapshots')).filter(name => name.endsWith('.json')).sort()
    .map(name => readJson(path.join(FIXTURES, 'snapshots', name)))
    .map(({date, recordedAt, positions, notes}) => ({date, recordedAt, positions, notes}));
  return {version: 1, builtAt: '2026-10-04T02:00:00+00:00', accounts, snapshots, latestDate: snapshots.at(-1).date};
}
const state = buildState();
const payload = {state, status: {status: 'ok', pushedAt: null}};
const sumValues = snapshot => snapshot.positions.reduce((sum, p) => sum + p.valueJpy, 0);

test('class labels cover every class in the fixtures and match the backend', async () => {
  const {CLASS_ORDER, CLASS_LABELS} = await import(web('asset-model.js'));
  const backend = fs.readFileSync(path.join(ROOT, 'backend', 'assets.py'), 'utf8');
  const block = backend.match(/CLASS_LABELS = \{([\s\S]*?)\}/)[1];
  const expected = Object.fromEntries([...block.matchAll(/'([a-z]+)': '([^']+)'/g)].map(m => [m[1], m[2]]));
  assert.deepEqual(CLASS_LABELS, expected);
  assert.deepEqual([...CLASS_ORDER].sort(), Object.keys(expected).sort());
  const classes = new Set(state.snapshots.flatMap(s => s.positions.map(p => p.class)));
  for (const cls of classes) assert.ok(CLASS_LABELS[cls], cls);
});

test('series by class and account total to the snapshot, and a sold position ends with null', async () => {
  const {seriesByDate, totals, datesOf, limitDates, positionKey} = await import(web('asset-model.js'));
  const dates = datesOf(state);
  assert.deepEqual(dates, ['2026-09-20', '2026-09-27', '2026-10-04']);
  const byClass = seriesByDate(state, 'class');
  assert.deepEqual(byClass.dates, dates);
  assert.deepEqual(byClass.keys, ['stock', 'fund', 'crypto', 'cash', 'private']);
  dates.forEach((date, i) => {
    const classTotal = byClass.keys.reduce((sum, key) => sum + byClass.values[key][i], 0);
    assert.equal(classTotal, sumValues(state.snapshots[i]));
  });
  assert.deepEqual(totals(state).map(t => t.total), state.snapshots.map(sumValues));
  const byAccount = seriesByDate(state, 'account');
  assert.equal(byAccount.keys[0], 'mizuho');
  assert.deepEqual(byAccount.values.mizuho, [1200000, 1180000, 1234567]);
  const positions = seriesByDate(state, 'position');
  assert.deepEqual(positions.values['sbi-nisa/stock/523A'], [180000, 176000, null]);
  assert.deepEqual(positions.values['sbi-tokutei/stock/4062'], [null, null, 800000]);
  const stockOnly = seriesByDate(state, 'account', {cls: 'stock', dates: dates.slice(-2)});
  assert.deepEqual(stockOnly.keys, ['sbi-tokutei', 'sbi-nisa', 'daiwa']);
  assert.deepEqual(stockOnly.values['sbi-nisa'], [176000, 0]);
  assert.equal(positionKey({account: 'a', class: 'stock', symbol: 'X'}), 'a/stock/X');
  assert.deepEqual(limitDates(dates, '26'), dates);
  assert.deepEqual(limitDates(dates, '2'), dates.slice(-2));
  assert.deepEqual(limitDates(dates, 'all'), dates);
  assert.deepEqual(seriesByDate(null, 'class'), {dates: [], keys: [], values: {}});
});

test('portfolio summary compares the two newest snapshots and shares sum to one', async () => {
  const {portfolioSummary} = await import(web('asset-model.js'));
  const summary = portfolioSummary(state);
  const [, previous, latest] = state.snapshots;
  assert.equal(summary.latestDate, '2026-10-04');
  assert.equal(summary.previousDate, '2026-09-27');
  assert.equal(summary.total, sumValues(latest));
  assert.equal(summary.delta, sumValues(latest) - sumValues(previous));
  assert.ok(Math.abs(summary.deltaPct - summary.delta / sumValues(previous)) < 1e-12);
  assert.equal(summary.weeks, 3);
  assert.equal(summary.recordedAt, '2026-10-04T10:05:00+09:00');
  const shareSum = rows => rows.reduce((sum, row) => sum + row.share, 0);
  assert.ok(Math.abs(shareSum(summary.byClass) - 1) < 1e-9);
  assert.ok(Math.abs(shareSum(summary.byAccount) - 1) < 1e-9);
  assert.equal(summary.byClass.find(row => row.cls === 'private').delta, 0);
  assert.equal(summary.byAccount.find(row => row.id === 'sbi-nisa').label, 'SBI証券 NISA');
  assert.equal(portfolioSummary(null), null);
  const single = portfolioSummary({...state, snapshots: state.snapshots.slice(0, 1)});
  assert.equal(single.previousDate, null);
  assert.equal(single.delta, null);
});

test('movers flag new and sold positions and count the missing side as zero', async () => {
  const {movers} = await import(web('asset-model.js'));
  const {up, down} = movers(state);
  const appeared = up.find(row => row.symbol === '4062');
  assert.ok(appeared?.appeared);
  assert.equal(appeared.previous, 0);
  assert.equal(appeared.delta, 800000);
  assert.equal(up[0].symbol, '4062');
  const sold = down.find(row => row.symbol === '523A');
  assert.ok(sold?.disappeared);
  assert.equal(sold.value, 0);
  assert.equal(sold.delta, -176000);
  assert.equal(sold.accountLabel, 'SBI証券 NISA');
  assert.ok(up.length <= 5 && down.length <= 5);
  assert.ok(down.every(row => row.delta < 0));
  assert.deepEqual(movers({...state, snapshots: state.snapshots.slice(-1)}), {up: [], down: []});
});

test('holdings sort by value, keep history, and show pnl only with a cost', async () => {
  const {holdings} = await import(web('asset-model.js'));
  const stock = holdings(state, 'stock');
  assert.deepEqual(stock.map(row => row.symbol), ['6857', '4062', '285A', 'AAPL', '7203']);
  assert.ok(stock.every((row, i) => i === 0 || stock[i - 1].value >= row.value));
  const toyota = stock.find(row => row.symbol === '7203');
  assert.equal(toyota.costJpy, null);
  assert.equal(toyota.pnl, null);
  assert.equal(toyota.delta, 4000);
  const kioxia = stock.find(row => row.symbol === '285A');
  assert.equal(kioxia.pnl, 250000);
  assert.deepEqual(kioxia.history, [600000, 630000, 650000]);
  assert.deepEqual(stock.find(row => row.symbol === '4062').history, [null, null, 800000]);
  assert.ok(Math.abs(stock.reduce((sum, row) => sum + row.share, 0) - 1) < 1e-9);
  const apple = stock.find(row => row.symbol === 'AAPL');
  assert.equal(apple.market, 'US');
  assert.equal(apple.currency, 'USD');
  assert.ok(holdings(state, 'private')[0].carryForward);
  assert.deepEqual(holdings(state, 'bond'), []);
});

test('research lookup matches code or slug prefix within the same asset class', async () => {
  const {researchEntryFor} = await import(web('asset-model.js'));
  const kioxia = researchEntryFor({class: 'stock', symbol: '285A'}, catalog);
  assert.equal(kioxia.slug, '285A-kioxia');
  assert.equal(kioxia.date, '2026-10-03', 'newest version wins');
  assert.equal(researchEntryFor({class: 'stock', symbol: '7203'}, catalog), null);
  assert.equal(researchEntryFor({class: 'crypto', symbol: '285A'}, catalog), null, 'class must match');
  const withCrypto = {...catalog, groups: [...catalog.groups.filter(g => g.id !== 'crypto'), {id: 'crypto', label: '仮想通貨', kind: 'crypto', assetClass: 'crypto', entries: [{id: 'BTC-bitcoin-2026-10-04', slug: 'BTC-bitcoin', kind: 'crypto', date: '2026-10-04', title: 'ビットコイン', items: [{label: 'x', type: 'md', path: 'research/crypto/BTC-bitcoin/2026-10-04/report.md'}]}]}]};
  assert.equal(researchEntryFor({class: 'crypto', symbol: 'BTC'}, withCrypto).slug, 'BTC-bitcoin');
  assert.equal(researchEntryFor({class: 'stock', symbol: '285A'}, null), null);
  assert.equal(researchEntryFor({cls: 'stock', symbol: '6857'}, catalog).slug, '6857-advantest', 'holdings rows use cls');
});

test('week rows carry a short label, the full date and the year group; formatting helpers', async () => {
  const {weekRows, yen, man, signedYen, signedMan, percent, deltaClass} = await import(web('asset-model.js'));
  const rows = weekRows(['2025-12-27', '2026-01-03', '2026-01-10']);
  assert.deepEqual(rows[0], {label: '12/27', name: '2025年12月27日', group: '2025年'});
  assert.deepEqual(rows.map(r => r.group), ['2025年', '2026年', '2026年']);
  assert.equal(yen(1234567), '￥1,234,567');
  assert.equal(yen(null), '—');
  assert.equal(man(1234567), '123.5万円');
  assert.equal(man(0), '0万円');
  assert.equal(signedYen(-500), '−￥500');
  assert.equal(signedMan(20000), '+2万円');
  assert.equal(percent(0.1234), '12.3%');
  assert.equal(deltaClass(5), 'delta-up');
  assert.equal(deltaClass(-5), 'delta-down');
  assert.equal(deltaClass(0), 'delta-flat');
  assert.equal(deltaClass(null), 'delta-flat');
});

test('assets view renders tiles, checkbox-driven charts, movers and per-class sections', async () => {
  const {assetsView, EMPTY_TEXT} = await import(web('asset-view.js'));
  const html = assetsView(payload, catalog, {range: '52', mode: 'stack'});
  assert.doesNotMatch(html, /style=/);
  assert.doesNotMatch(html, /NaN|undefined|Infinity/);
  for (const text of ['総資産', '前週比', '記録週数', '最終記録日', '資産全体の推移', '今週の増減', '資産ごとの内訳']) assert.match(html, new RegExp(text));
  assert.match(html, /id="asset-range"/);
  assert.match(html, /name="asset-mode" value="stack" checked/);
  for (const cls of ['stock', 'fund', 'crypto', 'cash', 'private']) assert.match(html, new RegExp(`data-toggle="c:${cls}" checked`));
  assert.match(html, /data-toggle="p:sbi-tokutei\/stock\/6857" checked/);
  for (const cls of ['stock', 'fund', 'crypto', 'cash', 'private']) assert.match(html, new RegExp(`id="asset-class-${cls}"`));
  assert.doesNotMatch(html, /id="asset-class-bond"/);
  assert.equal((html.match(/class="ui-chart"/g) || []).length, 6, 'overall chart plus one per class');
  assert.match(html, /、合計 /, 'stacked charts describe a total');
  assert.match(html, /href="#r\/4062-ibiden-2026-10-03\/0"/, 'movers and holdings link to research');
  assert.match(html, /href="#r\/285A-kioxia-2026-10-03\/0"/);
  assert.doesNotMatch(html, /href="#r\/[^"]*7203/);
  assert.match(html, /<span class="asset-tag">米国<\/span>/);
  assert.match(html, /新規/);
  assert.match(html, /売却・解約/);
  assert.match(html, /各サイト表示の円換算評価額を週次で手入力した記録/);
  assert.doesNotMatch(html, /data-slot/);

  const empty = assetsView({state: null, status: {status: 'not_configured', pushedAt: null}}, catalog, {});
  assert.match(empty, new RegExp(EMPTY_TEXT.replace(/[/]/g, '\\/')));
  assert.match(empty, /weekly-assets/);
  assert.doesNotMatch(empty, /ui-chart/);
  assert.match(assetsView(null, null, {loading: true}), /読み込んでいます/);
  assert.match(assetsView(null, null, {error: 'x<y'}), /x&lt;y/);
});

test('unchecked classes and positions leave the charts and line mode adds a selection total', async () => {
  const {assetsView} = await import(web('asset-view.js'));
  const html = assetsView(payload, catalog, {mode: 'stack', hiddenClasses: new Set(['cash', 'private']), hiddenPositions: new Set(['sbi-tokutei/stock/6857'])});
  assert.match(html, /data-toggle="c:cash"(?! checked)/);
  assert.match(html, /data-toggle="p:sbi-tokutei\/stock\/6857"(?! checked)/);
  assert.match(html, /data-toggle="c:stock" checked/);
  assert.match(html, /id="asset-class-cash"/);
  const line = assetsView(payload, catalog, {mode: 'line'});
  assert.match(line, /選択の合計/);
  assert.match(line, /name="asset-mode" value="line" checked/);
  assert.doesNotMatch(assetsView(payload, catalog, {mode: 'stack'}), /選択の合計/);
  const none = assetsView(payload, catalog, {hiddenClasses: new Set(['stock', 'fund', 'crypto', 'cash', 'private'])});
  assert.match(none, /表示する項目にチェックを入れてください/);
});

test('assets view escapes names and account labels', async () => {
  const {assetsView} = await import(web('asset-view.js'));
  const evil = JSON.parse(JSON.stringify(state));
  evil.snapshots.at(-1).positions.push({account: 'daiwa', class: 'stock', symbol: '9999', name: '<img src=x>', valueJpy: 5000000});
  evil.accounts.find(a => a.id === 'daiwa').label = '<b>大和</b>';
  const html = assetsView({state: evil, status: {status: 'ok'}}, catalog, {});
  assert.doesNotMatch(html, /<img src=x>|<b>大和<\/b>/);
  assert.match(html, /&lt;img src=x&gt;/);
});

test('assets.js accepts the API shape and rejects malformed payloads', async () => {
  global.document = {getElementById: () => null, addEventListener() {}, hidden: false};
  const {validPayload} = await import(web('assets.js'));
  assert.equal(validPayload(payload), true);
  assert.equal(validPayload({state: null, status: {status: 'not_configured', pushedAt: null}}), true);
  assert.equal(validPayload({state: {}, status: {status: 'ok'}}), false);
  assert.equal(validPayload({state, status: null}), false);
  assert.equal(validPayload({state}), false);
  assert.equal(validPayload(null), false);
  assert.equal(validPayload('x'), false);
});
