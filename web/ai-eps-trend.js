import {buildEpsSeries} from './ai-eps-model.js';

const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[ch]));
const number = value => Number.isFinite(value) ? new Intl.NumberFormat('ja-JP', {maximumFractionDigits: 2}).format(value) : '取得なし';
const dateTime = date => Date.parse(`${date}T00:00:00Z`);

export function mountEpsTrend(host, doc) {
  if (!host) return () => {};
  let valuation, prices;
  try {
    valuation = JSON.parse(doc.getElementById('valuation-data').textContent);
    prices = JSON.parse(doc.getElementById('price-data').textContent);
    if (!Array.isArray(valuation.companies) || !Array.isArray(prices.companies)) throw new Error('missing companies');
  } catch {
    host.innerHTML = '<p class="empty" role="alert">この保存版のEPSデータを表示できません。別の調査の版を選んでください。</p>';
    return () => {};
  }
  const bySymbol = new Map(valuation.companies.map(company => [company.symbol, company]));
  const priceBySymbol = new Map(prices.companies.map(company => [company.symbol, company]));
  const view = doc.defaultView;
  let active = true, charts = [];
  host.innerHTML = `<div class="ai-eps-heading"><div><h3>直近12か月の実績EPS（TTM）</h3><p>決算の公表後に更新する階段状の線です。0・赤字も表示します。</p></div><label>表示方法<select data-eps-mode><option value="native">EPS実額（現地通貨別）</option><option value="index">開始時点＝100で比較</option></select></label></div>
    <p class="ai-eps-method">TTM＝直近12か月の利益／株。実額は通貨ごとにグラフを分け、為替換算しません。指数は選択期間の開始日にEPSが正の企業だけを表示します。既存43社は10/3保存値、発電3社は10/18確認値です。</p>
    <p class="ai-eps-period" data-eps-period></p><div class="ai-eps-charts" data-eps-charts></div>
    <div class="ai-actual-scroll" role="region" aria-label="期間の始点と終点の実績EPS" tabindex="0"><table class="ai-actual-table"><caption>選択期間の開始日と終了日に分かっていた実績EPS</caption><thead><tr><th scope="col">企業</th><th scope="col">通貨／株</th><th scope="col">開始EPS</th><th scope="col">終了EPS</th><th scope="col">増減率</th><th scope="col">終了EPSの対象期</th></tr></thead><tbody data-eps-summary></tbody></table></div>
    <p class="ai-eps-method" data-eps-missing></p><p class="ai-eps-warning" data-eps-warning hidden></p>
    <details class="ai-actual-notes"><summary>計算基準・データの時点</summary><p>PER推移の保存版と同じTTM EPSを使用します。各期の公表済み日から適用し、欠損や古すぎるEPSは線を切ります。既存43社は2026-10-03版の保存値、発電3社は2026-10-18確認値です。7銘柄の新しい月次実績表は「PERの推移」で確認できます。</p><p>既存43社の公表日は原則として期末＋45日と仮定しています。発電3社は公式公表日を使用します。EPSの再構成・株数変動・丸めにより公式通期値と差が生じる場合があります。会社予想とアナリスト予想は「EPS予想・決算」に表示します。</p></details>`;
  const mode = host.querySelector('[data-eps-mode]');
  const plotHost = host.querySelector('[data-eps-charts]');
  const destroy = () => { for (const chart of charts) chart.destroy(); charts = []; };
  const render = () => {
    if (!active) return;
    destroy();
    const selected = [...doc.querySelectorAll('#fund-choices input:checked')].map(input => input.value);
    host.hidden = selected.length === 0;
    if (host.hidden) return;
    const start = doc.getElementById('start').value, end = doc.getElementById('end').value;
    const rows = selected.map(symbol => {
      const company = bySymbol.get(symbol), price = priceBySymbol.get(symbol);
      if (!company) return null;
      const cutoff = price?.rows?.at(-1)?.date || end;
      const effectiveEnd = end < cutoff ? end : cutoff;
      const result = buildEpsSeries(company, {start, end: effectiveEnd, maxAgeDays: valuation.method?.maxAgeDays});
      return {company, ...result, end: effectiveEnd};
    }).filter(Boolean);
    host.querySelector('[data-eps-period]').textContent = `${start} → ${end}。各社の保存データ最終日まで表示します。`;
    const indexed = mode.value === 'index';
    const groups = new Map();
    const missing = [];
    for (const row of rows) {
      const points = indexed ? row.indexPoints : row.points;
      if (!points?.some(point => Number.isFinite(point.eps))) { missing.push(row.company.name); continue; }
      const key = indexed ? 'index' : row.company.epsCurrency;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push({...row, chartPoints: points});
    }
    plotHost.innerHTML = '';
    // The shell's tokens are already loaded. Render before the iframe's async
    // stylesheet so its initial content height is available to fitFrame().
    const styles = window.getComputedStyle(document.body);
    const colors = ['--chart-cat-1', '--chart-cat-2', '--chart-cat-3', '--chart-cat-4', '--chart-cat-5', '--chart-cat-6'].map(token => styles.getPropertyValue(token).trim());
    const symbolColors = new Map([...doc.querySelectorAll('#fund-choices input')].map(input => {
      const swatch = input.closest('label')?.querySelector('.swatch');
      return [input.value, swatch ? view.getComputedStyle(swatch).backgroundColor : colors[selected.indexOf(input.value) % colors.length]];
    }));
    const ink = styles.getPropertyValue('--muted').trim(), line = styles.getPropertyValue('--line').trim();
    const font = {family: styles.getPropertyValue('--font-family-sans').trim(), size: Number(styles.getPropertyValue('--chart-font-axis'))};
    for (const [currency, members] of groups) {
      const card = doc.createElement('div');
      card.className = 'ai-eps-chart';
      card.innerHTML = `<h4>${indexed ? '開始時点＝100' : `${esc(currency)}／株`}</h4><div class="ai-eps-legend" aria-label="グラフの凡例">${members.map(row => `<span><i aria-hidden="true"></i>${esc(row.company.name)}</span>`).join('')}</div><div class="ai-eps-plot"><canvas role="img" aria-label="${esc(members.map(row => row.company.name).join('・'))}の実績TTM EPS推移"></canvas></div><p class="ai-eps-chart-note">${members.map(row => `${esc(row.company.name)}：${esc(row.end)}まで`).join(' ／ ')}</p>`;
      plotHost.append(card);
      card.querySelectorAll('.ai-eps-legend i').forEach((marker, i) => { marker.style.backgroundColor = symbolColors.get(members[i].company.symbol); });
      const canvas = card.querySelector('canvas');
      if (!view.Chart) { card.innerHTML += '<p class="empty" role="alert">グラフを表示できません。下の表でEPSを確認できます。</p>'; continue; }
      const datasets = members.map(row => ({
        label: row.company.name, symbol: row.company.symbol,
        data: row.chartPoints.flatMap((point, i, points) => {
          const previous = points[i - 1];
          // Retain a known EPS up to expiry, then break the line at null.
          const edge = point.eps == null && previous?.eps != null && point.x > previous.x
            ? [{...previous, x: point.x - 1, date: new Date(point.x - 1).toISOString().slice(0, 10), y: previous.eps}]
            : [];
          return [...edge, {...point, y: point.eps}];
        }),
        borderColor: symbolColors.get(row.company.symbol), backgroundColor: symbolColors.get(row.company.symbol),
        // Chart.js 'before' holds the previous EPS until the next release date.
        borderWidth: 2, pointRadius: 2, pointHoverRadius: 4, stepped: 'before', spanGaps: false,
      }));
      charts.push(new view.Chart(canvas, {type: 'line', data: {datasets}, options: {
        responsive: true, maintainAspectRatio: false, animation: false, parsing: false,
        interaction: {mode: 'nearest', intersect: false},
        plugins: {legend: {display: false}, tooltip: {callbacks: {
          title: items => items[0]?.raw.date || '',
          label: context => `${context.dataset.label}：${number(context.parsed.y)}${indexed ? '（開始＝100）' : ` ${currency}／株`}（${context.raw.periodEnd || '対象期なし'}期）`,
        }}},
        scales: {
          x: {type: 'linear', min: dateTime(start), max: dateTime(end), grid: {color: line}, ticks: {color: ink, font, maxTicksLimit: 6, callback: value => {const date = new Date(value); return `${date.getUTCFullYear()}/${date.getUTCMonth() + 1}`;}}},
          y: {type: 'linear', grid: {color: line}, ticks: {color: ink, font}, title: {display: true, text: indexed ? '開始時点＝100' : `${currency}／株`, color: ink, font}},
        },
      }}));
    }
    if (!groups.size) plotHost.innerHTML = '<p class="empty" role="status">この期間・表示方法で描けるEPSがありません。期間や表示方法を変更してください。</p>';
    host.querySelector('[data-eps-summary]').innerHTML = rows.map(row => `<tr><th scope="row">${esc(row.company.name)}<small>${esc(row.company.symbol)}</small></th><td>${esc(row.company.epsCurrency)}</td><td>${number(row.startEPS)}</td><td>${number(row.endEPS)}</td><td>${row.changePercent == null ? '算出不可' : `${row.changePercent >= 0 ? '+' : ''}${number(row.changePercent)}%`}</td><td>${esc(row.endEPS == null ? '取得なし' : row.points.at(-1)?.periodEnd || '取得なし')}<small>表示終了 ${esc(row.end)}</small></td></tr>`).join('');
    host.querySelector('[data-eps-missing]').textContent = missing.length ? `${indexed ? '開始日のEPSが正でない、または取得できないため指数に表示しない企業' : 'この期間に取得できるEPSがない企業'}：${missing.join('、')}` : '';
    const warnings = [];
    if (selected.includes('GEV')) warnings.push('GE Vernova：税便益・Prolec再評価益を含みます。');
    if (selected.includes('4062.T')) warnings.push('イビデン：株式売却益を含む実績です。売却益を除く推計は「PERの推移」の月次表で確認できます。');
    const warning = host.querySelector('[data-eps-warning]');
    warning.hidden = !warnings.length;
    warning.textContent = warnings.join(' ');
  };
  const click = event => { if (event.target.closest?.('[data-chain], [data-fund-period]')) render(); };
  const change = event => { if (event.target.matches?.('#fund-choices input, #start, #end, [data-eps-mode]')) render(); };
  doc.addEventListener('click', click);
  doc.addEventListener('change', change);
  render();
  return () => { active = false; destroy(); doc.removeEventListener('click', click); doc.removeEventListener('change', change); };
}
