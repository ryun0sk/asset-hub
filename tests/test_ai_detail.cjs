const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const ROOT = path.join(__dirname, '..');
const helpers = () => import(pathToFileURL(path.join(ROOT, 'web/ai-detail.js')).href);
const source = fs.readFileSync(path.join(ROOT, 'research/themes/ai-supply-chain/2026-10-03/dashboard.template.html'), 'utf8');

// A small document fixture exercises presentation and listener lifetime without a browser dependency.
class Element {
  constructor(tag = 'div') {
    this.tag = tag;
    this.children = [];
    this.dataset = {};
    this.attributes = {};
    this.listeners = new Map();
    this.hidden = false;
    this.textContent = '';
    this.classList = {add: name => { this.className = name; }};
  }
  append(...elements) { for (const element of elements) element.parentElement = this; this.children.push(...elements); }
  insertBefore(element, before) { element.parentElement = this; this.children.splice(this.children.indexOf(before), 0, element); }
  remove() { if (this.parentElement) this.parentElement.children = this.parentElement.children.filter(child => child !== this); }
  querySelector(selector) {
    const matches = element => selector.startsWith('.') ? element.className === selector.slice(1) : element.tag === selector;
    return this.children.find(matches) || this.children.map(child => child.querySelector(selector)).find(Boolean) || null;
  }
  setAttribute(key, value) { this.attributes[key] = value; }
  addEventListener(event, fn) {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set());
    this.listeners.get(event).add(fn);
  }
  removeEventListener(event, fn) { this.listeners.get(event)?.delete(fn); }
  fire(event, detail) { for (const fn of this.listeners.get(event) || []) fn(detail); }
}

function fixture() {
  const ids = new Map(['panel-chart', 'panel-map', 'panel-guide', 'subpanel-price', 'subpanel-fund', 'val-now', 'val-decomp', 'val-pe', 'val-eps'].map(id => [id, new Element()]));
  const panel = ids.get('panel-chart'), fund = ids.get('subpanel-fund');
  const picker = new Element();
  picker.className = 'chain-picker';
  const controls = new Element();
  controls.className = 'fund-controls';
  controls.value = {period: 'ytd', companies: ['285A.T', 'SNDK']};
  controls.onchange = () => {};
  panel.append(picker, fund);
  fund.append(controls, ...['val-now', 'val-decomp', 'val-pe', 'val-eps'].map(id => ids.get(id)));
  const repeated = Array.from({length: 5}, () => new Element());
  const head = new Element('head');
  const hint = new Element('span');
  hint.textContent = '需要側から、設備・部品・製造・材料へ';
  const events = new Element('document');
  const doc = {
    body: new Element('body'), head, readyState: 'complete',
    createElement: tag => new Element(tag),
    getElementById: id => ids.get(id) || panel.children.find(element => element.id === id),
    querySelectorAll: () => repeated,
    querySelector: selector => selector === '.chain-picker-head span' ? hint : head.children.find(element => 'aiDetailStyle' in element.dataset) || null,
    addEventListener: (...args) => events.addEventListener(...args),
    removeEventListener: (...args) => events.removeEventListener(...args),
  };
  return {doc, ids, picker, controls, repeated, hint, events};
}

test('detail routes select distinct existing valuation panels with their original controls', async () => {
  const {AI_DETAIL_SECTIONS, applyAiDetail} = await helpers();
  const {doc, ids, picker, controls, repeated} = fixture();
  const onchange = controls.onchange, values = structuredClone(controls.value);
  assert.deepEqual(Object.values(AI_DETAIL_SECTIONS).map(section => section.blockId), ['val-decomp', 'val-pe', 'val-eps']);
  for (const [key, metadata] of Object.entries(AI_DETAIL_SECTIONS)) {
    assert.match(source, new RegExp(`id="${metadata.blockId}"`));
    assert.equal(applyAiDetail(doc, key), true);
    assert.equal(doc.body.dataset.aiDetail, key);
    assert.equal(ids.get('panel-chart').hidden, false);
    assert.equal(ids.get('subpanel-fund').hidden, false);
    for (const id of ['val-now', 'val-decomp', 'val-pe', 'val-eps']) assert.equal(ids.get(id).hidden, id !== metadata.blockId, id);
    for (const id of ['panel-map', 'panel-guide', 'subpanel-price']) assert.equal(ids.get(id).hidden, true, id);
    assert.ok(repeated.every(element => element.hidden));
    assert.equal(picker.hidden, false);
    assert.equal(controls.hidden, false);
    assert.equal(controls.onchange, onchange);
    assert.deepEqual(controls.value, values);
    assert.equal(doc.getElementById('ai-detail-heading').querySelector('h2').textContent, metadata.title);
  }
  assert.equal(ids.get('panel-chart').children.filter(element => element.id === 'ai-detail-heading').length, 1);
  assert.match(source, /class="fund-controls"/);
  assert.match(source, /id="fund-choices"/);
  assert.match(source, /id="fund-presets"/);
});

test('unknown routes and incompatible source documents keep the original presentation', async () => {
  const {applyAiDetail} = await helpers();
  const {doc, ids} = fixture();
  assert.equal(applyAiDetail(doc, 'unknown'), false);
  assert.equal(doc.body.dataset.aiDetail, undefined);
  assert.ok([...ids.values()].every(element => !element.hidden));
  ids.delete('val-eps');
  assert.equal(applyAiDetail(doc, 'drivers'), false);
  assert.equal(doc.body.dataset.aiDetail, undefined);
  assert.ok([...ids.values()].every(element => !element.hidden));
});

test('iframe remounts replace listeners and load one self-hosted stylesheet', async () => {
  const {mountAiDetail} = await helpers();
  const {doc} = fixture();
  const frame = new Element('iframe');
  frame.contentDocument = doc;
  frame.contentWindow = {
    requestAnimationFrame: fn => { fn(); return 1; },
    cancelAnimationFrame: () => {},
    Event: class { constructor(type) { this.type = type; } },
    dispatchEvent: () => {},
  };
  const first = mountAiDetail(frame, 'drivers');
  const second = mountAiDetail(frame, 'earnings');
  assert.equal(frame.listeners.get('load').size, 1);
  assert.equal(doc.head.children.length, 2);
  const stylesheet = doc.head.children.find(element => element.tag === 'link');
  const script = doc.head.children.find(element => element.tag === 'script');
  assert.equal(script.src, '/ai-multi-chain.js');
  assert.equal(script.async, false);
  assert.equal(script.listeners.get('load').size, 1);
  assert.equal(stylesheet.href, '/ai-detail.css');
  assert.equal(stylesheet.rel, 'stylesheet');
  assert.equal(stylesheet.listeners.get('load').size, 1);
  assert.equal(doc.body.dataset.aiDetail, 'earnings');
  first();
  assert.equal(frame.listeners.get('load').size, 1, 'old cleanup cannot remove a newer mount');
  second();
  assert.equal(frame.listeners.get('load').size, 0);
  assert.equal(stylesheet.listeners.get('load').size, 0);
  assert.equal(script.listeners.get('load').size, 0);
  assert.equal(doc.head.children.length, 1, 'cleanup removes only its script');
});

test('multi-chain script readiness owns its hint, resize and cleanup without evaluating source strings', async () => {
  const {mountAiDetail} = await helpers();
  const {doc, hint, events} = fixture();
  const frame = new Element('iframe');
  let groups = ['nand'], cleaned = 0, resized = 0;
  const view = {
    requestAnimationFrame: fn => { fn(); return 1; }, cancelAnimationFrame: () => {},
    Event: class { constructor(type) { this.type = type; } }, dispatchEvent: () => { resized++; },
  };
  const api = {getState: () => ({selectedGroups: [...groups]}), cleanup: () => { cleaned++; delete view.ASSET_MULTI_CHAIN; }};
  view.ASSET_MULTI_CHAIN = api;
  frame.contentDocument = doc;
  frame.contentWindow = view;
  const cleanup = mountAiDetail(frame, 'drivers');
  const script = doc.head.children.find(element => element.tag === 'script');
  script.fire('load');
  assert.match(hint.textContent, /複数選択可/);
  assert.equal(events.listeners.get('click').size, 1);
  groups = [];
  events.fire('click', {target: {closest: () => ({})}});
  assert.match(hint.textContent, /工程を1つ以上/);
  assert.ok(resized >= 2);
  cleanup();
  assert.equal(cleaned, 1);
  assert.equal(events.listeners.get('click').size, 0);
  assert.equal(hint.textContent, '需要側から、設備・部品・製造・材料へ');
  script.fire('load');
  assert.equal(cleaned, 1, 'late load cannot remount a disposed script');
});
