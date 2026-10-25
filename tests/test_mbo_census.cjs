const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const ui = () => import(pathToFileURL(path.join(__dirname, '../web/mbo-census.js')).href);
function fixture() {
  const cases = Array.from({length: 61}, (_, index) => ({case_id: `episode-${index}`, code: index < 2 ? '3408' : String(1000 + index), name: `企業${index}`, first_formal_mbo_announcement_date: index === 60 ? null : `202${index % 2 + 1}-02-08`, public_motives: index === 60 ? [] : [{text: '海外展開の先行投資'}], observed_obstacles: index === 0 ? [{text: '応募が下限に満たなかった'}] : [], outcome: {summary: '原本で結果を確認'}, census: {year: index === 60 ? 2026 : 2021 + index % 2, status: index === 0 ? 'failed' : index === 60 ? 'unknown' : 'succeeded', verification: {announcement: index === 60 ? 'unknown' : 'verified', motive: index === 60 ? 'unknown' : 'verified', outcome: index === 60 ? 'unknown' : 'verified'}, motive_categories: index === 60 ? [] : ['growth_investment']}}));
  return {schema_version: 1, as_of: '2026-10-18', start_date: '2021-01-01', cases, company_count: 60, source_count: 61, verified: {announcement: 60, motive: 60, outcome: 60}, yearly: [{year: 2021, episodes: 30, companies: 30, tse_episodes: 30, tse_benchmark: 17, announcement_verified: 30, motive_verified: 30}, {year: 2026, episodes: 1, companies: 1, tse_episodes: 1, announcement_verified: 0, motive_verified: 0}], motive_labels: {growth_investment: '成長投資・海外展開'}, motive_counts: {growth_investment: 60}, exclusions: [], coverage_notes: [], cautions: []};
}

test('census filters all episodes before pagination and keeps repeated-company attempts distinct', async () => {
  const {censusSubset, renderCensusResults} = await ui(), data = fixture();
  assert.equal(censusSubset(data, {query: '３４０８'}).length, 2);
  assert.equal(censusSubset(data, {status: 'failed'}).length, 1);
  assert.equal(censusSubset(data, {year: '2026', verification: 'pending'})[0].case_id, 'episode-60');
  const filtered = renderCensusResults(data, {query: '企業60', page: 1});
  assert.match(filtered, /企業60/);
  assert.match(filtered, /未確認/);
  const first = renderCensusResults(data, {page: 1}), last = renderCensusResults(data, {page: 3});
  assert.equal((first.match(/data-census-case=/g) || []).length, 25);
  assert.equal((last.match(/data-census-case=/g) || []).length, 11);
  assert.match(last, /企業60/);
  assert.doesNotMatch(first, /data-census-case="episode-60"/);
});

test('coverage distinguishes nationwide episodes, the TSE benchmark, read reasons and a partial 2026 period', async () => {
  const {renderCensusOverview} = await ui();
  const html = renderCensusOverview(fixture());
  for (const text of ['61件', '60社', '60 / 61', '全国台帳', '東証公式', '2026（10/18まで）', '複数の理由', '予測力や因果効果の推定ではありません', '応募下限未達という直接の結果']) assert.ok(html.includes(text), text);
  assert.doesNotMatch(html, /成立確率|予測精度は\d|的中率は\d/);
});

test('census source titles, company text, reasons and exclusions cannot inject markup or local paths', async () => {
  const {renderCensusOverview, renderCensusResults, mountMboCensus} = await ui(), data = fixture();
  data.cases[0].name = '<img src=x onerror="bad"> /Users/ryu/raw.pdf';
  data.cases[0].observed_obstacles[0].text = '<script>bad</script>';
  data.exclusions = [{name: '<svg onload=bad>', reason: '/private/raw.pdf', sources: [{url: 'javascript:alert(1)', title: '<script>source</script>'}]}];
  const host = {innerHTML: '', querySelector: () => null, addEventListener() {}, removeEventListener() {}};
  mountMboCensus(host, {data, renderDetail: () => ''});
  const html = renderCensusOverview(data) + renderCensusResults(data, {}) + host.innerHTML;
  assert.doesNotMatch(html, /<script|<img|<svg|href="javascript:|\/Users\/|\/private\//);
  assert.match(html, /&lt;script&gt;/);
});

test('mounted census preserves filter and selected episode state and removes all delegated listeners', async () => {
  const {mountMboCensus} = await ui(), data = fixture(), handlers = new Map();
  const results = {innerHTML: ''}, detail = {innerHTML: '', querySelector: () => ({focus() {}})};
  const host = {innerHTML: '', querySelector: selector => selector === '[data-census-results]' ? results : detail, addEventListener: (name, cb) => handlers.set(name, cb), removeEventListener: (name, cb) => { if (handlers.get(name) === cb) handlers.delete(name); }};
  const mounted = mountMboCensus(host, {data, renderDetail: item => item.case_id});
  handlers.get('input')({target: {closest: selector => selector === '[data-census-filter]' ? {dataset: {censusFilter: 'query'}, value: '企業60'} : null}});
  assert.match(results.innerHTML, /企業60/);
  handlers.get('click')({target: {closest: selector => selector === '[data-census-case]' ? {dataset: {censusCase: 'episode-60'}} : null}});
  assert.equal(detail.innerHTML, 'episode-60');
  assert.equal(mounted.getState().selectedCase, 'episode-60');
  assert.equal(mounted.getState().query, '企業60');
  mounted.destroy();
  assert.equal(handlers.size, 0);
});
