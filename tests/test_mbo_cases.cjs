const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const ROOT = path.join(__dirname, '..');
const ui = () => import(pathToFileURL(path.join(ROOT, 'web/mbo-cases.js')).href);
const saved = JSON.parse(fs.readFileSync(path.join(ROOT, 'research/themes/mbo-evaluation/2026-10-18/cases-research.json'), 'utf8'));
const lessons = {'7816': ['長期投資の説明とMBOの意思を区別する。', '初報後の検討確認は独立予測に数えない。'], '7523': ['初回と再試行を分ける。']};

test('saved comparison shows all eight cases and source scope without claiming frequency or predictive precision', async () => {
  const {renderMboCases, caseSubset, validateCaseData} = await ui();
  const html = renderMboCases(saved, lessons);
  assert.equal(caseSubset(saved).length, 8);
  for (const item of saved.cases) assert.ok(html.includes(item.name), item.name);
  for (const text of ['ケース集は2026-10-18の保存版', '8社表示 / 保存版 8社', '31件の一次資料', '発生頻度・成立率・予測精度は未検証', '目的抽出', '現評価への反映', '2020年公表の補助例']) assert.ok(html.includes(text), text);
  assert.throws(() => validateCaseData({...saved, schema_version: 2}), /保存データ形式/);
  assert.throws(() => validateCaseData({...saved, sources: []}), /保存データ形式/);
});

test('published collection includes INFORICH as a searchable reference while preserving the original eight cases', async () => {
  const {MBO_CASE_DATA: data, MBO_CASE_LESSONS: notes} = await import(pathToFileURL(path.join(ROOT, 'web/mbo-case-data.js')).href);
  const {caseSubset, renderMboCases, renderCaseDetail} = await ui();
  assert.equal(data.cases.length, 9);
  assert.deepEqual(data.cases.filter(item => item.code !== '9338'), saved.cases);
  const reference = data.cases.find(item => item.code === '9338');
  assert.equal(data.cases[0].code, '9338', 'the added reference is visible at the top of the list');
  assert.deepEqual(caseSubset(data, {query: 'インフォリッチ'}).map(item => item.code), ['9338']);
  assert.equal(reference.transaction_class, 'formal_mbo_tob_succeeded_and_delisted');
  assert.equal(reference.outcome.actual_delisting_date, '2026-06-16');
  assert.equal(reference.outcome.delisting_status, 'completed');
  const html = renderMboCases(data, notes), detail = renderCaseDetail(data, reference, notes);
  for (const text of ['9社表示 / 保存版 9社', '全MBO案件を網羅した一覧ではありません', '着想源の参考事例']) assert.ok(html.includes(text), text);
  assert.match(detail, /配点調整や的中率の評価には使いません/);
  assert.match(detail, /上場廃止（実績）/);
  assert.doesNotMatch(detail, /上場廃止（予定・未完了）/);
  assert.ok(notes['9338'].length > 0);
  assert.ok(reference.first_date_source_ids.every(id => data.sources[id]));
  assert.ok(reference.outcome.source_ids.every(id => data.sources[id]));
});

test('result filters keep retry, different buyer and unlaunched funding proposal separate and searches normalize Japanese', async () => {
  const {caseSubset, renderMboCases} = await ui();
  assert.deepEqual(caseSubset(saved, {query: '７８１６　スノーピーク'}).map(item => item.code), ['7816']);
  assert.equal(caseSubset(saved, {result: 'succeeded'}).length, 4);
  assert.deepEqual(caseSubset(saved, {result: 'retry'}).map(item => item.code), ['7523']);
  assert.deepEqual(caseSubset(saved, {result: 'different'}).map(item => item.code), ['4464', '3751']);
  assert.deepEqual(caseSubset(saved, {result: 'funding'}).map(item => item.code), ['3382']);
  assert.match(renderMboCases(saved, lessons, {query: '存在しない企業'}), /条件に合う過去事例はありません/);
  const copy = saved.cases.map(item => item.case_id);
  caseSubset(saved, {result: 'different'});
  assert.deepEqual(saved.cases.map(item => item.case_id), copy);
});

test('Snow Peak separates February 16 report acknowledgment from formal February 20 MBO announcement', async () => {
  const {renderCaseDetail} = await ui();
  const html = renderCaseDetail(saved, saved.cases.find(item => item.code === '7816'), lessons);
  for (const text of ['2024-02-16', '2024-02-20', '最初の公式確認', '正式MBOの公表', '報道後の公式な検討確認', '初報前の独立予測とは区別', '初報より前の独立資料', '未確認・事前予測の実績には未採用', '長期投資の説明とMBOの意思を区別する。', '非公開化を検討しているのは事実', 'PDF p1']) assert.ok(html.includes(text), text);
  assert.match(html, /href="https:\/\/ir\.snowpeak\.co\.jp\/news\/files\/140120240216538923\.pdf" target="_blank" rel="noopener noreferrer"/);
});

test('future delisting and meeting dates are planned while prior failed and successful TOBs retain their distinct outcomes', async () => {
  const {renderCaseDetail} = await ui();
  const art = renderCaseDetail(saved, saved.cases.find(item => item.code === '7523'), lessons);
  for (const text of ['初回MBO不成立 → 再TOB成立', '2025-10-29', '2026-08-26', '2026-09-01', '2026-10-20', '2026-11-11', '上場廃止（予定・未完了）', '保存基準日時点の予定', '予定日を完了実績には数えていません']) assert.ok(art.includes(text), text);
  assert.doesNotMatch(art, /上場廃止（実績）/);
  const soft = renderCaseDetail(saved, saved.cases.find(item => item.code === '4464'), lessons);
  assert.match(soft, /MBO不成立 → 別買収・非公開化計画/);
  assert.match(soft, /2026-12-17 · 保存基準日時点の予定/);
  const seven = renderCaseDetail(saved, saved.cases.find(item => item.code === '3382'), lessons);
  assert.match(seven, /創業家提案・資金未達（TOB未開始）/);
  assert.match(seven, /正式MBOの実施公表なし/);
  assert.doesNotMatch(seven, /<dt>TOB結果公表/);
  const jag = renderCaseDetail(saved, saved.cases.find(item => item.code === '3751'), lessons);
  assert.match(jag, /補助例/);
  assert.match(jag, /MBO不成立 → 別買収者/);
});

test('source publication dates remain unknown when null, and all case, lesson and source strings are escaped', async () => {
  const {renderMboCases, renderCaseDetail} = await ui();
  const taisho = renderCaseDetail(saved, saved.cases.find(item => item.code === '4581'), lessons);
  assert.match(taisho, /大正製薬 · 公表 未確認 · HTML冒頭/);
  const data = structuredClone(saved), item = data.cases[0];
  item.name = '<img src=x onerror="bad">'; item.case_id = 'x" onclick="bad'; item.actors = '/Users/ryu/private.txt';
  item.public_motives[0].text = '<script>motive</script>'; item.public_motives[0].locator = '/tmp/private.txt';
  item.outcome.summary = '<svg onload="bad">'; item.classification_cautions.push('/private/raw.pdf');
  data.sources['taisho-start'].url = 'javascript:alert(1)';
  data.sources['taisho-start'].title = '<script>source</script>';
  data.sources['taisho-start'].short_quote = '<img src=x> /Users/ryu/quote.pdf';
  const html = renderMboCases(data, {[item.code]: ['<script>lesson</script>']}, {selectedCase: item.case_id, query: '<img'});
  assert.match(html, /&lt;script&gt;motive/);
  assert.match(html, /&lt;script&gt;lesson/);
  assert.match(html, /&lt;script&gt;source/);
  assert.doesNotMatch(html, /<img|<script|<svg|\sonclick="|\sonerror="|href="javascript:|\/Users\/|\/private\/|\/tmp\//);
});

test('mounted case filters and selected detail retain state and all delegated listeners are removed on destroy', async () => {
  const {mountMboCases} = await ui();
  const listeners = new Map(), detail = {innerHTML: '', querySelector: () => ({focus() { this.focused = true; }})};
  const host = {innerHTML: '', ownerDocument: {}, addEventListener: (name, callback) => listeners.set(name, callback), removeEventListener: (name, callback) => { if (listeners.get(name) === callback) listeners.delete(name); }, querySelector: selector => selector === '[data-case-detail]' ? detail : null};
  const mounted = mountMboCases(host, {data: saved, lessons});
  assert.equal(listeners.size, 3);
  const selected = saved.cases.find(item => item.code === '7523');
  listeners.get('click')({target: {closest: selector => selector === '[data-mbo-case]' ? {dataset: {mboCase: selected.case_id}} : null}});
  assert.equal(mounted.getState().selectedCase, selected.case_id);
  assert.match(detail.innerHTML, /アールビバン/);
  listeners.get('input')({target: {closest: selector => selector === '[data-case-query]' ? {value: '７５２３'} : null}});
  assert.equal(mounted.getState().query, '７５２３');
  assert.match(host.innerHTML, /1社表示/);
  mounted.destroy();
  assert.equal(listeners.size, 0);
});
