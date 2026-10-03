const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const ROOT = path.join(__dirname, '..');
const catalog = JSON.parse(fs.readFileSync(path.join(ROOT, 'research', 'catalog.json'), 'utf8'));
const helpers = () => import(pathToFileURL(path.join(ROOT, 'web', 'catalog.js')).href);
const TYPES = new Set(['html', 'md', 'pdf', 'code']);

test('research/catalog.json has the shared schema', () => {
  assert.equal(catalog.version, 1);
  assert.match(catalog.generatedAt, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/);
  assert.deepEqual(catalog.groups.map(g => [g.id, g.label]), [['themes', 'テーマ'], ['companies', '企業']]);
  const ids = new Set();
  for (const group of catalog.groups) {
    for (const entry of group.entries) {
      assert.equal(entry.kind, group.id === 'themes' ? 'theme' : 'company');
      assert.match(entry.date, /^\d{4}-\d{2}-\d{2}$/);
      assert.equal(entry.id, `${entry.slug}-${entry.date}`);
      assert.ok(!ids.has(entry.id), `duplicate id ${entry.id}`);
      ids.add(entry.id);
      assert.ok(entry.title && !/[[\]()]/.test(entry.title));
      assert.ok(entry.items.length > 0);
      for (const item of entry.items) {
        assert.ok(item.label);
        assert.ok(TYPES.has(item.type), item.type);
        assert.ok(item.path.startsWith(`research/${group.id}/${entry.slug}/${entry.date}/`), item.path);
        assert.ok(fs.statSync(path.join(ROOT, item.path)).isFile(), `${item.path} exists`);
      }
    }
  }
});

test('catalog lists documents only: no working/, qa/, templates, scripts or data files', () => {
  const paths = catalog.groups.flatMap(g => g.entries.flatMap(e => e.items.map(i => i.path)));
  for (const p of paths) {
    assert.doesNotMatch(p, /\/(working|qa)\//);
    assert.doesNotMatch(p, /\.template\.html$|\.py$|\.json$|\.cjs$/);
  }
  const types = Object.fromEntries(catalog.groups.flatMap(g => g.entries.flatMap(e => e.items.map(i => [i.path.split('/').pop(), i.type]))));
  assert.equal(types['valuation.mjs'], 'code');
  assert.equal(types['index.html'], 'html');
  assert.equal(types['report.md'], 'md');
  assert.ok(paths.some(p => /\/sources\/[^/]+\.pdf$/.test(p)));
});

test('titles come from the existing README names', () => {
  const titles = catalog.groups.flatMap(g => g.entries.map(e => e.title));
  for (const title of ['AI関連銘柄・サプライチェーン', 'キオクシア（285A）', '光半導体・光インターコネクト', 'セイワホールディングス（523A）']) assert.ok(titles.includes(title), title);
});

test('hash routes parse and round-trip', async () => {
  const {parseRoute, routeFor, lookup} = await helpers();
  assert.deepEqual(parseRoute(''), {view: 'home'});
  assert.deepEqual(parseRoute('#home'), {view: 'home'});
  assert.deepEqual(parseRoute('#cost'), {view: 'cost'});
  assert.deepEqual(parseRoute('#r/285A-kioxia-2026-09-05/2'), {view: 'research', entryId: '285A-kioxia-2026-09-05', index: 2, anchor: ''});
  assert.deepEqual(parseRoute('#r/x'), {view: 'research', entryId: 'x', index: 0, anchor: ''});
  assert.deepEqual(parseRoute(routeFor('x', 1, 'md-結論')), {view: 'research', entryId: 'x', index: 1, anchor: 'md-結論'});
  assert.deepEqual(parseRoute('#r/a/b/c'), {view: 'home'});
  const first = catalog.groups[0].entries[0];
  const found = lookup(catalog, parseRoute(routeFor(first.id, 1)));
  assert.equal(found.entry.id, first.id);
  assert.equal(found.item.path, first.items[1].path);
  assert.equal(lookup(catalog, parseRoute(routeFor(first.id, 99))).index, 0);
  assert.equal(lookup(catalog, parseRoute('#r/missing/0')), null);
});

test('paths map to routes and safe research URLs', async () => {
  const {routeForPath, fileUrl, stats, latestGroups} = await helpers();
  const entry = catalog.groups[1].entries[0];
  assert.equal(routeForPath(catalog, entry.items[0].path), `#r/${entry.id}/0`);
  assert.equal(routeForPath(catalog, entry.items[0].path, 'md-出典'), `#r/${entry.id}/0/${encodeURIComponent('md-出典')}`);
  assert.equal(routeForPath(catalog, 'README.md'), '#home');
  assert.equal(routeForPath(catalog, 'research/nope.md'), null);
  assert.equal(fileUrl('research/a b/c.pdf'), '/research/a%20b/c.pdf');
  assert.equal(fileUrl('README.md'), null);
  assert.equal(fileUrl('research/../x'), null);
  const s = stats(catalog);
  assert.equal(s.themes, catalog.groups[0].entries.length && new Set(catalog.groups[0].entries.map(e => e.slug)).size);
  const latest = latestGroups(catalog).flatMap(g => g.entries);
  assert.equal(s.documents, latest.flatMap(e => e.items).length);
  assert.equal(s.archives, catalog.groups.flatMap(g => g.entries).length - latest.length);
});

test('versions group dated snapshots of one target; the newest is current, the rest archives', async () => {
  const {versionsOf, isLatest, latestGroups, counterpartIndex, stats} = await helpers();
  const doc = (slug, date, name) => ({label: name, path: `research/companies/${slug}/${date}/${name}`, type: 'md'});
  const make = (slug, date, names) => ({id: `${slug}-${date}`, title: slug, date, kind: 'company', slug, items: names.map(name => doc(slug, date, name))});
  const fixture = {groups: [{id: 'companies', label: '企業', entries: [
    make('a', '2026-10-03', ['report.md', 'README.md']),
    make('b', '2026-09-05', ['README.md']),
    make('a', '2026-09-05', ['README.md', 'report.md', 'valuation.mjs']),
  ]}]};
  const [newA, b, oldA] = fixture.groups[0].entries;
  assert.deepEqual(versionsOf(fixture, oldA).map(e => e.date), ['2026-10-03', '2026-09-05']);
  assert.equal(isLatest(fixture, newA), true);
  assert.equal(isLatest(fixture, oldA), false);
  assert.deepEqual(latestGroups(fixture)[0].entries.map(e => e.id), [newA.id, b.id]);
  assert.equal(counterpartIndex(oldA.items[1], newA), 0, 'report.md keeps the same document');
  assert.equal(counterpartIndex(oldA.items[0], newA), 1, 'README.md keeps the same document');
  assert.equal(counterpartIndex(oldA.items[2], newA), 0, 'missing documents fall back to the first');
  const s = stats(fixture);
  assert.equal(s.companies, 2);
  assert.equal(s.documents, 3, 'only the newest versions count');
  assert.equal(s.archives, 1);
});
