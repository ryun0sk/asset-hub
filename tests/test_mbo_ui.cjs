const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const ROOT = path.join(__dirname, '..');
const ui = () => import(pathToFileURL(path.join(ROOT, 'web/mbo-app.js')).href);
const clone = value => structuredClone(value);
const company = (id, extra = {}) => ({security_id: id, code: id, name: `架空企業${id}`, exchange: 'TSE', status: 'pending', priority: 50, is_new: false, reasons: ['所有関係を原本で確認する'], missing: ['借入条件を確認'], price: null, facts: [], evidence: [], review_notes: [], valuation: {standalone: {status: 'pending', scenarios: []}, discount_to_base: {value: null, status: 'pending', reasons: ['株価未入力']}, lbo: {status: 'pending', reasons: ['借入条件未確認']}}, ...extra});
const assessment = (state = 'awaiting', extra = {}) => ({version: 'mbo-evidence-1', validation_status: 'hypothesis_not_calibrated', workflow: {state, reason: '公開資料を追加確認する'}, axes: [{id: 'ownership', label: '所有構造', state: 'supported', note: '経営陣の直接保有を確認', evidence: []}, {id: 'motive', label: 'MBOの動機', state: 'unknown', evidence: []}, {id: 'execution', label: '実行可能性', state: 'unknown', evidence: []}, {id: 'obstacles', label: '障害・反証', state: 'unknown', evidence: []}], information: {verified_count: 1, hypothesis_count: 0, unresolved_count: 3, coverage_label: '動機等の確認待ち'}, financial_context: ['営業CFは正だが、MBOの意思を示さない'], cautions: ['事例比較による校正は未実施'], ...extra});
const run = (id, extra = {}) => ({run_id: id, as_of: '2026-10-18', created_at: '2026-10-18T09:00:00+09:00', demo: false, status: 'success', coverage: {universe: 3, prices: 1, valued: 1, pending: 2, events: 0}, rule_version: 'rules-1', ...extra});
const meta = id => ({schema_version: 1, run_id: id, as_of: '2026-10-18', demo: false});
const response = value => ({ok: true, status: 200, json: async () => clone(value)});

function apiFixture({runs = [run('run-1')], status = {}, candidates = {}, events = {}, detail = {}} = {}) {
  const calls = [];
  const fetcher = async (href, options) => {
    calls.push({href, options});
    const url = new URL(href, 'http://127.0.0.1:4331');
    const id = url.searchParams.get('run_id') || runs[0]?.run_id;
    if (url.pathname === '/api/mbo/status') return response({schema_version: 1, mode: 'mbo-local', offline: true, storage_state: runs.length ? 'ready' : 'empty', latest_success_run_id: runs[0]?.run_id || null, last_attempt: null, ...status});
    if (url.pathname === '/api/mbo/runs') return response({items: runs, total: runs.length});
    if (url.pathname === '/api/mbo/candidates') return response({...meta(id), items: [company('285A')], total: 1, limit: 200, offset: 0, coverage: runs.find(item => item.run_id === id)?.coverage, diff: {previous_run_id: null, summary: '初回です'}, ...candidates});
    if (url.pathname === '/api/mbo/events') return response({...meta(id), items: [], total: 0, ...events});
    if (url.pathname.startsWith('/api/mbo/companies/')) return response({...meta(id), company: company('285A'), ...detail});
    throw Error(`unexpected request: ${href}`);
  };
  return {fetcher, calls};
}

function fakeDocument(hash = '') {
  const html = fs.readFileSync(path.join(ROOT, 'web/mbo.html'), 'utf8');
  class Element {
    constructor(id) { this.id = id; this.innerHTML = ''; this.textContent = ''; this.hidden = false; this.disabled = false; this.value = ''; this.listeners = {}; this.attributes = {}; }
    addEventListener(name, listener) { this.listeners[name] = listener; }
    removeEventListener(name, listener) { if (this.listeners[name] === listener) delete this.listeners[name]; }
    setAttribute(name, value) { this.attributes[name] = value; }
    removeAttribute(name) { delete this.attributes[name]; }
    replaceChildren() { this.innerHTML = ''; this.textContent = ''; }
    insertAdjacentHTML(_position, value) { this.innerHTML += value; }
    focus() { this.focused = true; }
  }
  const elements = new Map([...html.matchAll(/id="([^"]+)"/g)].map(match => [match[1], new Element(match[1])]));
  elements.get('mboFilter').value = 'all';
  elements.get('mboSort').value = 'rank';
  const links = ['candidates', 'events', 'history', 'cases'].map(view => Object.assign(new Element(view), {dataset: {mboNav: view}}));
  return {
    elements, links, listeners: {},
    getElementById(id) { return elements.get(id); },
    querySelectorAll(selector) { assert.equal(selector, '[data-mbo-nav]'); return links; },
    addEventListener(name, listener) { this.listeners[name] = listener; },
    defaultView: {location: {hash}, addEventListener() {}},
  };
}

test('MBO entry loads only local module/assets and keeps fixed safety notes visible', () => {
  const html = fs.readFileSync(path.join(ROOT, 'web/mbo.html'), 'utf8');
  assert.match(html, /<script type="module" src="\/mbo-app\.js"><\/script>/);
  assert.match(html, /MBO確率や有力度ではありません/);
  assert.match(html, /保存済みの時点を表示/);
  assert.match(html, /評価軸は設計仮説・未検証/);
  assert.match(html, /架空デモの表示です/);
  assert.match(html, /id="mboSearch"/);
  assert.doesNotMatch(html, /https?:\/\/|<script(?![^>]*src=)|\son\w+=|\sstyle=|<form/i);
  const js = fs.readFileSync(path.join(ROOT, 'web/mbo-app.js'), 'utf8');
  assert.doesNotMatch(js, /(?:\/api\/(?:assets|costs|catalog)|setInterval\(|localStorage|sessionStorage|navigator\.sendBeacon|WebSocket|\.innerHTML\s*=\s*(?:payload|company|source)\b)/);
});

test('embedded panel accepts the authenticated dashboard API and cleans up its own requests and handlers', async () => {
  const {initMboApp} = await ui();
  const doc = fakeDocument('#ai/eps');
  const events = new Map();
  const host = {
    querySelector: selector => doc.getElementById(selector.slice(1)),
    querySelectorAll: () => [],
    setAttribute() {},
    addEventListener: (name, handler) => events.set(name, handler),
    removeEventListener: (name, handler) => { if (events.get(name) === handler) events.delete(name); },
  };
  const fixture = apiFixture({status: {mode: 'mbo-dashboard', offline: false}});
  const app = initMboApp(doc, fixture.fetcher, {root: host, listenHash: false, initialView: 'history'});
  await app.ready;
  assert.equal(app.getView(), 'history');
  assert.equal(doc.getElementById('mboHistorySection').hidden, false);
  app.setView('events');
  assert.equal(doc.getElementById('mboEventsSection').hidden, false);
  assert.equal(doc.defaultView.location.hash, '#ai/eps', 'child never rewrites the Asset Hub route');
  app.destroy();
  assert.equal(events.size, 0);
  assert.deepEqual(doc.getElementById('mboReload').listeners, {});
  assert.equal(fixture.calls[0].options.signal.aborted, true);
  const calls = fixture.calls.length;
  await app.reload();
  app.setView('history');
  assert.equal(app.getView(), 'events');
  assert.equal(fixture.calls.length, calls);
});

test('past cases open without weekly APIs, hide weekly context, and preserve case and weekly state across tab changes', async () => {
  const {initMboApp} = await ui();
  const doc = fakeDocument('#mbo/cases'), fixture = apiFixture({runs: [run('new'), run('old')]});
  let mounts = 0, destroys = 0;
  const caseLoader = async () => ({mount(host) { mounts++; host.textContent = 'ケース集は2026-10-18の保存版'; return {destroy() { destroys++; }}; }});
  const app = initMboApp(doc, fixture.fetcher, {caseLoader});
  await app.ready;
  assert.equal(app.getView(), 'cases');
  assert.equal(fixture.calls.length, 0, 'initial cases do not depend on weekly state or API availability');
  for (const id of ['mboRunToolbar', 'mboCoverage', 'mboStatus', 'mboError', 'mboReload', 'mboDemoNotice', 'mboWeeklyNotice']) assert.equal(doc.getElementById(id).hidden, true, id);
  assert.equal(doc.getElementById('mboCasesSection').hidden, false);
  await app.setView('candidates');
  await app.reload('old');
  assert.equal(app.getState().selected.run_id, 'old');
  doc.getElementById('mboSearch').value = '保存した検索';
  const calls = fixture.calls.length;
  await app.setView('cases');
  await app.setView('candidates');
  assert.equal(fixture.calls.length, calls);
  assert.equal(app.getState().selected.run_id, 'old');
  assert.equal(doc.getElementById('mboSearch').value, '保存した検索');
  assert.equal(doc.getElementById('mboRunToolbar').hidden, false);
  assert.equal(mounts, 1, 'case panel remains mounted while hidden');
  app.destroy();
  assert.equal(destroys, 1);
});

test('case schema failure stays within its own section and late case loading cannot mount after teardown', async () => {
  const {initMboApp} = await ui();
  const doc = fakeDocument('#mbo/cases'), fixture = apiFixture();
  const app = initMboApp(doc, fixture.fetcher, {caseLoader: async () => { throw Error('保存schema未対応'); }});
  await app.ready;
  assert.match(doc.getElementById('mboCases').innerHTML, /過去事例を表示できませんでした/);
  assert.equal(fixture.calls.length, 0);
  await app.setView('candidates');
  assert.equal(app.getState().selected.run_id, 'run-1');
  assert.equal(doc.getElementById('mboError').hidden, true);
  app.destroy();
  let resolve, mounts = 0;
  const late = initMboApp(fakeDocument('#mbo/cases'), fixture.fetcher, {caseLoader: () => new Promise(done => { resolve = done; })});
  await Promise.resolve();
  late.destroy();
  resolve({mount() { mounts++; }});
  await late.ready;
  assert.equal(mounts, 0);
});

test('case loading can retry from its escaped error button and a subsequent visit without repeating weekly requests', async () => {
  const {initMboApp} = await ui();
  const doc = fakeDocument('#mbo/cases'), fixture = apiFixture();
  let attempts = 0, mounts = 0;
  const app = initMboApp(doc, fixture.fetcher, {caseLoader() {
    if (++attempts < 3) throw Error('<img src=x onerror="bad"> /Users/ryu/private.txt');
    return {mount(host) { mounts++; host.innerHTML = '<p>過去事例の保存版</p>'; return {destroy() {}}; }};
  }});
  await app.ready;
  const error = doc.getElementById('mboCases').innerHTML;
  assert.match(error, /data-mbo-case-retry/);
  assert.match(error, /&lt;img/);
  assert.doesNotMatch(error, /<img|\sonerror="|\/Users\//);
  doc.listeners.click({target: {closest: selector => selector === '[data-mbo-case-retry]' ? {} : null}});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(attempts, 2);
  assert.equal(fixture.calls.length, 0);
  await app.setView('candidates');
  const weeklyCalls = fixture.calls.length;
  await app.setView('cases');
  assert.equal(attempts, 3);
  assert.equal(mounts, 1);
  assert.match(doc.getElementById('mboCases').innerHTML, /過去事例の保存版/);
  assert.equal(fixture.calls.length, weeklyCalls);
  app.destroy();
});

test('embedded stylesheet cannot change the Asset Hub body and markup has no second sidebar', async () => {
  const panel = await import(pathToFileURL(path.join(ROOT, 'web/mbo-panel.js')).href);
  const html = panel.renderMboPanel();
  assert.match(html, /class="mbo-embedded"/);
  assert.doesNotMatch(html, /<aside|<h1|<iframe|https?:\/\//);
  const css = fs.readFileSync(path.join(ROOT, 'web/mbo-panel.css'), 'utf8');
  assert.doesNotMatch(css, /(?:^|\})\s*(?:body|h[123]|table|button|select|input|\*)\s*\{/m);
  assert.match(css, /\.mbo-embedded table/);
});

test('null and unavailable prices remain missing rather than zero or 100% undervalued', async () => {
  const {priceLabel, formatNumber, formatPercent, renderCandidateTable, renderCompanyDetail} = await ui();
  for (const value of [null, undefined, '', NaN, Infinity]) assert.equal(formatNumber(value), '未確認');
  assert.equal(formatPercent(null), '未計算');
  assert.equal(formatPercent(0.25), '25%');
  assert.equal(formatPercent(-0.1), '-10%');
  assert.equal(formatPercent(0), '0%');
  assert.equal(priceLabel(company('285A')), '株価未入力');
  const html = renderCandidateTable([company('285A', {valuation: {discount_to_base: {status: 'ok', value: 1}}})]);
  assert.match(html, /株価未入力/);
  assert.match(html, /未計算/);
  assert.doesNotMatch(html, /100%|0 JPY/);
  assert.match(renderCompanyDetail(company('285A')), /株価未入力のため、割安率は未計算/);
});

test('filter/search/sort retain unpriced candidates, normalize Japanese input, and leave missing values last', async () => {
  const {candidateSubset} = await ui();
  const ready = company('285A', {name: '架空キオクシア', status: 'ready', priority: 10, is_new: true, missing: [], price: {value: '1000', currency: 'JPY'}, valuation: {discount_to_base: {status: 'ok', value: '0.25'}}});
  const pending = company('1234', {priority: 80});
  const negative = company('5678', {priority: 30, price: {value: '2000', currency: 'JPY'}, valuation: {discount_to_base: {status: 'ok', value: '-0.1'}}});
  const items = [ready, pending, negative];
  assert.deepEqual(candidateSubset(items).map(item => item.code), ['1234', '5678', '285A']);
  assert.deepEqual(items.map(item => item.code), ['285A', '1234', '5678'], 'sorting does not mutate the saved DTO');
  assert.deepEqual(candidateSubset(items, {query: '２８５Ａ　キオクシア'}).map(item => item.code), ['285A']);
  assert.deepEqual(candidateSubset(items, {filter: 'missing_price'}).map(item => item.code), ['1234']);
  assert.deepEqual(candidateSubset(items, {filter: 'new'}).map(item => item.code), ['285A']);
  assert.deepEqual(candidateSubset(items, {filter: 'ready'}).map(item => item.code), ['285A']);
  assert.deepEqual(candidateSubset(items, {sort: 'discount_desc'}).map(item => item.code), ['285A', '5678', '1234']);
});

test('new assessments order research work by workflow then code and never use the old financial score as an MBO rank', async () => {
  const {candidateSubset, renderCandidateTable} = await ui();
  const items = [company('3000', {priority: 999, mbo_assessment: assessment('awaiting')}), company('2200', {priority: 100, mbo_assessment: assessment('research')}), company('2100', {priority: 0, mbo_assessment: assessment('research')}), company('1000', {priority: -10, status: 'ready', mbo_assessment: assessment('monitor')}), company('4000', {priority: 9000, mbo_assessment: assessment('deferred')})];
  assert.deepEqual(candidateSubset(items).map(item => item.code), ['1000', '2100', '2200', '3000', '4000']);
  assert.deepEqual(candidateSubset(items, {filter: 'ready'}).map(item => item.code), ['1000']);
  assert.deepEqual(items.map(item => item.code), ['3000', '2200', '2100', '1000', '4000']);
  const html = renderCandidateTable(items);
  for (const text of ['監視', '詳細調査', '調査待ち', '見送り', '所有構造', 'MBOの動機', '実行可能性', '障害・反証', '確認済み 1件', '未解決 3件', '価格評価可', 'MBO確率や有力度ではありません']) assert.ok(html.includes(text), text);
  assert.doesNotMatch(html, /優先度|999|9000/);
  const legacy = renderCandidateTable([company('old', {priority: 4})]);
  assert.match(legacy, /旧優先度 4/);
  assert.match(legacy, /初期の未検証ルール/);
  assert.match(legacy, /旧版では動機等の軸別評価はありません/);
});

test('assessment detail separates public evidence, interpretation, hypotheses and post-announcement information with source dates', async () => {
  const {renderCompanyDetail} = await ui();
  const factors = [
    {factor_id: 'long_term', label: '長期投資', state: 'supported', evidence_type: 'public_fact', speaker: 'company', usable_for_candidate: true, quote: '中長期の事業変革に取り組む。', interpretation: '投資方針の表明でありMBO意思は未確認', source_id: 'S1', locator: 'p.3', public_at: '2025-06-20', quality_status: 'verified'},
    {factor_id: 'hypothesis', label: '承継の可能性', state: 'unknown', evidence_type: 'analyst_hypothesis', quote: '', interpretation: '追加の一次資料が必要', quality_status: 'pending'},
    {factor_id: 'financing', label: '借入条件', state: 'supported', evidence_type: 'own_scenario'},
    {factor_id: 'released', label: '買収公表後の説明', state: 'supported', evidence_type: 'post_announcement', speaker: 'shareholder', usable_for_candidate: false, exclusion_reason: '株主の説明であり、公表前の会社の意思ではない'},
  ];
  const item = company('1234', {priority: 4, reasons: ['OLD_FINANCIAL_SCORE_REASON'], evidence: [{source_id: 'S1', title: '中期計画', source_url: 'https://example.com/plan.pdf'}], mbo_assessment: assessment('research', {workflow: {state: 'research', reason: '動機を追加調査', watch_trigger: '資本政策の変更', next_review_at: '2026-10-25', reviewer: '調査担当'}, axes: [{id: 'motive', label: 'MBOの動機', state: 'conflicting', note: '動機の根拠を照合', factors: [{factor_id: 'succession', label: '承継方針', state: 'unknown'}], evidence: factors}]})});
  const html = renderCompanyDetail(item);
  for (const text of ['設計仮説・未検証', '校正は未実施', 'MBO発生確率は算出していません', '根拠原文', '中長期の事業変革', '解釈', 'MBO意思は未確認', '公開された事実', '調査者の仮説', '独自シナリオ', '公表後の情報（事前評価には使わない）', '2025-06-20', 'S1', 'p.3', '資本政策の変更', '2026-10-25', '調査担当', '件数は情報の充足', '財務・価格評価の参考情報', '営業CFは正だが', '根拠が矛盾']) assert.ok(html.includes(text), text);
  assert.match(html, /href="https:\/\/example.com\/plan.pdf" target="_blank" rel="noopener noreferrer">根拠資料/);
  for (const text of ['確認する論点', '承継方針：未確認', '軸内の全論点を確認済みとは限りません', '発言・説明の主体', '会社', '株主', '候補評価に利用', '候補評価から除外', '株主の説明であり、公表前の会社の意思ではない']) assert.ok(html.includes(text), text);
  assert.doesNotMatch(html, /OLD_FINANCIAL_SCORE_REASON|旧優先度/);
  assert.match(renderCompanyDetail(company('old')), /旧版の調査優先度 50/);
});

test('new assessment fields remain escaped and cannot expose local paths or inject source links', async () => {
  const {renderCompanyDetail, renderCandidateTable, candidateSubset} = await ui();
  const evil = company('1234', {mbo_assessment: assessment('awaiting', {version: '<img src=x>', validation_status: '<script>status</script>', workflow: {state: '<svg onload=1>', label: '<img onerror="x">', reason: '/Users/ryu/secret.txt', watch_trigger: '<script>x</script>', reviewer: '/private/reviewer'}, axes: [{id: 'motive', label: '<script>axis</script>', state: '<img src=x>', note: '/tmp/note', evidence: [{label: '<script>factor</script>', state: '<svg>', evidence_type: '<script>type</script>', quote: '<img src=x onerror="x"> /Users/ryu/quote.pdf', interpretation: '<script>meaning</script>', source_id: '<script>source</script>', public_at: '<script>date</script>', locator: '/private/raw.txt', source_url: 'https://evil.example/raw', quality_status: '<svg>'}]}], information: {coverage_label: '<script>coverage</script>', verified_count: '<img>'}, cautions: ['<script>caution</script>']})});
  const html = renderCandidateTable([evil]) + renderCompanyDetail(evil);
  assert.match(html, /&lt;script&gt;factor/);
  assert.match(html, /&lt;svg/);
  assert.doesNotMatch(html, /<img|<svg|<script|\sonerror="|\/Users\/|\/private\/|\/tmp\/|https:\/\/evil/);
  assert.equal(candidateSubset([evil])[0].code, '1234');
  // A source without an ID must not accidentally match an unidentified document.
  const missingId = company('5678', {evidence: [{source_url: 'https://example.com/unrelated.pdf'}], mbo_assessment: assessment('research', {axes: [{id: 'motive', state: 'unknown', evidence: [{quote: '原文', source_id: null}]}]})});
  assert.doesNotMatch((await ui()).renderMboAssessment(missingId), /href=/);
});

test('untrusted text is escaped, local paths and giant source fields are not exposed, and only safe HTTPS source links work', async () => {
  const {renderCandidateTable, renderCompanyDetail, safeHttpsUrl, safeText} = await ui();
  for (const url of ['javascript:alert(1)', 'data:text/html,x', 'http://example.com', 'file:///Users/ryu/secret.pdf', '/research/raw.pdf', 'https://user:pass@example.com', 'https://example.com?api_key=secret', 'https://localhost/x', 'https://127.0.0.1/x']) assert.equal(safeHttpsUrl(url), null, url);
  assert.equal(safeHttpsUrl('https://example.com/report.pdf?page=2'), 'https://example.com/report.pdf?page=2');
  const evil = company('x" onclick="alert(1)', {name: '<img src=x onerror=alert(1)>', reasons: ['/Users/ryu/private.pdf', '<script>secret</script>'], evidence: [{title: '<script>alert(1)</script>', filename: '/Users/ryu/secret.pdf', raw_path: '/private/raw.txt', source_url: 'javascript:alert(1)', raw_html: 'NEVER_RENDER_THIS'.repeat(10000)}], valuation: {standalone: {scenarios: [{name: '弱気<script>', status: 'ok', value_per_share: '1000', assumptions: {tax_rate: 0.3, api_key: 'DONT_PRINT_ME', raw_path: '/Users/ryu/secrets'}}]}, lbo: {status: 'infeasible'}}});
  const html = renderCandidateTable([evil]) + renderCompanyDetail(evil);
  assert.match(html, /&lt;img/);
  assert.match(html, /成立範囲なし/);
  assert.doesNotMatch(html, /<img|<script|href="javascript:|\s(?:onclick|onerror)="|DONT_PRINT_ME|NEVER_RENDER_THIS|\/Users\/|\/private\/raw/);
  assert.ok(html.length < 10000);
  assert.ok(safeText('a'.repeat(10000)).length <= 361);
  const safe = renderCompanyDetail(company('1234', {evidence: [{title: '有価証券報告書', source_url: 'https://example.com/ir.pdf?x=1&y=2'}]}));
  assert.match(safe, /href="https:\/\/example.com\/ir.pdf\?x=1&amp;y=2" target="_blank" rel="noopener noreferrer"/);
});

test('events, weekly additions/removals/changes and run history show their separate meanings', async () => {
  const {renderEvents, renderDiff, renderRuns} = await ui();
  const events = renderEvents([{security_id: 'a', code: '1234', name: '架空A', event_type: 'mbo', status: 'announced', announced_at: '2026-10-01', source_id: 'S1'}, {security_id: 'b', code: '5678', name: '架空B', event_type: 'tob', status: 'withdrawn', source_id: 'S2'}]);
  assert.match(events, /公表済み · 1件/);
  assert.match(events, /撤回 · 1件/);
  assert.match(events, /MBO/);
  const diff = renderDiff({previous_run_id: 'before', summary: '価格・根拠が変わりました', added: [company('1234')], removed: [company('5678')], changed: [company('285A', {changes: ['株価未入力になった', '借入条件を確認']})]});
  for (const text of ['新しく加わった候補', '候補から外れた企業', '内容が変わった企業', '株価未入力になった']) assert.ok(diff.includes(text));
  assert.match(renderDiff({previous_run_id: null}), /初回/);
  assert.match(renderRuns([run('run-demo', {demo: true})]), /架空デモ/);
  assert.match(renderRuns([run('past', {retrospective: true})]), /過去日を再構成。後日取得したデータは除外/);
});

test('evidence lookup provides a selectable command containing only a validated document ID, and detailed calculations retain their yearly checks', async () => {
  const {evidenceCommand, renderCompanyDetail} = await ui();
  assert.equal(evidenceCommand('doc-a_1'), 'python3 -m backend.mbo evidence locate --document-id doc-a_1');
  for (const id of ['x;echo hi', '$(secret)', '../secret', '/Users/ryu/private', 'x\nls']) assert.equal(evidenceCommand(id), null);
  const item = company('1234', {facts: [{metric: 'owner_ratio', value: '.42', unit: 'ratio', fact_kind: 'own_scenario'}], evidence: [{document_id: 'doc-a_1', title: '資料'}], valuation: {standalone: {scenarios: [{name: 'base', status: 'ok', assumptions: {wacc: '.09'}, yearly: [{year: 1, ebit: 100, fcff: 70}]}]}, lbo: {status: 'ok', max_price_per_share: 200, yearly: [{year: 1, closing_debt: 500, closing_cash: 100}], financing: {total_uses: 1000, total_sources: 1000}}}});
  const html = renderCompanyDetail(item);
  assert.match(html, /資料ID：doc-a_1/);
  assert.match(html, /evidence locate --document-id doc-a_1/);
  assert.match(html, /42%/);
  assert.match(html, /9%/);
  assert.match(html, /年別のCF・現在価値/);
  assert.match(html, /年別の返済・現金/);
  assert.match(html, /総調達額/);
  assert.match(html, /<h3>基準<\/h3>/);
});

test('load order is status then runs then candidates/events, and all run-based reads pin the selected saved run', async () => {
  const {loadWorkspace, loadCompany} = await ui();
  const fixture = apiFixture({runs: [run('new'), run('old')]});
  const state = await loadWorkspace(fixture.fetcher, undefined, 'old');
  assert.equal(state.selected.run_id, 'old');
  assert.deepEqual(fixture.calls.slice(0, 2).map(call => call.href.split('?')[0]), ['/api/mbo/status', '/api/mbo/runs']);
  assert.equal(fixture.calls.length, 4);
  for (const call of fixture.calls.slice(2)) assert.equal(new URL(call.href, 'http://localhost').searchParams.get('run_id'), 'old');
  await loadCompany('old', '285A', fixture.fetcher);
  assert.match(fixture.calls.at(-1).href, /\/companies\/285A\?run_id=old/);
  for (const {options} of fixture.calls) { assert.equal(options.method, 'GET'); assert.equal(options.cache, 'no-store'); assert.equal(options.credentials, 'same-origin'); }
});

test('empty setup works without candidate/EDINET/cloud reads and fails closed on a nonlocal status', async () => {
  const {loadWorkspace, requestApi} = await ui();
  const fixture = apiFixture({runs: []});
  const state = await loadWorkspace(fixture.fetcher);
  assert.equal(state.selected, null);
  assert.equal(state.candidates, null);
  assert.equal(fixture.calls.length, 2);
  const unsafe = apiFixture({status: {mode: 'cloud', offline: false}});
  await assert.rejects(loadWorkspace(unsafe.fetcher), /閲覧モード/);
  assert.equal(unsafe.calls.length, 1);
  await assert.rejects(requestApi('https://example.com/api/mbo/status', fixture.fetcher), /許可されていない/);
});

test('inconsistent run IDs are rejected and an individual API failure does not suppress another successful section', async () => {
  const {loadRunData, loadCompany} = await ui();
  const fixture = apiFixture({candidates: {run_id: 'wrong'}});
  const state = await loadRunData('run-1', fixture.fetcher);
  assert.equal(state.candidates, null);
  assert.ok(state.events);
  assert.match(state.errors[0], /版が一致しません/);
  const wrongDetail = apiFixture({detail: {run_id: 'wrong'}});
  await assert.rejects(loadCompany('run-1', '285A', wrongDetail.fetcher), /版が一致しません/);
  const failure = await loadRunData('run-1', async href => href.startsWith('/api/mbo/candidates') ? {ok: false, status: 503} : response({...meta('run-1'), items: [], total: 0}));
  assert.equal(failure.candidates, null);
  assert.ok(failure.events);
  assert.match(failure.errors[0], /HTTP 503/);
});

test('all run/candidate/event pages are fetched before filtering and ranking, including an unpriced match after row 200', async () => {
  const {loadWorkspace, candidateSubset} = await ui();
  const runs = Array.from({length: 405}, (_, index) => run(`run-${index}`));
  const companies = Array.from({length: 451}, (_, index) => company(String(index), {priority: index, name: index === 450 ? '後半の価格未入力企業' : `架空${index}`}));
  const events = Array.from({length: 403}, (_, index) => ({security_id: `event-${index}`, name: `案件${index}`, status: 'announced'}));
  const requests = [];
  const fetcher = async href => {
    const url = new URL(href, 'http://localhost');
    requests.push(url);
    if (url.pathname === '/api/mbo/status') return response({schema_version: 1, mode: 'mbo-local', offline: true, storage_state: 'ready', latest_success_run_id: 'run-0'});
    const offset = Number(url.searchParams.get('offset') || 0), pinnedRun = url.searchParams.get('run_id');
    const items = url.pathname.endsWith('/runs') ? runs : url.pathname.endsWith('/candidates') ? companies : events;
    return response({...meta(pinnedRun), items: items.slice(offset, offset + 200), total: items.length, limit: 200, offset});
  };
  const result = await loadWorkspace(fetcher, undefined, 'run-404');
  assert.equal(result.runs.length, 405);
  assert.equal(result.selected.run_id, 'run-404');
  assert.equal(result.candidates.items.length, 451);
  assert.equal(result.events.items.length, 403);
  assert.equal(candidateSubset(result.candidates.items, {query: '後半', filter: 'missing_price'})[0].security_id, '450');
  assert.equal(candidateSubset(result.candidates.items)[0].security_id, '450');
  for (const route of ['runs', 'candidates', 'events']) assert.deepEqual(requests.filter(url => url.pathname.endsWith(`/${route}`)).map(url => url.searchParams.get('offset')), ['0', '200', '400']);
  for (const request of requests.filter(url => /\/(?:candidates|events)$/.test(url.pathname))) assert.equal(request.searchParams.get('run_id'), 'run-404');
});

test('an incomplete page or a changed total cannot be presented as a complete saved list', async () => {
  const {loadAllPages} = await ui();
  let page = 0;
  await assert.rejects(loadAllPages('/api/mbo/runs', {}, async () => response({items: page++ ? [] : [run('a')], total: 2})), /途中ページ/);
  page = 0;
  await assert.rejects(loadAllPages('/api/mbo/runs', {}, async () => response({items: [run('a')], total: page++ ? 3 : 2})), /件数が変わりました/);
});

test('bootstrap marks fictional demo persistently, supports empty setup and displays the last failed build without losing a successful saved run', async () => {
  const {initMboApp} = await ui();
  const doc = fakeDocument('#mbo/history');
  const fixture = apiFixture({runs: [run('demo', {demo: true})], status: {last_attempt: {status: 'failed', as_of: '2026-10-19'}}, candidates: {demo: true}});
  const app = initMboApp(doc, fixture.fetcher);
  await app.ready;
  assert.equal(doc.getElementById('mboDemoNotice').hidden, false);
  assert.equal(app.getView(), 'history');
  assert.equal(doc.getElementById('mboHistorySection').hidden, false);
  assert.match(doc.getElementById('mboError').textContent, /前回成功版/);
  await app.openCompany('285A');
  assert.equal(doc.getElementById('mboDemoNotice').hidden, false);
  assert.match(doc.getElementById('mboDetail').innerHTML, /株価未入力/);
  assert.ok(doc.getElementById('mboDetailTitle').focused);

  const emptyDoc = fakeDocument();
  const blank = initMboApp(emptyDoc, apiFixture({runs: []}).fetcher);
  await blank.ready;
  assert.match(emptyDoc.getElementById('mboCandidates').innerHTML, /株価CSVやAPIキーがなくても/);
  assert.equal(emptyDoc.getElementById('mboRunSelect').disabled, true);
  assert.equal(emptyDoc.getElementById('mboError').hidden, true);
});
