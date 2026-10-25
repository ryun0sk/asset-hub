import {escapeHtml as esc, safeText, safeHttpsUrl} from './mbo-app.js';

const array = value => Array.isArray(value) ? value : [];
const STATUS = Object.freeze({succeeded: '成立', failed: '不成立', withdrawn: '撤回・中止', ongoing: '進行中', unknown: '結果未確認'});
const verified = value => ['verified', 'confirmed', 'primary_verified', 'verified_primary', 'verified_primary_public_rationale', 'verified_primary_later_confirmation', 'verified_exchange', 'verified_exchange_delisting'].includes(value);
const link = source => { const url = safeHttpsUrl(source?.url); return url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(source.title || '原本')} ↗</a>` : ''; };
const number = value => Number.isSafeInteger(value) ? value.toLocaleString('ja-JP') : '未確認';
const metric = (title, value, note) => `<article class="mbo-metric"><span class="mbo-metric-label">${esc(title)}</span><strong class="mbo-metric-value">${esc(value)}</strong><span class="mbo-metric-note">${esc(note)}</span></article>`;

export function censusSubset(data, {query = '', year = 'all', status = 'all', motive = 'all', verification = 'all'} = {}) {
  const words = safeText(query, 100).normalize('NFKC').toLocaleLowerCase('ja-JP').trim().split(/\s+/).filter(Boolean);
  return array(data?.cases).filter(item => {
    const c = item.census || {}, checks = c.verification || {};
    const text = `${item.name} ${item.code} ${item.actors || ''} ${array(item.aliases).join(' ')} ${array(c.motive_categories).map(key => data.motive_labels?.[key] || key).join(' ')}`.normalize('NFKC').toLocaleLowerCase('ja-JP');
    return words.every(word => text.includes(word)) && (year === 'all' || String(c.year) === year) &&
      (status === 'all' || c.status === status) && (motive === 'all' || array(c.motive_categories).includes(motive)) &&
      (verification === 'all' || (verification === 'motive' ? verified(checks.motive) : !verified(checks.announcement) || !verified(checks.motive) || !verified(checks.outcome)));
  });
}

export function renderCensusOverview(data) {
  const total = array(data.cases).length, checks = data.verified || {};
  const yearly = array(data.yearly).map(row => `<tr><th scope="row">${esc(row.year)}${row.year === 2026 ? '（10/18まで）' : ''}</th><td class="mbo-number">${number(row.episodes)}</td><td class="mbo-number">${number(row.tse_episodes)}${Number.isSafeInteger(row.tse_formal_mbo) ? `<small>TOB型 ${number(row.tse_formal_mbo)} / 非TOB準拠 ${number(row.tse_equivalent_no_tob)}</small>` : ''}</td><td class="mbo-number">${number(row.tse_benchmark)}</td><td class="mbo-number">${number(row.announcement_verified)} / ${number(row.episodes)}</td><td class="mbo-number">${number(row.motive_verified)} / ${number(row.episodes)}</td></tr>`).join('');
  const motiveRows = Object.entries(data.motive_labels || {}).map(([key, title]) => `<tr><th scope="row">${esc(title)}</th><td class="mbo-number">${number(data.motive_counts?.[key] || 0)}</td></tr>`).join('');
  const failureRows = array(data.cases).filter(item => ['failed', 'withdrawn'].includes(item.census?.status)).map(item => `<article class="mbo-panel"><button type="button" class="mbo-company-button" data-census-case="${esc(item.case_id)}">${esc(item.name)} · ${esc(item.first_formal_mbo_announcement_date || '日付未確認')}</button><p>${esc(STATUS[item.census.status])}</p>${array(item.observed_obstacles).length ? array(item.observed_obstacles).map(entry => `<p>${esc(entry.text, 1200)}</p>`).join('') : '<p class="mbo-muted">理由の原本確認待ち。結果だけから原因を補いません。</p>'}</article>`).join('');
  return `<div class="mbo-section-head"><div><h2>過去約5年のMBO台帳と分析</h2><p class="mbo-muted">初回正式公表 ${esc(data.start_date)}〜${esc(data.as_of)}。再実施は別件、予定された二段階買付けは同じ計画として整理。</p></div></div>
    <p class="mbo-notice">上場廃止一覧・年別名簿・会社と買付者の開示を照合しています。公表日・理由・結果の確認状況を別々に表示します。未確認は「なし」と扱いません。</p>${data.coverage_summary ? `<p class="mbo-notice">${esc(data.coverage_summary, 1000)}</p>` : ''}
    <div class="mbo-metrics">${metric('収録エピソード', `${number(total)}件`, `${number(data.company_count)}社 · MBO・経営陣主導の非TOB非公開化`)}${metric('正式公表日を確認', `${number(checks.announcement)} / ${number(total)}`, 'TOB開始日・上場廃止日と区別')}${metric('理由の本文を確認', `${number(checks.motive)} / ${number(total)}`, '当事者の公表説明・複数分類あり')}${metric('結果を確認', `${number(checks.outcome)} / ${number(total)}`, '進行中・不成立・再実施を区別')}</div>
    <details class="mbo-case-sources"><summary>年別の収録範囲・公式件数との照合</summary><p class="mbo-muted">全国と東証は範囲が異なります。非TOBの経営陣主導株式併合は「MBOに準ずる非公開化」として内数を分けています。公式図表と件数が同じでも、準ずる行為の算入定義まで一致したことを保証しません。2026年は途中集計です。東証の基準件数は2026/1/26のJPX資料（PDF3頁）によります。</p><p><a href="https://www.jpx.co.jp/equities/follow-up/nlsgeu000006gevo-att/t13vrt000000njd5.pdf" target="_blank" rel="noopener noreferrer">JPXの公式集計 ↗</a></p><div class="mbo-table-wrap"><table><thead><tr>${['初回公表年', '全国台帳', '東証区分', '東証公式', '公表日確認', '理由本文確認'].map(x => `<th scope="col">${esc(x)}</th>`).join('')}</tr></thead><tbody>${yearly}</tbody></table></div>${array(data.coverage_notes).map(text => `<p>${esc(typeof text === 'string' ? text : JSON.stringify(text), 1400)}</p>`).join('')}</details>
    <details class="mbo-case-sources"><summary>起きた理由の整理と評価への反映</summary><p>理由本文を確認した${number(checks.motive)}件（非TOBの準ずる取引を含む）の説明を分類しています。複数の理由を持つ案件があります。全上場企業との比較による予測力や因果効果の推定ではありません。会社ごとに全理由を同じ深さで抽出し切った発生率でもありません。</p><div class="mbo-detail-grid"><div class="mbo-table-wrap"><table><thead><tr><th scope="col">当事者が説明した論点</th><th scope="col">確認した案件数</th></tr></thead><tbody>${motiveRows}</tbody></table></div><article class="mbo-panel"><h3>候補調査で確認すること</h3><ul class="mbo-list"><li>長期投資・再編の必要性と、非公開化を選ぶ意思を分ける。</li><li>承継やスポンサー参加は、当事者の説明と実際の参加経路を確認する。</li><li>応募下限、応募・不応募合意、担保・貸株、反対株主を一つの持分比率にまとめない。</li><li>価格への納得、競合提案、資金・許認可の条件を別に確認する。</li><li>低PBR・余剰現金・公表後のプレミアムだけでMBO有力とは判定しない。</li></ul></article></div></details>
    <details class="mbo-case-sources"><summary>不成立・撤回の事例と理由</summary><p>応募下限未達という直接の結果と、価格・株主・競合・資金等の背景を分けて確認します。不成立後の再実施は別のエピソードです。</p><div class="mbo-detail-grid">${failureRows || '<p>不成立・撤回の原本を確認しています。</p>'}</div></details>`;
}

function options(values, selected) { return values.map(([value, title]) => `<option value="${esc(value)}"${selected === value ? ' selected' : ''}>${esc(title)}</option>`).join(''); }

export function renderCensusResults(data, state) {
  const rows = censusSubset(data, state), size = 25, pages = Math.max(1, Math.ceil(rows.length / size));
  const page = Math.min(Math.max(1, state.page || 1), pages), start = (page - 1) * size;
  const tableRows = rows.slice(start, start + size).map(item => {
    const c = item.census || {}, checks = c.verification || {};
    return `<tr><td><button type="button" class="mbo-company-button" data-census-case="${esc(item.case_id)}">${esc(item.name)}</button><small>${esc(item.code)}</small></td><td>${esc(item.first_formal_mbo_announcement_date || '未確認')}<small>${c.market ? esc(c.market) : '市場区分の確認待ち'}</small>${c.scope_class === 'mbo_equivalent_no_tob' ? '<small>MBOに準ずる非TOB非公開化</small>' : ''}</td><td>${esc(item.outcome?.completion_evidence === 'exchange_delisting' ? '非公開化完了' : c.scope_class === 'mbo_equivalent_no_tob' ? '非TOB手続の実施確認' : STATUS[c.status] || '結果未確認')}<small>${esc(item.outcome?.summary, 400)}</small></td><td>${array(item.public_motives).length ? esc(item.public_motives.map(x => x.text).join(' / '), 210) : '理由の本文確認待ち'}</td><td>${['announcement', 'motive', 'outcome'].map((key, i) => `<small>${['公表日', '理由', '結果'][i]}：${verified(checks[key]) ? '原本確認' : '未確認'}</small>`).join('')}</td></tr>`;
  }).join('');
  return `<p class="mbo-muted">絞込 ${number(rows.length)}件 / 台帳 ${number(data.cases.length)}件 · ${number(data.company_count)}社 · 原本URL ${number(data.source_count)}件</p>${rows.length ? `<div class="mbo-table-wrap" tabindex="0" role="region" aria-label="MBO調査台帳"><table><thead><tr>${['企業・エピソード', '初回正式公表日', '結果', '公表された理由', '原本確認状況'].map(x => `<th scope="col">${esc(x)}</th>`).join('')}</tr></thead><tbody>${tableRows}</tbody></table></div><div class="mbo-section-head"><button class="mbo-button" type="button" data-census-page="${page - 1}"${page <= 1 ? ' disabled' : ''}>前の25件</button><span>${number(page)} / ${number(pages)}ページ</span><button class="mbo-button" type="button" data-census-page="${page + 1}"${page >= pages ? ' disabled' : ''}>次の25件</button></div>` : '<p class="mbo-empty">条件に合う案件はありません。</p>'}`;
}

function renderScopeGaps(data) {
  const gaps = array(data.scope_gap_candidates);
  if (!gaps.length) return '';
  return `<details class="mbo-case-sources"><summary>分類の追加確認が必要な案件（${number(gaps.length)}件・主台帳に未算入）</summary><p>買収の事実と、対象会社の経営陣が買い手側へ参加したかを分けて確認しています。MBOでないと確定した一覧でも、非MBO比較群でもありません。</p>${gaps.map(item => `<article class="mbo-evidence"><strong>${esc(item.code)} ${esc(item.name)}</strong><p>${esc(item.reason, 1600)}</p>${array(item.sources).map(source => `<p>${link(source)}<small>${esc(source.locator || '')} · 公表 ${esc(source.public_at || '日付未確認')}</small></p>`).join('')}</article>`).join('')}</details>`;
}

export function mountMboCensus(host, {data, renderDetail, referenceHtml = ''}) {
  if (data?.schema_version !== 1 || !Array.isArray(data.cases)) throw Error('MBO台帳の保存データ形式を確認できませんでした。');
  const state = {query: '', year: 'all', status: 'all', motive: 'all', verification: 'all', page: 1, selectedCase: ''};
  const view = `<div class="mbo-cases">${renderCensusOverview(data)}${renderScopeGaps(data)}<div class="mbo-section-head"><h2>案件を調べる</h2></div><div class="mbo-filters"><label>企業・コード・論点<input data-census-filter="query" type="search" maxlength="100" placeholder="企業名・コード・論点で検索"></label><label>初回公表年<select data-census-filter="year">${options([['all', 'すべて'], ...array(data.yearly).map(x => [String(x.year), String(x.year)])], 'all')}</select></label><label>結果<select data-census-filter="status">${options([['all', 'すべて'], ...Object.entries(STATUS)], 'all')}</select></label><label>公表理由<select data-census-filter="motive">${options([['all', 'すべて'], ...Object.entries(data.motive_labels || {})], 'all')}</select></label><label>確認状況<select data-census-filter="verification">${options([['all', 'すべて'], ['motive', '理由本文を確認'], ['pending', '未確認項目あり']], 'all')}</select></label></div><div data-census-results></div><div data-census-detail><p class="mbo-empty">企業名を選ぶと理由・結果と原本を確認できます。</p></div><details class="mbo-case-sources"><summary>除外・別枠にした案件と理由（${number(array(data.exclusions).length)}件）</summary>${array(data.exclusions).map(item => `<article class="mbo-evidence"><strong>${esc(item.name || item.code || '案件')}</strong><p>${esc(item.reason || item.exclusion_reason || item.note || '採否の追加確認中', 1600)}</p>${array(item.sources).map(link).join('<br>')}${item.source_url ? link({title:'確認資料', url:item.source_url}) : ''}</article>`).join('')}</details>${referenceHtml}<details class="mbo-case-sources"><summary>解釈の限界</summary><ul class="mbo-list">${array(data.cautions).map(x => `<li>${esc(x)}</li>`).join('')}</ul></details></div>`;
  host.innerHTML = view;
  let destroyed = false;
  const results = host.querySelector('[data-census-results]'), detail = host.querySelector('[data-census-detail]');
  const render = () => { if (!destroyed && results) results.innerHTML = renderCensusResults(data, state); };
  const filter = event => {
    const target = event.target.closest?.('[data-census-filter]');
    if (!target || destroyed) return;
    const key = target.dataset.censusFilter;
    if (!['query', 'year', 'status', 'motive', 'verification'].includes(key)) return;
    state[key] = safeText(target.value, 100); state.page = 1; render();
  };
  const click = event => {
    if (destroyed) return;
    const page = event.target.closest?.('[data-census-page]');
    if (page) { state.page = Math.max(1, Number(page.dataset.censusPage) || 1); render(); return; }
    const selected = event.target.closest?.('[data-census-case]');
    if (!selected) return;
    const item = data.cases.find(x => x.case_id === selected.dataset.censusCase);
    if (!item || !detail) return;
    state.selectedCase = item.case_id;
    detail.innerHTML = renderDetail(item);
    detail.querySelector?.('[data-case-heading]')?.focus();
  };
  host.addEventListener('input', filter); host.addEventListener('change', filter); host.addEventListener('click', click);
  render();
  return {getState: () => ({...state}), destroy() { destroyed = true; host.removeEventListener('input', filter); host.removeEventListener('change', filter); host.removeEventListener('click', click); }};
}
