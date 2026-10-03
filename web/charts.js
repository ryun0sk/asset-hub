// Shared chart component. See docs/design-system.md for its public contract.
// Layout geometry belongs here; visual tokens belong in tokens.css and charts.css.
export const UiCharts = (() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const number = (value, digits = 2) => value.toLocaleString('ja-JP', {maximumFractionDigits: digits});
  const geometry = Object.freeze({height: 260, left: 72, right: 24, top: 28, bottom: 48, minWidth: 280, lineSlot: 44, barSlot: 24, axisLabelWidth: 40, labelOffset: 14, nearOffset: 7.5, labelGap: 16});
  const tones = new Set(['primary', 'secondary', 'target', 'accent', 'negative', 'context']);
  const units = new Set(['count', 'man', 'yen']);
  let sequence = 0;
  const mounted = new WeakMap();

  // Values are numbers in the unit given by `unit`: count (件), man (円を万円で表示), yen (currency).
  function formats(options) {
    const currency = options.currency || 'JPY';
    const money = (value, digits) => new Intl.NumberFormat('ja-JP', {style: 'currency', currency, minimumFractionDigits: digits[0], maximumFractionDigits: digits[1]}).format(value);
    if (options.unit === 'man') return {tick: v => number(v / 10000), value: v => `${number(v / 10000)}万`, exact: v => `${number(v / 10000)}万円`, label: '万円'};
    if (options.unit === 'yen') return {tick: v => money(v, [0, 2]), value: v => money(v, [0, 2]), exact: v => money(v, [2, 2]), label: currency === 'JPY' ? '円' : currency};
    return {tick: v => number(v), value: v => `${number(v)}件`, exact: v => `${number(v)}件`, label: '件'};
  }

  // Nice 1/2/5 steps. `integer` keeps steps whole (counts); `minimumRange` avoids a flat scale.
  function domain(values, {floor = 0, ceiling = 0, minimumRange = 1, integer = false} = {}) {
    const valid = values.filter(finite);
    const low = Math.min(0, floor, ...valid), high = Math.max(0, ceiling, ...valid);
    const rough = Math.max(high - low, minimumRange) / 4;
    const power = 10 ** Math.floor(Math.log10(rough)), fraction = rough / power;
    let step = (fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10) * power;
    if (integer) step = Math.max(1, Math.ceil(step));
    const min = Math.floor(low / step) * step, max = Math.max(min + step, Math.ceil(high / step) * step);
    const ticks = Array.from({length: Math.round((max - min) / step) + 1}, (_, i) => min + i * step);
    return {min, max, ticks};
  }

  function normalize(options) {
    const series = options.series.map(s => ({...s, kind: s.kind === 'bar' ? 'bar' : 'line', marker: s.marker === 'ring' ? 'ring' : 'solid', tone: tones.has(s.tone) ? s.tone : 'primary'}));
    return {...options, unit: units.has(options.unit) ? options.unit : 'count', series, rows: options.rows.map(row => ({...row}))};
  }

  function layout(input, availableWidth = 0) {
    const options = normalize(input), {rows, series} = options, format = formats(options);
    const bars = series.filter(s => s.kind === 'bar');
    const slot = options.slot || (bars.length ? geometry.barSlot * bars.length : geometry.lineSlot);
    const width = Math.max(geometry.minWidth, availableWidth, rows.length * slot + geometry.left + geometry.right);
    const step = (width - geometry.left - geometry.right) / Math.max(1, rows.length);
    const scale = domain(rows.flatMap(r => series.map(s => r[s.key])), {floor: options.floor, ceiling: options.ceiling, minimumRange: options.minimumRange || (options.unit === 'man' ? 10000 : options.unit === 'count' ? 4 : 1), integer: options.unit === 'count'});
    const height = options.height || geometry.height;
    const x = i => geometry.left + step * (i + 0.5);
    const y = value => geometry.top + (scale.max - value) / (scale.max - scale.min) * (height - geometry.top - geometry.bottom);
    const barWidth = Math.max(3, Math.min(22, (step - 8) / Math.max(1, bars.length)));
    const plots = series.map(s => {
      let connected = false, path = '';
      const points = rows.map((row, index) => {
        const value = row[s.key];
        if (!finite(value)) {connected = false; return null;}
        const point = {x: x(index) + (s.kind === 'bar' ? (bars.indexOf(s) - (bars.length - 1) / 2) * (barWidth + 2) : 0), y: y(value), value, index};
        path += `${connected ? 'L' : 'M'}${point.x},${point.y} `;
        connected = true;
        return point;
      });
      return {series: s, path, points};
    });
    const labels = [];
    if (options.labels !== 'none') {
      const placed = [];
      plots.forEach(({series: s, points}, seriesIndex) => points.forEach(point => {
        if (!point) return;
        // Series that share a value at a month keep one label; the tooltip lists all of them.
        if (plots.slice(0, seriesIndex).some(other => other.points[point.index]?.value === point.value)) return;
        const text = format.value(point.value), halfWidth = text.length * 3.1;
        const offsets = s.kind === 'bar' && point.value < 0 ? [14, -14, 30, -30] : [-14, 14, -30, 30];
        const near = options.labels === 'near-point';
        const candidates = near ? [point.y - geometry.nearOffset] : offsets.map(offset => point.y + offset);
        const labelY = candidates.find(candidate => candidate >= 12 && candidate <= height - geometry.bottom + 18 && (near || placed.every(other => Math.abs(point.x - other.x) >= halfWidth + other.halfWidth + 4 || Math.abs(candidate - other.y) >= geometry.labelGap)));
        // A dense label that cannot fit stays available through the tooltip.
        if (labelY === undefined) return;
        placed.push({x: point.x, y: labelY, halfWidth});
        labels.push({x: point.x, y: labelY, text, tone: s.tone});
      }));
    }
    return {options, format, width, height, scale, plots, labels, step, barWidth, x, y, labelEvery: Math.max(1, Math.ceil(geometry.axisLabelWidth / step))};
  }

  function exact(value, model) {
    return finite(value) ? model.format.exact(value) : (model.options.missingLabel || '未確認');
  }
  function description(row, model) {
    return `${row.name || row.label} ${model.options.series.map(s => `${s.label} ${exact(row[s.key], model)}`).join('、')}`;
  }
  function tooltip(row, model) {
    return `<strong>${esc(row.name || row.label)}</strong>${model.options.series.map(s => `<div><span>${esc(s.label)}</span><b>${esc(exact(row[s.key], model))}</b></div>`).join('')}`;
  }

  function svg(model, id) {
    const {options, format, width, height, scale, plots, labels, step, barWidth, x, y, labelEvery} = model, {rows} = options;
    const grid = scale.ticks.map(v => `<line class="ui-chart-grid${v === 0 ? ' ui-chart-zero' : ''}" x1="${geometry.left}" x2="${width - geometry.right}" y1="${y(v)}" y2="${y(v)}"/><text class="ui-chart-axis" x="${geometry.left - 10}" y="${y(v)}" text-anchor="end">${esc(format.tick(v))}</text>`).join('');
    const marks = plots.map(({series: s, points, path}) => {
      const tone = `ui-chart-tone-${s.tone}${s.dashed ? ' ui-chart-dashed' : ''}`;
      if (s.kind === 'bar') return points.filter(Boolean).map(p => `<rect class="ui-chart-bar ${tone}" x="${p.x - barWidth / 2}" y="${Math.min(p.y, y(0))}" width="${barWidth}" height="${Math.max(1, Math.abs(p.y - y(0)))}" rx="2"/>`).join('');
      return `<path class="ui-chart-line ${tone}" d="${path}"/>${points.filter(Boolean).map(p => `<circle class="ui-chart-point${s.marker === 'ring' ? ' ui-chart-point-ring' : ''} ui-chart-tone-${s.tone}" cx="${p.x}" cy="${p.y}"/>`).join('')}`;
    }).join('');
    const axis = rows.map((row, i) => {
      if (i % labelEvery && i !== rows.length - 1) return '';
      const group = row.group && (i === 0 || rows[i - 1].group !== row.group) ? `<text class="ui-chart-axis ui-chart-group" x="${x(i)}" y="${height - 12}" text-anchor="middle">${esc(row.group)}</text>` : '';
      return `<text class="ui-chart-axis" x="${x(i)}" y="${height - 30}" text-anchor="middle">${esc(row.label)}</text>${group}`;
    }).join('');
    return `<svg class="ui-chart-svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="group" aria-label="${esc(options.title)}。左右キーで移動して値を確認できます。">
      <g aria-hidden="true">${grid}${marks}${axis}<g>${labels.map(l => `<text class="ui-chart-value ui-chart-tone-${l.tone}" x="${l.x}" y="${l.y}" text-anchor="middle">${esc(l.text)}</text>`).join('')}</g></g>
      ${rows.map((row, i) => `<rect class="ui-chart-hit" data-chart-index="${i}" x="${x(i) - step / 2}" y="${geometry.top - 12}" width="${step}" height="${height - geometry.top - geometry.bottom + 24}" tabindex="${i === 0 ? 0 : -1}" role="button" aria-label="${esc(description(row, model))}" aria-describedby="${id}-tooltip"/>`).join('')}</svg>`;
  }

  function render(input) {
    const options = normalize(input);
    if (!options.rows.some(r => options.series.some(s => finite(r[s.key])))) return `<p class="ui-chart-empty" role="status">${esc(options.emptyText || '表示できるデータがありません。')}</p>`;
    const model = layout(options), id = `chart-${++sequence}`;
    return `<div class="ui-chart" data-chart-options="${esc(JSON.stringify(options))}" id="${id}">
      <div class="ui-chart-legend">${options.series.map(s => `<span><i aria-hidden="true" class="ui-chart-key ui-chart-key-${s.kind}${s.dashed ? ' ui-chart-dashed' : ''} ui-chart-tone-${s.tone}"></i>${esc(s.label)}</span>`).join('')}<span>単位：${esc(model.format.label)}</span></div>
      <div class="ui-chart-scroll" tabindex="-1" role="region" aria-label="${esc(options.title)}。横にスクロールできます">${svg(model, id)}</div>
      <div class="ui-chart-tooltip" id="${id}-tooltip" role="tooltip" hidden></div></div>`;
  }

  function destroy(host) {
    mounted.get(host)?.forEach(dispose => dispose());
    mounted.delete(host);
  }

  function mount(host) {
    destroy(host);
    const disposers = [...host.querySelectorAll('.ui-chart')].map(wrapper => {
      const options = JSON.parse(wrapper.dataset.chartOptions);
      const scroller = wrapper.querySelector('.ui-chart-scroll'), tip = wrapper.querySelector('.ui-chart-tooltip');
      const abort = new AbortController(), on = (target, name, handler) => target.addEventListener(name, handler, {signal: abort.signal});
      let width = -1, dismissed = null, model = null;
      const hide = () => {tip.hidden = true;};
      const show = (target, event) => {
        const index = Number(target.dataset.chartIndex);
        if (dismissed === index) return;
        model ||= layout(options);
        tip.innerHTML = tooltip(model.options.rows[index], model); tip.hidden = false;
        const bounds = wrapper.getBoundingClientRect(), hit = target.getBoundingClientRect();
        const px = event?.clientX ?? hit.left + hit.width / 2, py = event?.clientY ?? hit.top;
        tip.style.left = Math.max(0, Math.min(px - bounds.left + 12, bounds.width - tip.offsetWidth)) + 'px';
        tip.style.top = Math.max(0, py - bounds.top - tip.offsetHeight - 12) + 'px';
      };
      const targetOf = event => event.target.closest('[data-chart-index]');
      on(wrapper, 'pointermove', event => {const target = targetOf(event); if (target) show(target, event);});
      on(wrapper, 'pointerleave', () => {dismissed = null; hide();});
      on(wrapper, 'focusin', event => {const target = targetOf(event); if (target) {dismissed = null; show(target);}});
      on(wrapper, 'focusout', hide);
      on(wrapper, 'click', event => {const target = targetOf(event); if (target) {dismissed = null; show(target, event);}});
      on(scroller, 'scroll', () => {
        hide();
        const target = document.activeElement;
        if (wrapper.contains(target) && target.matches('[data-chart-index]')) show(target);
      });
      on(wrapper, 'keydown', event => {
        const target = targetOf(event); if (!target) return;
        if (event.key === 'Enter' || event.key === ' ') {event.preventDefault(); dismissed = null; show(target); return;}
        if (event.key === 'Escape') {dismissed = Number(target.dataset.chartIndex); hide(); return;}
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        const hits = [...wrapper.querySelectorAll('[data-chart-index]')], current = Number(target.dataset.chartIndex);
        const index = event.key === 'Home' ? 0 : event.key === 'End' ? hits.length - 1 : Math.max(0, Math.min(hits.length - 1, current + (event.key === 'ArrowLeft' ? -1 : 1)));
        hits.forEach((hit, i) => hit.setAttribute('tabindex', i === index ? '0' : '-1'));
        hits[index].focus({preventScroll: true}); hits[index].scrollIntoView({block: 'nearest', inline: 'nearest'});
        show(hits[index]);
      });
      // One SVG unit stays one CSS pixel: redraw at the container width instead of scaling.
      const resize = () => {
        const available = Math.floor(scroller.getBoundingClientRect().width);
        if (!available || available === width) return;
        width = available;
        const focused = wrapper.contains(document.activeElement) ? document.activeElement.dataset.chartIndex : null;
        const active = wrapper.querySelector('[data-chart-index][tabindex="0"]')?.dataset.chartIndex || '0';
        model = layout(options, available);
        scroller.innerHTML = svg(model, wrapper.id); hide();
        const hits = [...scroller.querySelectorAll('[data-chart-index]')];
        hits.forEach(hit => hit.setAttribute('tabindex', hit.dataset.chartIndex === active ? '0' : '-1'));
        if (focused != null) hits[Number(focused)]?.focus({preventScroll: true});
      };
      const observer = new ResizeObserver(resize); observer.observe(scroller); resize();
      return () => {observer.disconnect(); abort.abort();};
    });
    mounted.set(host, disposers);
  }

  return Object.freeze({render, mount, destroy, layout, domain, geometry, tooltip});
})();
