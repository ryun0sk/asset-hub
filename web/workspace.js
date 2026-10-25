import {latestGroups, routeFor, versionsOf} from './catalog.js';
const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[ch]));
export const ASSET_SECTIONS = Object.freeze({
  summary: {label: '資産サマリー', description: '今の資産配分と、前週からの増減を確認'},
  all: {label: '資産推移', description: '資産クラス・銘柄の推移を、期間と表示形式を切り替えて比較'},
  holdings: {label: '保有一覧', description: '口座・銘柄・数量・評価額・評価損益を確認'},
  policy: {label: '全体方針', description: '資産配分・資金移動・購入スケジュールを確認'},
});
export const MBO_SECTIONS = Object.freeze({
  candidates: {label: '候補', description: '保存済みの候補・独自の企業価値・不足項目を確認する'},
  events: {label: '公表案件', description: '公表済み・検討報道・成立・撤回を候補と分けて確認する'},
  cases: {label: '過去事例', description: 'MBOの動機・成立と不成立の経緯・評価軸への示唆を根拠資料と確認する'},
  history: {label: '週次履歴', description: '前回からの変化と、保存された調査結果を確認する'},
});

// Keep a mounted panel when switching MBO subviews. A separate mount slot per
// visit also keeps late async work from an old panel out of the current page.
export function createMboPanelLifecycle(host, mount, {onError = () => {}} = {}) {
  let instance = null, slot = null, currentSection = '';
  return {
    show(section = 'candidates') {
      const next = MBO_SECTIONS[section] ? section : 'candidates';
      if (instance) {
        if (currentSection !== next) instance.setView(next);
        currentSection = next;
        return instance;
      }
      slot = host.ownerDocument.createElement('div');
      host.replaceChildren(slot);
      try {
        const mounted = mount(slot, next);
        if (!mounted || typeof mounted.setView !== 'function' || typeof mounted.destroy !== 'function') throw Error('Invalid MBO panel');
        instance = mounted;
        currentSection = next;
        if (mounted.ready && typeof mounted.ready.then === 'function') {
          Promise.resolve(mounted.ready).catch(() => { if (instance === mounted) onError(); });
        }
        return mounted;
      } catch {
        host.replaceChildren();
        slot = null;
        onError();
        return null;
      }
    },
    leave() {
      if (!instance && !slot) return;
      const previous = instance;
      instance = null;
      slot = null;
      currentSection = '';
      try { previous?.destroy(); } finally { host.replaceChildren(); }
    },
  };
}
export const AI_SECTIONS = Object.freeze([
  {id: 'forward', label: '将来利益・割安度', group: '銘柄を比較', description: '46社の2028〜2029年利益・EPSと、現在株価に対する価格余地を比較する'},
  {id: 'valuation', label: 'EPS・PER一覧', group: '銘柄を比較', description: '発電3社を含む46銘柄の実績・会社予想・今期／来期予想を一覧で比べる', view: 'fund'},
  {id: 'price', label: '株価の比較', group: '銘柄を比較', description: '同じ工程の銘柄を、期間をそろえて比べる', view: 'price'},
  {id: 'drivers', label: '株価変化の要因', group: '銘柄を比較', description: '株価の変化をEPSとPERの寄与に分けて確認する', view: 'fund'},
  {id: 'multiples', label: 'PERの推移', group: '銘柄を比較', description: '7銘柄の実績月次表（TTM・半年年換算）と保存版のPERグラフ', view: 'fund'},
  {id: 'eps', label: 'EPSの推移', group: '銘柄を比較', description: '直近12か月の実績EPSを、現地通貨と開始時点＝100で比較する', view: 'fund'},
  {id: 'earnings', label: 'EPS予想・決算', group: '銘柄を比較', description: '利益の実績・予想と、次の決算日を確認する', view: 'fund'},
  {id: 'map', label: '調達の流れ', group: '事業を理解', description: '設備・部品・製造・材料のつながりをたどる', view: 'map'},
  {id: 'guide', label: 'AI時代の機能整理', group: '事業を理解', description: 'NAND・DRAM・HBM・GPUの役割と違いを確認する', view: 'guide'},
  {id: 'reports', label: '比較・考察レポート', group: '考察と根拠', description: '工程別の見通し・事業の強さ・個別企業の調査を読む'},
  {id: 'sources', label: '調査の前提・出典', group: '考察と根拠', description: '数値の基準・出典・関連資料・過去の版を確認する'},
]);
export const aiRoute = section => `#ai/${section}`;
export const newestEntries = catalog => latestGroups(catalog).flatMap(group => group.entries);
export const aiEntry = catalog => newestEntries(catalog).find(entry => entry.kind === 'theme' && entry.slug === 'ai-supply-chain');
export function aiDocument(catalog, section) {
  const entry = aiEntry(catalog), definition = AI_SECTIONS.find(item => item.id === section);
  const index = entry?.items.findIndex(item => item.view === definition?.view && item.type === 'html');
  return definition?.view && index >= 0 ? {entry, item: entry.items[index], index} : null;
}
export function aiSectionForResearch(catalog, found) {
  if (!found || versionsOf(catalog, found.entry)[0]?.id !== found.entry.id) return '';
  if (found.entry.slug === 'ai-supply-chain') {
    if (found.item.view === 'fund') return 'valuation';
    if (['map', 'guide', 'price'].includes(found.item.view)) return found.item.view;
    return found.item.path.endsWith('/report.md') ? 'reports' : 'sources';
  }
  return ['ai-business-quality', 'ai-year-end-comparison', 'photonics'].includes(found.entry.slug) ? 'reports' : '';
}
export function filterResearch(catalog, {query = '', kind = ''} = {}) {
  const words = query.normalize('NFKC').toLocaleLowerCase('ja-JP').trim().split(/\s+/).filter(Boolean);
  return newestEntries(catalog).filter(entry => (!kind || entry.kind === kind) && words.every(word => `${entry.title} ${entry.slug} ${entry.items.map(item => item.label).join(' ')}`.normalize('NFKC').toLocaleLowerCase('ja-JP').includes(word)));
}
const shortcut = (href, label, description = '') => `<a class="hub-shortcut" href="${esc(href)}"><strong>${esc(label)}<span aria-hidden="true">→</span></strong>${description ? `<small>${esc(description)}</small>` : ''}</a>`;
function documentCard(catalog, entry, description = '') {
  const main = entry.items.findIndex(item => item.path.endsWith('/report.md'));
  const index = main >= 0 ? main : 0, older = versionsOf(catalog, entry).slice(1);
  return `<article class="hub-document"><div class="hub-document-heading"><h3><a href="${routeFor(entry.id, index)}">${esc(entry.title)}</a></h3><span class="hub-date">${esc(entry.date)}</span></div>${description ? `<p>${esc(description)}</p>` : ''}
    <div class="hub-document-links"><a class="hub-primary-link" href="${routeFor(entry.id, index)}">調査を読む →</a><details><summary>資料 ${entry.items.length}件${older.length ? `・過去 ${older.length}版` : ''}</summary><div class="hub-link-list">${entry.items.map((item, i) => `<a href="${routeFor(entry.id, i)}">${esc(item.label)}</a>`).join('')}${older.map(version => `<a href="${routeFor(version.id)}">過去の版 · ${esc(version.date)}</a>`).join('')}</div></details></div></article>`;
}
export function renderHomeHub(catalog) {
  const ai = aiEntry(catalog), recent = newestEntries(catalog).sort((a, b) => b.date.localeCompare(a.date)).slice(0, 3);
  return `<div class="hub-home-grid"><section class="hub-feature"><span class="hub-kicker">PORTFOLIO</span><h2>保有・推移</h2><p>資産の現在地、値動き、保有明細、方針を目的別に確認できます。</p><div class="hub-shortcuts">${Object.entries(ASSET_SECTIONS).map(([key, item]) => shortcut(`#a/${key}`, item.label, item.description)).join('')}</div></section>
    <section class="hub-feature"><span class="hub-kicker">AI RESEARCH</span><h2>AI関連銘柄・サプライチェーン</h2><p>まず銘柄を比較し、気になる会社の利益・事業・調査根拠へ進めます。</p><div class="hub-shortcuts">${shortcut(aiRoute('forward'), '将来利益・割安度', '46社の2028〜2029年利益と現在株価を比較')}${shortcut(aiRoute('valuation'), 'EPS・PER一覧', '実績・会社予想・アナリスト予想を比較')}${shortcut(aiRoute('price'), '株価の比較', '同じ工程の銘柄を比較')}${shortcut(aiRoute('overview'), 'AI調査の全体像', '比較・事業理解・レポートの入口を一覧')}</div><p class="hub-meta">${ai ? `保存版 ${esc(ai.date)} · 数値の時点は各画面に表示` : '調査資料の登録待ち'}</p></section></div>
    <section class="hub-section"><div class="hub-section-heading"><div><h2>MBO調査</h2><p>保存済みの候補と根拠、独自の価値評価、週次の変化を確認できます。</p></div></div><div class="hub-shortcuts">${Object.entries(MBO_SECTIONS).map(([section, item]) => shortcut(`#mbo/${section}`, item.label, item.description)).join('')}</div></section>
    <section class="hub-section"><div class="hub-section-heading"><div><h2>最近の調査</h2><p>すべての資料は調査ライブラリから探せます。</p></div><a class="hub-primary-link" href="#library">調査ライブラリへ →</a></div><div class="hub-document-grid">${recent.map(entry => documentCard(catalog, entry)).join('')}</div></section>`;
}
export function renderAiHub(catalog, section = 'overview') {
  const entry = aiEntry(catalog);
  if (!entry) return '<p class="empty">AIサプライチェーンの調査資料はまだありません。</p>';
  if (section === 'reports') {
    const descriptions = {'ai-valuation-ranking': '46社の2028〜2029年利益・EPSと現在株価を、独自シナリオで比較。', 'ai-forward-valuation': '中心8社の市場・費用からの詳細試算と、取り分固定・現金価値の感応度。', 'ai-supply-chain': '工程別の需給・見通し・リスクと、前回の調査からの変化。', 'ai-business-quality': '22銘柄の事業の強さと、株価上昇に必要な条件。', 'ai-year-end-comparison': '日本12・海外10銘柄の年末までの比較材料と組み合わせ。', photonics: '光半導体・光インターコネクトの考察と株価比較。'};
    const themes = newestEntries(catalog).filter(item => item.slug in descriptions), companies = newestEntries(catalog).filter(item => item.kind === 'company');
    return `<section class="hub-section"><div class="hub-section-heading"><div><h2>テーマ別の考察</h2><p>比較表の数字を、事業・需給・リスクから掘り下げる。</p></div></div><div class="hub-document-grid">${themes.map(item => documentCard(catalog, item, descriptions[item.slug])).join('')}</div></section>
      <section class="hub-section"><div class="hub-section-heading"><div><h2>個別企業の調査</h2><p>投資判断・株価の変動要因・評価モデル・元資料。</p></div></div><div class="hub-document-grid">${companies.map(item => documentCard(catalog, item)).join('')}</div></section>`;
  }
  if (section === 'sources') {
    const docs = entry.items.map((item, i) => ({item, i})).filter(({item}) => !item.view && !item.path.endsWith('/report.md'));
    return `<section class="hub-feature"><h2>比較表の基準と出典</h2><p>保存版 ${esc(entry.date)}。実績・会社予想・外部予想・独自計算の区別、通貨と株式分割の補正、予想の取得範囲を確認できます。</p><div class="hub-shortcuts">${docs.map(({item, i}) => shortcut(routeFor(entry.id, i), item.label)).join('')}</div></section>
      <section class="hub-section"><div class="hub-section-heading"><div><h2>過去の版</h2><p>当時の調査内容をそのまま確認できます。</p></div></div><div class="hub-document-grid">${versionsOf(catalog, entry).slice(1).map(item => documentCard(catalog, item)).join('') || '<p class="hub-meta">過去の版はまだありません。</p>'}</div></section><p class="hub-meta"><a href="#library">全テーマ・全企業の資料は調査ライブラリへ →</a></p>`;
  }
  return `<p class="hub-snapshot">保存版 ${esc(entry.date)} · 記載された株価・予想・見解は各調査日時点のものです。</p><div class="hub-ai-grid">${['銘柄を比較', '事業を理解', '考察と根拠'].map(group => `<section class="hub-feature"><span class="hub-kicker">${group === '銘柄を比較' ? 'COMPARE' : group === '事業を理解' ? 'UNDERSTAND' : 'RESEARCH'}</span><h2>${esc(group)}</h2><div class="hub-shortcuts">${AI_SECTIONS.filter(item => item.group === group).map(item => shortcut(aiRoute(item.id), item.label, item.description)).join('')}</div></section>`).join('')}</div>`;
}
export function renderResearchLibrary(catalog) {
  return `<section class="hub-library"><div class="hub-filters"><label>資料を検索<input type="search" data-library-query placeholder="企業名・テーマ・証券コード" autocomplete="off"></label><label>区分<select data-library-kind><option value="">すべて</option><option value="theme">テーマ</option><option value="company">企業</option><option value="crypto">仮想通貨</option></select></label><span data-library-count aria-live="polite">${newestEntries(catalog).length}件</span></div><p class="hub-snapshot">最新版を対象別に掲載。各カードの「資料」から元資料と過去の版を開けます。</p><div class="hub-document-grid" data-library-results>${newestEntries(catalog).map(entry => documentCard(catalog, entry)).join('')}</div></section>`;
}
export function mountResearchLibrary(host, catalog) {
  host.innerHTML = renderResearchLibrary(catalog);
  const update = () => {
    const result = filterResearch(catalog, {query: host.querySelector('[data-library-query]').value, kind: host.querySelector('[data-library-kind]').value});
    host.querySelector('[data-library-count]').textContent = `${result.length}件`;
    host.querySelector('[data-library-results]').innerHTML = result.map(entry => documentCard(catalog, entry)).join('') || '<p class="hub-meta" role="status">条件に一致する資料はありません。</p>';
  };
  host.querySelector('[data-library-query]').addEventListener('input', update);
  host.querySelector('[data-library-kind]').addEventListener('change', update);
}
