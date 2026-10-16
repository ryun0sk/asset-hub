import {UiCharts} from './charts.js';
import {STOCKS, readPriceHistory, periodRows, priceSummary} from './stock-chart-model.js';

const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const money = value => value === null || value === undefined ? '—' : new Intl.NumberFormat('ja-JP', {style:'currency', currency:'USD', minimumFractionDigits:2, maximumFractionDigits:2}).format(value);
const percent = value => value === null || value === undefined ? '—' : `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
const root = document.getElementById('stock-chart');
const selector = document.getElementById('stock-period');
const symbol = document.body.dataset.stockSymbol || 'SPCX';
const stock = STOCKS[symbol];
let history;

function render() {
  const rows = periodRows(history.rows, Number(selector.value)), summary = priceSummary(history.rows), window = priceSummary(rows);
  UiCharts.destroy(root);
  root.innerHTML = `<div class="stock-metrics">
    <div><span>最終終値 · ${esc(summary.last.date)}</span><strong>${money(summary.last.close)}</strong></div>
    <div><span>前取引日比</span><strong>${summary.change > 0 ? '+' : ''}${money(summary.change)} <small>${percent(summary.changePercent)}</small></strong></div>
    <div><span>表示期間の騰落率</span><strong>${percent(window.periodPercent)}</strong></div>
  </div>
  <p class="stock-caption">${esc(rows[0].date)}〜${esc(rows.at(-1).date)} · ${rows.length}取引日 · 米ドル建て通常取引の終値</p>
  ${UiCharts.render({title:`${stock.label}の日次終値`,unit:'yen',currency:'USD',includeZero:false,labels:'none',slot:1,rows:rows.map(row=>({label:row.date.slice(5).replace('-','/'),name:row.date,group:`${row.date.slice(0,4)}年`,close:row.close})),series:[{key:'close',label:`${stock.label}終値`,kind:'line',tone:'primary'}]})}
  <p class="stock-caption">縦軸は表示期間の価格に合わせています。休場日は除き、取引日を等間隔で表示。点にカーソルを合わせるか、左右キーで日付・終値を確認できます。</p>
  <details class="stock-data"><summary>表示期間の日次データ</summary><div class="stock-table-scroll"><table><thead><tr><th scope="col">取引日（米国）</th><th scope="col">終値（USD）</th></tr></thead><tbody>${rows.map(row=>`<tr><td>${esc(row.date)}</td><td>${money(row.close)}</td></tr>`).join('')}</tbody></table></div></details>`;
  UiCharts.mount(root);
}

try {
  if (!stock) throw new Error('対象銘柄を確認できません。');
  const response = await fetch(stock.historyUrl);
  if (!response.ok) throw new Error('取得できません。');
  history = readPriceHistory(await response.json(), symbol);
  render();
  selector.disabled = false;
  selector.addEventListener('change', render);
} catch {
  root.innerHTML = '<p role="alert">株価チャートを読み込めませんでした。再読み込みするか、下の出典ページで確認してください。</p>';
}
