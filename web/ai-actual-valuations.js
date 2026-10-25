import {fileUrl} from './catalog.js';

export const ACTUAL_VALUATION_PATH = 'research/themes/ai-actual-valuation/2026-10-18/valuation-history.json';
const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[ch]));
const finite = value => typeof value === 'number' && Number.isFinite(value);
const number = (value, digits = 2) => finite(value) ? value.toLocaleString('ja-JP', {minimumFractionDigits: digits, maximumFractionDigits: digits}) : '—';
const per = (value, eps) => finite(value) && value > 0 && !(finite(eps) && eps <= 0) ? `${number(value, 1)}倍` : '算出不能';
const dates = (start, end) => start && end ? `${start}〜${end}` : '対象期間は出典参照';
const profitBasis = (company, basis) => basis === 'exStockGain' && company.exStockGain ? 'exStockGain' : 'reported';
const series = (company, basis) => profitBasis(company, basis) === 'exStockGain' ? company.exStockGain : company;
const latest = (company, basis) => series(company, basis).monthly.at(-1);
const close = row => row.close ?? row.closeJPY;
const ttmEps = row => row.ttmDilutedEPS ?? row.ttmDilutedEPSJPY;
const halfEps = row => row.halfYearAnnualizedDilutedEPS ?? row.halfYearAnnualizedDilutedEPSJPY;
const currency = company => company.currency || 'JPY';
const currencyLabel = company => ({JPY: '円', USD: '米ドル', EUR: 'ユーロ'}[currency(company)] || currency(company));
const validRows = rows => Array.isArray(rows) && rows.length && rows.every(row => row &&
  /^\d{4}-\d{2}-\d{2}$/.test(row.date) && finite(close(row)) && close(row) > 0);
const reportLink = company => {
  const url = fileUrl(company.reportPath);
  return url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">計算基準・出典 ↗</a>` : '';
};

export function validActualValuations(data) {
  return Boolean(data && typeof data.asOf === 'string' && typeof data.dataAsOf === 'string' &&
    Array.isArray(data.companies) && data.companies.length && data.companies.every(company => company &&
      typeof company.code === 'string' && typeof company.name === 'string' && typeof company.symbol === 'string' &&
      validRows(company.monthly) && (!company.exStockGain || (
        typeof company.exStockGain.label === 'string' && typeof company.exStockGain.basis === 'string' &&
        Array.isArray(company.exStockGain.notes) && company.exStockGain.notes.every(note => typeof note === 'string') &&
        validRows(company.exStockGain.monthly) && company.exStockGain.monthly.length === company.monthly.length &&
        company.exStockGain.monthly.every((row, index) => row.date === company.monthly[index].date && close(row) === close(company.monthly[index]))))));
}

export function actualCompanyForSelection(companies, symbols = [], preferred = '') {
  return companies.find(company => company.symbol === preferred && symbols.includes(preferred)) ||
    symbols.map(symbol => companies.find(company => company.symbol === symbol)).find(Boolean) || null;
}

export function renderActualCompany(company, basis = 'reported') {
  const mode = profitBasis(company, basis), current = series(company, mode), last = latest(company, mode);
  const unit = esc(currencyLabel(company));
  const adjusted = mode === 'exStockGain';
  const notes = [...(company.notes || []), ...(adjusted ? current.notes || [] : [])];
  return `<div class="ai-actual-company-heading"><div><h4>${esc(company.name)} <small>${esc(company.code)}</small></h4><p>${esc(company.basis || 'EPS基準は出典参照')} · ${esc(company.splitBasis || '株式分割は出典参照')}</p></div>${reportLink(adjusted ? {reportPath: current.reportPath || company.reportPath} : company)}</div>
    ${company.exStockGain ? `<div class="ai-actual-heading"><label>利益基準<select data-actual-basis><option value="reported"${!adjusted ? ' selected' : ''}>実績</option><option value="exStockGain"${adjusted ? ' selected' : ''}>${esc(company.exStockGain.label)}</option></select></label></div>` : ''}
    ${adjusted ? `<p class="ai-actual-method">${esc(current.label)}：${esc(current.basis)}</p>` : ''}
    <p class="ai-actual-period">最新の利益対象期間：TTM ${esc(dates(last.profitPeriodStart, last.profitPeriodEnd))} ／ 半年 ${esc(dates(last.halfYearProfitPeriodStart, last.halfYearProfitPeriodEnd))}</p>
    ${notes.length ? `<details class="ai-actual-notes" open><summary>この会社の計算上の注記</summary><ul>${notes.map(note => `<li>${esc(note)}</li>`).join('')}</ul></details>` : ''}
    <div class="ai-actual-scroll" tabindex="0" role="region" aria-label="${esc(company.name)}の月次EPS・PER。横幅が収まらない場合は横スクロールで確認">
      <table class="ai-actual-table"><caption>${esc(company.name)}の${adjusted ? `${esc(current.label)}・` : '実績'}EPS・PER月次推移（${unit}・倍）</caption><thead><tr><th scope="col">時点</th><th scope="col">株価（${unit}）</th><th scope="col">TTM EPS（${unit}）</th><th scope="col">TTM PER</th><th scope="col">半年年換算<br>EPS（${unit}）</th><th scope="col">半年年換算<br>PER</th></tr></thead><tbody>
      ${current.monthly.map(row => `<tr${row === last ? ' class="ai-actual-latest"' : ''} title="${esc(`TTM ${dates(row.profitPeriodStart, row.profitPeriodEnd)} ／ 半年 ${dates(row.halfYearProfitPeriodStart, row.halfYearProfitPeriodEnd)} ／ 決算公表 ${row.reportDate || '出典参照'}`)}"><th scope="row">${esc(row.date)}</th><td>${number(close(row))}</td><td>${number(ttmEps(row))}</td><td>${per(row.trailingPER, ttmEps(row))}</td><td>${number(halfEps(row))}</td><td>${per(row.halfYearAnnualizedPER, halfEps(row))}</td></tr>`).join('')}
      </tbody></table></div>`;
}

export function renderActualValuations(data, symbol = '', basis = 'reported') {
  const selected = data.companies.find(company => company.symbol === symbol) || data.companies[0];
  const selectedBasis = profitBasis(selected, basis);
  const summaryRow = (company, mode = 'reported') => {
    const adjusted = mode === 'exStockGain', last = latest(company, mode);
    return `<tr><th scope="row"><button type="button" data-actual-symbol="${esc(company.symbol)}" data-actual-profit-basis="${mode}" aria-pressed="${company === selected && mode === selectedBasis}">${esc(company.name)}${adjusted ? `：${esc(company.exStockGain.label)}` : ''}</button>${company.warning ? `<small>${esc(company.warning)}</small>` : ''}</th><td>${esc(last.date)}</td><td>${number(close(last))} ${esc(currency(company))}</td><td>${number(ttmEps(last))} ${esc(currency(company))}</td><td>${per(last.trailingPER, ttmEps(last))}</td><td>${per(last.halfYearAnnualizedPER, halfEps(last))}</td></tr>`;
  };
  return `<div class="ai-actual-heading"><div><h3 id="ai-actual-title">${data.companies.length}銘柄の実績EPS・PER月次推移</h3><p>株価は各行の基準日（最大 ${esc(data.asOf)}） · 資料確認 ${esc(data.dataAsOf)} · 現地通貨・株式分割調整後</p></div><label>月次表の銘柄<select data-actual-company>${data.companies.map(company => `<option value="${esc(company.symbol)}"${company === selected ? ' selected' : ''}>${esc(company.name)}（${esc(company.code)}）</option>`).join('')}</select></label></div>
    <p class="ai-actual-method">TTMは発表済みの直近12か月実績。半年年換算は直近6か月実績を2倍した参考値で、会社予想ではありません。各時点で公表済みの決算を使います。EPSの基本・希薄化後の別は各社に表示します。</p>
    <div class="ai-actual-scroll" tabindex="0" role="region" aria-label="${data.companies.length}銘柄の最新EPS・PER比較。基準日と通貨は各行、推計は行名に明記"><table class="ai-actual-table ai-actual-summary"><caption>保存時点のEPS・PER比較（実績／明記した除外推計）</caption><thead><tr><th scope="col">銘柄・利益基準</th><th scope="col">株価基準日</th><th scope="col">株価・通貨</th><th scope="col">TTM EPS・通貨</th><th scope="col">TTM PER</th><th scope="col">半年年換算PER</th></tr></thead><tbody>${data.companies.map(company => summaryRow(company) + (company.exStockGain ? summaryRow(company, 'exStockGain') : '')).join('')}</tbody></table></div>
    <div data-actual-monthly aria-live="polite">${renderActualCompany(selected, selectedBasis)}</div>
    <p class="ai-actual-separation">以下のグラフは${esc(data.chartAsOf || '2026-10-03')}保存版です。上の月次表とは株価・決算の時点と計算基準が異なる銘柄があります。各社の基準日と注記を確認してください。</p>`;
}

// This supplement is separate from the older 43-company forecast snapshot.
// Follow supported companies in its picker, while also allowing comparison across stages.
export function mountActualValuationHistory(host, doc) {
  let active = true, payload = null, selectedSymbol = '', selectedBasis = 'reported';
  const selected = () => [...doc.querySelectorAll('#fund-choices input:checked')].map(input => input.value);
  const choose = (symbol, basis = 'reported') => {
    const company = payload?.companies.find(candidate => candidate.symbol === symbol);
    if (!company) return;
    selectedSymbol = symbol;
    selectedBasis = profitBasis(company, basis);
    host.querySelector('[data-actual-company]').value = symbol;
    host.querySelector('[data-actual-monthly]').innerHTML = renderActualCompany(company, selectedBasis);
    for (const button of host.querySelectorAll('[data-actual-symbol]')) button.setAttribute('aria-pressed', String(button.dataset.actualSymbol === symbol && (button.dataset.actualProfitBasis || 'reported') === selectedBasis));
  };
  const click = event => {
    const button = event.target.closest?.('[data-actual-symbol]');
    if (button && host.contains(button)) choose(button.dataset.actualSymbol, button.dataset.actualProfitBasis);
    else if (event.target.closest?.('[data-chain]') && payload) {
      const company = actualCompanyForSelection(payload.companies, selected());
      if (company) choose(company.symbol);
    }
    if (event.target.closest?.('[data-actual-retry]') && host.contains(event.target)) load();
  };
  const change = event => {
    if (event.target.matches?.('[data-actual-company]') && host.contains(event.target)) choose(event.target.value);
    else if (event.target.matches?.('[data-actual-basis]') && host.contains(event.target)) choose(selectedSymbol, event.target.value);
    else if (event.target.matches?.('#fund-choices input') && payload) {
      const company = actualCompanyForSelection(payload.companies, selected(), event.target.value);
      if (company) choose(company.symbol);
    }
  };
  const load = async () => {
    host.innerHTML = '<p class="ai-actual-method" role="status">実績EPS・PERの月次表を読み込んでいます…</p>';
    try {
      const response = await fetch(fileUrl(ACTUAL_VALUATION_PATH));
      if (!response.ok) throw Error('unavailable snapshot');
      const data = await response.json();
      if (!validActualValuations(data)) throw Error('invalid snapshot');
      if (!active || !host.isConnected) return;
      payload = data;
      selectedSymbol = actualCompanyForSelection(data.companies, selected())?.symbol || data.companies[0].symbol;
      selectedBasis = 'reported';
      host.innerHTML = renderActualValuations(data, selectedSymbol);
    } catch {
      if (active && host.isConnected) host.innerHTML = '<p class="ai-actual-method" role="alert">実績EPS・PERの月次表を読み込めませんでした。<button type="button" data-actual-retry>再試行</button></p>';
    }
  };
  doc.addEventListener('click', click);
  doc.addEventListener('change', change);
  load();
  return () => { active = false; doc.removeEventListener('click', click); doc.removeEventListener('change', change); };
}
