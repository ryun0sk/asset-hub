import {fileUrl} from './catalog.js';

const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[ch]));
const finite = value => typeof value === 'number' && Number.isFinite(value);
const number = value => finite(value) ? value.toLocaleString('ja-JP', {minimumFractionDigits: 2, maximumFractionDigits: Math.abs(value) < 1 ? 4 : 2}) : '—';
const multiple = value => finite(value) && value > 0 ? `${value.toLocaleString('ja-JP', {minimumFractionDigits: 1, maximumFractionDigits: 1})}倍` : '算出不能';
const period = value => value ? `${esc(value)}期` : '期末未取得';
const missing = label => `<span class="ai-val-missing">${esc(label)}</span>`;

// The dated documents remain untouched. This overview belongs to the dashboard's latest view.
export function isAiValuationView(entry, item, archived = false) {
  return !archived && entry?.kind === 'theme' && entry.slug === 'ai-supply-chain' && item?.type === 'html' && item.view === 'fund' && Boolean(fileUrl(item.path));
}

function perValue(company, sort) {
  const value = sort === 'actual' ? company.snapshot?.pe : company.analyst?.periods?.[sort === 'next' ? '+1y' : '0y']?.pe;
  return finite(value) && value > 0 ? value : null;
}

export function filterAiCompanies(companies, groups, {query = '', group = '', sort = 'order'} = {}) {
  const words = query.normalize('NFKC').toLocaleLowerCase('ja-JP').trim().split(/\s+/).filter(Boolean);
  const chosen = groups.find(item => item.id === group);
  const seen = new Set();
  const result = companies.filter(company => {
    if (seen.has(company.symbol)) return false;
    seen.add(company.symbol);
    if (group && (!chosen || !chosen.symbols.includes(company.symbol))) return false;
    const stages = groups.filter(item => item.symbols.includes(company.symbol));
    const text = [company.name, company.symbol, ...stages.flatMap(item => [item.name, item.roles?.[company.symbol] || ''])].join(' ').normalize('NFKC').toLocaleLowerCase('ja-JP');
    return words.every(word => text.includes(word));
  });
  if (['actual', 'current', 'next'].includes(sort)) result.sort((a, b) => {
    const av = perValue(a, sort), bv = perValue(b, sort);
    return av == null ? (bv == null ? 0 : 1) : bv == null ? -1 : av - bv;
  });
  return result;
}

function forecastCell(forecast, currency, originalCurrency, originalEps) {
  if (!forecast || !finite(forecast.eps)) return missing('取得なし');
  const converted = originalCurrency && originalCurrency !== currency
    ? `<small>報告 ${number(originalEps)} ${esc(originalCurrency)}／株・為替換算</small>` : '';
  return `<strong>${number(forecast.eps)} <small class="ai-val-unit">${esc(currency)}／株</small></strong><small>${period(forecast.periodEnd)}</small><span class="ai-val-per">→ ${multiple(forecast.pe)}</span>${converted}${forecast.announced ? `<small>公表 ${esc(forecast.announced)}</small>` : ''}`;
}

function analystCell(company, key) {
  const forecast = company.analyst?.periods?.[key];
  if (!forecast) return missing('取得なし');
  // Use the preserved currency conversion and P/E; never replace it with a current quote.
  const eps = forecast.avgPriceCurrency ?? (company.analyst.currency === company.priceCurrency ? forecast.avg : null);
  return forecastCell({eps, periodEnd: forecast.endDate, pe: forecast.pe}, company.priceCurrency, company.analyst.currency, forecast.avg);
}

function companyRow(company, groups) {
  const snapshot = company.snapshot || {}, currency = company.priceCurrency;
  const stages = groups.filter(group => group.symbols.includes(company.symbol)).map(group => group.name);
  const notes = [...(snapshot.notes || []), ...(company.analyst?.relabelNote ? [company.analyst.relabelNote] : [])];
  const fx = company.epsCurrency !== currency ? `<small>報告 ${number(snapshot.ttmEps)} ${esc(company.epsCurrency)}／株・為替換算</small>` : '';
  const companyForecast = company.companyForecast ? forecastCell(company.companyForecast, currency) : missing(company.companyForecastNote || '取得なし');
  return `<tr data-symbol="${esc(company.symbol)}">
    <th scope="row"><strong>${esc(company.name)}</strong><small>${esc(company.symbol)}</small><small>${esc(stages.join(' / '))}</small></th>
    <td class="ai-val-num"><strong>${number(snapshot.close)} <small class="ai-val-unit">${esc(currency)}</small></strong><small>${esc(snapshot.date)}</small></td>
    <td class="ai-val-num"><strong>${number(snapshot.ttmEpsPriceCurrency)} <small class="ai-val-unit">${esc(currency)}／株</small></strong><small>${period(snapshot.ttmPeriodEnd)}</small>${fx}</td>
    <td class="ai-val-num ai-val-per">${snapshot.status === 'loss' ? missing('赤字・算出不能') : multiple(snapshot.pe)}</td>
    <td class="ai-val-num">${companyForecast}</td>
    <td class="ai-val-num">${analystCell(company, '0y')}</td>
    <td class="ai-val-num">${analystCell(company, '+1y')}</td>
    <td class="ai-val-note">${notes.length ? `<details><summary>注記 ${notes.length}件</summary><ul>${notes.map(note => `<li>${esc(note)}</li>`).join('')}</ul></details>` : '<span class="ai-val-subtle">—</span>'}</td>
  </tr>`;
}

function rowsHtml(companies, groups) {
  return companies.map(company => companyRow(company, groups)).join('') || '<tr><td colspan="8" class="ai-val-empty">条件に一致する銘柄はありません。</td></tr>';
}

export function renderAiValuations(valuation, chainCatalog, sourceUrl = '') {
  const companies = valuation.companies, groups = chainCatalog.groups;
  const total = companies.length;
  return `<section class="ai-valuations" aria-labelledby="ai-val-title">
    <div class="ai-val-heading"><div><h2 id="ai-val-title">AI銘柄のEPS・PER一覧 <span class="ai-val-count" data-ai-count aria-live="polite">${total} / ${total}社</span></h2>
      <p>株価は${esc(valuation.asOf)}までの終値 · アナリスト予想は${esc(valuation.analystRetrieved?.from?.slice(0, 10) || '取得日未確認')}取得 · 保存時点の比較表</p>
      <p><a href="#ai/multiples">キオクシア・アドバンテスト・イビデン・ディスコの実績月次表 →</a><small> 2026-10-15終値まで／TTM・半年年換算</small></p></div></div>
    <div class="ai-val-controls">
      <label>銘柄を検索<input type="search" data-ai-query placeholder="銘柄名・コード" autocomplete="off"></label>
      <label>工程<select data-ai-group><option value="">全工程（${total}社）</option>${groups.map(group => `<option value="${esc(group.id)}">${esc(group.name)}</option>`).join('')}</select></label>
      <label>並べ替え<select data-ai-sort><option value="order">掲載順</option><option value="actual">実績PERの低い順</option><option value="current">今期予想PERの低い順</option><option value="next">来期予想PERの低い順</option></select></label>
    </div>
    <p class="ai-val-intro">全${total}社を重複なく掲載。EPSは株価と同じ通貨・株式分割基準。PERは保存株価÷EPSの独自計算です。保存時点の固定値で比較しています。</p>
    <div class="ai-val-scroll" tabindex="0" role="region" aria-label="AI銘柄のEPS・PER一覧。横幅が収まらない場合は横スクロールで列を確認">
      <table class="ai-val-table"><caption class="ai-val-sr-only">AI関連銘柄の保存時点の株価、実績EPS・PER、会社予想とアナリスト予想のEPS・PER</caption>
        <thead><tr><th scope="col">銘柄・工程</th><th scope="col">株価・基準日</th><th scope="col">実績EPS<br>直近12か月（TTM）</th><th scope="col">実績PER</th><th scope="col">会社予想<br>通期EPS → PER</th><th scope="col">外部予想・今期<br>平均EPS → PER</th><th scope="col">外部予想・来期<br>平均EPS → PER</th><th scope="col">個別の注記</th></tr></thead>
        <tbody data-ai-rows>${rowsHtml(companies, groups)}</tbody>
      </table></div>
    <div class="ai-val-footer"><span>株価・EPSの通貨は各セルに表示。予想の会計期末は会社ごとに異なります。</span>${sourceUrl ? `<a href="${esc(sourceUrl)}" target="_blank" rel="noopener noreferrer">保存データ・出所を開く ↗</a>` : ''}</div>
    <details class="ai-val-method"><summary>計算基準と注意点</summary><ul>
      <li>株価・実績EPSは既存の調査資料を使用。休場の銘柄は直前の取引日を表示し、株価や予想を更新していません。赤字・EPSが0以下の場合はPERを算出せず、未取得の予想は「取得なし」と表示します。</li>
      <li>実績EPSは希薄化後（なければ基本EPS）のTTM。原資料に公表日がない場合は期末＋${esc(valuation.method?.knownLagDays)}日から既知とする前提で、期末から${esc(valuation.method?.maxAgeDays)}日を超えるTTMは使いません。ASMLとLenovoは保存時点の為替で株価通貨に換算しています。</li>
      <li>会社予想は会社開示、外部予想はYahoo Financeのアナリスト平均。海外の外部予想は調整後（Non-GAAP）EPSの場合があり、実績EPSと会計基準が異なることがあります。両者のPERの差を利益成長だけで解釈しないでください。</li>
      <li>MicronのTTMは1四半期遅れ。外部予想の会計年度の補正を含む個別の前提は、該当銘柄の「注記」で確認できます。</li>
    </ul></details>
  </section>`;
}

// Fetch only the selected snapshot's local files, with a visible retry on failure.
export async function mountAiValuations(host, item) {
  const base = item.path.slice(0, item.path.lastIndexOf('/') + 1);
  const valuationUrl = fileUrl(base + 'valuation.json'), catalogUrl = fileUrl(base + 'catalog.json');
  try {
    const [valuation, chainCatalog] = await Promise.all([valuationUrl, catalogUrl].map(async url => {
      const response = await fetch(url);
      if (!response.ok) throw Error('保存データの読み込みに失敗');
      return response.json();
    }));
    if (!Array.isArray(valuation.companies) || !Array.isArray(chainCatalog.groups)) throw Error('invalid data');
    if (!host.isConnected) return;
    host.innerHTML = renderAiValuations(valuation, chainCatalog, valuationUrl);
    const update = () => {
      const companies = filterAiCompanies(valuation.companies, chainCatalog.groups, {query: host.querySelector('[data-ai-query]').value, group: host.querySelector('[data-ai-group]').value, sort: host.querySelector('[data-ai-sort]').value});
      host.querySelector('[data-ai-rows]').innerHTML = rowsHtml(companies, chainCatalog.groups);
      host.querySelector('[data-ai-count]').textContent = `${companies.length} / ${valuation.companies.length}社`;
    };
    host.querySelector('[data-ai-query]').addEventListener('input', update);
    for (const selector of ['[data-ai-group]', '[data-ai-sort]']) host.querySelector(selector).addEventListener('change', update);
  } catch {
    if (!host.isConnected) return;
    host.innerHTML = '<p class="ai-val-error" role="alert">AI銘柄のEPS・PER一覧を読み込めませんでした。<button type="button" class="button" data-ai-retry>再試行</button></p>';
    host.querySelector('[data-ai-retry]').addEventListener('click', () => mountAiValuations(host, item));
  }
}
