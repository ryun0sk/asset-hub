const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ROOT = path.join(__dirname, '..');
const SNAPSHOT = path.join(ROOT, 'research/themes/ai-supply-chain/2026-10-03');
const template = fs.readFileSync(path.join(SNAPSHOT, 'dashboard.template.html'), 'utf8');
const snapshotScript = [...template.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1];
const adapter = fs.readFileSync(path.join(ROOT, 'web/ai-multi-chain.js'), 'utf8');
const savedData = {
  'price-data': fs.readFileSync(path.join(SNAPSHOT, 'prices.json'), 'utf8'),
  'catalog-data': fs.readFileSync(path.join(SNAPSHOT, 'catalog.json'), 'utf8'),
  'fundamental-data': fs.readFileSync(path.join(SNAPSHOT, 'fundamentals.json'), 'utf8'),
  'valuation-data': fs.readFileSync(path.join(SNAPSHOT, 'valuation.json'), 'utf8'),
};
const plain = value => JSON.parse(JSON.stringify(value));

// Only layout and painting are stubbed. The saved page's own selection, period,
// valuation calculations and Chart configurations execute unchanged in a VM.
function fixture() {
  const ids = new Map(), elements = new Set();
  const matches = (element, selector) => {
    if (selector === 'input') return element.tagName === 'INPUT';
    if (selector === 'input:checked') return element.tagName === 'INPUT' && element.checked;
    const attr = selector.match(/^\[([^=\]]+)(?:="([^"]*)")?\](\.active)?$/);
    if (attr) return attr[1] in element.attributes && (attr[2] === undefined || element.attributes[attr[1]] === attr[2]) && (!attr[3] || element.classList.contains('active'));
    return false;
  };
  class Element {
    constructor(tagName = 'div', attributes = {}) {
      this.tagName = tagName.toUpperCase();
      this.attributes = attributes;
      this.dataset = Object.fromEntries(Object.entries(attributes).filter(([key]) => key.startsWith('data-')).map(([key, value]) => [key.slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase()), value]));
      this.value = attributes.value || '';
      this.checked = 'checked' in attributes;
      this.hidden = 'hidden' in attributes;
      this.children = [];
      this.style = {};
      this.textContent = '';
      this.onclick = null;
      this.onchange = null;
      const classes = new Set((attributes.class || '').split(' ').filter(Boolean));
      this.classList = {
        contains: name => classes.has(name),
        toggle: (name, enabled = !classes.has(name)) => { if (enabled) classes.add(name); else classes.delete(name); },
        add: name => classes.add(name),
        remove: name => classes.delete(name),
      };
      elements.add(this);
      if (attributes.id) ids.set(attributes.id, this);
    }
    set innerHTML(html) {
      for (const child of this.children) {
        elements.delete(child);
        if (ids.get(child.attributes.id) === child) ids.delete(child.attributes.id);
      }
      this.html = html;
      this.children = parse(html);
    }
    get innerHTML() { return this.html || ''; }
    querySelectorAll(selector) { return this.children.filter(element => matches(element, selector)); }
    insertAdjacentHTML(position, html) {
      assert.equal(position, 'beforeend');
      this.html = (this.html || '') + html;
      this.children.push(...parse(html));
    }
    setAttribute(name, value) { this.attributes[name] = String(value); }
    getAttribute(name) { return this.attributes[name] ?? null; }
    scrollIntoView() {}
    click() {
      const event = {target: this, preventDefault() {}, stopPropagation() { this.stopped = true; }};
      this.onclick?.(event);
      if (!event.stopped) for (const listener of document.listeners.get('click') || []) listener(event);
    }
  }
  function parse(html) {
    return [...html.matchAll(/<([a-z][a-z0-9]*)\b([^>]*)>/gi)].map(([, tag, source]) => {
      const attributes = Object.fromEntries([...source.matchAll(/([:\w-]+)(?:=(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g)].map(([, key, quoted, single, bare]) => [key, quoted ?? single ?? bare ?? '']));
      return new Element(tag, attributes);
    });
  }
  parse(template.replace(/<script\b[^>]*>[\s\S]*?<\/script>/g, ''));
  for (const [id, textContent] of Object.entries(savedData)) new Element('script', {id}).textContent = textContent;
  ids.get('mode').value = 'index';
  ids.get('basis').value = 'close';
  const nav = new Element('nav');
  const document = {
    body: new Element('body'),
    listeners: new Map(),
    getElementById: id => ids.get(id),
    querySelectorAll: selector => [...elements].filter(element => matches(element, selector)),
    querySelector: selector => selector === 'header nav' ? nav : [...elements].find(element => matches(element, selector)),
    createElement: tagName => new Element(tagName),
    addEventListener: (type, listener) => {
      if (!document.listeners.has(type)) document.listeners.set(type, new Set());
      document.listeners.get(type).add(listener);
    },
  };
  const charts = [];
  class Chart {
    constructor(canvas, config) {
      assert.ok(canvas, 'every real graph canvas exists');
      this.canvas = canvas;
      this.data = config.data;
      this.options = config.options;
      this.destroyed = false;
      charts.push(this);
    }
    destroy() { assert.equal(this.destroyed, false, 'a graph is destroyed only once'); this.destroyed = true; }
    resize() {}
  }
  const context = vm.createContext({document, Chart, URLSearchParams, location: {search: '?view=fund'}, setTimeout, URL, Blob, console});
  context.window = context;
  context.innerWidth = 1440;
  context.addEventListener = () => {};
  vm.runInContext(snapshotScript, context, {filename: 'saved-dashboard.js'});
  const runAdapter = () => vm.runInContext(adapter, context, {filename: 'ai-multi-chain.js'});
  const stage = id => ids.get('chain-picker-stages').querySelectorAll('[data-chain]').find(button => button.dataset.chain === id);
  const check = (symbol, checked, box = 'fund-choices') => {
    const input = ids.get(box).querySelectorAll('input').find(element => element.value === symbol);
    assert.ok(input, symbol + ' is an eligible company');
    input.checked = checked;
    input.onchange();
  };
  return {context, ids, document, charts, runAdapter, stage, check,
    state: () => plain(context.ASSET_MULTI_CHAIN.getState()),
    savedState: () => context.DASHBOARD_TEST.getState(),
  };
}

function assertCharts(f, selected) {
  const state = f.savedState();
  assert.deepEqual(plain(state.selected), selected);
  assert.deepEqual(plain(state.chart.data.datasets.map(dataset => dataset.symbol)), selected);
  assert.deepEqual(plain(state.peChart.data.datasets.filter(dataset => !dataset.median).map(dataset => dataset.symbol)), selected);
  assert.deepEqual(plain(state.fund.now.map(row => row.symbol)), selected);
  assert.deepEqual(plain(state.fund.decomp.map(row => row.symbol)), selected);
  assert.equal(state.epsCharts.length, selected.length);
  assert.ok(state.chart.data.datasets.every(dataset => typeof dataset.borderColor === 'string'));
}

test('two stages share the original calculations and preserve company choices and button identity', () => {
  const f = fixture();
  const initial = f.savedState();
  const nandButton = f.stage('nand'), testButton = f.stage('test');
  const catalogBefore = vm.runInContext('JSON.stringify(CAT)', f.context);
  let bubbledSelection;
  f.document.addEventListener('click', () => {
    bubbledSelection = f.ids.get('fund-choices').querySelectorAll('input:checked').map(input => input.value);
  });
  f.runAdapter();
  assert.deepEqual(f.state().selectedGroups, ['nand']);
  assert.deepEqual(f.state().selected, ['285A.T', 'SNDK']);
  assert.equal(initial.chart.destroyed, true);
  testButton.click();
  assert.equal(f.stage('nand'), nandButton, 'toggling does not replace a focused button');
  assert.equal(f.stage('test'), testButton);
  assert.equal(nandButton.getAttribute('aria-pressed'), 'true');
  assert.equal(testButton.getAttribute('aria-pressed'), 'true');
  assert.deepEqual(bubbledSelection, ['285A.T', 'SNDK', '6857.T', 'TER'], 'monthly supplement sees the updated company selection during bubbling');
  assertCharts(f, ['285A.T', 'SNDK', '6857.T', 'TER']);
  f.check('TER', false);
  f.stage('packaging').click();
  assert.ok(!f.state().selected.includes('TER'), 'a manual OFF survives addition of another stage');
  assert.ok(!f.state().selected.includes('005930.KS'), 'initial unchecked NAND candidates remain OFF');
  f.stage('nand').click();
  assert.deepEqual(f.state().selectedGroups, ['test', 'packaging']);
  assert.deepEqual(f.state().selected, ['6857.T', '2802.T', '4062.T', '3037.TW', '6146.T']);
  assert.equal(vm.runInContext('JSON.stringify(CAT)', f.context), catalogBefore, 'the saved catalog is unchanged');
});

test('overlapping stages deduplicate companies and roles and retain manual OFF choices', () => {
  const f = fixture();
  f.runAdapter();
  f.stage('ssd').click();
  assert.deepEqual(f.state().selected, ['285A.T', 'SNDK']);
  assert.equal(f.ids.get('fund-choices').querySelectorAll('input').length, 5);
  f.check('SNDK', false);
  f.stage('nand').click();
  assert.deepEqual(f.state().selected, ['285A.T']);
  assert.equal(f.ids.get('fund-choices').querySelectorAll('input').length, 5);
  f.stage('compute').click();
  f.stage('network').click();
  const state = f.state();
  assert.equal(state.symbols.filter(symbol => symbol === 'NVDA').length, 1);
  assert.equal(state.selected.filter(symbol => symbol === 'AVGO').length, 1);
  assert.equal(f.ids.get('fund-choices').querySelectorAll('input').filter(input => input.value === 'NVDA').length, 1);
  const roles = vm.runInContext('GROUPS[activeGroup].roles.AVGO', f.context);
  assert.ok(roles.includes(' ／ '), 'multiple roles are combined');
  f.stage('compute').click();
  assert.ok(f.state().selected.includes('NVDA'), 'shared companies survive removing one of their stages');
  assert.ok(f.state().selected.includes('AVGO'));
});

test('zero stages destroy old charts and selecting a stage again recovers the display', () => {
  const f = fixture();
  f.runAdapter();
  const before = f.savedState();
  f.stage('nand').click();
  assert.deepEqual(f.state(), {selectedGroups: [], symbols: [], selected: []});
  const empty = f.savedState();
  assert.equal(empty.chart, null);
  assert.equal(empty.peChart, null);
  assert.equal(empty.decompChart, null);
  assert.equal(empty.epsCharts.length, 0);
  assert.equal(before.chart.destroyed, true);
  assert.equal(before.peChart.destroyed, true);
  assert.equal(f.ids.get('pe-legend').innerHTML, '');
  assert.equal(f.ids.get('context').textContent, '比較する工程を1つ以上選んでください。');
  f.stage('test').click();
  assertCharts(f, ['6857.T', 'TER']);
});

test('period and checkbox handlers remain active; repeated loads and cleanup are reversible', () => {
  const f = fixture();
  const originalChoose = f.context.chooseGroup;
  const originalRender = f.context.renderChainPicker;
  const originalClick = f.stage('nand').onclick;
  f.runAdapter();
  const api = f.context.ASSET_MULTI_CHAIN;
  f.runAdapter();
  assert.equal(f.context.ASSET_MULTI_CHAIN, api);
  f.stage('test').click();
  assert.deepEqual(f.state().selectedGroups, ['nand', 'test'], 'a second load cannot install a second toggle');
  f.check('TER', false, 'choices');
  const expected = f.state();
  f.document.querySelector('[data-fund-period="3m"]').click();
  assert.deepEqual(f.state(), expected);
  assert.equal(f.ids.get('start').value, '2026-07-02');
  assertCharts(f, ['285A.T', 'SNDK', '6857.T']);
  const copy = api.getState();
  copy.selectedGroups.push('cloud'); copy.symbols.length = 0; copy.selected.length = 0;
  assert.deepEqual(f.state(), expected, 'state inspection returns independent arrays');
  api.cleanup();
  api.cleanup();
  assert.equal(f.context.ASSET_MULTI_CHAIN, undefined);
  assert.equal(f.context.chooseGroup, originalChoose);
  assert.equal(f.context.renderChainPicker, originalRender);
  assert.equal(f.stage('nand').onclick, originalClick);
  assert.equal(f.savedState().activeGroup, 'nand');
  assertCharts(f, ['285A.T', 'SNDK']);
  assert.equal(vm.runInContext('Object.keys(GROUPS).length === CAT.groups.length', f.context), true);
  f.runAdapter();
  f.stage('test').click();
  assert.deepEqual(f.state().selectedGroups, ['nand', 'test']);
});

test('single-stage entry points keep their contract and unsupported pages remain untouched', () => {
  const f = fixture();
  f.runAdapter();
  f.stage('test').click();
  f.context.chooseGroup('packaging');
  assert.deepEqual(f.state().selectedGroups, ['packaging']);
  assert.deepEqual(f.state().selected, ['2802.T', '4062.T', '3037.TW', '6146.T']);
  f.context.chooseGroup('missing');
  assert.deepEqual(f.state().selectedGroups, ['packaging']);
  const other = vm.createContext({window: {}});
  vm.runInContext(adapter, other);
  assert.equal(other.window.ASSET_MULTI_CHAIN, undefined);
});
