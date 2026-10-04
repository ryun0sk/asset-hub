// Loader for the weekly asset state (same shape as costs.js): fetch /api/assets, keep the last good
// payload, and render the single 保有・推移 page into #assetSection. Chart choices (range, stacked or
// lines, unchecked classes / positions) live here and survive re-renders until the page is reloaded.
import {assetsView} from './asset-view.js';
import {UiCharts} from './charts.js';

let catalogRef = null, payload = null, loading = false, error = '', loadedAt = 0, range = '52', mode = 'stack', active = false;
const hiddenClasses = new Set(), hiddenPositions = new Set();
const TTL = 60000;

// `status` is always an object; `state` is null until the first snapshot is pushed.
export const validPayload = next => Boolean(next && typeof next === 'object' && next.status && typeof next.status === 'object'
  && (next.state === null || (next.state && typeof next.state === 'object' && Array.isArray(next.state.snapshots))));

const host = () => document.getElementById('assetSection');

function render(focus = null) {
  const root = host();
  if (!active || !root || root.hidden) return;
  UiCharts.destroy(root);
  root.innerHTML = assetsView(payload, catalogRef, {loading, error, range, mode, hiddenClasses, hiddenPositions});
  UiCharts.mount(root);
  const rangeSelect = root.querySelector('#asset-range');
  if (rangeSelect) rangeSelect.onchange = () => { range = rangeSelect.value; render({select: true}); };
  root.querySelectorAll('input[name="asset-mode"]').forEach(input => { input.onchange = () => { mode = input.value; render({mode: input.value}); }; });
  root.querySelectorAll('input[data-toggle]').forEach(input => {
    input.onchange = () => {
      const [kind, ...rest] = input.dataset.toggle.split(':'), key = rest.join(':');
      const hidden = kind === 'c' ? hiddenClasses : hiddenPositions;
      if (input.checked) hidden.delete(key); else hidden.add(key);
      render({toggle: input.dataset.toggle});
    };
  });
  if (!focus) return;
  // Re-rendering replaces the controls; hand the keyboard focus to the same one.
  const next = focus.toggle ? [...root.querySelectorAll('input[data-toggle]')].find(input => input.dataset.toggle === focus.toggle)
    : focus.mode ? root.querySelector(`input[name="asset-mode"][value="${focus.mode}"]`) : root.querySelector('#asset-range');
  next?.focus();
}

async function load() {
  if (loading) return;
  loading = true; error = ''; render();
  try {
    const response = await fetch('/api/assets');
    if (!response.ok) throw Error();
    const next = await response.json();
    if (!validPayload(next)) throw Error();
    payload = next; loadedAt = Date.now();
  } catch {
    error = payload ? '資産データを更新できませんでした。前回の表示を保持しています。' : '資産データを読み込めませんでした。';
  } finally {
    loading = false; render();
  }
}

// `catalog` links holdings to their research entries; it may still be null while the catalog loads.
export function showAssets(catalog) {
  active = true;
  catalogRef = catalog;
  if (!payload || Date.now() - loadedAt > TTL) load(); else render();
}
export const leaveAssets = () => { active = false; };

export function initAssets() {
  load();
  // No polling: the state changes once a week. Re-read when the tab comes back after a while.
  document.addEventListener('visibilitychange', () => { if (!document.hidden && Date.now() - loadedAt > TTL) load(); });
}

