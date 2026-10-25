import {showCosts, initCostAlerts} from './costs.js';
import {showAssets, leaveAssets, initAssets} from './assets.js';
import {renderMarkdown} from './markdown.js';
import {isAiValuationView, mountAiValuations} from './ai-valuations.js';
import {AI_DETAIL_SECTIONS, mountAiDetail} from './ai-detail.js';
import {mountMboPanel} from './mbo-panel.js';
import {mountForwardRanking} from './ai-forward-ranking.js';
import {ASSET_SECTIONS, MBO_SECTIONS, AI_SECTIONS, aiEntry, aiDocument, aiSectionForResearch, renderHomeHub, renderAiHub, mountResearchLibrary, createMboPanelLifecycle} from './workspace.js';
import {KIND_LABELS, parseRoute, routeFor, lookup, routeForPath, fileUrl, itemUrl, versionsOf, counterpartIndex} from './catalog.js';

const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[ch]));
const SNAPSHOT_NOTE = 'すべて調査日時点のスナップショットです。記載の株価・予想・投資判断は各調査日の見解で、現在の判断ではありません。';
const icon = paths => `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" focusable="false">${paths}</svg>`;
// Research kinds shown in the sidebar.
const ICONS = {
  theme: icon('<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/><path d="m3 17.5 9 4.5 9-4.5"/>'),
  company: icon('<path d="M4 21V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17M16 9h3a1 1 0 0 1 1 1v11M2 21h20M8 7h4M8 11h4M8 15h4M9 21v-3h2v3"/>'),
  crypto: icon('<circle cx="12" cy="12" r="9"/><path d="M9.5 7.5h3.5a2 2 0 0 1 0 4h-3.5zM9.5 11.5h4a2 2 0 0 1 0 4h-4zM9.5 7.5v8M11 6v1.5M11 15.5V17"/>'),
};
// allow-same-origin is required: research pages render charts inside nested srcdoc iframes, which
// stay blank under an opaque origin. Their CDN scripts are limited by RESEARCH_HTML_CSP instead.
const SANDBOX = 'allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-downloads';

let catalog = null, catalogError = '', renderToken = 0;
const textCache = new Map();
const mboPanel = createMboPanelLifecycle($('mboSection'), mountMboPanel, {
  onError: () => { $('mboSection').textContent = 'MBO調査を読み込めませんでした。ページを再読み込みしてください。'; },
});

async function loadCatalog() {
  try {
    const response = await fetch('/api/catalog');
    if (!response.ok) throw Error(String(response.status));
    const next = await response.json();
    if (!Array.isArray(next?.groups)) throw Error('invalid catalog');
    catalog = next;
    catalogError = '';
  } catch {
    catalogError = '調査一覧を読み込めませんでした。時間をおいて再読み込みしてください。';
  }
  renderNav();
  changeView();
}

// Frequent workflows stay at the top; the library keeps every original document reachable.
function renderNav() {
  const host = $('classNav');
  if (!catalog) {
    host.innerHTML = `<p class="nav-label nav-status">${esc(catalogError || '調査一覧を読み込んでいます…')}</p>`;
    return;
  }
  const ai = aiEntry(catalog);
  host.innerHTML = `${ai ? `<a href="#ai/overview" class="nav-link" data-view="ai"><span class="nav-icon" aria-hidden="true">${ICONS.theme}</span><span class="nav-text">AI関連銘柄・サプライチェーン</span></a><div class="subnav" id="aiSubnav" aria-label="AI調査の表示切替" hidden>${['銘柄を比較', '事業を理解', '考察と根拠'].map(group => `<span class="nav-group-label">${group}</span>${AI_SECTIONS.filter(item => item.group === group).map(item => `<a href="#ai/${item.id}" data-ai-section="${item.id}">${esc(item.label)}</a>`).join('')}`).join('')}</div>` : ''}
    <p class="nav-label">資料</p><a href="#library" class="nav-link" data-view="library"><span class="nav-icon" aria-hidden="true">${ICONS.company}</span><span class="nav-text">調査ライブラリ</span></a><div class="subnav" id="librarySubnav" hidden></div>`;
}

// Expand the viewed target in the sidebar with the documents of the version being shown.
function syncNav(view, found, route) {
  const aiSection = view === 'ai' ? route.section : aiSectionForResearch(catalog, found);
  const assetView = ASSET_SECTIONS[route.cls] ? route.cls : 'all';
  $('assetSubnav').classList.toggle('inactive', view !== 'asset');
  $('assetSubnav').parentElement.classList.toggle('is-active', view === 'asset');
  document.querySelectorAll('#assetSubnav [data-asset-view]').forEach(link => {
    const selected = view === 'asset' && link.dataset.assetView === assetView;
    link.classList.toggle('selected', selected);
    if (selected) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
  const parent = aiSection ? 'ai' : view === 'research' ? 'library' : view;
  document.querySelectorAll('#mainNav [data-view]').forEach(link => {
    const selected = link.dataset.view === parent;
    link.classList.toggle('selected', selected);
    if (selected) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
  });
  const aiSubnav = $('aiSubnav');
  if (aiSubnav) {
    aiSubnav.hidden = !aiSection;
    aiSubnav.querySelectorAll('[data-ai-section]').forEach(link => {
      const selected = link.dataset.aiSection === aiSection;
      link.classList.toggle('selected', selected);
      if (selected) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
    });
  }
  const mboSubnav = $('mboSubnav');
  if (mboSubnav) {
    mboSubnav.hidden = view !== 'mbo';
    const section = MBO_SECTIONS[route.section] ? route.section : 'candidates';
    mboSubnav.querySelectorAll('[data-mbo-section]').forEach(link => {
      const selected = view === 'mbo' && link.dataset.mboSection === section;
      link.classList.toggle('selected', selected);
      if (selected) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
    });
  }
  const librarySubnav = $('librarySubnav');
  if (librarySubnav) {
    librarySubnav.hidden = view !== 'research' || Boolean(aiSection) || !found;
    librarySubnav.innerHTML = librarySubnav.hidden ? '' : `<span class="nav-group-label">${esc(found.entry.title)}</span>${found.entry.items.map((item, index) => `<a href="${routeFor(found.entry.id, index)}"${index === found.index ? ' class="selected" aria-current="page"' : ''}>${esc(item.label)}</a>`).join('')}`;
  }
}

// compact: research documents use a one-line heading (title + meta) so the document starts higher.
function setHead({eyebrow, title, meta, crumb, openUrl, topMeta, compact = false}) {
  document.body.classList.toggle('compact-head', compact);
  $('pageEyebrow').textContent = eyebrow || '';
  $('pageTitle').textContent = title;
  $('pageMeta').textContent = meta || '';
  $('breadcrumb').textContent = crumb || title;
  $('topbarMeta').textContent = topMeta || '';
  const open = $('openNewTab');
  open.hidden = !openUrl;
  if (openUrl) open.href = openUrl;
  document.title = `${crumb || title} · Asset Hub`;
}

// Which section a route shows right now (a research route waits for the catalog).
function parseView(route) {
  const found = lookup(catalog, route);
  if (route.view === 'library') return 'library';
  if (route.view === 'ai') return 'ai';
  if (route.view === 'mbo') return 'mbo';
  return route.view === 'research' && (found || (!catalog && !catalogError)) ? 'research' : route.view === 'cost' ? 'cost' : route.view === 'asset' ? 'asset' : 'home';
}

function changeView() {
  const route = parseRoute(location.hash);
  const found = lookup(catalog, route);
  const view = parseView(route);
  ++renderToken;
  $('homeSection').hidden = !['home', 'library'].includes(view);
  $('researchSection').hidden = !['research', 'ai'].includes(view);
  $('costSection').hidden = view !== 'cost';
  $('assetSection').hidden = view !== 'asset';
  $('mboSection').hidden = view !== 'mbo';
  $('pageActions').innerHTML = '';
  syncNav(view, found, route);
  if (view !== 'asset') leaveAssets();
  if (view !== 'mbo') mboPanel.leave();
  if (view === 'cost') {
    setHead({eyebrow: 'COST', title: 'コスト', meta: '', crumb: 'コスト'});
    showCosts();
  } else if (view === 'asset') {
    const section = ASSET_SECTIONS[route.cls] || ASSET_SECTIONS.all;
    setHead({eyebrow: 'ASSETS', title: section.label, meta: section.description, crumb: `保有・推移 / ${section.label}`});
    showAssets(catalog, route.cls);
  } else if (view === 'ai') {
    showAi(route.section);
  } else if (view === 'mbo') {
    const section = MBO_SECTIONS[route.section] ? route.section : 'candidates';
    const definition = MBO_SECTIONS[section];
    setHead({eyebrow: 'MBO RESEARCH', title: `MBO調査 · ${definition.label}`, meta: definition.description, crumb: `MBO調査 / ${definition.label}`});
    mboPanel.show(section);
  } else if (view === 'library') {
    setHead({eyebrow: 'LIBRARY', title: '調査ライブラリ', meta: 'テーマ・企業ごとに、レポート・元資料・過去の版を探す', crumb: '調査ライブラリ'});
    if (catalog) mountResearchLibrary($('homeSection'), catalog); else $('homeSection').innerHTML = catalogStatus();
  } else if (view === 'research') {
    if (found) showResearch(found, route.anchor);
    else setHead({eyebrow: 'RESEARCH', title: '読み込み中', crumb: '読み込み中'});
  } else {
    // Unknown research ids wait for the catalog.
    if (route.view !== 'home' && catalog && location.hash && location.hash !== '#home') history.replaceState(null, '', '#home');
    showHome();
  }
}

function showHome() {
  setHead({eyebrow: 'OVERVIEW', title: 'ホーム', meta: 'よく使う情報から、目的に合わせて確認する', crumb: 'ホーム'});
  const host = $('homeSection');
  host.innerHTML = catalog
    ? renderHomeHub(catalog)
    : catalogStatus();
}

const catalogStatus = () => `<p class="empty" role="${catalogError ? 'alert' : 'status'}">${esc(catalogError || '調査一覧を読み込んでいます…')}</p>`;

function showAi(section = 'overview') {
  if (!catalog) {
    setHead({title: 'AI関連銘柄・サプライチェーン', crumb: 'AI調査'});
    $('researchSection').innerHTML = catalogStatus();
    return;
  }
  const definition = AI_SECTIONS.find(item => item.id === section);
  if (section === 'forward') {
    setHead({eyebrow: 'AI RESEARCH', title: definition.label, meta: '46社 · 株価2026-10-16終値 · 2028〜2029年の独自シナリオ', crumb: `AI調査 / ${definition.label}`, compact: true});
    mountForwardRanking($('researchSection'));
    return;
  }
  if (definition?.view) {
    const found = aiDocument(catalog, section);
    if (found) { showResearch(found, '', {aiSection: section}); return; }
  }
  setHead({eyebrow: 'AI RESEARCH', title: definition?.label || 'AI関連銘柄・サプライチェーン', meta: definition?.description || '銘柄の比較 → 事業の理解 → 考察と根拠', crumb: `AI調査 / ${definition?.label || '全体像'}`});
  $('researchSection').innerHTML = renderAiHub(catalog, section);
}

// Snapshots of the same target, newest first; the shown one is marked and the others keep the
// same document when it exists in that version.
function versionBar(entry, item) {
  const versions = versionsOf(catalog, entry);
  if (versions.length < 2) return '';
  const links = versions.map((version, n) => {
    const current = version.id === entry.id;
    const tag = n === 0 ? '最新' : 'アーカイブ';
    return `<a class="version-chip${current ? ' current' : ''}${n === 0 ? ' latest' : ''}" href="${routeFor(version.id, counterpartIndex(item, version))}"${current ? ' aria-current="page"' : ''}>${esc(version.date)}<span>${tag}</span></a>`;
  }).join('');
  return `<nav class="version-bar" aria-label="調査の版"><span class="version-label">調査の版</span>${links}</nav>`;
}

function showResearch({entry, item, index}, anchor = '', {aiSection = ''} = {}) {
  const url = itemUrl(item);
  const versions = versionsOf(catalog, entry), newest = versions[0], archived = newest && newest.id !== entry.id;
  const section = aiSection || aiSectionForResearch(catalog, {entry, item, index});
  const detail = AI_DETAIL_SECTIONS[aiSection];
  const overviewEnabled = isAiValuationView(entry, item, archived) && !detail;
  const actualHistory = aiSection === 'multiples' && !archived;
  const definition = AI_SECTIONS.find(candidate => candidate.id === section);
  const label = overviewEnabled ? 'EPS・PER一覧' : aiSection ? definition?.label || item.label : item.label;
  setHead({
    title: label,
    meta: actualHistory ? `${entry.title} · 実績月次 2026-10-18確認 · グラフ保存版 ${entry.date}` : `${entry.title} · 保存版 ${entry.date}${archived ? ' · アーカイブ' : ''}`,
    compact: true,
    crumb: `${entry.title} · ${label}`,
    openUrl: aiSection || overviewEnabled ? `#ai/${section}` : url,
    topMeta: actualHistory ? '実績月次 2026-10-18確認' : `調査日 ${entry.date}`,
  });
  if (item.type === 'pdf' && url) $('pageActions').innerHTML = `<a class="button" href="${esc(url)}" download>PDFをダウンロード</a>`;
  const host = $('researchSection');
  const versionNav = versionBar(entry, item);
  const archiveNote = archived ? `<p class="notice snapshot-note archive-note" role="note"><span aria-hidden="true">⏱</span><span class="archive-text">過去の調査（${esc(entry.date)}時点）をアーカイブとして表示しています。<a href="${routeFor(newest.id, counterpartIndex(item, newest))}">最新の調査（${esc(newest.date)}）を開く →</a></span></p>` : '';
  const note = archiveNote || (actualHistory ? `<p class="notice snapshot-note"><span aria-hidden="true">ⓘ</span>実績月次表：既存4社は10/15・追加の発電3社は10/16終値まで（10/18資料確認） ／ 下部グラフ：${esc(entry.date)}保存版。各行の基準日・通貨・一時利益の注記を確認できます。</p>` : `<p class="notice snapshot-note"><span aria-hidden="true">ⓘ</span>${esc(entry.date)}時点のスナップショット（現在の株価・投資判断ではありません）</p>`);
  const token = ++renderToken;
  const title = `${entry.title} — ${item.label}`;
  // Version bar and notice share one row so the document starts close to the heading.
  const context = section ? '<div class="workspace-context"><a href="#ai/overview">← AI調査の全体像</a><a href="#ai/sources">数値の基準・出典</a></div>' : '';
  const meta = notice => `${context}${versionNav || notice ? `<div class="viewer-meta">${versionNav}${notice}</div>` : ''}`;
  if (!url) {
    host.innerHTML = `${meta('')}<p class="empty" role="alert">この資料は表示できません。</p>`;
    return;
  }
  if (item.type === 'html') {
    const overview = overviewEnabled ? '<div data-ai-valuations><p class="ai-val-error" role="status">AI銘柄のEPS・PER一覧を読み込んでいます…</p></div>' : '';
    if (overview) {
      host.innerHTML = `${meta(note)}${overview}`;
      mountAiValuations(host.querySelector('[data-ai-valuations]'), item);
      return;
    }
    host.innerHTML = `${meta(note)}<div class="viewer${section && !archived ? ' ai-viewer' : ''}"><iframe class="viewer-frame" src="${esc(url)}" title="${esc(title)}" sandbox="${SANDBOX}" referrerpolicy="no-referrer"></iframe></div>`;
    const frame = host.querySelector('.viewer-frame');
    if (detail) mountAiDetail(frame, aiSection);
    else if (section && !archived) compactAiFrame(frame);
    fitFrame(frame);
    return;
  }
  if (item.type === 'pdf') {
    host.innerHTML = `${meta(archiveNote)}<div class="viewer"><iframe class="viewer-frame" src="${esc(url)}" title="${esc(title)}"></iframe></div><p class="viewer-fallback">PDFが表示されない場合は <a href="${esc(url)}" download>ダウンロード</a> するか、<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">新しいタブで開いて</a>ください。</p>`;
    return;
  }
  host.innerHTML = `${meta(note)}<div class="doc-panel"><p class="empty" role="status">資料を読み込んでいます…</p></div>`;
  fetchText(url).then(text => {
    if (token !== renderToken) return;
    const body = item.type === 'md'
      ? `<article class="doc">${renderMarkdown(text, {basePath: item.path, resolveLink: (path, anchor) => routeForPath(catalog, path, anchor), fileUrl})}</article>`
      : `<div class="doc-code-head"><span>${esc(item.path.split('/').pop())}</span><span>${text.split('\n').length}行 · 読み取り専用</span></div><pre class="doc-code"><code>${esc(text)}</code></pre>`;
    host.querySelector('.doc-panel').innerHTML = body;
    if (anchor) document.getElementById(anchor)?.scrollIntoView({block: 'start'});
  }).catch(() => {
    if (token !== renderToken) return;
    host.querySelector('.doc-panel').innerHTML = '<p class="empty" role="alert">資料を読み込めませんでした。</p>';
  });
}

function compactAiFrame(frame) {
  frame.addEventListener('load', () => {
    const doc = frame.contentDocument;
    if (!doc?.body) return;
    doc.body.classList.add('workspace-frame');
    for (const href of ['/tokens.css', '/workspace.css']) {
      const link = doc.createElement('link'); link.rel = 'stylesheet'; link.href = href; doc.head.append(link);
    }
  }, {once: true});
}

// Grow an HTML document's frame to its content so the page scrolls instead of the frame
// (same origin: research pages are sandboxed with allow-same-origin). A page whose height
// follows the frame (100vh layouts) keeps the fixed frame height and its own scrollbar.
let frameObserver = null;
function fitFrame(frame) {
  frameObserver?.disconnect();
  frameObserver = null;
  frame.addEventListener('load', () => {
    let doc;
    try { doc = frame.contentDocument; } catch { return; }
    if (!doc?.documentElement) return;
    const fixed = frame.clientHeight;
    const fit = () => {
      if (!frame.isConnected) { frameObserver?.disconnect(); return; }
      const height = doc.documentElement.scrollHeight;
      if (Math.abs(height - frame.clientHeight) <= 2) return;
      frame.style.height = `${Math.max(height, 200)}px`;
    };
    // Probe once: if the content height tracks the frame height it is viewport-sized.
    frame.style.height = `${fixed + 100}px`;
    requestAnimationFrame(() => {
      const viewportSized = Math.abs(doc.documentElement.scrollHeight - (fixed + 100)) <= 2;
      frame.style.height = '';
      if (viewportSized) return;
      fit();
      frameObserver = new ResizeObserver(fit);
      frameObserver.observe(doc.documentElement);
      if (doc.body) frameObserver.observe(doc.body);
    });
  }, {once: true});
}

async function fetchText(url) {
  if (textCache.has(url)) return textCache.get(url);
  const response = await fetch(url);
  if (!response.ok) throw Error(String(response.status));
  const text = await response.text();
  textCache.set(url, text);
  return text;
}

// In-document anchors (#見出し) scroll within the rendered Markdown instead of changing the route.
document.addEventListener('click', event => {
  const anchor = event.target.closest?.('a[data-doc-anchor]');
  if (!anchor) return;
  event.preventDefault();
  document.getElementById(anchor.dataset.docAnchor)?.scrollIntoView({block: 'start'});
});

addEventListener('hashchange', () => { changeView(); window.scrollTo(0, 0); });
changeView();
loadCatalog();
initCostAlerts();
initAssets();
