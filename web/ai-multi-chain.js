// The immutable research page keeps its state in classic-script lexical bindings.
// Load this adapter as a classic script in that page, after its own script has run.
(function () {
  'use strict';
  if (window.ASSET_MULTI_CHAIN) return;
  if (typeof CAT === 'undefined' || typeof GROUPS === 'undefined' ||
      typeof activeGroup === 'undefined' || typeof selected === 'undefined' ||
      typeof chooseGroup !== 'function' || typeof renderChainPicker !== 'function' ||
      typeof renderChoices !== 'function' || typeof renderContext !== 'function' ||
      typeof drawChart !== 'function') return;
  const picker = document.getElementById('chain-picker-stages');
  const groupSelect = document.getElementById('group');
  const mode = document.getElementById('mode');
  const catalogGroups = new Map(CAT.groups.map(group => [group.id, group]));
  if (!picker || !groupSelect || !mode || !catalogGroups.has(activeGroup)) return;

  let active = true;
  let chosen = [activeGroup];
  let symbols = [];
  let unionId = '__asset_multi_chain__';
  while (Object.prototype.hasOwnProperty.call(GROUPS, unionId)) unionId += '_';
  const original = {
    activeGroup,
    selected: [...selected],
    mode: mode.value,
    chooseGroup,
    renderChainPicker,
    renderContext,
  };
  const buttons = [...picker.querySelectorAll('[data-chain]')];
  if (buttons.length !== CAT.groups.length) return;
  const originalClicks = new Map(buttons.map(button => [button, button.onclick]));

  const members = ids => [...new Set(ids.flatMap(id => catalogGroups.get(id).symbols))];
  const defaults = id => id === 'nand' || id === 'ssd'
    ? ['285A.T', 'SNDK'].filter(symbol => catalogGroups.get(id).symbols.includes(symbol))
    : catalogGroups.get(id).symbols;
  const updateButtons = () => {
    for (const button of buttons) button.setAttribute('aria-pressed', String(chosen.includes(button.dataset.chain)));
  };
  const updateGroup = () => {
    const groups = chosen.map(id => catalogGroups.get(id));
    const candidates = members(chosen);
    // The original color function reserves red/blue for these two symbols.
    symbols = ['285A.T', 'SNDK'].filter(symbol => candidates.includes(symbol))
      .concat(candidates.filter(symbol => symbol !== '285A.T' && symbol !== 'SNDK'));
    const roles = Object.fromEntries(symbols.map(symbol => [symbol,
      [...new Set(groups.map(group => group.roles?.[symbol]).filter(Boolean))].join(' ／ '),
    ]));
    GROUPS[unionId] = {
      id: unionId,
      name: groups.length ? groups.map(group => group.name).join(' ＋ ') : '工程未選択',
      note: groups.length ? groups.map(group => group.note).filter(Boolean).join(' ') : '比較する工程を1つ以上選んでください。',
      purpose: '選択した工程の企業を重複なく比較します。',
      symbols,
      roles,
    };
    activeGroup = unionId;
    // This hidden single-select belongs to the price panel. An empty value avoids
    // implying that one real stage alone represents the combined comparison.
    groupSelect.value = chosen.length === 1 ? chosen[0] : '';
  };
  const redraw = draw => {
    updateGroup();
    updateButtons();
    if (mode.value === 'dual' && selected.length !== 2) mode.value = 'index';
    renderChoices();
    renderContext();
    if (draw) drawChart();
  };
  const toggle = (id, draw = true) => {
    if (!active || !catalogGroups.has(id)) return;
    const previous = new Set(members(chosen));
    const removing = chosen.includes(id);
    chosen = removing ? chosen.filter(candidate => candidate !== id) : [...chosen, id];
    const next = new Set(members(chosen));
    selected = [...new Set(selected)].filter(symbol => next.has(symbol));
    if (!removing) {
      for (const symbol of defaults(id)) {
        if (!previous.has(symbol) && next.has(symbol) && !selected.includes(symbol)) selected.push(symbol);
      }
    }
    redraw(draw);
  };

  // Replacing onclick preserves ordinary bubbling, used by the newer monthly
  // EPS supplement to follow supported companies after this selection changes.
  for (const button of buttons) button.onclick = () => toggle(button.dataset.chain);
  renderChainPicker = updateButtons;
  renderContext = () => {
    const group = GROUPS[unionId];
    document.getElementById('compare-title').textContent = group.name;
    document.getElementById('context').textContent = group.note;
  };
  // Map/guide links and the hidden original select still mean a single stage.
  // Keep that contract, while the visible comparison buttons toggle stages.
  chooseGroup = (id, draw = true) => {
    if (!active || !catalogGroups.has(id)) return;
    chosen = [id];
    selected = [...defaults(id)];
    redraw(draw);
  };
  const api = {
    getState: () => ({selectedGroups: [...chosen], symbols: [...symbols], selected: [...selected]}),
    cleanup: () => {
      if (!active) return;
      active = false;
      chooseGroup = original.chooseGroup;
      renderChainPicker = original.renderChainPicker;
      renderContext = original.renderContext;
      for (const [button, onclick] of originalClicks) button.onclick = onclick;
      activeGroup = original.activeGroup;
      selected = [...original.selected];
      mode.value = original.mode;
      groupSelect.value = activeGroup;
      delete GROUPS[unionId];
      for (const button of buttons) button.setAttribute('aria-pressed', String(button.dataset.chain === activeGroup));
      renderChoices();
      renderContext();
      drawChart();
      if (window.ASSET_MULTI_CHAIN === api) delete window.ASSET_MULTI_CHAIN;
    },
  };
  window.ASSET_MULTI_CHAIN = api;
  redraw(true);
}());
