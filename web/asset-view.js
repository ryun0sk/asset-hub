// 保有・推移 as separate summary, trend, holdings and policy HTML views.
// Charts come from UiCharts only; every string is escaped and no style attribute is emitted.
import {CLASS_ORDER, CLASS_LABELS, RANGES, datesOf, limitDates, seriesByDate, portfolioSummary, movers, holdings, trendPositions, researchEntryFor, weekRows, yen, signedYen, man, signedMan, percent, signedPercent, quantityText, deltaClass} from './asset-model.js';
import {routeFor} from './catalog.js';
import {UiCharts} from './charts.js';
import {renderMarkdown} from './markdown.js';

const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const time = value => {
  if (!value) return '—';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? '—' : new Intl.DateTimeFormat('ja-JP', {timeZone: 'Asia/Tokyo', dateStyle: 'short', timeStyle: 'short'}).format(parsed);
};
const dayText = date => {
  const [, month, day] = String(date || '').split('-').map(Number);
  return month && day ? `${month}月${day}日` : '—';
};
export const EMPTY_TEXT = '週末の記録がまだありません。/weekly-assets で今週の資産を記録してください。';
export const FOOTNOTE = '各サイト表示の円換算評価額を週次で手入力した記録。為替・税金は未考慮。';
const CLASS_TONES = Object.fromEntries(CLASS_ORDER.map((cls, index) => [cls, `cat-${(index % 6) + 1}`]));

const metric = (label, value, unit, note, tone = '', valueClass = '') => `<section class="metric ${tone}"><p class="metric-label">${esc(label)}</p><p class="metric-value ${valueClass}">${esc(value)}${unit ? `<small>${esc(unit)}</small>` : ''}</p><p class="metric-note">${esc(note)}</p></section>`;
const deltaMetric = (label, delta, ratio, previousDate) => delta === null
  ? metric(label, '—', '', '前週の記録がありません', 'amber-top')
  : metric(label, signedMan(delta), '', `${signedPercent(ratio)} · 前週 ${previousDate || '—'} 比`, 'amber-top', deltaClass(delta));
const deltaCell = value => `<td class="numeric ${deltaClass(value)}">${esc(signedYen(value))}</td>`;

const status = ({loading, error}) => `${loading ? '<div class="sync-progress" role="status"><span class="sync-spinner" aria-hidden="true"></span>資産データを読み込んでいます…</div>' : ''}${error ? `<div class="notice asset-notice" role="alert">${esc(error)}</div>` : ''}`;

export function assetPolicyView(payload, {loading = false, error = ''} = {}) {
  const policy = payload?.state?.policy;
  const head = status({loading, error});
  if (!policy || typeof policy.markdown !== 'string') return `<section class="asset-page">${head}${loading ? '' : '<section class="panel"><p class="asset-empty" role="status">全体方針はまだ登録されていません。</p></section>'}</section>`;
  return `<section class="asset-page asset-policy">${head}<section class="panel">
    <div class="panel-heading"><h2>${esc(policy.title)}</h2><span class="subtle">方針更新 ${esc(policy.date)} · 残高基準 ${esc(policy.balanceDate)}</span></div>
    <article class="doc asset-policy-body" aria-label="全体方針の内容">${renderMarkdown(policy.markdown)}</article>
  </section></section>`;
}
const emptyState = (payload, text = EMPTY_TEXT) => `<section class="panel"><p class="asset-empty" role="status">${esc(text)}${payload?.status?.status === 'not_configured' ? '<br><small>ローカルでは data/private/assets/state.json、Cloud Run では state バケットの assets/state.json を読みます。</small>' : ''}</p></section>`;
const rangeSelect = (range, dates) => `<label>表示期間 <select id="asset-range" aria-label="グラフの表示期間">${RANGES.map(option => `<option value="${option.value}"${option.value === range ? ' selected' : ''}>${esc(option.label)}</option>`).join('')}</select></label><span>${dates.length}週分の記録${dates.length ? `（${esc(dates[0])} 〜 ${esc(dates.at(-1))}）` : ''}</span>`;

// Research link for a holding when the catalog has an entry for its symbol.
function nameCell(row, catalog) {
  const entry = researchEntryFor(row, catalog);
  const label = `<span class="asset-symbol">${esc(row.symbol)}</span>${esc(row.name)}`;
  return entry ? `<a class="entry-link" href="${routeFor(entry.id, 0)}" title="調査を開く">${label}</a>` : label;
}

// One checkbox per series; `toggle` identifies it for assets.js ("c:<class>" or "p:<position key>").
const checkbox = (toggle, label, checked, tone) => `<label class="asset-check"><input type="checkbox" data-toggle="${esc(toggle)}"${checked ? ' checked' : ''}><span class="asset-check-swatch ${tone}" aria-hidden="true"></span>${esc(label)}</label>`;
const positionLabel = row => `${row.symbol === row.name || row.symbol === 'JPY' ? row.name : `${row.symbol} ${row.name}`}（${row.accountLabel}）${row.pastHolding ? ' · 過去保有' : ''}`;

// Every asset chart is a line chart, with a distinct selection total even for one
// chosen item. Missing position rows break that item; the recorded absence adds 0 to the total.
function seriesChart({title, entries, values, rows}) {
  if (!entries.length) return '<p class="asset-empty" role="status">表示する項目にチェックを入れてください。</p>';
  const data = rows.map((row, index) => ({...row, ...Object.fromEntries(entries.map(entry => [entry.id, values[entry.key]?.[index] ?? null])), total: entries.reduce((sum, entry) => sum + (values[entry.key]?.[index] ?? 0), 0)}));
  const series = entries.map(entry => ({key: entry.id, label: entry.label, kind: 'line', tone: entry.tone}));
  series.push({key: 'total', label: '選択項目の合計', kind: 'line', tone: 'primary', dashed: true, marker: 'ring'});
  return UiCharts.render({title, unit: 'man', height: 442, labels: 'all', labelSize: 'compact', rows: data, series});
}

function moversPanel(state, catalog, summary) {
  const {up, down} = movers(state);
  const list = (title, rows, emptyText) => `<div class="asset-movers-column"><h3>${esc(title)}</h3><div class="table-scroll" tabindex="0" role="region" aria-label="${esc(title)}"><table class="asset-table asset-movers-table"><thead><tr><th scope="col">銘柄</th><th scope="col">口座</th><th scope="col" class="numeric">前週差</th><th scope="col" class="numeric">評価額</th></tr></thead><tbody>${rows.map(row => `<tr><td>${nameCell(row, catalog)}${row.appeared ? '<span class="asset-tag">新規</span>' : row.disappeared ? '<span class="asset-tag">売却・解約</span>' : ''}</td><td>${esc(row.accountLabel)}</td>${deltaCell(row.delta)}<td class="numeric">${esc(yen(row.value))}</td></tr>`).join('') || `<tr><td colspan="4" class="empty">${esc(emptyText)}</td></tr>`}</tbody></table></div></div>`;
  return `<section class="panel"><div class="panel-heading"><h2>今週の増減</h2><span class="subtle">${summary.previousDate ? `${esc(summary.previousDate)} → ${esc(summary.latestDate)} の銘柄別の差` : '前週の記録がないため比較できません'}</span></div><div class="asset-movers">${list('増加', up, '増加した銘柄はありません')}${list('減少', down, '減少した銘柄はありません')}</div></section>`;
}

function holdingsTable(rows, label, catalog) {
  const showCost = rows.some(row => row.costJpy !== null);
  const total = rows.reduce((sum, row) => sum + row.value, 0);
  return `<div class="table-scroll" tabindex="0" role="region" aria-label="${esc(label)}の保有一覧。横スクロールで列を確認">
    <table class="asset-table"><thead><tr><th scope="col">口座</th><th scope="col">銘柄</th><th scope="col" class="numeric">数量</th><th scope="col" class="numeric">評価額</th><th scope="col" class="numeric">前週差</th>${showCost ? '<th scope="col" class="numeric">取得額</th><th scope="col" class="numeric">評価損益</th>' : ''}<th scope="col" class="numeric">クラス内比率</th></tr></thead>
    <tbody>${rows.map(row => `<tr><td>${esc(row.accountLabel)}</td><td>${nameCell(row, catalog)}${row.market === 'US' ? '<span class="asset-tag">米国</span>' : ''}${row.carryForward ? '<span class="asset-tag">前回値</span>' : ''}</td><td class="numeric">${esc(quantityText(row.quantity))}</td><td class="numeric">${esc(yen(row.value))}${row.nativeAmount !== null ? `<small class="asset-native">${esc(row.nativeAmount.toLocaleString('ja-JP', {maximumFractionDigits: 2}))} ${esc(row.currency || '')}</small>` : ''}</td>${deltaCell(row.delta)}${showCost ? `<td class="numeric">${esc(yen(row.costJpy))}</td><td class="numeric ${row.pnl === null ? '' : deltaClass(row.pnl)}">${esc(signedYen(row.pnl))}</td>` : ''}<td class="numeric">${esc(percent(row.share))}</td></tr>`).join('')}</tbody>
    <tfoot><tr><th scope="row" colspan="3">合計</th><th class="numeric">${esc(yen(total))}</th><th class="numeric ${deltaClass(rows.reduce((sum, row) => sum + (row.delta ?? 0), 0))}">${esc(signedYen(rows.reduce((sum, row) => sum + (row.delta ?? 0), 0)))}</th>${showCost ? '<th></th><th></th>' : ''}<th class="numeric">100%</th></tr></tfoot></table></div>`;
}

function metrics(summary) {
  return `<div class="metrics">
    ${metric('総資産', man(summary.total), '', `${yen(summary.total)} · ${summary.latestDate}時点`, 'green-top')}
    ${deltaMetric('前週比', summary.delta, summary.deltaPct, summary.previousDate)}
    ${metric('記録週数', String(summary.weeks), '週', `初回 ${summary.firstDate}`, 'blue-top')}
    ${metric('最終記録日', dayText(summary.latestDate), '', summary.recordedAt ? `${time(summary.recordedAt)}（日本時間）に記録` : `${summary.latestDate} の週末記録`)}
  </div>`;
}

const footnote = summary => `<p class="asset-footnote">${esc(FOOTNOTE)}${summary.notes.length ? ` 今週のメモ: ${summary.notes.map(esc).join(' / ')}` : ''}</p>`;
const classHeading = (label, held, part) => `<div class="panel-heading"><h2>${esc(label)}<span class="count">${held.length}件</span></h2><span class="subtle">${esc(man(part.value))} · 総資産の${esc(percent(part.share))} · 前週比 <span class="${deltaClass(part.delta)}">${esc(signedMan(part.delta))}</span></span></div>`;

function compositionPanel(title, label, rows, summary, classes = false) {
  return `<section class="panel asset-composition-panel"><div class="panel-heading"><h2>${esc(title)}</h2><span class="subtle">${esc(summary.latestDate)}時点</span></div>
    <div class="table-scroll" tabindex="0" role="region" aria-label="${esc(title)}"><table class="asset-table asset-composition-table"><thead><tr><th scope="col">${esc(label)}</th><th scope="col" class="numeric">評価額</th><th scope="col" class="numeric">構成比</th><th scope="col" class="numeric">前週差</th></tr></thead>
    <tbody>${rows.filter(row => row.value > 0).map(row => `<tr><th scope="row">${classes ? `<span class="asset-composition-dot ${CLASS_TONES[row.cls] || 'cat-1'}" aria-hidden="true"></span>` : ''}${esc(row.label)}</th><td class="numeric">${esc(man(row.value))}</td><td class="numeric">${esc(percent(row.share))}</td><td class="numeric ${deltaClass(row.delta)}">${esc(signedMan(row.delta))}</td></tr>`).join('')}</tbody></table></div>
  </section>`;
}

// options.view selects the page. The default remains the existing trend route (#a/all).
// hiddenClasses / hiddenPositions are Sets of unchecked ids (everything is checked by default).
export function assetsView(payload, catalog, {view = 'all', loading = false, error = '', range = '52', hiddenClasses = new Set(), hiddenPositions = new Set()} = {}) {
  const state = payload?.state || null, summary = portfolioSummary(state);
  const head = status({loading, error});
  if (!summary) return `<section class="asset-page">${head}${payload || !loading ? emptyState(payload) : ''}</section>`;
  if (view === 'summary') return `<section class="asset-page asset-summary">${head}${metrics(summary)}
    <div class="asset-grid">${compositionPanel('クラス別の構成', '資産クラス', summary.byClass, summary, true)}${compositionPanel('口座別の構成', '口座', [...summary.byAccount].sort((a, b) => b.value - a.value), summary)}</div>
    ${moversPanel(state, catalog, summary)}${footnote(summary)}
  </section>`;
  if (view === 'holdings') {
    const sections = CLASS_ORDER.map(cls => {
      const label = CLASS_LABELS[cls] || cls, held = holdings(state, cls);
      if (!held.length) return '';
      const part = summary.byClass.find(row => row.cls === cls);
      return `<section class="panel asset-class-panel" id="asset-class-${esc(cls)}">${classHeading(label, held, part)}${holdingsTable(held, label, catalog)}</section>`;
    }).join('');
    return `<section class="asset-page asset-holdings">${head}${metrics(summary)}${sections}${footnote(summary)}</section>`;
  }
  const allDates = datesOf(state), dates = limitDates(allDates, range), rows = weekRows(dates);
  const byClass = seriesByDate(state, 'class', {dates});
  const classes = CLASS_ORDER.filter(cls => byClass.keys.includes(cls));
  const classEntries = classes.map(cls => ({id: `c-${cls}`, key: cls, label: CLASS_LABELS[cls] || cls, tone: CLASS_TONES[cls] || 'cat-1'}));
  const overall = classEntries.filter(entry => !hiddenClasses.has(entry.key));
  const sections = classes.map(cls => {
    const label = CLASS_LABELS[cls] || cls, held = trendPositions(state, cls, {dates});
    if (!held.length) return '';
    const part = summary.byClass.find(row => row.cls === cls) || {value: 0, delta: null, previous: null, share: 0};
    const entries = held.map((row, index) => ({id: `p${index}`, key: row.key, label: positionLabel(row), tone: `cat-${(index % 6) + 1}`}));
    const shown = entries.filter(entry => !hiddenPositions.has(entry.key));
    return `<section class="panel asset-class-panel" id="asset-class-${esc(cls)}">
      ${classHeading(label, held, part)}
      <div class="asset-checks" role="group" aria-label="${esc(label)}の表示する内訳">${entries.map(entry => checkbox(`p:${entry.key}`, entry.label, !hiddenPositions.has(entry.key), entry.tone)).join('')}</div>
      <div class="asset-chart">${seriesChart({title: `${label}の内訳の推移`, entries: shown, values: Object.fromEntries(held.map(row => [row.key, row.history])), rows})}</div>
    </section>`;
  }).join('');
  return `<section class="asset-page asset-trends">${head}${metrics(summary)}
    <div class="asset-toolbar">${rangeSelect(range, dates)}<span>折れ線 · 破線は選択項目の合計</span></div>
    <section class="panel asset-chart-panel"><div class="panel-heading"><h2>資産全体の推移</h2><span class="subtle">チェックした資産クラスだけを表示</span></div>
      <div class="asset-checks" role="group" aria-label="表示する資産クラス">${classEntries.map(entry => checkbox(`c:${entry.key}`, entry.label, !hiddenClasses.has(entry.key), entry.tone)).join('')}</div>
      <div class="asset-chart">${seriesChart({title: '資産全体の推移', entries: overall, values: byClass.values, rows})}</div>
    </section>
    <h2 class="asset-section-title">資産クラスごとの推移</h2>
    ${sections}
    ${footnote(summary)}
  </section>`;
}

export const assetSummaryView = (payload, catalog, options = {}) => assetsView(payload, catalog, {...options, view: 'summary'});
export const assetHoldingsView = (payload, catalog, options = {}) => assetsView(payload, catalog, {...options, view: 'holdings'});
export const homeAssetsView = assetSummaryView;
