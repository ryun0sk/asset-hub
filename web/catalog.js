// Catalog helpers and hash routing. Pure functions so tests can run them without a DOM.
// Routes: #home (default), #cost, #r/<entryId>/<itemIndex>[/<heading id>].
export const KIND_LABELS = Object.freeze({theme: 'テーマ', company: '企業'});
export const TYPE_LABELS = Object.freeze({html: 'HTML', md: '文書', pdf: 'PDF', code: 'コード'});

export function entries(catalog) {
  return (catalog?.groups || []).flatMap(group => (group.entries || []).map(entry => ({...entry, group: group.id})));
}

// Every dated snapshot of the same target (kind + slug), newest first. The first one is the
// current version; the rest are archives.
export function versionsOf(catalog, entry) {
  if (!entry) return [];
  return entries(catalog).filter(e => e.kind === entry.kind && e.slug === entry.slug).sort((a, b) => b.date.localeCompare(a.date));
}

export const isLatest = (catalog, entry) => versionsOf(catalog, entry)[0]?.id === entry?.id;

// The newest snapshot of each target, in catalog order (groups keep their own order).
export function latestGroups(catalog) {
  const newest = new Map();
  for (const entry of entries(catalog)) {
    const key = `${entry.kind}/${entry.slug}`;
    if (!newest.has(key) || entry.date > newest.get(key).date) newest.set(key, entry);
  }
  return (catalog?.groups || []).map(group => ({...group, entries: (group.entries || []).filter(entry => newest.get(`${entry.kind}/${entry.slug}`)?.id === entry.id)}));
}

// Index of the same document (same path inside the dated folder) in another version, else 0.
export function counterpartIndex(item, to) {
  const tail = path => String(path || '').split('/').slice(4).join('/');
  const same = other => tail(other.path) === tail(item?.path) && (other.view || '') === (item?.view || '');
  const index = (to?.items || []).findIndex(same);
  return index >= 0 ? index : 0;
}

export function parseRoute(hash) {
  const value = String(hash || '').replace(/^#/, '');
  if (value === 'cost') return {view: 'cost'};
  const match = value.match(/^r\/([^/]+)(?:\/(\d+)(?:\/([^/]+))?)?\/?$/);
  if (match) {
    const decode = raw => { try { return decodeURIComponent(raw); } catch { return raw; } };
    return {view: 'research', entryId: decode(match[1]), index: match[2] ? Number(match[2]) : 0, anchor: match[3] ? decode(match[3]) : ''};
  }
  return {view: 'home'};
}

export const routeFor = (entryId, index = 0, anchor = '') => `#r/${encodeURIComponent(entryId)}/${index}${anchor ? `/${encodeURIComponent(anchor)}` : ''}`;

// Find the catalog entry and item for a route; falls back to the first item.
export function lookup(catalog, route) {
  if (route?.view !== 'research') return null;
  const entry = entries(catalog).find(e => e.id === route.entryId);
  if (!entry || !entry.items?.length) return null;
  const index = Number.isInteger(route.index) && route.index >= 0 && route.index < entry.items.length ? route.index : 0;
  return {entry, item: entry.items[index], index};
}

// Map a repo-relative path (and optional heading id) to an in-app route when it is a catalog item.
export function routeForPath(catalog, path, anchor = '') {
  if (path === 'README.md') return '#home';
  for (const entry of entries(catalog)) {
    const index = (entry.items || []).findIndex(item => item.path === path);
    if (index >= 0) return routeFor(entry.id, index, anchor);
  }
  return null;
}

// Files under research/ are served at the same path; everything else is not public.
export const fileUrl = path => /^research\/[^?#]+$/.test(String(path || '')) && !String(path).split('/').includes('..') ? '/' + String(path).split('/').map(encodeURIComponent).join('/') : null;

// URL to open a catalog item: its file, plus ?view=<name> when the item is a named view of that file.
export const itemUrl = item => {
  const base = fileUrl(item?.path);
  return base && item.view ? `${base}?view=${encodeURIComponent(item.view)}` : base;
};

export function stats(catalog) {
  const all = entries(catalog);
  const dates = all.map(e => e.date).filter(Boolean).sort();
  const latest = latestGroups(catalog).flatMap(group => group.entries);
  return {
    themes: new Set(all.filter(e => e.kind === 'theme').map(e => e.slug)).size,
    companies: new Set(all.filter(e => e.kind === 'company').map(e => e.slug)).size,
    latest: dates.at(-1) || null,
    documents: latest.reduce((sum, e) => sum + (e.items || []).length, 0),
    archives: all.length - latest.length,
  };
}
