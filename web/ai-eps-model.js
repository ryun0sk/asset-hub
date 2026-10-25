const DAY = 86400000;
const finite = value => typeof value === 'number' && Number.isFinite(value);

// Parse date-only values explicitly in UTC and reject normalized invalid dates.
const utcDate = value => {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const time = Date.parse(`${value}T00:00:00Z`);
  return Number.isFinite(time) && new Date(time).toISOString().slice(0, 10) === value ? time : null;
};
const dateString = time => new Date(time).toISOString().slice(0, 10);
const empty = () => ({points: [], startEPS: null, endEPS: null, baseEPS: null, indexPoints: null, changePercent: null});

// Use the latest accounting period that was public on each date. The returned
// event points are intended for a stepped line; no future release is backfilled.
// Values stay in the company's saved EPS currency and split basis.
export function buildEpsSeries(company, {start, end, maxAgeDays = 550} = {}) {
  const first = utcDate(start), last = utcDate(end);
  if (first == null || last == null || first > last) return empty();
  const age = finite(maxAgeDays) && maxAgeDays >= 0 ? Math.floor(maxAgeDays) : 550;
  const rows = (Array.isArray(company?.ttmSeries) ? company.ttmSeries : [])
    .map(row => ({row, period: utcDate(row?.periodEnd), known: utcDate(row?.knownFrom)}))
    .filter(item => item.period != null && item.known != null);
  const events = new Set([first, last]);
  for (const item of rows) {
    const expires = item.period + (age + 1) * DAY;
    if (item.known >= first && item.known <= last) events.add(item.known);
    if (expires >= first && expires <= last) events.add(expires);
  }
  const points = [...events].sort((a, b) => a - b).map(time => {
    let best = null;
    // Equal period ends use the later saved entry, matching the existing PER
    // model's knownTtm rule without sorting or otherwise mutating the input.
    for (const item of rows) {
      if (item.known <= time && (!best || item.period >= best.period)) best = item;
    }
    const valid = best && time - best.period <= age * DAY && finite(best.row.eps);
    return {
      date: dateString(time), x: time,
      eps: valid ? best.row.eps : null,
      periodEnd: best?.row.periodEnd ?? null,
      knownFrom: best?.row.knownFrom ?? null,
    };
  });
  const startEPS = points[0].eps, endEPS = points.at(-1).eps;
  const baseEPS = startEPS != null && startEPS > 0 ? startEPS : null;
  return {
    points, startEPS, endEPS, baseEPS,
    indexPoints: baseEPS == null ? null : points.map(point => ({...point, eps: point.eps == null ? null : point.eps / baseEPS * 100})),
    changePercent: baseEPS != null && endEPS != null ? (endEPS / baseEPS - 1) * 100 : null,
  };
}
