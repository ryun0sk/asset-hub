const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const ROOT = path.join(__dirname, '..');
const catalog = JSON.parse(fs.readFileSync(path.join(ROOT, 'research/catalog.json'), 'utf8'));
const helpers = () => import(pathToFileURL(path.join(ROOT, 'web/workspace.js')).href);
const routing = () => import(pathToFileURL(path.join(ROOT, 'web/catalog.js')).href);
const allEntries = catalog.groups.flatMap(group => group.entries);
const hrefs = html => new Set([...html.matchAll(/href="([^"]+)"/g)].map(match => match[1]));

test('new workflow routes coexist with every dated numeric document route', async () => {
  const {parseRoute, routeFor, lookup} = await routing();
  const {AI_SECTIONS, ASSET_SECTIONS} = await helpers();
  assert.deepEqual(parseRoute('#library'), {view: 'library'});
  for (const section of ['overview', ...AI_SECTIONS.map(item => item.id)]) {
    assert.deepEqual(parseRoute(`#ai/${section}`), {view: 'ai', section});
  }
  for (const cls of Object.keys(ASSET_SECTIONS)) {
    assert.deepEqual(parseRoute(`#a/${cls}`), {view: 'asset', cls});
  }
  for (const entry of allEntries) {
    for (const [index, item] of entry.items.entries()) {
      const route = parseRoute(routeFor(entry.id, index, 'md-出典'));
      assert.deepEqual(route, {view: 'research', entryId: entry.id, index, anchor: 'md-出典'});
      const found = lookup(catalog, route);
      assert.equal(found.entry.id, entry.id);
      assert.equal(found.index, index);
      assert.deepEqual(found.item, item);
    }
  }
});

test('AI comparison routes use the newest saved HTML and its named source views', async () => {
  const {AI_SECTIONS, aiEntry, aiDocument} = await helpers();
  const {itemUrl, versionsOf} = await routing();
  const current = aiEntry(catalog);
  assert.equal(current.id, versionsOf(catalog, current)[0].id);
  for (const section of AI_SECTIONS.filter(item => item.view)) {
    const found = aiDocument(catalog, section.id);
    assert.equal(found.entry.id, current.id, section.id);
    assert.equal(found.item.type, 'html', section.id);
    assert.equal(found.item.view, section.view, section.id);
    assert.equal(found.item.path, `research/themes/ai-supply-chain/${current.date}/index.html`);
    assert.equal(itemUrl(found.item), `/${found.item.path}?view=${section.view}`);
  }
  for (const section of ['overview', 'reports', 'sources', 'missing']) assert.equal(aiDocument(catalog, section), null);

  // A newer saved version must take precedence without changing the dated URLs.
  const fixture = structuredClone(catalog);
  const future = structuredClone(current);
  future.date = '2026-11-01';
  future.id = `${future.slug}-${future.date}`;
  future.items.forEach(item => { item.path = item.path.replace(current.date, future.date); });
  fixture.groups.find(group => group.id === 'themes').entries.push(future);
  for (const section of AI_SECTIONS.filter(item => item.view)) assert.equal(aiDocument(fixture, section.id).entry.id, future.id);
});

test('old snapshots retain their own research identity and current AI documents map to their workflow', async () => {
  const {aiSectionForResearch, aiEntry} = await helpers();
  const {versionsOf} = await routing();
  assert.equal(aiSectionForResearch(catalog, null), '');
  const current = aiEntry(catalog);
  const expected = {fund: 'valuation', map: 'map', guide: 'guide', price: 'price'};
  for (const [index, item] of current.items.entries()) {
    assert.equal(aiSectionForResearch(catalog, {entry: current, item, index}), expected[item.view] || (item.path.endsWith('/report.md') ? 'reports' : 'sources'));
  }
  for (const entry of allEntries.filter(entry => versionsOf(catalog, entry)[0].id !== entry.id)) {
    for (const [index, item] of entry.items.entries()) assert.equal(aiSectionForResearch(catalog, {entry, item, index}), '', entry.id);
  }
  const unrelated = allEntries.find(entry => entry.kind === 'company');
  assert.ok(unrelated, 'catalog includes an unrelated company research entry');
  assert.equal(aiSectionForResearch(catalog, {entry: unrelated, item: unrelated.items[0]}), '');
});

test('library keeps all current documents and every archived version reachable', async () => {
  const {renderResearchLibrary, newestEntries} = await helpers();
  const {routeFor, versionsOf} = await routing();
  const links = hrefs(renderResearchLibrary(catalog));
  const latest = newestEntries(catalog);
  for (const entry of latest) {
    for (const index of entry.items.keys()) assert.ok(links.has(routeFor(entry.id, index)), `${entry.id}/${index}`);
    for (const older of versionsOf(catalog, entry).slice(1)) assert.ok(links.has(routeFor(older.id)), older.id);
  }
  const currentIds = new Set(latest.map(entry => entry.id));
  for (const older of allEntries.filter(entry => !currentIds.has(entry.id))) assert.ok(links.has(routeFor(older.id)), older.id);
});

test('AI reports and sources retain the related documents and archived source files', async () => {
  const {renderAiHub, aiEntry, newestEntries} = await helpers();
  const {routeFor, versionsOf} = await routing();
  const reports = hrefs(renderAiHub(catalog, 'reports'));
  const related = newestEntries(catalog).filter(entry => entry.kind === 'company' || ['ai-supply-chain', 'ai-business-quality', 'ai-year-end-comparison', 'photonics'].includes(entry.slug));
  for (const entry of related) {
    for (const index of entry.items.keys()) assert.ok(reports.has(routeFor(entry.id, index)), `${entry.id}/${index}`);
  }
  const current = aiEntry(catalog), sources = hrefs(renderAiHub(catalog, 'sources'));
  for (const [index, item] of current.items.entries()) {
    if (!item.view && !item.path.endsWith('/report.md')) assert.ok(sources.has(routeFor(current.id, index)));
  }
  for (const archived of versionsOf(catalog, current).slice(1)) {
    for (const index of archived.items.keys()) assert.ok(sources.has(routeFor(archived.id, index)), `${archived.id}/${index}`);
  }
  assert.ok(sources.has('#library'));
});

test('library search combines normalized words and kind without including superseded versions', async () => {
  const {filterResearch, newestEntries} = await helpers();
  const latest = newestEntries(catalog);
  assert.deepEqual(filterResearch(catalog).map(entry => entry.id), latest.map(entry => entry.id));
  assert.deepEqual(filterResearch(catalog, {query: '２８５Ａ　キオクシア'}).map(entry => entry.slug), ['285A-kioxia']);
  assert.deepEqual(filterResearch(catalog, {query: 'TSLA テスラ', kind: 'company'}).map(entry => entry.slug), ['TSLA-tesla']);
  assert.equal(filterResearch(catalog, {query: 'TSLA', kind: 'theme'}).length, 0);
  assert.equal(filterResearch(catalog, {query: '一致しない検索語'}).length, 0);
  assert.equal(filterResearch(catalog, {query: '  ', kind: 'theme'}).length, latest.filter(entry => entry.kind === 'theme').length);
  assert.equal(filterResearch(catalog, {query: '285a'}).length, 1);
});

test('hub labels and library results escape catalog text before rendering', async () => {
  const {renderHomeHub, renderResearchLibrary, renderAiHub, filterResearch} = await helpers();
  const fixture = structuredClone(catalog);
  const entry = fixture.groups.find(group => group.id === 'themes').entries.find(entry => entry.slug === 'ai-supply-chain');
  entry.title = '<img src=x onerror="alert(1)"> & "見出し"';
  entry.items[0].label = '<script>alert(1)</script> & "資料"';
  assert.equal(filterResearch(fixture, {query: 'onerror'}).length, 1);
  for (const html of [renderHomeHub(fixture), renderResearchLibrary(fixture), renderAiHub(fixture, 'reports')]) {
    assert.doesNotMatch(html, /<img|<script/);
    if (html.includes('onerror')) assert.match(html, /&lt;img src=x onerror=&quot;alert\(1\)&quot;&gt; &amp; &quot;見出し&quot;/);
  }
  const library = renderResearchLibrary(fixture);
  assert.match(library, /&lt;script&gt;alert\(1\)&lt;\/script&gt; &amp; &quot;資料&quot;/);
});

test('home exposes the two primary entrances and AI overview lists each task once', async () => {
  const {renderHomeHub, renderAiHub, AI_SECTIONS, ASSET_SECTIONS} = await helpers();
  const home = renderHomeHub(catalog);
  assert.match(home, /<h2>保有・推移<\/h2>/);
  assert.match(home, /<h2>AI関連銘柄・サプライチェーン<\/h2>/);
  const links = hrefs(home);
  for (const section of Object.keys(ASSET_SECTIONS)) assert.ok(links.has(`#a/${section}`));
  for (const route of ['#ai/valuation', '#ai/price', '#ai/overview', '#library']) assert.ok(links.has(route));
  const overview = renderAiHub(catalog);
  for (const section of AI_SECTIONS) assert.equal([...overview.matchAll(new RegExp(`href="#ai/${section.id}"`, 'g'))].length, 1);
});

test('missing catalogs and unfamiliar routes fail safely without losing dated routing', async () => {
  const {parseRoute, lookup} = await routing();
  const {aiEntry, aiDocument, aiSectionForResearch, filterResearch, renderHomeHub, renderAiHub, renderResearchLibrary} = await helpers();
  assert.equal(aiEntry(null), undefined);
  assert.equal(aiDocument(null, 'valuation'), null);
  assert.equal(aiSectionForResearch(null, null), '');
  assert.deepEqual(filterResearch(null), []);
  assert.doesNotThrow(() => renderHomeHub(null));
  assert.doesNotThrow(() => renderResearchLibrary(null));
  assert.match(renderAiHub(null), /まだありません/);
  assert.equal(renderAiHub(catalog, 'unknown'), renderAiHub(catalog, 'overview'));
  assert.equal(lookup(catalog, parseRoute('#r/missing/3')), null);
  for (const route of ['#ai/', '#ai/drivers/more', '#library/more', '#ai/<script>']) assert.deepEqual(parseRoute(route), {view: 'home'});
});
