// Research snapshots only: reject a different security or pre-listing prices.
export const STOCKS = Object.freeze({
  SPCX: {label:'SpaceX（SPCX）',firstTradingDate:'2026-06-12',historyUrl:'/research/companies/SPCX-spacex/2026-10-05/sources/price-history.json'},
  TSLA: {label:'テスラ（TSLA）',firstTradingDate:'2010-06-29',historyUrl:'/research/companies/TSLA-tesla/2026-10-05/sources/price-history.json'},
});
const validDate = value => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
export function readPriceHistory(payload, expectedSymbol = 'SPCX') {
  const stock = STOCKS[expectedSymbol];
  if (!stock || payload?.symbol !== expectedSymbol || payload.currency !== 'USD' || payload.firstTradingDate !== stock.firstTradingDate || !validDate(payload.through) || !Array.isArray(payload.rows) || !payload.rows.length) throw new Error('株価データの対象を確認できません。');
  let previous = '';
  const rows = payload.rows.map(row => {
    if (!validDate(row.date) || row.date < payload.firstTradingDate || row.date > payload.through || row.date <= previous || !(row.close === null || typeof row.close === 'number' && Number.isFinite(row.close) && row.close > 0)) throw new Error('株価データの日付・価格を確認できません。');
    previous = row.date;
    return {date: row.date, close: row.close};
  });
  if (!rows.some(row => row.close !== null)) throw new Error('表示できる終値がありません。');
  return {...payload, rows};
}

export function periodRows(rows, days = 0) {
  if (!days) return rows;
  const start = new Date(`${rows.at(-1).date}T00:00:00Z`);
  start.setUTCDate(start.getUTCDate() - days + 1);
  const cutoff = start.toISOString().slice(0, 10);
  return rows.filter(row => row.date >= cutoff);
}

export function priceSummary(rows) {
  const observed = rows.filter(row => row.close !== null);
  const first = observed[0], last = observed.at(-1), prior = observed.at(-2);
  return {first, last, prior, change: prior ? last.close - prior.close : null, changePercent: prior ? (last.close / prior.close - 1) * 100 : null, periodPercent: first && last ? (last.close / first.close - 1) * 100 : null};
}
