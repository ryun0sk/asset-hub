const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {pathToFileURL} = require('node:url');

const ROOT = path.join(__dirname, '..');
const fromWeb = name => import(pathToFileURL(path.join(ROOT, 'web', name)).href);
const html = fs.readFileSync(path.join(ROOT, 'web/index.html'), 'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));

function documentFixture() {
  const all = new Map();
  class Element {
    constructor(id = '') {
      this.id = id; this.hidden = false; this.innerHTML = ''; this.textContent = ''; this.children = [];
      this.attributes = {}; this.dataset = {}; this.listeners = {}; this.ownerDocument = doc;
      const classes = new Set();
      this.classList = {toggle(name, selected) { if (selected) classes.add(name); else classes.delete(name); }, contains: name => classes.has(name)};
    }
    setAttribute(name, value) { this.attributes[name] = value; }
    removeAttribute(name) { delete this.attributes[name]; }
    replaceChildren(...children) { this.children = children; }
    querySelectorAll(selector) { return selector === '[data-mbo-section]' ? mboLinks : []; }
    addEventListener(name, listener) { this.listeners[name] = listener; }
  }
  const doc = {
    getElementById(id) { return all.get(id) || null; },
    createElement() { return new Element(); },
    addEventListener() {},
    querySelectorAll(selector) {
      if (selector === '#mainNav [data-view]') return mainLinks;
      if (selector === '#assetSubnav [data-asset-view]') return assetLinks;
      return [];
    },
  };
  for (const match of html.matchAll(/\bid="([^"]+)"/g)) all.set(match[1], new Element(match[1]));
  const mainLinks = ['home', 'asset', 'mbo', 'cost'].map(view => Object.assign(new Element(), {dataset: {view}}));
  const assetLinks = ['summary', 'all', 'holdings', 'policy'].map(assetView => Object.assign(new Element(), {dataset: {assetView}}));
  const mboLinks = ['candidates', 'events', 'history', 'cases'].map(mboSection => Object.assign(new Element(), {dataset: {mboSection}}));
  all.get('assetSubnav').parentElement = new Element();
  doc.body = new Element();
  return {doc, all, mboLinks, mainLinks};
}

async function appFixture(initialHash = '#mbo/candidates', {mount, catalogFails = true} = {}) {
  const workspace = await fromWeb('workspace.js'), routing = await fromWeb('catalog.js');
  const dom = documentFixture(), listeners = {}, mounts = [], calls = {assets: 0, costs: 0, initAssets: 0, initCosts: 0};
  const context = {
    ...workspace, ...routing, document: dom.doc, location: {hash: initialHash},
    window: {scrollTo() {}}, history: {replaceState(_state, _title, hash) { context.location.hash = hash; }},
    addEventListener(name, listener) { listeners[name] = listener; },
    fetch: async () => catalogFails ? {ok: false, status: 503} : {ok: true, json: async () => ({groups: []})},
    showCosts() { calls.costs++; }, initCostAlerts() { calls.initCosts++; },
    showAssets() { calls.assets++; }, leaveAssets() {}, initAssets() { calls.initAssets++; },
    renderMarkdown() { return ''; }, isAiValuationView() { return false; }, mountAiValuations() {},
    AI_DETAIL_SECTIONS: {}, mountAiDetail() {},
    mountMboPanel(host, section) {
      const panel = mount ? mount(host, section) : {host, section, sections: [], destroyed: 0, setView(next) { this.sections.push(next); this.section = next; }, destroy() { this.destroyed++; }};
      mounts.push(panel);
      return panel;
    },
  };
  // Execute the real shell with its external modules substituted at the import
  // boundary. This exercises catalog failure, hash changes and view teardown.
  const source = fs.readFileSync(path.join(ROOT, 'web/app.js'), 'utf8').replace(/^import .* from '[^']+';\n/gm, '');
  vm.runInNewContext(source, context, {filename: 'app.js'});
  await flush();
  const changeHash = hash => { context.location.hash = hash; listeners.hashchange(); };
  return {...dom, context, mounts, calls, changeHash};
}

test('MBO hashes coexist with existing AI, assets, cost and dated research routes', async () => {
  const {parseRoute, routeFor} = await fromWeb('catalog.js');
  for (const section of ['candidates', 'events', 'history', 'cases']) {
    assert.deepEqual(parseRoute(`#mbo/${section}`), {view: 'mbo', section});
    assert.deepEqual(parseRoute(`#mbo/${section}/`), {view: 'mbo', section});
  }
  assert.deepEqual(parseRoute('#mbo'), {view: 'mbo', section: 'candidates'});
  assert.deepEqual(parseRoute('#mbo/not-a-section'), {view: 'home'});
  assert.deepEqual(parseRoute('#ai/eps'), {view: 'ai', section: 'eps'});
  assert.deepEqual(parseRoute('#a/policy'), {view: 'asset', cls: 'policy'});
  assert.deepEqual(parseRoute('#cost'), {view: 'cost'});
  assert.deepEqual(parseRoute(routeFor('some-theme-2026-10-18', 3)), {view: 'research', entryId: 'some-theme-2026-10-18', index: 3, anchor: ''});
});

test('MBO is a permanent same-origin shell tab and the home entry uses real routes without invented counts', async () => {
  const {renderHomeHub, MBO_SECTIONS} = await fromWeb('workspace.js');
  const staticMbo = html.indexOf('data-view="mbo"');
  assert.ok(staticMbo > 0 && staticMbo < html.indexOf('id="classNav"'));
  assert.match(html, /<section id="mboSection" hidden aria-label="MBO調査"><\/section>/);
  assert.match(html, /href="\/mbo-panel\.css"/);
  for (const section of Object.keys(MBO_SECTIONS)) assert.ok(html.includes(`href="#mbo/${section}"`));
  const home = renderHomeHub({groups: []});
  for (const section of Object.keys(MBO_SECTIONS)) assert.ok(home.includes(`href="#mbo/${section}"`));
  const mboHome = home.match(/<h2>MBO調査<\/h2>[\s\S]*?(?=<section class="hub-section">)/)[0];
  assert.doesNotMatch(mboHome, /\d+件|localhost|127\.0\.0\.1|<iframe/);
});

test('embedded MBO controls distinguish research work and price readiness from unvalidated MBO strength', async () => {
  const {renderMboPanel} = await fromWeb('mbo-panel.js');
  const panel = renderMboPanel();
  assert.match(panel, /<option value="rank">調査作業順<\/option>/);
  assert.match(panel, /<option value="ready">価格評価可<\/option>/);
  assert.match(panel, /MBO確率や有力度ではありません/);
  assert.match(panel, /設計仮説・未検証/);
  assert.doesNotMatch(panel, /調査優先順|value="ready">確認済み/);
});

test('catalog failure never removes or blocks the MBO tab, its metadata or active subnavigation', async () => {
  const app = await appFixture('#mbo/events');
  assert.equal(app.mounts.length, 1, 'initial route and late catalog failure share one panel');
  assert.equal(app.mounts[0].section, 'events');
  assert.equal(app.all.get('mboSection').hidden, false);
  assert.equal(app.all.get('homeSection').hidden, true);
  assert.equal(app.all.get('mboSubnav').hidden, false);
  assert.equal(app.all.get('pageTitle').textContent, 'MBO調査 · 公表案件');
  assert.equal(app.all.get('breadcrumb').textContent, 'MBO調査 / 公表案件');
  assert.equal(app.mboLinks.find(link => link.dataset.mboSection === 'events').attributes['aria-current'], 'page');
  assert.equal(app.mainLinks.find(link => link.dataset.view === 'mbo').attributes['aria-current'], 'page');
  assert.match(app.all.get('classNav').innerHTML, /調査一覧を読み込めませんでした/);
});

test('past cases remain a distinct shell route when the research catalog fails', async () => {
  const app = await appFixture('#mbo/cases');
  assert.equal(app.mounts[0].section, 'cases');
  assert.equal(app.all.get('pageTitle').textContent, 'MBO調査 · 過去事例');
  assert.equal(app.mboLinks.find(link => link.dataset.mboSection === 'cases').attributes['aria-current'], 'page');
  app.changeHash('#mbo/candidates');
  assert.equal(app.mounts.length, 1);
  assert.deepEqual(app.mounts[0].sections, ['candidates']);
});

test('intra-MBO changes preserve the mounted state; leaving destroys it and returning gets a fresh panel', async () => {
  const app = await appFixture();
  const first = app.mounts[0];
  first.selectedRun = 'saved-run-123';
  app.changeHash('#mbo/history');
  app.changeHash('#mbo/events');
  assert.equal(app.mounts.length, 1);
  assert.equal(first.selectedRun, 'saved-run-123');
  assert.deepEqual(first.sections, ['history', 'events']);
  app.changeHash('#a/summary');
  assert.equal(first.destroyed, 1);
  assert.equal(app.calls.assets, 1);
  assert.equal(app.all.get('mboSection').hidden, true);
  assert.equal(app.all.get('mboSubnav').hidden, true);
  assert.equal(app.all.get('mboSection').children.length, 0);
  app.changeHash('#mbo/candidates');
  assert.equal(app.mounts.length, 2);
  assert.notEqual(app.mounts[1], first);
  app.changeHash('#cost');
  assert.equal(app.calls.costs, 1);
  assert.equal(app.mounts[1].destroyed, 1);
  assert.equal(app.calls.initAssets, 1);
  assert.equal(app.calls.initCosts, 1);
});

test('late work from a departed panel stays detached and rejected readiness cannot overwrite a new visit', async () => {
  const {createMboPanelLifecycle} = await fromWeb('workspace.js');
  const {all} = documentFixture(), host = all.get('mboSection'), panels = [], errors = [];
  const lifecycle = createMboPanelLifecycle(host, (slot, section) => {
    let reject;
    const panel = {slot, section, ready: new Promise((_resolve, fail) => { reject = fail; }), setView() {}, destroy() { this.destroyed = true; }, reject: () => reject(Error('late error'))};
    panels.push(panel);
    return panel;
  }, {onError() { errors.push('failed'); }});
  lifecycle.show('candidates');
  const old = panels[0];
  lifecycle.leave();
  lifecycle.show('history');
  old.slot.textContent = 'stale result';
  old.reject();
  await flush();
  assert.equal(old.destroyed, true);
  assert.equal(host.children.length, 1);
  assert.notEqual(host.children[0], old.slot);
  assert.equal(host.children[0].textContent, '');
  assert.deepEqual(errors, []);
  panels[1].reject();
  await flush();
  assert.deepEqual(errors, ['failed']);
});
