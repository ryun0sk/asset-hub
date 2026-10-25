// Local-only, read-only MBO workspace. Every value comes from a pinned saved run.
const MAX_TEXT = 360;
const STATUS_LABELS = Object.freeze({ready: '価格評価可', pending: '確認待ち', event: '案件あり', ok: '計算済み', infeasible: '成立範囲なし', verified: '確認済み', missing: '未入力', conflicting: '矛盾あり', not_applicable: '対象外', success: '成功', failed: '失敗'});
const EVENT_LABELS = Object.freeze({mbo: 'MBO', tob: 'TOB', other_tob: 'その他TOB', parent_take_private: '親会社による非公開化', buyout: '買収', reported: '検討報道', considering: '検討中', ongoing: '手続中', announced: '公表済み', completed: '成立', settled: '成立', withdrawn: '撤回', cancelled: '中止', pending: '確認待ち'});
const SCENARIO_LABELS = Object.freeze({bear: '弱気', base: '基準', bull: '強気'});
const ASSUMPTION_LABELS = Object.freeze({wacc: '割引率', discount_rate: '割引率', terminal_growth: '永久成長率', growth_rate: '成長率', tax_rate: '税率', years: '予測年数', horizon_years: '予測年数', revenue_growth: '営業利益等の成長率', ebit_margin: '営業利益率', exit_multiple: '出口倍率', target_irr: '要求IRR', holding_years: '保有年数', debt_rate: '借入金利', interest_rate: '借入金利', debt_interest: '借入金利', debt_amortization: '元本返済率', entry_debt_multiple: '取得時の借入倍率', fee_rate: '手数料率', rollover_ratio: '経営陣の再出資比率', minimum_cash: '追加の最低現金', fcf_basis: 'CFの定義', growth_basis: '成長の仮定', tax_policy: '税の扱い', equity_bridge: '株主価値への調整', scenario: 'シナリオ', financing: '資金調達の前提', debt_amortization_basis: '元本返済率の基準', cash_policy: '留保現金の扱い', minimum_cash_policy: '最低現金の扱い', rollover_policy: '再出資の扱い', fee_basis: '手数料の基準', lease_policy: 'リースの扱い'});
const RATE_FIELDS = new Set(['wacc', 'discount_rate', 'terminal_growth', 'growth_rate', 'tax_rate', 'revenue_growth', 'ebit_margin', 'target_irr', 'debt_rate', 'interest_rate', 'debt_interest', 'debt_amortization', 'fee_rate', 'rollover_ratio']);
const array = value => Array.isArray(value) ? value : [];
const label = value => STATUS_LABELS[value] || safeText(value, 60) || '未確認';
const MBO_AXES = Object.freeze([['ownership', '所有構造'], ['motive', 'MBOの動機'], ['execution', '実行可能性'], ['obstacles', '障害・反証']]);
const AXIS_STATES = Object.freeze({supported: '根拠あり', contradicted: '反する根拠あり', unknown: '未確認', conflicting: '根拠が矛盾', not_applicable: '対象外'});
const WORKFLOW_LABELS = Object.freeze({awaiting: '調査待ち', research: '詳細調査', monitor: '監視', deferred: '見送り', event: '公表案件'});
const WORKFLOW_ORDER = Object.freeze({monitor: 0, research: 1, awaiting: 2, deferred: 3, event: 4});
const EVIDENCE_TYPES = Object.freeze({public_fact: '公開された事実', analyst_hypothesis: '調査者の仮説', own_scenario: '独自シナリオ', post_announcement: '公表後の情報（事前評価には使わない）'});
const EVIDENCE_SPEAKERS = Object.freeze({company: '会社', management: '経営陣', shareholder: '株主', bidder: '買付者', adviser: '助言者', analyst: '調査者'});
const assessmentFor = company => company?.mbo_assessment && typeof company.mbo_assessment === 'object' && !Array.isArray(company.mbo_assessment) ? company.mbo_assessment : null;
const axisState = value => AXIS_STATES[value] || safeText(value, 60) || '未確認';
const workflowLabel = assessment => assessment?.workflow?.label || WORKFLOW_LABELS[assessment?.workflow?.state] || assessment?.workflow?.state || '調査待ち';
const assessmentAxes = assessment => MBO_AXES.map(([id, title]) => ({id, label: title, state: 'unknown', ...array(assessment?.axes).find(axis => axis?.id === id)}));

export function safeText(value, maximum = MAX_TEXT) {
  if (value === null || value === undefined) return '';
  const text = String(value).replace(/(?:file:\/\/|\/Users\/|\/private\/|\/tmp\/|[A-Za-z]:\\)[^\s<>"']*/g, '[ローカル情報は非表示]');
  return text.length > maximum ? `${text.slice(0, maximum)}…` : text;
}
export const escapeHtml = (value, maximum = MAX_TEXT) => safeText(value, maximum).replace(/[&<>"']/g, ch => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[ch]));
const esc = escapeHtml;
const number = value => value === null || value === undefined || value === '' || typeof value === 'boolean' || !Number.isFinite(Number(value)) ? null : Number(value);
export function formatNumber(value, digits = 2) {
  const parsed = number(value);
  return parsed === null ? '未確認' : new Intl.NumberFormat('ja-JP', {maximumFractionDigits: digits}).format(parsed);
}
export function formatPercent(value) {
  const parsed = number(value);
  return parsed === null ? '未計算' : `${formatNumber(parsed * 100, 1)}%`;
}
const money = (value, currency = 'JPY') => number(value) === null ? '未計算' : `${formatNumber(value)} ${/^[A-Z]{3}$/.test(currency) ? currency : '通貨未確認'}`;
const badge = (text, tone = '') => `<span class="mbo-badge${tone ? ` mbo-badge-${tone}` : ''}">${esc(text)}</span>`;
const empty = (title, description = '') => `<div class="mbo-empty"><h3>${esc(title)}</h3>${description ? `<p>${esc(description)}</p>` : ''}</div>`;
const list = (values, fallback = '登録されていません。') => array(values).length ? `<ul class="mbo-list">${values.map(value => `<li>${esc(typeof value === 'object' ? value.label || value.reason || value.text || '内容の確認待ち' : value)}</li>`).join('')}</ul>` : `<p class="mbo-muted">${esc(fallback)}</p>`;
const table = (heads, rows, caption = '') => `<div class="mbo-table-wrap" tabindex="0" role="region" aria-label="${esc(caption || '調査結果の表')}"><table>${caption ? `<caption>${esc(caption)}</caption>` : ''}<thead><tr>${heads.map(head => `<th scope="col">${esc(head)}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div>`;

export function safeHttpsUrl(value) {
  if (typeof value !== 'string' || value.length > 2048) return null;
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.username || url.password) return null;
    if ([...url.searchParams.keys()].some(key => /(?:key|token|secret|password|authorization|signature)/i.test(key))) return null;
    if (/^(?:localhost|127\.|0\.|\[?::1\]?)/i.test(url.hostname)) return null;
    return url.href;
  } catch { return null; }
}

export function evidenceCommand(documentId) {
  return typeof documentId === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(documentId) ? `python3 -m backend.mbo evidence locate --document-id ${documentId}` : null;
}

export function priceLabel(company) {
  const price = company?.price;
  if (number(price?.value) === null) return '株価未入力';
  return `${money(price.value, price.currency)}${price.price_at ? ` · ${safeText(price.price_at, 32)}` : ' · 基準日未確認'}`;
}

export function candidateSubset(items, {query = '', filter = 'all', sort = 'rank'} = {}) {
  const words = safeText(query, 100).normalize('NFKC').toLocaleLowerCase('ja-JP').trim().split(/\s+/).filter(Boolean);
  const result = array(items).filter(company => {
    const text = `${company.name || ''} ${company.code || ''}`.normalize('NFKC').toLocaleLowerCase('ja-JP');
    if (!words.every(word => text.includes(word))) return false;
    if (filter === 'new') return company.is_new === true;
    if (filter === 'needs_review') return company.status === 'pending' || array(company.missing).length > 0;
    if (filter === 'missing_price') return number(company.price?.value) === null;
    if (filter === 'ready') return company.status === 'ready';
    return true;
  });
  const validDiscount = company => company.valuation?.discount_to_base?.status === 'ok' ? number(company.valuation.discount_to_base.value) : null;
  const descending = (a, b) => a === null ? (b === null ? 0 : 1) : b === null ? -1 : b - a;
  const usesAssessment = result.some(company => assessmentFor(company));
  const workflowOrder = company => {
    const assessment = assessmentFor(company);
    return assessment ? WORKFLOW_ORDER[assessment.workflow?.state] ?? WORKFLOW_ORDER.awaiting : 5;
  };
  return result.sort((a, b) => (sort === 'name' ? String(a.name).localeCompare(String(b.name), 'ja-JP') : sort === 'discount_desc' ? descending(validDiscount(a), validDiscount(b)) : usesAssessment ? workflowOrder(a) - workflowOrder(b) : descending(number(a.priority), number(b.priority))) || String(a.code).localeCompare(String(b.code)));
}

export function renderCandidateTable(items) {
  if (!array(items).length) return empty('条件に合う候補はありません', '価格未入力の企業も「すべて」または「株価未入力」から確認できます。');
  const rows = items.map(company => {
    const discount = company.valuation?.discount_to_base, assessment = assessmentFor(company);
    const workflow = assessment ? `${badge(workflowLabel(assessment))}<small>${esc(assessment.workflow?.reason || '調査作業の区分です。MBOの有力度を示しません。')}</small>` : `${badge('旧版の調査状態', 'muted')}<small>旧優先度 ${esc(formatNumber(company.priority, 0))} · 初期の未検証ルール</small>`;
    const axes = assessment ? assessmentAxes(assessment).map(axis => `<small>${esc(axis.label)}：${esc(axisState(axis.state))}</small>`).join('') : `${esc(safeText(array(company.reasons).slice(0, 2).join(' / '), 160) || '根拠の確認待ち')}<small>旧版では動機等の軸別評価はありません。</small>`;
    const information = assessment?.information;
    return `<tr><td><button type="button" class="mbo-company-button" data-company="${esc(company.security_id)}">${esc(company.name)}</button><small>${esc(company.code)} · ${esc(company.exchange)}</small></td>
      <td>${company.is_new ? badge('新規') : ''}${workflow}</td>
      <td>${axes}</td>
      <td>${assessment ? `${esc(information?.coverage_label || '情報充足は未確認')}<small>確認済み ${esc(formatNumber(information?.verified_count, 0))}件 / 仮説 ${esc(formatNumber(information?.hypothesis_count, 0))}件 / 未解決 ${esc(formatNumber(information?.unresolved_count, 0))}件</small>` : '旧版：軸別の充足件数なし'}<small>${array(company.missing).length ? `数値の不足 ${company.missing.length}項目` : assessment ? '数値の必須欄に欠測なし。MBO論点は別途確認' : '登録済み項目に不足なし'}</small></td>
      <td class="mbo-number">${esc(number(company.price?.value) === null ? '株価未入力' : money(company.price.value, company.price.currency))}<small>${esc(company.price?.price_at || '価格の基準日なし')}</small></td>
      <td class="mbo-number">${esc(discount?.status === 'ok' && number(company.price?.value) !== null ? formatPercent(discount.value) : '未計算')}<small>${esc(label(company.status))} · ${esc(number(company.price?.value) === null ? '価格入力後に比較' : discount?.status === 'ok' ? '基準価値との差' : array(discount?.reasons)[0] || '前提の確認待ち')}</small></td></tr>`;
  }).join('');
  return `<p class="mbo-muted">調査作業の区分・情報の件数はMBO確率や有力度ではありません。「根拠あり」は一部の確認で、軸内の全論点を確認済みとは限りません。価格評価可は割安計算の準備状態です。</p>${table(['企業', 'MBO調査の作業状態', 'MBOの評価軸', '情報の確かさ・不足', '保存株価', '基準価値への割安率'], rows, '持込銘柄の調査候補')}`;
}

export function renderCoverage(coverage = {}) {
  return [['対象企業', coverage.universe, '持込銘柄の範囲'], ['株価あり', coverage.prices, '価格未入力でも調査可能'], ['価格と価値を比較', coverage.valued, '独自シナリオとの比較済み'], ['確認待ち', coverage.pending, '欠測・未確認のある企業']].map(([title, value, note]) => `<article class="mbo-metric"><span class="mbo-metric-label">${esc(title)}</span><strong class="mbo-metric-value">${esc(formatNumber(value, 0))}</strong><span class="mbo-metric-note">${esc(note)}</span></article>`).join('');
}

function properties(value) {
  if (value === null || value === undefined) return '<p class="mbo-muted">仮定は未登録です。</p>';
  if (Array.isArray(value)) return list(value);
  if (typeof value !== 'object') return `<p>${esc(value)}</p>`;
  const entries = Object.entries(value).filter(([key]) => !/(?:key|token|password|secret|path|filename|raw|html|script)/i.test(key));
  const display = (key, entry) => typeof entry === 'object' ? Array.isArray(entry) ? entry.map(item => typeof item === 'object' ? '[確認項目]' : item).join(' / ') : '[詳細な仮定あり]' : RATE_FIELDS.has(key) && number(entry) !== null ? formatPercent(entry) : key === 'scenario' ? SCENARIO_LABELS[entry] || entry : key === 'minimum_cash' ? money(entry) : entry ?? '未確認';
  return entries.length ? `<dl class="mbo-definition">${entries.map(([key, entry]) => `<dt>${esc(ASSUMPTION_LABELS[key] || key)}</dt><dd>${esc(display(key, entry))}</dd>`).join('')}</dl>` : '<p class="mbo-muted">表示可能な仮定は未登録です。</p>';
}

function renderYearly(items, kind = 'dcf') {
  if (!array(items).length) return '';
  const fields = kind === 'lbo' ? [['year', '年目'], ['opening_debt', '期首借入'], ['interest', '利払い'], ['cash_before_repayment', '返済前CF'], ['repayment', '元本返済'], ['closing_debt', '期末借入'], ['closing_cash', '期末現金']] : [['year', '年目'], ['ebit', '営業利益'], ['taxes', '税'], ['depreciation', '減価償却'], ['capex', '設備投資'], ['delta_nwc', '運転資本増加'], ['fcff', '非借入FCF'], ['present_value', '現在価値']];
  return `<details><summary>年別の${kind === 'lbo' ? '返済・現金' : 'CF・現在価値'}を確認</summary><p class="mbo-muted">金額はJPY。独自の固定仮定による試算です。</p>${table(fields.map(([, title]) => title), items.map(row => `<tr>${fields.map(([key]) => `<td class="mbo-number">${esc(formatNumber(row[key], 0))}</td>`).join('')}</tr>`).join(''), '年別の独自試算')}</details>`;
}

function renderFinancing(financing) {
  if (!financing || typeof financing !== 'object') return '';
  const fields = [['purchase_equity_value', '株式取得対価'], ['existing_debt_refinanced', '既存借入の借換'], ['fees', '手数料'], ['additional_cash_reserve', '追加の最低現金'], ['total_uses', '総資金需要'], ['new_debt', '新規借入'], ['excess_cash_used', '余剰現金の充当'], ['rollover_equity', '経営陣の再出資'], ['sponsor_equity', 'スポンサー出資'], ['total_sources', '総調達額'], ['exit_enterprise_value', '出口事業価値'], ['exit_equity_value', '出口株主価値']];
  return `<details><summary>資金使途・調達の内訳</summary><dl class="mbo-definition">${fields.map(([key, title]) => `<dt>${esc(title)}</dt><dd>${esc(money(financing[key]))}</dd>`).join('')}</dl></details>`;
}

function renderScenarios(standalone = {}, currency = 'JPY') {
  const scenarios = array(standalone.scenarios);
  if (!scenarios.length) return `<p>${badge(label(standalone.status || 'pending'), 'warning')}</p><p class="mbo-muted">必要な財務・株数・前提を確認すると評価できます。</p>`;
  return scenarios.map(scenario => `<article class="mbo-panel"><h3>${esc(SCENARIO_LABELS[scenario.name] || scenario.name || 'シナリオ')}</h3>${badge(label(scenario.status || 'pending'), scenario.status === 'ok' ? '' : 'warning')}
    <dl class="mbo-definition"><dt>1株価値</dt><dd>${esc(scenario.status === 'ok' ? money(scenario.value_per_share, currency) : '計算保留')}</dd><dt>株主価値</dt><dd>${esc(scenario.status === 'ok' ? money(scenario.equity_value, currency) : '計算保留')}</dd><dt>事業価値</dt><dd>${esc(scenario.status === 'ok' ? money(scenario.enterprise_value, currency) : '計算保留')}</dd></dl>
    ${array(scenario.reasons).length ? list(scenario.reasons) : ''}<details><summary>独自の仮定</summary>${properties(scenario.assumptions)}</details>${renderYearly(scenario.yearly)}</article>`).join('');
}

export function renderMboAssessment(company) {
  const assessment = assessmentFor(company);
  if (!assessment) return `<p class="mbo-notice">旧版の調査優先度 ${esc(formatNumber(company?.priority, 0))} を保存時点のまま表示します。初期の未検証ルールで、過去MBOの動機分析に基づく評価ではありません。この版にはMBOの軸別評価がありません。</p>`;
  const workflow = assessment.workflow || {}, information = assessment.information || {};
  const evidence = factor => {
    const source = factor.source_id ? array(company.evidence).find(item => item?.source_id === factor.source_id) : null;
    const url = safeHttpsUrl(source?.source_url);
    return `<article class="mbo-evidence"><strong>${esc(factor.label || factor.factor_id || '確認項目')}</strong><p>${badge(axisState(factor.state))}${badge(EVIDENCE_TYPES[factor.evidence_type] || factor.evidence_type || '根拠区分未確認', factor.evidence_type === 'public_fact' ? 'muted' : 'warning')}${badge(factor.usable_for_candidate === true ? '候補評価に利用' : factor.usable_for_candidate === false ? '候補評価から除外' : '利用可否未確認', factor.usable_for_candidate === true ? 'muted' : 'warning')}</p>
      <dl class="mbo-definition"><dt>発言・説明の主体</dt><dd>${esc(EVIDENCE_SPEAKERS[factor.speaker] || factor.speaker || '主体未確認')}</dd><dt>根拠原文</dt><dd>${esc(factor.quote || '原文未登録', 1200)}</dd><dt>解釈</dt><dd>${esc(factor.interpretation || '解釈未登録', 600)}</dd><dt>公表日・出所</dt><dd>${esc(factor.public_at || '公表日時未確認')} · ${esc(factor.source_id || '出所未確認')} · ${esc(factor.locator || '位置未確認')} · ${esc(label(factor.quality_status))}</dd>${factor.agreement_parties ? `<dt>資金合意の当事者</dt><dd>${esc(factor.agreement_parties, 600)}</dd>` : ''}${factor.agreement_terms ? `<dt>資金合意の条件</dt><dd>${esc(factor.agreement_terms, 600)}</dd>` : ''}${factor.exclusion_reason ? `<dt>候補評価からの除外理由</dt><dd>${esc(factor.exclusion_reason, 600)}</dd>` : ''}</dl>
      ${url ? `<a href="${esc(url, 2048)}" target="_blank" rel="noopener noreferrer">根拠資料を開く ↗</a>` : ''}</article>`;
  };
  return `<h3>MBOの条件と根拠</h3><p class="mbo-notice">設計仮説・未検証。過去案件との比較による校正は未実施で、MBO発生確率は算出していません。${assessment.validation_status && assessment.validation_status !== 'hypothesis_not_calibrated' ? ` 保存版の検証区分：${esc(assessment.validation_status)}。` : ''}</p>
    <article class="mbo-panel"><h3>調査の作業状態</h3><p>${badge(workflowLabel(assessment))}</p><p>${esc(workflow.reason || '作業状態の理由は未登録です。')}</p><p class="mbo-muted">作業の区分はMBOの有力度を示しません。</p><dl class="mbo-definition"><dt>監視・再確認する変化</dt><dd>${esc(workflow.watch_trigger || '未登録')}</dd><dt>次回確認</dt><dd>${esc(workflow.next_review_at || '未設定')}</dd><dt>確認者</dt><dd>${esc(workflow.reviewer || '未登録')}</dd></dl></article>
    <p class="mbo-muted">各軸の「根拠あり」は一部の確認で、軸内の全論点を確認済みとは限りません。発言者と会社の意思を分けて確認します。</p><div class="mbo-detail-grid">${assessmentAxes(assessment).map(axis => `<article class="mbo-panel"><h3>${esc(axis.label)}</h3><p>${badge(axisState(axis.state), ['unknown', 'conflicting'].includes(axis.state) ? 'warning' : 'muted')}</p>${axis.note ? `<p>${esc(axis.note, 600)}</p>` : ''}${array(axis.factors).length ? `<h4>確認する論点</h4><ul class="mbo-list">${axis.factors.map(factor => `<li>${esc(factor?.label || factor?.factor_id || '確認項目')}：${esc(axisState(factor?.state))}${factor?.criterion ? `<p class="mbo-muted">${esc(factor.criterion, 600)}</p>` : ''}</li>`).join('')}</ul>` : ''}${array(axis.evidence).length ? axis.evidence.map(factor => evidence(factor || {})).join('') : '<p class="mbo-muted">この軸の根拠はまだ登録されていません。</p>'}</article>`).join('')}</div>
    <article class="mbo-panel"><h3>情報の確かさ</h3><p>${esc(information.coverage_label || '充足状況は未確認')}</p><p>確認済み ${esc(formatNumber(information.verified_count, 0))}件 / 仮説 ${esc(formatNumber(information.hypothesis_count, 0))}件 / 未解決 ${esc(formatNumber(information.unresolved_count, 0))}件</p><p class="mbo-muted">件数は情報の充足を示し、MBO確率や根拠の強さを数値化したものではありません。</p></article>
    ${array(assessment.cautions).length ? `<article class="mbo-panel"><h3>評価上の注意</h3>${list(assessment.cautions)}</article>` : ''}<p class="mbo-muted">評価軸の版：${esc(assessment.version || '未登録')}</p>`;
}

export function renderCompanyDetail(company) {
  if (!company || typeof company !== 'object') return empty('企業の調査内容がありません');
  const facts = array(company.facts), evidence = array(company.evidence), valuation = company.valuation || {}, currency = company.price?.currency || 'JPY';
  const factValue = fact => number(fact.value) === null ? '未確認' : fact.unit === 'ratio' ? formatPercent(fact.value) : fact.unit === 'shares' ? `${formatNumber(fact.value, 0)} 株` : fact.unit === 'JPY' ? money(fact.value, fact.currency || 'JPY') : `${formatNumber(fact.value)} ${fact.unit || fact.currency || ''}`;
  const factRows = facts.map(fact => `<tr><td>${esc(fact.label || fact.metric)}</td><td class="mbo-number">${esc(factValue(fact))}</td><td>${esc(fact.period_end || '対象期未確認')}<small>${esc(({actual: '実績', company_forecast: '会社予想', external_forecast: '外部予想', own_scenario: '独自シナリオ', scenario: '独自シナリオ'})[fact.fact_kind] || fact.fact_kind || '区分未確認')}</small></td><td>${esc(label(fact.quality_status))}<small>${esc(fact.source_id || '出所未確認')} / ${esc(fact.locator || '位置未確認')}</small>${fact.missing_reason ? `<small>${esc(fact.missing_reason)}</small>` : ''}</td></tr>`).join('');
  const lbo = valuation.lbo || {}, discount = valuation.discount_to_base || {}, assessment = assessmentFor(company);
  return `<p>${badge(company.code)}${badge(label(company.status), company.status === 'pending' ? 'warning' : '')}${company.is_new ? badge('新規候補') : ''}</p><p class="mbo-muted">保存株価：${esc(priceLabel(company))}</p>
    ${renderMboAssessment(company)}
    <div class="mbo-detail-grid"><article class="mbo-panel"><h3>${assessment ? '財務の観察・補助メモ' : '旧版の調査根拠'}</h3>${assessment ? '<p class="mbo-muted">財務・価格評価の参考情報です。</p>' : ''}${list(assessment ? assessment.financial_context : company.reasons, '参考情報はまだ確認されていません。')}</article><article class="mbo-panel"><h3>数値の不足・追加確認</h3>${list(company.missing, assessmentFor(company) ? '数値計算の必須欄に欠測はありません。MBO論点・投資計画・原本の追加確認は別途必要です。' : '登録済み項目に不足はありません。原本と評価の前提も確認してください。')}</article></div>
    <h3>単独継続価値 · 独自シナリオ</h3><p class="mbo-muted">MBO買付価格の予測ではありません。公表後に初めて判明した計画を公表前の入力へ混ぜません。</p><div class="mbo-detail-grid">${renderScenarios(valuation.standalone, currency)}</div>
    <div class="mbo-detail-grid"><article class="mbo-panel"><h3>保存株価との比較</h3><p>${esc(number(company.price?.value) === null ? '株価未入力のため、割安率は未計算です。' : discount.status === 'ok' ? `基準価値への割安率 ${formatPercent(discount.value)}` : '価値と価格の前提を確認するまで計算保留です。')}</p>${list(discount.reasons, '基準日・株式分割の基準をそろえて比較します。')}</article>
    <article class="mbo-panel"><h3>LBOの資金試算 · 独自シナリオ</h3><p>${badge(label(lbo.status || 'pending'), lbo.status === 'ok' ? '' : 'warning')}</p><p>${lbo.status === 'ok' ? `条件を満たす上限価格：${esc(money(lbo.max_price_per_share, currency))}` : lbo.status === 'infeasible' ? 'この仮定では、要求収益率と返済条件を満たす買収価格は求まりません。' : '買収資金・借入条件・返済余力の確認が必要です。'}</p>${list(lbo.reasons, '買付価格の予測や金融機関の融資確約ではありません。')}<details><summary>LBOの仮定</summary>${properties(lbo.assumptions)}</details>${renderFinancing(lbo.financing)}${renderYearly(lbo.yearly, 'lbo')}</article></div>
    <h3>財務・確認済みの数値</h3>${facts.length ? table(['項目', '値', '対象期・区分', '確認状態・根拠'], factRows, '実績・予想・独自シナリオを区別') : empty('財務データは未登録です', '資料・財務CSVを取込み、出所と対象期を確認してください。')}
    <div class="mbo-section-head"><h3>根拠資料</h3></div><div class="mbo-panel">${evidence.length ? evidence.map(source => {
      const url = safeHttpsUrl(source.source_url), command = evidenceCommand(source.document_id);
      return `<article class="mbo-evidence"><strong>${esc(source.title || '資料名の確認待ち')}</strong><p class="mbo-muted">公表 ${esc(source.published_at || '日時未確認')} · ${esc(source.locator || '位置未確認')} · ${esc(label(source.quality_status))}</p><p class="mbo-muted">資料ID：${esc(source.document_id || '未登録')}</p>${url ? `<a href="${esc(url, 2048)}" target="_blank" rel="noopener noreferrer">出所URLを開く ↗</a>` : '<span class="mbo-muted">HTTPSの出所URLは未登録です。原本はMac内で確認してください。</span>'}${command ? `<details><summary>Mac内で原本の場所を確認する</summary><p class="mbo-muted">次の文字列を選択してコピーし、Macのターミナルで実行します。デモや保存先を変更した場合は、CLIの --data-dir を表示中と同じ保存先に指定してください。</p><code class="mbo-cli">${esc(command)}</code></details>` : ''}</article>`;
    }).join('') : '<p class="mbo-muted">根拠資料は未登録です。</p>'}</div>
    <div class="mbo-section-head"><h3>人手確認のメモ</h3></div><div class="mbo-panel">${list(company.review_notes, '人手確認のメモはありません。')}</div>`;
}

export function renderEvents(items) {
  if (!array(items).length) return empty('登録済みの案件はありません', '未取得・未確認の案件が存在しないことを示すものではありません。');
  const groups = new Map();
  for (const event of items) {
    const key = event.status || 'pending';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(event);
  }
  return [...groups].map(([status, rows]) => `<section class="mbo-event-group"><h3>${esc(EVENT_LABELS[status] || label(status))} · ${rows.length}件</h3>${table(['企業', '種別', '公表日', '根拠'], rows.map(event => `<tr><td><button type="button" class="mbo-company-button" data-company="${esc(event.security_id)}">${esc(event.name)}</button><small>${esc(event.code)}</small></td><td>${esc(EVENT_LABELS[event.event_type] || event.event_type)}</td><td>${esc(event.announced_at || '未確認')}</td><td>${esc(event.source_id || '確認待ち')}</td></tr>`).join(''), '登録済みの案件')}</section>`).join('');
}

export function renderDiff(diff) {
  if (!diff || !diff.previous_run_id) return empty('前回との差分はまだありません', diff?.summary || '初回の保存結果です。次の週次実行から比較できます。');
  const blocks = [['新しく加わった候補', diff.added], ['候補から外れた企業', diff.removed], ['内容が変わった企業', diff.changed]];
  return `<p class="mbo-muted">${esc(diff.summary || '選択した実行結果と前回を比較しています。')}</p><div class="mbo-detail-grid">${blocks.map(([title, items]) => `<article class="mbo-panel"><h3>${esc(title)} · ${array(items).length}件</h3>${array(items).length ? `<ul class="mbo-list">${items.map(company => `<li>${esc(company.name)} (${esc(company.code)})${array(company.changes).length ? `<p class="mbo-muted">${esc(company.changes.join(' / '))}</p>` : ''}</li>`).join('')}</ul>` : '<p class="mbo-muted">該当なし</p>'}</article>`).join('')}</div>`;
}

export function renderRuns(items) {
  if (!array(items).length) return empty('実行結果はまだありません', 'Mac内のCLIで資料を取込み、週次の調査結果を作成してください。');
  return table(['基準日', '保存日時', '区分', '対象・確認待ち', 'ルール'], items.map(run => `<tr><td><button type="button" class="mbo-company-button" data-run="${esc(run.run_id)}">${esc(run.as_of)}</button>${run.retrospective ? '<small>過去日を再構成。後日取得したデータは除外</small>' : ''}</td><td>${esc(run.created_at)}</td><td>${run.demo ? badge('架空デモ', 'warning') : badge('持込データ', 'muted')}${badge(label(run.status))}</td><td>対象 ${esc(formatNumber(run.coverage?.universe, 0))} / 確認待ち ${esc(formatNumber(run.coverage?.pending, 0))}</td><td>${esc(run.rule_version || '未確認')}</td></tr>`).join(''), '保存された実行結果');
}

export async function requestApi(path, fetcher = globalThis.fetch, signal) {
  if (typeof path !== 'string' || !/^\/api\/mbo\/[a-z]+(?:\/[A-Za-z0-9%_.~-]+)?(?:\?[^#]*)?$/.test(path)) throw Error('許可されていない取得先です。');
  const response = await fetcher(path, {method: 'GET', cache: 'no-store', credentials: 'same-origin', signal});
  if (!response.ok) throw Error(`保存済みデータを読み込めませんでした（HTTP ${response.status}）。`);
  const payload = await response.json();
  if (!payload || typeof payload !== 'object' || payload.error) throw Error('保存済みデータの形式を確認できませんでした。');
  return payload;
}

const query = params => new URLSearchParams(Object.entries(params).filter(([, value]) => value !== undefined)).toString();
function pinned(payload, runId) {
  if (payload.schema_version !== 1 || payload.run_id !== runId) throw Error('実行結果の版が一致しません。保存済み結果を再読込してください。');
  return payload;
}

// Filtering and ordering must use the entire saved universe, including rows after
// the first API page. Each list is published only once every page is validated.
export async function loadAllPages(endpoint, params = {}, fetcher = globalThis.fetch, signal, runId = null) {
  let first = null, expectedTotal = null, offset = 0;
  const items = [];
  for (;;) {
    if (signal?.aborted) throw new DOMException('読込を中断しました。', 'AbortError');
    const payload = await requestApi(`${endpoint}?${query({...params, limit: 200, offset})}`, fetcher, signal);
    if (runId !== null) pinned(payload, runId);
    if (!Array.isArray(payload.items) || !Number.isSafeInteger(payload.total) || payload.total < 0 || payload.items.length > 200 || (payload.offset !== undefined && payload.offset !== offset)) throw Error('保存済み一覧のページ形式を確認できませんでした。');
    if (first === null) { first = payload; expectedTotal = payload.total; }
    if (payload.total !== expectedTotal) throw Error('読込中に一覧の件数が変わりました。保存済み結果を再読込してください。');
    items.push(...payload.items);
    if (items.length > expectedTotal) throw Error('保存済み一覧の件数が一致しません。');
    if (items.length === expectedTotal) return {...first, items, total: expectedTotal, offset: 0, limit: items.length};
    if (payload.items.length === 0) throw Error('一覧の途中ページを取得できませんでした。全件を表示するため再読込してください。');
    offset = items.length;
  }
}

export async function loadRunData(runId, fetcher = globalThis.fetch, signal) {
  const results = await Promise.allSettled([
    loadAllPages('/api/mbo/candidates', {run_id: runId}, fetcher, signal, runId),
    loadAllPages('/api/mbo/events', {run_id: runId}, fetcher, signal, runId),
  ]);
  return {
    candidates: results[0].status === 'fulfilled' ? results[0].value : null,
    events: results[1].status === 'fulfilled' ? results[1].value : null,
    errors: results.flatMap((result, index) => result.status === 'rejected' ? [`${index === 0 ? '候補' : '案件一覧'}：${safeText(result.reason?.message || '読込に失敗しました。')}`] : []),
  };
}

export async function loadWorkspace(fetcher = globalThis.fetch, signal, requestedRun = '') {
  const status = await requestApi('/api/mbo/status', fetcher, signal);
  if (status.schema_version !== 1 || !['mbo-local', 'mbo-dashboard'].includes(status.mode) || typeof status.offline !== 'boolean' || (status.mode === 'mbo-local' && !status.offline)) throw Error('MBOの閲覧モードを確認できませんでした。Asset Hubから開いてください。');
  const runs = await loadAllPages('/api/mbo/runs', {}, fetcher, signal);
  if (!Array.isArray(runs.items)) throw Error('実行履歴の形式を確認できませんでした。');
  const successful = runs.items.filter(run => run.status === 'success');
  const selected = successful.find(run => run.run_id === requestedRun) || successful.find(run => run.run_id === status.latest_success_run_id) || successful[0] || null;
  return {status, runs: runs.items, selected, ...(selected ? await loadRunData(selected.run_id, fetcher, signal) : {candidates: null, events: null, errors: []})};
}

export async function loadCompany(runId, securityId, fetcher = globalThis.fetch, signal) {
  return pinned(await requestApi(`/api/mbo/companies/${encodeURIComponent(securityId)}?${query({run_id: runId})}`, fetcher, signal), runId);
}

export function initMboApp(doc = document, fetcher = globalThis.fetch, options = {}) {
  const root = options.root || doc;
  const get = id => root === doc ? doc.getElementById(id) : root.querySelector(`#${id}`);
  const removals = [];
  const listen = (target, name, handler) => { if (!target) return; target.addEventListener(name, handler); removals.push(() => target.removeEventListener?.(name, handler)); };
  let state = null, generation = 0, detailGeneration = 0, controller = null, currentView = 'candidates', destroyed = false, weeklyStarted = false, casesPanel = null, casesPromise = null;
  const showError = errors => { const host = get('mboError'); host.hidden = currentView === 'cases' || !errors.length; host.textContent = errors.join(' / '); };
  const closeDetail = () => { ++detailGeneration; get('mboDetailSection').hidden = true; get('mboDetail').replaceChildren(); };
  const setBusy = busy => { get('mboReload').disabled = busy; get('mboRunSelect').disabled = busy || !state?.runs?.length; (options.root || get('mainContent'))?.setAttribute('aria-busy', String(busy)); };

  function viewFromHash() {
    const hash = doc.defaultView?.location.hash || '';
    setView(hash === '#mbo/cases' ? 'cases' : hash === '#mbo/events' ? 'events' : hash === '#mbo/history' ? 'history' : 'candidates');
  }

  function syncViewVisibility() {
    const isCases = currentView === 'cases';
    for (const section of ['Candidates', 'Events', 'History', 'Cases']) {
      const host = get(`mbo${section}Section`);
      if (host) host.hidden = section.toLowerCase() !== currentView;
    }
    for (const id of ['mboRunToolbar', 'mboCoverage', 'mboStatus', 'mboReload', 'mboWeeklyNotice']) { const host = get(id); if (host) host.hidden = isCases; }
    const toolbar = get('mboRunSelect')?.closest?.('.mbo-run-toolbar');
    if (toolbar) toolbar.hidden = isCases;
    get('mboDemoNotice').hidden = isCases || !(state?.selected?.demo || state?.candidates?.demo);
    get('mboError').hidden = isCases || !get('mboError').textContent;
  }

  async function ensureCases() {
    const host = get('mboCases');
    if (!host || destroyed) return;
    if (casesPromise) return casesPromise;
    host.textContent = '保存済みの過去事例を読み込んでいます…';
    casesPromise = (async () => {
      try {
        const load = options.caseLoader || (() => Promise.all([import('./mbo-cases.js'), import('./mbo-case-data.js'), import('./mbo-census-data.js')]).then(([ui, saved, census]) => ({mount: ui.mountMboCases, data: saved.MBO_CASE_DATA, lessons: saved.MBO_CASE_LESSONS, census: census.MBO_CENSUS_DATA})));
        const loaded = await Promise.resolve().then(load);
        if (!destroyed) casesPanel = loaded.mount(host, {data: loaded.data, lessons: loaded.lessons, census: loaded.census});
      } catch (error) {
        casesPromise = null;
        if (!destroyed) host.innerHTML = `<p class="mbo-notice mbo-error">過去事例を表示できませんでした。${esc(error?.message || '保存データを確認してください。')}</p><button type="button" class="mbo-button" data-mbo-case-retry>${options.caseLoader ? '保存済み事例を再読込' : 'ページを再読込'}</button>`;
      }
    })();
    return casesPromise;
  }

  function setView(section) {
    if (destroyed) return;
    const view = ['candidates', 'events', 'history', 'cases'].includes(section) ? section : 'candidates';
    currentView = view;
    syncViewVisibility();
    root.querySelectorAll('[data-mbo-nav]').forEach(anchor => {
      if (anchor.dataset.mboNav === view) anchor.setAttribute('aria-current', 'page'); else anchor.removeAttribute('aria-current');
    });
    closeDetail();
    if (view === 'cases') return ensureCases();
    if (!weeklyStarted) return reload();
  }

  function renderCandidates() {
    const payload = state?.candidates;
    if (!state?.selected) {
      get('mboCandidates').innerHTML = empty('まだ調査結果がありません', options.embedded ? '週次調査が完了すると、候補と根拠・価値評価をここで確認できます。' : '資料・銘柄CSVを取込み、Mac内のCLIで週次結果を作成してください。株価CSVやAPIキーがなくても利用できます。');
      get('mboCandidateCount').textContent = '持込銘柄の範囲を対象にします。';
      return;
    }
    if (!payload) { get('mboCandidates').innerHTML = empty('候補を読み込めませんでした', '保存済み結果を再読込してください。'); return; }
    const filtered = candidateSubset(payload.items, {query: get('mboSearch').value, filter: get('mboFilter').value, sort: get('mboSort').value});
    get('mboCandidateCount').textContent = `${filtered.length}件表示 / 登録候補 ${payload.total}件 · 全件から検索・絞り込み・並べ替え`;
    get('mboCandidates').innerHTML = renderCandidateTable(filtered);
  }

  function renderWorkspace() {
    const selected = state.selected, status = state.status;
    get('mboDemoNotice').hidden = !(selected?.demo || state.candidates?.demo);
    get('mboStatus').textContent = selected ? `保存済み結果を表示 · 基準日 ${safeText(selected.as_of, 32)} · ${selected.demo ? '架空デモ' : '持込銘柄の調査'} · 取得・更新は行っていません` : options.embedded ? '週次の調査結果はまだ登録されていません' : '資料持込モード · APIキー不要 · まだ実行結果がありません';
    get('mboRunSelect').innerHTML = state.runs.length ? state.runs.map(run => `<option value="${esc(run.run_id)}"${run.run_id === selected?.run_id ? ' selected' : ''}>${esc(run.as_of)} · ${run.demo ? '架空デモ' : '持込データ'} · ${esc(safeText(run.run_id, 48))}</option>`).join('') : '<option value="">実行結果なし</option>';
    get('mboRunMeta').textContent = selected ? `保存 ${safeText(selected.created_at, 48)} · ルール ${safeText(selected.rule_version, 60)}${selected.retrospective ? ' · 過去日を再構成。後日取得したデータは除外' : ''}` : options.embedded ? 'Macで調査を実行し、確認した結果を反映すると表示されます。' : '準備：python3 -m backend.mbo init → import → build。架空デモ：python3 -m backend.mbo demo（別の保存先）。';
    get('mboCoverage').innerHTML = renderCoverage(state.candidates?.coverage || selected?.coverage || {universe: 0, prices: 0, valued: 0, pending: 0});
    get('mboEvents').innerHTML = state.events ? renderEvents(state.events.items) : selected ? empty('案件一覧を読み込めませんでした', '再読込すると保存済み結果の取得を再試行します。') : renderEvents([]);
    get('mboDiff').innerHTML = renderDiff(state.candidates?.diff);
    get('mboRuns').innerHTML = renderRuns(state.runs);
    const errors = [...state.errors];
    if (['failed', 'error'].includes(status.last_attempt?.status)) errors.push(`最後の処理は失敗しました。表示中は前回成功版です。基準日 ${safeText(status.last_attempt.as_of, 32)}`);
    showError(errors);
    renderCandidates();
    syncViewVisibility();
  }

  async function reload(requestedRun = '') {
    if (destroyed) return;
    weeklyStarted = true;
    const token = ++generation;
    controller?.abort();
    controller = new AbortController();
    closeDetail();
    setBusy(true);
    get('mboStatus').textContent = '保存済みの実行結果を読み込んでいます…';
    showError([]);
    try {
      const next = await loadWorkspace(fetcher, controller.signal, requestedRun);
      if (token !== generation) return;
      state = next;
      renderWorkspace();
    } catch (error) {
      if (token !== generation || error.name === 'AbortError') return;
      showError([safeText(error.message || 'ローカルの保存結果を読み込めませんでした。')]);
      if (state) { get('mboStatus').textContent = '再読込に失敗しました。前回表示した保存結果を保持しています。'; get('mboRunSelect').value = state.selected?.run_id || ''; }
      else { get('mboStatus').textContent = '保存結果を確認してください。'; get('mboCandidates').innerHTML = empty('調査結果を取得できません', '保存済み結果の再読込で再試行できます。'); }
    } finally { if (token === generation) setBusy(false); }
  }

  async function openCompany(securityId) {
    if (destroyed || !state?.selected) return;
    const token = ++detailGeneration, selectedRun = state.selected.run_id;
    get('mboDetailSection').hidden = false;
    get('mboDetailTitle').textContent = '企業の調査内容';
    get('mboDetail').textContent = '選択した実行結果の企業詳細を読み込んでいます…';
    get('mboDetailTitle').focus();
    try {
      const payload = await loadCompany(selectedRun, securityId, fetcher, controller?.signal);
      if (token !== detailGeneration || state.selected?.run_id !== selectedRun) return;
      get('mboDetailTitle').textContent = safeText(payload.company?.name || '企業の調査内容', 120);
      get('mboDetail').innerHTML = renderCompanyDetail(payload.company);
    } catch (error) {
      if (token === detailGeneration && error.name !== 'AbortError') get('mboDetail').textContent = safeText(error.message || '企業詳細を読み込めませんでした。');
    }
  }

  listen(get('mboReload'), 'click', () => reload(state?.selected?.run_id || ''));
  listen(get('mboRunSelect'), 'change', event => reload(event.target.value));
  listen(get('mboSearch'), 'input', renderCandidates);
  listen(get('mboFilter'), 'change', renderCandidates);
  listen(get('mboSort'), 'change', renderCandidates);
  listen(get('mboCloseDetail'), 'click', closeDetail);
  listen(root, 'click', event => {
    const company = event.target.closest?.('[data-company]'), run = event.target.closest?.('[data-run]'), retry = event.target.closest?.('[data-mbo-case-retry]');
    if (company) openCompany(company.dataset.company);
    else if (run) reload(run.dataset.run);
    else if (retry) { if (options.caseLoader) ensureCases(); else window.location.reload(); }
  });
  if (options.listenHash !== false && doc.defaultView) listen(doc.defaultView, 'hashchange', viewFromHash);
  const initialView = options.listenHash === false ? options.initialView : (doc.defaultView?.location.hash || '').replace(/^#mbo\//, '');
  const ready = Promise.resolve(setView(initialView));
  const destroy = () => { destroyed = true; ++generation; ++detailGeneration; controller?.abort(); casesPanel?.destroy(); removals.splice(0).forEach(remove => remove()); };
  return {ready, reload, openCompany, setView, destroy, getState: () => state, getView: () => currentView};
}

if (typeof document !== 'undefined' && document.getElementById('mboStatus')) initMboApp(document);
