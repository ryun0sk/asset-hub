import {fileUrl} from './catalog.js';

export const RANKING_PATH = 'research/themes/ai-valuation-ranking/2026-10-18/ranking.json';
const REPORT_PATH = 'research/themes/ai-valuation-ranking/2026-10-18/report.md';
const CSV_PATH = 'research/themes/ai-valuation-ranking/2026-10-18/results.csv';
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const finite = value => typeof value === 'number' && Number.isFinite(value);
const number = (value, digits = 2) => finite(value) ? value.toLocaleString('ja-JP', {maximumFractionDigits: digits, minimumFractionDigits: digits}) : '—';
const pct = value => finite(value) ? `${value >= 0 ? '+' : ''}${number(value, 0)}%` : '算出不能';
const unit = currency => ({JPY: '円', USD: 'ドル', EUR: 'ユーロ', TWD: '台湾ドル', KRW: 'ウォン', HKD: '香港ドル'}[currency] || currency);
const priceText = (value, currency) => `${number(value, ['JPY', 'KRW'].includes(currency) ? 0 : 2)} ${esc(currency)}`;
const profitText = (value, currency) => {
  if (!finite(value)) return '—';
  return Math.abs(value) >= 1000 ? `${number(value / 1000, 2)}兆${unit(currency)}` : `${number(value * 10, 1)}億${unit(currency)}`;
};
const caseNames = {weak: '弱気', base: '基準', strong: '強気'};
const safeUrl = value => {
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) ? esc(url.href) : ''; } catch { return ''; }
};

export function forwardValue(company, {year = 2029, scenario = 'base', requiredReturn = 0.12} = {}) {
  const row = company.scenarios?.[year]?.[scenario];
  const price = company.price?.close;
  if (!row || !finite(price) || price <= 0) return {row, per: null, value: null, gap: null};
  const eps = row.eps_quote_currency;
  if (!finite(eps) || eps <= 0 || !finite(row.terminal_pe) || row.terminal_pe <= 0) return {row, per: null, value: null, gap: null};
  const years = (Date.parse(`${year}-12-31T00:00:00Z`) - Date.parse(`${company.price.date}T00:00:00Z`)) / (365.25 * 86400000);
  const value = eps * row.terminal_pe / (1 + requiredReturn) ** years;
  return {row, per: price / eps, value, gap: (value / price - 1) * 100};
}

export function filterForwardCompanies(data, options = {}) {
  const {query = '', group = '', quality = '', sort = 'gap'} = options;
  const words = query.normalize('NFKC').toLocaleLowerCase('ja-JP').trim().split(/\s+/).filter(Boolean);
  const seen = new Set();
  const result = data.companies.filter(company => {
    if (seen.has(company.symbol)) return false;
    seen.add(company.symbol);
    if (group && !company.stages.includes(group)) return false;
    if (quality && company.model_quality !== quality) return false;
    const stages = data.groups.filter(g => company.stages.includes(g.id)).map(g => g.name);
    const text = [company.name, company.symbol, ...stages].join(' ').normalize('NFKC').toLocaleLowerCase('ja-JP');
    return words.every(word => text.includes(word));
  });
  return result.sort((a, b) => {
    if (a.rank_eligible === false || b.rank_eligible === false) return a.rank_eligible === false ? (b.rank_eligible === false ? 0 : 1) : -1;
    if (sort === 'name') return a.name.localeCompare(b.name, 'ja');
    const key = sort === 'per' ? 'per' : 'gap';
    const av = forwardValue(a, options)[key], bv = forwardValue(b, options)[key];
    return !finite(av) ? (!finite(bv) ? 0 : 1) : !finite(bv) ? -1 : sort === 'per' ? av - bv : bv - av;
  });
}

function detailHtml(company) {
  const method = Array.isArray(company.method) ? company.method.join(' ') : company.method;
  const base = company.scenarios?.['2029']?.base;
  const modelUrl = company.source_input ? fileUrl(company.source_input.endsWith('/') ? company.source_input + 'report.md' : company.source_input) : '';
  const assumptions = base?.segments ? `<p><strong>2029基準の独自前提</strong>（金額は${esc(company.financial_currency)}の10億単位）</p><ul>${base.segments.map(s => `<li>${esc(s.name)}：校正${number(s.market_or_revenue_anchor_bn, 2)}×需要等${number(s.growth_factor, 2)}×取り分等${number(s.share_factor, 2)}＝売上${number(s.revenue_bn, 2)}。営業率${number(s.operating_margin * 100, 1)}%。</li>`).join('')}</ul><p>全社費用${number(base.unallocated_cost_bn || 0, 2)}、純金融損益${number(base.net_finance_bn, 2)}、税率${number(base.tax_rate * 100, 1)}%、希薄化後株数${number(base.diluted_shares_bn, 3)}十億株。需要倍率・取り分・採算は独自仮定です。</p>` : '';
  const sources = (company.sources || []).map(source => {
    const href = safeUrl(source.url);
    return href ? `<li><a href="${href}" target="_blank" rel="noopener noreferrer">${esc(source.title || source.url)}</a>${source.date ? ` · ${esc(source.date)}` : ''}${source.status ? ` · ${esc(source.status)}` : ''}</li>` : '';
  }).join('');
  return `<details class="ai-forward-detail"><summary>前提・6ケース・出典</summary>
    <p>${esc(method)}</p>${assumptions}<ul>${(company.risks || []).map(risk => `<li>${esc(risk)}</li>`).join('')}</ul>
    <p>${esc(company.basis_note || '')}</p>
    <div class="ai-forward-detail-scroll"><table><caption>${esc(company.name)}の独自シナリオ。利益は${esc(company.financial_currency)}、EPSは${esc(company.price.currency)}／株</caption>
    <thead><tr><th>年・ケース</th><th>売上</th><th>純利益</th><th>EPS</th><th>想定PER</th></tr></thead><tbody>${[2028, 2029].flatMap(year => ['weak', 'base', 'strong'].map(scenario => {
      const row = company.scenarios?.[year]?.[scenario];
      return row ? `<tr><th scope="row">${year} ${caseNames[scenario]}</th><td>${esc(profitText(row.revenue_bn, company.financial_currency))}</td><td>${esc(profitText(row.normal_net_income_bn, company.financial_currency))}</td><td>${priceText(row.eps_quote_currency, company.price.currency)}</td><td>${number(row.terminal_pe, 0)}倍</td></tr>` : '';
    })).join('')}</tbody></table></div><ul>${sources}</ul>
    ${company.valuation_note ? `<p>${esc(company.valuation_note)}</p>` : ''}${modelUrl ? `<p><a href="${esc(modelUrl)}" target="_blank" rel="noopener noreferrer">詳細モデル・入力を開く ↗</a></p>` : ''}</details>`;
}

function rowsHtml(data, companies, options) {
  const year = options.year || 2029, scenario = options.scenario || 'base';
  return companies.map((company, index) => {
    const value = forwardValue(company, options), weak = forwardValue(company, {...options, scenario: 'weak'}), strong = forwardValue(company, {...options, scenario: 'strong'});
    const currency = company.price.currency;
    const eps = y => priceText(company.scenarios?.[y]?.[scenario]?.eps_quote_currency, currency);
    const stages = data.groups.filter(g => company.stages.includes(g.id)).map(g => g.name).join(' / ');
    const missing = value.row?.eps_quote_currency <= 0 ? '赤字・利益法で評価不能' : '算出不能';
    const eligible = company.rank_eligible !== false;
    return `<tr data-forward-symbol="${esc(company.symbol)}"><td>${eligible ? (finite(value.gap) ? index + 1 : '—') : '参考'}</td>
      <th scope="row"><strong>${esc(company.name)}</strong><small>${esc(company.symbol)} · ${esc(stages)}</small></th>
      <td class="ai-forward-num">${priceText(company.price.close, currency)}<small>${esc(company.price.date)}</small></td>
      <td class="ai-forward-num"><strong class="${!eligible || !finite(value.gap) ? '' : value.gap >= 0 ? 'ai-forward-positive' : 'ai-forward-negative'}">${eligible ? pct(value.gap) : '比較対象外'}</strong></td>
      <td class="ai-forward-num">${finite(value.value) ? priceText(value.value, currency) : missing}<small>弱 ${finite(weak.value) ? priceText(weak.value, currency) : '評価不能'}<br>強 ${finite(strong.value) ? priceText(strong.value, currency) : '評価不能'}</small></td>
      <td class="ai-forward-num">${eps(2028)}<small>→ ${eps(2029)}</small></td>
      <td class="ai-forward-num">${esc(profitText(value.row?.normal_net_income_bn, company.financial_currency))}</td>
      <td class="ai-forward-num">${finite(value.per) ? `${number(value.per, 1)}倍` : missing}</td>
      <td class="ai-forward-num">${number(value.row?.terminal_pe, 0)}倍</td>
      <td class="ai-forward-condition"><span class="ai-forward-quality">${esc(company.model_quality_label)}</span><p>${esc(company.key_condition || company.risks?.[0] || '')}</p>${detailHtml(company)}</td></tr>`;
  }).join('') || '<tr><td colspan="10" class="ai-val-empty">条件に一致する企業はありません。</td></tr>';
}

export function renderForwardRanking(data, options = {}) {
  options = {year: 2029, scenario: 'base', requiredReturn: 0.12, query: '', group: '', quality: '', sort: 'gap', ...options};
  const selected = (value, current) => String(value) === String(current) ? ' selected' : '';
  const companies = filterForwardCompanies(data, options);
  const qualities = [...new Map(data.companies.map(c => [c.model_quality, c.model_quality_label])).entries()];
  const eligibleCount = data.companies.filter(c => c.rank_eligible !== false).length;
  return `<section class="ai-forward" aria-labelledby="ai-forward-title"><div class="ai-forward-heading">
    <h2 id="ai-forward-title">将来利益から見る割安度 <span data-forward-count aria-live="polite">${companies.length} / ${data.companies.length}社</span></h2>
    <p>確認 ${esc(data.as_of)} · 株価 ${esc(data.price_date)}終値 · 2028〜2029年の独自シナリオ</p>
    <p>${eligibleCount}社を順位比較・${data.companies.length - eligibleCount}社を参考掲載。事業分離の価値を未評価のEatonは順位比較対象外です。</p>
    <p class="ai-forward-warning"><strong>価格余地は独自シナリオに基づく条件付き比較です。</strong>売上の取り分・利益率・将来PERの仮定により順位は変わります。各社の確認範囲と弱気ケースも確認してください。</p>
    ${data.revision ? `<p>10/18追補：台湾2社の転換社債を保守的な経済分母へ反映。Wiwynnは既転換分が重複し得る上限試算です。<a href="${esc(fileUrl('research/themes/ai-valuation-ranking/2026-10-18/top-five-review.md'))}" target="_blank" rel="noopener noreferrer">上位5社の分析・購入候補の判断 ↗</a></p>` : ''}</div>
    <div class="ai-val-controls">
    <label>企業・工程を検索<input type="search" data-forward-query value="${esc(options.query)}" placeholder="企業名・コード・工程" autocomplete="off"></label>
    <label>工程<select data-forward-group><option value="">全工程</option>${data.groups.map(g => `<option value="${esc(g.id)}"${selected(g.id, options.group)}>${esc(g.name)}</option>`).join('')}</select></label>
    <label>対象年<select data-forward-year>${[2029, 2028].map(y => `<option value="${y}"${selected(y, options.year)}>${y}年</option>`).join('')}</select></label>
    <label>利益シナリオ<select data-forward-case>${Object.entries(caseNames).map(([key, name]) => `<option value="${key}"${selected(key, options.scenario)}>${name}</option>`).join('')}</select></label>
    <label>要求年率<select data-forward-return>${[0.12, 0.08, 0.16].map(r => `<option value="${r}"${selected(r, options.requiredReturn)}>${number(r * 100, 0)}%</option>`).join('')}</select></label>
    <label>モデルの確認範囲<select data-forward-quality><option value="">すべて</option>${qualities.map(([id, name]) => `<option value="${esc(id)}"${selected(id, options.quality)}>${esc(name)}</option>`).join('')}</select></label>
    <label>並べ替え<select data-forward-sort>${[['gap', '計算上の割安度が高い順'], ['per', '将来利益に対する倍率が低い順'], ['name', '企業名順']].map(([key, name]) => `<option value="${key}"${selected(key, options.sort)}>${name}</option>`).join('')}</select></label></div>
    <p class="ai-forward-formula" data-forward-formula>${options.year}年・${caseNames[options.scenario]}ケース：計算価格＝${options.year} EPS×想定PER÷${1 + options.requiredReturn}^残存年数。価格余地＝計算価格÷現在株価−1。</p>
    <div class="ai-forward-scroll" tabindex="0" role="region" aria-label="46社の将来利益と割安度。横スクロールで全列を確認"><table class="ai-forward-table"><caption class="ai-val-sr-only">2028年と2029年の独自利益・EPS試算と現在株価の比較。順番は表示中の並べ替え条件による。</caption>
      <thead><tr><th scope="col">順</th><th scope="col">企業・工程</th><th scope="col">株価</th><th scope="col">現値比<br>価格余地</th><th scope="col" data-forward-value-heading>${number(options.requiredReturn * 100, 0)}%条件の計算価格</th><th scope="col">EPS<br>2028 → 2029</th><th scope="col" data-forward-profit-heading>${options.year}通常純利益</th><th scope="col" data-forward-per-heading>現値÷${options.year} EPS</th><th scope="col">想定PER</th><th scope="col">確認範囲・成立条件</th></tr></thead>
      <tbody data-forward-rows>${rowsHtml(data, companies, options)}</tbody></table></div>
    <div class="ai-val-footer"><span>EPSと株価は同じ通貨・普通株/分割基準。純利益は各社の報告通貨。詳細モデルも将来予測の確度を保証しません。</span><span><a href="${esc(fileUrl(CSV_PATH))}" download>全276ケースCSV</a> · <a href="${esc(fileUrl(REPORT_PATH))}" target="_blank" rel="noopener noreferrer">計算方法・比較レポート ↗</a></span></div>
    <details class="ai-val-method"><summary>順位と利益の読み方</summary><ul>
      <li>すべて独自シナリオ。実績TTM、会社予想、アナリスト予想のPERとは区別します。各社の決算期を厳密にそろえた四半期積上げではなく、暦年相当の年間水準です。</li>
      <li>計算価格は終点EPSと想定PERによる比較で、完全なDCFや確定した買い価格ではありません。配当・税金・将来為替変動を含みません。途中の還元・余剰現金・資本負担の違いで判定は変わります。</li>
      <li>一時評価益等は将来へ延長せず、株式報酬・通常の償却・研究開発費は費用に残します。将来シェア・採算等は独自仮定を含み、企業ごとに仮定の強さが異なります。</li>
      <li>赤字・EPSが0以下のケースは利益法の計算価格を表示しません。株式価値がゼロという意味ではありません。未算出値は並べ替えの末尾に置きます。</li>
      <li>「詳細モデル」「事業別試算」「限定的な試算」は確認範囲の区分で、将来利益の発生確率ではありません。掲載46社に限定した比較です。</li>
    </ul></details></section>`;
}

export async function mountForwardRanking(host, {fetcher = fetch} = {}) {
  const slot = host.ownerDocument.createElement('div');
  host.replaceChildren(slot);
  slot.innerHTML = '<p class="ai-val-error" role="status">46社の将来利益・割安度を読み込んでいます…</p>';
  try {
    const response = await fetcher(fileUrl(RANKING_PATH));
    if (!response.ok) throw Error('ranking unavailable');
    const data = await response.json();
    if (!Array.isArray(data.companies) || !Array.isArray(data.groups) || data.schema !== 1) throw Error('invalid ranking');
    if (!slot.isConnected) return;
    slot.innerHTML = renderForwardRanking(data);
    const update = () => {
      const options = {query: slot.querySelector('[data-forward-query]').value, group: slot.querySelector('[data-forward-group]').value,
        year: Number(slot.querySelector('[data-forward-year]').value), scenario: slot.querySelector('[data-forward-case]').value,
        requiredReturn: Number(slot.querySelector('[data-forward-return]').value), quality: slot.querySelector('[data-forward-quality]').value,
        sort: slot.querySelector('[data-forward-sort]').value};
      const rows = filterForwardCompanies(data, options);
      slot.querySelector('[data-forward-rows]').innerHTML = rowsHtml(data, rows, options);
      slot.querySelector('[data-forward-count]').textContent = `${rows.length} / ${data.companies.length}社`;
      slot.querySelector('[data-forward-formula]').textContent = `${options.year}年・${caseNames[options.scenario]}ケース：計算価格＝${options.year} EPS×想定PER÷${1 + options.requiredReturn}^残存年数。価格余地＝計算価格÷現在株価−1。`;
      slot.querySelector('[data-forward-profit-heading]').textContent = `${options.year}通常純利益`;
      slot.querySelector('[data-forward-per-heading]').textContent = `現値÷${options.year} EPS`;
      slot.querySelector('[data-forward-value-heading]').textContent = `${number(options.requiredReturn * 100, 0)}%条件の計算価格`;
    };
    slot.querySelector('[data-forward-query]').addEventListener('input', update);
    for (const select of slot.querySelectorAll('select')) select.addEventListener('change', update);
  } catch {
    if (!slot.isConnected) return;
    slot.innerHTML = '<p class="ai-val-error" role="alert">将来利益の比較表を読み込めませんでした。<button type="button" class="button" data-forward-retry>再試行</button></p>';
    slot.querySelector('[data-forward-retry]').addEventListener('click', () => mountForwardRanking(host, {fetcher}));
  }
}
