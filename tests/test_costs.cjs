const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const web = name => pathToFileURL(path.join(__dirname, '..', 'web', name)).href;
const month = new Intl.DateTimeFormat('sv-SE', {timeZone: 'Asia/Tokyo', year: 'numeric', month: '2-digit'}).format(new Date());
const record = (date, serviceId, service, gross, credits, net) => ({date, serviceId, service, currency: 'JPY', gross, credits, net, exportedAt: '2026-09-30T00:00:00Z'});
const payload = (records, extra = {}) => ({
  project: 'asset-hub-prod',
  budget: {currency: 'JPY', projectBudget: 1000},
  snapshot: {version: 1, projectId: 'asset-hub-prod', fetchedAt: new Date().toISOString(), window: {start: '2026-08-01', end: '2026-10-03'}, currency: 'JPY', records, latestExportAt: null, latestUsageDate: null},
  syncStatus: {status: 'ok'},
  ...extra,
});

test('months run newest first across the snapshot window', async () => {
  const {costMonths} = await import(web('cost-model.js'));
  assert.deepEqual(costMonths({window: {start: '2026-08-01', end: '2026-10-03'}}), ['2026-10', '2026-09', '2026-08']);
  assert.deepEqual(costMonths(null), []);
});

test('summaries aggregate by service and day without floating point drift', async () => {
  const {summarizeCosts} = await import(web('cost-model.js'));
  const snapshot = payload([
    record('2026-09-01', 'run', 'Cloud Run', 0.1, 0, 0.1),
    record('2026-09-01', 'run', 'Cloud Run', 0.2, 0, 0.2),
    record('2026-09-02', 'gcs', 'Cloud Storage', 5, -1, 4),
    record('2026-08-31', 'run', 'Cloud Run', 99, 0, 99),
  ]).snapshot;
  const summary = summarizeCosts(snapshot, '2026-09');
  assert.equal(summary.hasData, true);
  assert.equal(summary.net, 4.3);
  assert.equal(summary.gross, 5.3);
  assert.equal(summary.credits, -1);
  assert.deepEqual(summary.services.map(s => [s.name, s.net]), [['Cloud Storage', 4], ['Cloud Run', 0.3]]);
  assert.deepEqual(summary.days, [{date: '2026-09-01', net: 0.3}, {date: '2026-09-02', net: 4}]);
  assert.deepEqual(summarizeCosts(snapshot, '2026-07'), {hasData: false, gross: null, credits: null, net: null, services: [], days: []});
});

test('money keeps two decimals and shows a dash for missing values', async () => {
  const {money} = await import(web('cost-model.js'));
  assert.equal(money(null), '—');
  assert.match(money(1234.5), /1,234\.50/);
});

test('budget states: unknown, normal, warning at 80%, danger at 100%', async () => {
  const {costBudgetAlert} = await import(web('cost-model.js'));
  const at = net => costBudgetAlert(payload([record(month + '-01', 'run', 'Cloud Run', net, 0, net)]));
  assert.equal(at(100).level, 'normal');
  assert.equal(at(800).level, 'warning');
  assert.equal(at(1000).level, 'danger');
  assert.equal(costBudgetAlert(payload([], {budget: {currency: 'JPY', projectBudget: null}})).level, 'unknown');
  assert.equal(costBudgetAlert(null).level, 'unknown');
});

test('cost view uses the payload project and escapes service names', async () => {
  const {costView, billingUrl} = await import(web('cost-view.js'));
  const html = costView(payload([record(month + '-01', 'x', '<b>Evil</b>', 900, 0, 900)]), {month});
  assert.match(html, /このシステムの維持費 · Asset Hub/);
  assert.match(html, /project=asset-hub-prod/);
  assert.doesNotMatch(html, /pathosion/i);
  assert.match(html, /&lt;b&gt;Evil&lt;\/b&gt;/);
  assert.match(html, /cost-budget-warning/);
  assert.doesNotMatch(html, /style=/);
  assert.equal(billingUrl(null), 'https://console.cloud.google.com/billing');
  assert.equal(billingUrl('a b'), 'https://console.cloud.google.com/billing/linkedaccount?project=a%20b');
  const pending = costView({project: null, budget: {currency: 'JPY', projectBudget: null}, snapshot: null, syncStatus: {status: 'not_configured'}});
  assert.match(pending, /連携を設定中/);
  assert.match(pending, /予算への接近状況は未確認です/);
});

test('costs.js accepts any project id but rejects malformed payloads', async () => {
  global.document = {getElementById: () => null, addEventListener() {}, hidden: false};
  const {validPayload} = await import(web('costs.js'));
  assert.equal(validPayload(payload([])), true);
  assert.equal(validPayload({...payload([]), project: 'another-project'}), true);
  assert.equal(validPayload({...payload([]), project: null}), true);
  assert.equal(validPayload({...payload([]), syncStatus: undefined}), false);
  assert.equal(validPayload({...payload([]), project: 42}), false);
  assert.equal(validPayload(null), false);
});
