// Aggregations over the weekly asset state (/api/assets). Pure functions so tests run without a DOM.
// The state keeps raw positions per snapshot; everything shown on screen is derived here.
import {latestGroups, groupClass} from './catalog.js';

export const CLASS_ORDER = Object.freeze(['stock', 'fund', 'crypto', 'cash', 'private', 'bond', 'other']);
// Labels match backend/assets.py CLASS_LABELS.
export const CLASS_LABELS = Object.freeze({stock: '個別株', fund: '投資信託・ETF', crypto: '仮想通貨', cash: '現金・預金', private: '未上場株', bond: '債券', other: 'その他'});
export const RANGES = Object.freeze([{value: '26', label: '直近26週'}, {value: '52', label: '直近52週'}, {value: 'all', label: '全期間'}]);

const finite = value => typeof value === 'number' && Number.isFinite(value);
const snapshotsOf = state => Array.isArray(state?.snapshots) ? state.snapshots : [];
const positionsOf = snapshot => Array.isArray(snapshot?.positions) ? snapshot.positions : [];
const valueOf = position => finite(position?.valueJpy) ? position.valueJpy : 0;
const sum = values => values.reduce((total, value) => total + value, 0);

export const positionKey = position => `${position.account}/${position.class}/${position.symbol}`;
export const datesOf = state => snapshotsOf(state).map(snapshot => snapshot.date);

// The last `weeks` snapshots ('26' / '52'); anything else keeps every date.
export function limitDates(dates, weeks) {
  const count = Number(weeks);
  return count > 0 ? dates.slice(-count) : dates.slice();
}

export function accountsOf(state) {
  const map = new Map();
  for (const account of Array.isArray(state?.accounts) ? state.accounts : []) map.set(account.id, account);
  return map;
}
export const accountLabel = (state, id) => accountsOf(state).get(id)?.label || id;

// Values per date keyed by class / account id / position key. A key missing from a snapshot is 0 for
// class and account totals (the holding is gone) and null for a position (its line ends).
// `cls` restricts the positions to one asset class; `dates` restricts the snapshots.
export function seriesByDate(state, groupBy = 'class', {cls = null, dates = null} = {}) {
  const wanted = dates ? new Set(dates) : null;
  const snapshots = snapshotsOf(state).filter(snapshot => !wanted || wanted.has(snapshot.date));
  const keyOf = position => groupBy === 'account' ? position.account : groupBy === 'position' ? positionKey(position) : position.class;
  const keys = [];
  const seen = new Set();
  const add = key => { if (!seen.has(key)) { seen.add(key); keys.push(key); } };
  if (groupBy === 'class') CLASS_ORDER.forEach(add);
  if (groupBy === 'account') (state?.accounts || []).forEach(account => add(account.id));
  const present = new Set();
  const totals = snapshots.map(snapshot => {
    const byKey = new Map();
    for (const position of positionsOf(snapshot)) {
      if (cls && position.class !== cls) continue;
      const key = keyOf(position);
      add(key);
      present.add(key);
      byKey.set(key, (byKey.get(key) || 0) + valueOf(position));
    }
    return byKey;
  });
  const used = keys.filter(key => present.has(key));
  const values = {};
  for (const key of used) values[key] = totals.map(byKey => byKey.has(key) ? byKey.get(key) : groupBy === 'position' ? null : 0);
  return {dates: snapshots.map(snapshot => snapshot.date), keys: used, values};
}

// Total value per snapshot: [{date, total}].
export const totals = state => snapshotsOf(state).map(snapshot => ({date: snapshot.date, total: sum(positionsOf(snapshot).map(valueOf))}));

const share = (value, total) => total > 0 ? value / total : 0;

export function portfolioSummary(state) {
  const snapshots = snapshotsOf(state);
  if (!snapshots.length) return null;
  const latest = snapshots.at(-1), previous = snapshots.length > 1 ? snapshots.at(-2) : null;
  const total = sum(positionsOf(latest).map(valueOf));
  const previousTotal = previous ? sum(positionsOf(previous).map(valueOf)) : null;
  const delta = previous ? total - previousTotal : null;
  const byClass = seriesByDate(state, 'class', {dates: [latest.date, previous?.date].filter(Boolean)});
  const byAccount = seriesByDate(state, 'account', {dates: [latest.date, previous?.date].filter(Boolean)});
  const rows = (series, build) => series.keys.map(key => {
    const values = series.values[key], value = values[series.dates.length - 1], before = previous ? values[0] : null;
    return build(key, {value, previous: before, delta: previous ? value - before : null, share: share(value, total)});
  });
  const accounts = accountsOf(state);
  return {
    latestDate: latest.date,
    previousDate: previous?.date || null,
    total,
    previousTotal,
    delta,
    deltaPct: previous && previousTotal > 0 ? delta / previousTotal : null,
    weeks: snapshots.length,
    firstDate: snapshots[0].date,
    recordedAt: latest.recordedAt || null,
    notes: Array.isArray(latest.notes) ? latest.notes : [],
    byClass: rows(byClass, (cls, fields) => ({cls, label: CLASS_LABELS[cls] || cls, ...fields})),
    byAccount: rows(byAccount, (id, fields) => ({id, label: accounts.get(id)?.label || id, institution: accounts.get(id)?.institution || '', ...fields})),
  };
}

const describe = (state, position) => ({
  key: positionKey(position),
  account: position.account,
  accountLabel: accountLabel(state, position.account),
  cls: position.class,
  symbol: position.symbol,
  name: position.name,
  market: position.market || null,
});

// Largest week-over-week gains and losses per position between the two newest snapshots. A position
// on only one side counts as 0 on the other and is flagged appeared / disappeared.
export function movers(state, n = 5) {
  const snapshots = snapshotsOf(state);
  if (snapshots.length < 2) return {up: [], down: []};
  const latest = new Map(positionsOf(snapshots.at(-1)).map(position => [positionKey(position), position]));
  const previous = new Map(positionsOf(snapshots.at(-2)).map(position => [positionKey(position), position]));
  const changes = [];
  for (const key of new Set([...latest.keys(), ...previous.keys()])) {
    const now = latest.get(key), before = previous.get(key);
    const value = now ? valueOf(now) : 0, was = before ? valueOf(before) : 0;
    const delta = value - was;
    if (delta === 0) continue;
    changes.push({...describe(state, now || before), value, previous: was, delta, deltaPct: was > 0 ? delta / was : null, appeared: !before, disappeared: !now});
  }
  const up = changes.filter(change => change.delta > 0).sort((a, b) => b.delta - a.delta).slice(0, n);
  const down = changes.filter(change => change.delta < 0).sort((a, b) => a.delta - b.delta).slice(0, n);
  return {up, down};
}

// Positions of one class in the newest snapshot, largest first, with their full weekly history.
export function holdings(state, cls) {
  const snapshots = snapshotsOf(state);
  if (!snapshots.length) return [];
  const latest = snapshots.at(-1), previous = snapshots.length > 1 ? snapshots.at(-2) : null;
  const before = new Map(positionsOf(previous).map(position => [positionKey(position), valueOf(position)]));
  const history = seriesByDate(state, 'position', {cls});
  const rows = positionsOf(latest).filter(position => position.class === cls);
  const total = sum(rows.map(valueOf));
  return rows.map(position => {
    const value = valueOf(position), key = positionKey(position);
    const costJpy = finite(position.costJpy) ? position.costJpy : null;
    return {
      ...describe(state, position),
      quantity: finite(position.quantity) ? position.quantity : null,
      currency: position.currency || null,
      nativeAmount: finite(position.nativeAmount) ? position.nativeAmount : null,
      carryForward: Boolean(position.carryForward),
      value,
      previous: previous ? (before.get(key) ?? 0) : null,
      delta: previous ? value - (before.get(key) ?? 0) : null,
      costJpy,
      pnl: costJpy === null ? null : value - costJpy,
      share: share(value, total),
      history: history.values[key] || history.dates.map(() => null),
    };
  }).sort((a, b) => b.value - a.value || a.key.localeCompare(b.key));
}

// Newest research entry for a holding: same asset class as its group and the symbol as entry code
// (285A) or slug prefix (BTC-bitcoin). Null when nothing matches.
export function researchEntryFor(position, catalog) {
  if (!position?.symbol || !catalog) return null;
  // Raw positions carry `class`; holdings / movers rows carry `cls`.
  const symbol = String(position.symbol), cls = position.class || position.cls;
  for (const group of latestGroups(catalog)) {
    if (groupClass(group) !== cls) continue;
    const entry = (group.entries || []).find(candidate => candidate.code === symbol || String(candidate.slug || '').startsWith(`${symbol}-`));
    if (entry) return entry;
  }
  return null;
}

// UiCharts rows for weekly dates: a short M/D label, the full date for tooltips and the year as the
// group line (charts.js prints a group label where it differs from the previous row, so every row
// carries its year and a range cut anywhere still starts with one).
export function weekRows(dates) {
  return dates.map(date => {
    const [year, month, day] = date.split('-').map(Number);
    return {label: `${month}/${day}`, name: `${year}年${month}月${day}日`, group: `${year}年`};
  });
}

const yenFormat = new Intl.NumberFormat('ja-JP', {style: 'currency', currency: 'JPY', maximumFractionDigits: 0});
export const yen = value => finite(value) ? yenFormat.format(value) : '—';
export const signedYen = value => finite(value) ? `${value > 0 ? '+' : value < 0 ? '−' : '±'}${yenFormat.format(Math.abs(value))}` : '—';
// 万円 with one decimal, as the charts' `man` unit shows it.
export const man = (value, digits = 1) => finite(value) ? `${(value / 10000).toLocaleString('ja-JP', {minimumFractionDigits: 0, maximumFractionDigits: digits})}万円` : '—';
export const signedMan = (value, digits = 1) => finite(value) ? `${value > 0 ? '+' : value < 0 ? '−' : '±'}${man(Math.abs(value), digits)}` : '—';
export const percent = (ratio, digits = 1) => finite(ratio) ? `${(ratio * 100).toLocaleString('ja-JP', {minimumFractionDigits: digits, maximumFractionDigits: digits})}%` : '—';
export const signedPercent = (ratio, digits = 1) => finite(ratio) ? `${ratio > 0 ? '+' : ratio < 0 ? '−' : '±'}${percent(Math.abs(ratio), digits)}` : '—';
export const quantityText = value => finite(value) ? value.toLocaleString('ja-JP', {maximumFractionDigits: 8}) : '—';
export const deltaClass = value => !finite(value) || value === 0 ? 'delta-flat' : value > 0 ? 'delta-up' : 'delta-down';
