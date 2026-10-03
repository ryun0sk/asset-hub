import {showCosts, initCostAlerts} from './costs.js';
import {renderMarkdown} from './markdown.js';
import {KIND_LABELS, TYPE_LABELS, parseRoute, routeFor, lookup, routeForPath, fileUrl, stats, versionsOf, latestGroups, counterpartIndex} from './catalog.js';

const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[ch]));
const SNAPSHOT_NOTE = 'すべて調査日時点のスナップショットです。記載の株価・予想・投資判断は各調査日の見解で、現在の判断ではありません。';
const ICONS = {
  theme: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" focusable="false"><path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/><path d="m3 17.5 9 4.5 9-4.5"/></svg>',
  company: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" focusable="false"><path d="M4 21V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17M16 9h3a1 1 0 0 1 1 1v11M2 21h20M8 7h4M8 11h4M8 15h4M9 21v-3h2v3"/></svg>',
};
// allow-same-origin is required: research pages render charts inside nested srcdoc iframes, which
// stay blank under an opaque origin. Their CDN scripts are limited by RESEARCH_HTML_CSP instead.
const SANDBOX = 'allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-downloads';

let catalog = null, catalogError = '', renderToken = 0;
const textCache = new Map();

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

function renderNav() {
  const host = $('researchNav');
  if (!catalog) {
    host.innerHTML = `<p class="nav-label nav-status">${esc(catalogError || '調査一覧を読み込んでいます…')}</p>`;
    return;
  }
  // One link per target (its newest snapshot); archives are reached from the version bar.
  host.innerHTML = latestGroups(catalog).map(group => `<p class="nav-label">${esc(group.label)}</p>${group.entries.map(entry => `
    <a href="${routeFor(entry.id, 0)}" class="nav-link" data-target="${esc(targetKey(entry))}"><span class="nav-icon" aria-hidden="true">${ICONS[entry.kind] || ICONS.theme}</span><span class="nav-text">${esc(entry.title)}</span></a>
    <div class="subnav" data-subnav="${esc(targetKey(entry))}" hidden></div>`).join('')}`).join('');
}

const targetKey = entry => `${entry.kind}/${entry.slug}`;

// Expand the viewed target in the sidebar with the documents of the version being shown.
function syncNav(view, found) {
  const key = view === 'research' && found ? targetKey(found.entry) : '';
  document.querySelectorAll('#mainNav .nav-link[data-target]').forEach(link => link.classList.toggle('selected', link.dataset.target === key));
  document.querySelectorAll('#mainNav [data-subnav]').forEach(sub => {
    sub.hidden = sub.dataset.subnav !== key;
    if (sub.hidden) { sub.textContent = ''; return; }
    sub.innerHTML = found.entry.items.map((item, index) => `<a href="${routeFor(found.entry.id, index)}"${index === found.index ? ' class="selected" aria-current="page"' : ''}>${esc(item.label)}</a>`).join('');
  });
}

function setHead({eyebrow, title, meta, crumb, openUrl, topMeta}) {
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

function changeView() {
  const route = parseRoute(location.hash);
  const found = lookup(catalog, route);
  const view = route.view === 'research' && (found || (!catalog && !catalogError)) ? 'research' : route.view === 'cost' ? 'cost' : 'home';
  $('homeSection').hidden = view !== 'home';
  $('researchSection').hidden = view !== 'research';
  $('costSection').hidden = view !== 'cost';
  $('pageActions').innerHTML = '';
  document.querySelectorAll('#mainNav [data-view]').forEach(link => link.classList.toggle('selected', link.dataset.view === view));
  syncNav(view, found);
  if (view === 'cost') {
    setHead({eyebrow: 'COST', title: 'コスト', meta: '', crumb: 'コスト'});
    showCosts();
  } else if (view === 'research') {
    if (found) showResearch(found, route.anchor);
    else setHead({eyebrow: 'RESEARCH', title: '読み込み中', crumb: '読み込み中'});
  } else {
    if (route.view !== 'home' && catalog && location.hash && location.hash !== '#home') history.replaceState(null, '', '#home');
    showHome();
  }
}

function showHome() {
  setHead({eyebrow: 'OVERVIEW', title: 'ホーム', meta: '企業・投資テーマの調査レポート、評価モデル、根拠資料', crumb: 'ホーム'});
  const host = $('homeSection');
  if (!catalog) {
    host.innerHTML = `<p class="empty" role="${catalogError ? 'alert' : 'status'}">${esc(catalogError || '調査一覧を読み込んでいます…')}</p>`;
    return;
  }
  const s = stats(catalog), latest = latestGroups(catalog).flatMap(group => group.entries);
  const metric = (tone, label, value, unit, note) => `<section class="metric ${tone}"><p class="metric-label">${label}</p><p class="metric-value">${esc(value)}${unit ? `<small>${unit}</small>` : ''}</p><p class="metric-note">${note}</p></section>`;
  host.innerHTML = `<div class="metrics">
      ${metric('green-top', 'テーマ', s.themes, '件', '業界・サプライチェーン単位の調査')}
      ${metric('blue-top', '企業', s.companies, '社', '個別銘柄の調査')}
      ${metric('amber-top', '最新の調査日', s.latest || '—', '', '新しい調査は日付別フォルダに追加')}
      ${metric('', '資料', s.documents, '件', `最新版の資料。過去の調査 ${s.archives}版はアーカイブ`)}
    </div>
    <p class="notice snapshot-note"><span aria-hidden="true">ⓘ</span>${SNAPSHOT_NOTE}</p>
    <section class="panel">
      <div class="panel-heading"><h2>調査一覧<span class="count">${latest.length}件</span></h2><span class="subtle">最新の調査を表示。過去の調査はアーカイブ欄から開けます</span></div>
      <div class="table-scroll" tabindex="0" role="region" aria-label="調査一覧。横スクロールで資料を確認">
        <table class="research-table"><colgroup><col class="col-title"><col class="col-kind"><col class="col-date"><col class="col-items"><col class="col-archive"></colgroup>
          <thead><tr><th scope="col">対象</th><th scope="col">区分</th><th scope="col">最新の調査日</th><th scope="col">資料</th><th scope="col">アーカイブ</th></tr></thead>
          <tbody>${latest.map(entry => `<tr>
            <td><a class="entry-link" href="${routeFor(entry.id, 0)}">${esc(entry.title)}</a></td>
            <td><span class="badge ${entry.kind === 'company' ? 'medium' : 'high'}">${esc(KIND_LABELS[entry.kind] || entry.kind)}</span></td>
            <td class="numeric-cell">${esc(entry.date)}</td>
            <td><div class="link-stack">${entry.items.map((item, index) => `<a class="channel" href="${routeFor(entry.id, index)}">${esc(item.label)}<span class="type-tag">${esc(TYPE_LABELS[item.type] || item.type)}</span></a>`).join('')}</div></td>
            <td>${archiveLinks(entry)}</td>
          </tr>`).join('') || '<tr><td colspan="5" class="empty">調査資料はまだありません。</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-footer"><span>出典: research/catalog.json${catalog.generatedAt ? ` · 生成 ${esc(catalog.generatedAt.slice(0, 10))}` : ''}</span><span>実績・会社予想・外部予想・独自シナリオの区別は各資料を参照</span></div>
    </section>`;
}

function archiveLinks(entry) {
  const older = versionsOf(catalog, entry).slice(1);
  if (!older.length) return '<span class="no-archive">—</span>';
  return `<div class="link-stack">${older.map(version => `<a class="archive-link" href="${routeFor(version.id, 0)}">${esc(version.date)}</a>`).join('')}</div>`;
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

function showResearch({entry, item}, anchor = '') {
  const url = fileUrl(item.path);
  const versions = versionsOf(catalog, entry), newest = versions[0], archived = newest && newest.id !== entry.id;
  setHead({
    eyebrow: `${KIND_LABELS[entry.kind] || ''} · 調査日 ${entry.date}${archived ? ' · アーカイブ' : ''}`,
    title: `【${entry.title}】${item.label}`,
    meta: item.path,
    crumb: `${entry.title} · ${item.label}`,
    openUrl: url,
    topMeta: `調査日 ${entry.date}`,
  });
  if (item.type === 'pdf' && url) $('pageActions').innerHTML = `<a class="button" href="${esc(url)}" download>PDFをダウンロード</a>`;
  const host = $('researchSection');
  const versionNav = versionBar(entry, item);
  const archiveNote = archived ? `<p class="notice snapshot-note archive-note" role="note"><span aria-hidden="true">⏱</span><span class="archive-text">過去の調査（${esc(entry.date)}時点）をアーカイブとして表示しています。<a href="${routeFor(newest.id, counterpartIndex(item, newest))}">最新の調査（${esc(newest.date)}）を開く →</a></span></p>` : '';
  const note = archiveNote || `<p class="notice snapshot-note"><span aria-hidden="true">ⓘ</span>調査日（${esc(entry.date)}）時点のスナップショットです。現在の株価・投資判断ではありません。</p>`;
  const token = ++renderToken;
  const title = `${entry.title} — ${item.label}`;
  if (!url) {
    host.innerHTML = `${versionNav}<p class="empty" role="alert">この資料は表示できません。</p>`;
    return;
  }
  if (item.type === 'html') {
    host.innerHTML = `${versionNav}${note}<div class="viewer"><iframe class="viewer-frame" src="${esc(url)}" title="${esc(title)}" sandbox="${SANDBOX}" referrerpolicy="no-referrer"></iframe></div>`;
    return;
  }
  if (item.type === 'pdf') {
    host.innerHTML = `${versionNav}${archiveNote}<div class="viewer"><iframe class="viewer-frame" src="${esc(url)}" title="${esc(title)}"></iframe></div><p class="viewer-fallback">PDFが表示されない場合は <a href="${esc(url)}" download>ダウンロード</a> するか、<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">新しいタブで開いて</a>ください。</p>`;
    return;
  }
  host.innerHTML = `${versionNav}${note}<div class="doc-panel"><p class="empty" role="status">資料を読み込んでいます…</p></div>`;
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
