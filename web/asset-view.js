// The single 保有・推移 page as an HTML string: every asset in one view, charts switched by checkboxes.
// Charts come from UiCharts only; every string is escaped and no style attribute is emitted.
import {CLASS_ORDER, CLASS_LABELS, RANGES, datesOf, limitDates, seriesByDate, portfolioSummary, movers, holdings, researchEntryFor, weekRows, accountsOf, yen, signedYen, man, signedMan, percent, signedPercent, quantityText, deltaClass} from './asset-model.js';
import {routeFor} from './catalog.js';
import {UiCharts} from './charts.js';

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
const emptyState = (payload, text = EMPTY_TEXT) => `<section class="panel"><p class="asset-empty" role="status">${esc(text)}${payload?.status?.status === 'not_configured' ? '<br><small>ローカルでは data/private/assets/state.json、Cloud Run では state バケットの assets/state.json を読みます。</small>' : ''}</p></section>`;
const rangeSelect = (range, dates) => `<label>表示期間 <select id="asset-range" aria-label="グラフの表示期間">${RANGES.map(option => `<option value="${option.value}"${option.value === range ? ' selected' : ''}>${esc(option.label)}</option>`).join('')}</select></label><span>${dates.length}週分の記録${dates.length ? `（${esc(dates[0])} 〜 ${esc(dates.at(-1))}）` : ''}</span>`;

// Research link for a holding when the catalog has an entry for its symbol.
function nameCell(row, catalog) {
  const entry = researchEntryFor(row, catalog);
  const label = `<span class="asset-symbol">${esc(row.symbol)}</span>${esc(row.name)}`;
  return entry ? `<a class="entry-link" href="${routeFor(entry.id, 0)}" title="調査を開く">${label}</a>` : label;
}

const MODES = [{value: 'stack', label: '積み上げ'}, {value: 'line', label: '折れ線'}];
const modeRadios = mode => `<fieldset class="asset-mode"><legend>表示形式</legend>${MODES.map(option => `<label><input type="radio" name="asset-mode" value="${option.value}"${option.value === mode ? ' checked' : ''}> ${option.label}</label>`).join('')}</fieldset>`;
// One checkbox per series; `toggle` identifies it for assets.js ("c:<class>" or "p:<position key>").
const checkbox = (toggle, label, checked, tone) => `<label class="asset-check"><input type="checkbox" data-toggle="${esc(toggle)}"${checked ? ' checked' : ''}><span class="asset-check-swatch ${tone}" aria-hidden="true"></span>${esc(label)}</label>`;
const positionLabel = row => `${row.symbol === row.name || row.symbol === 'JPY' ? row.name : `${row.symbol} ${row.name}`}（${row.accountLabel}）`;

// Stacked bars or lines for the chosen series; with lines a dashed line adds up the selection.
function seriesChart({title, mode, entries, values, rows}) {
  if (!entries.length) return '<p class="asset-empty" role="status">表示する項目にチェックを入れてください。</p>';
  const data = rows.map((row, index) => ({...row, ...Object.fromEntries(entries.map(entry => [entry.id, values[entry.key]?.[index] ?? null])), total: entries.reduce((sum, entry) => sum + (values[entry.key]?.[index] ?? 0), 0)}));
  const series = entries.map(entry => ({key: entry.id, label: entry.label, kind: mode === 'stack' ? 'bar' : 'line', tone: entry.tone}));
  if (mode === 'line' && entries.length > 1) series.push({key: 'total', label: '選択の合計', tone: 'primary', dashed: true});
  return UiCharts.render({title, unit: 'man', stacked: mode === 'stack', slot: 14, rows: data, series});
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
    <table class="asset-table"><thead><tr><th scope="col">口座</th><th scope="col">銘柄</th><th scope="col" class="numeric">数量</th><th scope="col" class="numeric">評価額</th><th scope="col" class="numeric">前週差</th>${showCost ? '<th scope="col" class="numeric">取得額</th><th scope="col" class="numeric">評価損益</th>' : ''}<th scope="col" class="numeric">構成比</th></tr></thead>
    <tbody>${rows.map(row => `<tr><td>${esc(row.accountLabel)}</td><td>${nameCell(row, catalog)}${row.market === 'US' ? '<span class="asset-tag">米国</span>' : ''}${row.carryForward ? '<span class="asset-tag">前回値</span>' : ''}</td><td class="numeric">${esc(quantityText(row.quantity))}</td><td class="numeric">${esc(yen(row.value))}${row.nativeAmount !== null ? `<small class="asset-native">${esc(row.nativeAmount.toLocaleString('ja-JP', {maximumFractionDigits: 2}))} ${esc(row.currency || '')}</small>` : ''}</td>${deltaCell(row.delta)}${showCost ? `<td class="numeric">${esc(yen(row.costJpy))}</td><td class="numeric ${row.pnl === null ? '' : deltaClass(row.pnl)}">${esc(signedYen(row.pnl))}</td>` : ''}<td class="numeric">${esc(percent(row.share))}</td></tr>`).join('')}</tbody>
    <tfoot><tr><th scope="row" colspan="3">合計</th><th class="numeric">${esc(yen(total))}</th><th class="numeric ${deltaClass(rows.reduce((sum, row) => sum + (row.delta ?? 0), 0))}">${esc(signedYen(rows.reduce((sum, row) => sum + (row.delta ?? 0), 0)))}</th>${showCost ? '<th></th><th></th>' : ''}<th class="numeric">100%</th></tr></tfoot></table></div>`;
}

// options.hiddenClasses / hiddenPositions: Sets of unchecked ids (everything is checked by default).
export function assetsView(payload, catalog, {loading = false, error = '', range = '52', mode = 'stack', hiddenClasses = new Set(), hiddenPositions = new Set()} = {}) {
  const state = payload?.state || null, summary = portfolioSummary(state);
  const head = status({loading, error});
  if (!summary) return `<section class="asset-page">${head}${payload || !loading ? emptyState(payload) : ''}</section>`;
  const allDates = datesOf(state), dates = limitDates(allDates, range), rows = weekRows(dates);
  const byClass = seriesByDate(state, 'class', {dates});
  const classes = CLASS_ORDER.filter(cls => byClass.keys.includes(cls));
  const classEntries = classes.map(cls => ({id: `c-${cls}`, key: cls, label: CLASS_LABELS[cls] || cls, tone: CLASS_TONES[cls] || 'cat-1'}));
  const overall = classEntries.filter(entry => !hiddenClasses.has(entry.key));
  const sections = classes.map(cls => {
    const label = CLASS_LABELS[cls] || cls, held = holdings(state, cls);
    if (!held.length) return '';
    const part = summary.byClass.find(row => row.cls === cls) || {value: 0, delta: null, previous: null, share: 0};
    const offset = allDates.length - dates.length;
    const entries = held.map((row, index) => ({id: `p${index}`, key: row.key, label: positionLabel(row), tone: `cat-${(index % 6) + 1}`}));
    const shown = entries.filter(entry => !hiddenPositions.has(entry.key));
    return `<section class="panel asset-class-panel" id="asset-class-${esc(cls)}">
      <div class="panel-heading"><h2>${esc(label)}<span class="count">${held.length}件</span></h2><span class="subtle">${esc(man(part.value))} · 総資産の${esc(percent(part.share))} · 前週比 <span class="${deltaClass(part.delta)}">${esc(signedMan(part.delta))}</span></span></div>
      <div class="asset-checks" role="group" aria-label="${esc(label)}の表示する内訳">${entries.map(entry => checkbox(`p:${entry.key}`, entry.label, !hiddenPositions.has(entry.key), entry.tone)).join('')}</div>
      <div class="asset-chart">${seriesChart({title: `${label}の内訳の推移`, mode, entries: shown, values: Object.fromEntries(held.map(row => [row.key, row.history.slice(offset)])), rows})}</div>
      ${holdingsTable(held, label, catalog)}
    </section>`;
  }).join('');
  return `<section class="asset-page">${head}
    <div class="metrics">
      ${metric('総資産', man(summary.total), '', `${yen(summary.total)} · ${summary.latestDate}時点`, 'green-top')}
      ${deltaMetric('前週比', summary.delta, summary.deltaPct, summary.previousDate)}
      ${metric('記録週数', String(summary.weeks), '週', `初回 ${summary.firstDate}`, 'blue-top')}
      ${metric('最終記録日', dayText(summary.latestDate), '', summary.recordedAt ? `${time(summary.recordedAt)}（日本時間）に記録` : `${summary.latestDate} の週末記録`)}
    </div>
    <div class="asset-toolbar">${rangeSelect(range, allDates)}${modeRadios(mode)}</div>
    <section class="panel asset-chart-panel"><div class="panel-heading"><h2>資産全体の推移</h2><span class="subtle">チェックした資産クラスだけを表示</span></div>
      <div class="asset-checks" role="group" aria-label="表示する資産クラス">${classEntries.map(entry => checkbox(`c:${entry.key}`, entry.label, !hiddenClasses.has(entry.key), entry.tone)).join('')}</div>
      <div class="asset-chart">${seriesChart({title: '資産全体の推移', mode, entries: overall, values: byClass.values, rows})}</div>
    </section>
    ${moversPanel(state, catalog, summary)}
    <h2 class="asset-section-title">資産ごとの内訳</h2>
    ${sections}
    <p class="asset-footnote">${esc(FOOTNOTE)}${summary.notes.length ? ` 今週のメモ: ${summary.notes.map(esc).join(' / ')}` : ''}</p>
  </section>`;
}
