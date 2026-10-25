import {mountMboCensus} from './mbo-census.js';
import {escapeHtml as esc, safeText, safeHttpsUrl} from './mbo-app.js';

const array = value => Array.isArray(value) ? value : [];
const record = value => value && typeof value === 'object' && !Array.isArray(value) ? value : {};
const CLASSIFICATIONS = Object.freeze({census_completion_observed: ['succeeded', '非公開化完了・TOB結果原本は未確認'], census_equivalent_succeeded: ['succeeded', 'MBOに準ずる非TOB非公開化・実施確認'], unlaunched_management_proposal_withdrawn: ['withdrawn', '正式実施前のMBO提案撤回'], census_succeeded: ['succeeded', '当該MBOエピソード成立'], census_failed: ['failed', '当該MBOエピソード不成立'], census_withdrawn: ['withdrawn', '撤回・中止'], census_ongoing: ['ongoing', '基準日時点で進行中'], census_unknown: ['unknown', '結果の原本確認待ち'],
  formal_mbo_tob_succeeded_and_delisted: ['succeeded', 'MBO成立・上場廃止'],
  formal_mbo_with_competing_proposal_tob_succeeded: ['succeeded', '競合提案後も元のMBO成立'],
  formal_mbo_failed_then_retry_tob_succeeded: ['retry', '初回MBO不成立 → 再TOB成立'],
  formal_mbo_failed_then_competing_acquisition_and_new_privatization_plan: ['different', 'MBO不成立 → 別買収・非公開化計画'],
  formal_mbo_failed_then_different_buyer_acquisition: ['different', 'MBO不成立 → 別買収者'],
  nonbinding_management_family_proposal_funding_not_secured: ['funding', '創業家提案・資金未達（TOB未開始）'],
});
const FACTORS = Object.freeze({tender_feasibility: '応募下限と株主合意', execution_conditions: '実施前提条件の充足', price_acceptability: '買付価格・条件への異論', management_alignment: '経営陣の参加', ownership_path: '所有・応募の経路', transformation: '事業変革・長期投資', succession: '経営承継', listing_tradeoff: '上場の利点と負担', funding_capacity: '資金余力', funding_commitment: '資金調達の合意', shareholder_resistance: '株主の反対・応募不足', funding_gap: '資金調達の不足', operating_uncertainty: '事業・投資の不確実性', listing_benefits: '上場を続ける利点', competing_policy: '競合提案・代替方針'});
const PHASES = Object.freeze({unknown: '資料公開時点の確認待ち', before_formal_announcement: '正式公表より前の説明・初報前予測とは別', at_announcement: '公表時の説明', after_announcement: '公表後の確認', after_failure: '不成立後の説明', after_proposal_acknowledgment: '提案受領の公表後', after_mbo_failure: 'MBO不成立後', after_retry_announcement: '再実施の公表後', reported_acknowledged_pre_formal: '報道後・正式公表前の確認'});
const KINDS = Object.freeze({documented_agreement: '公表された合意', announced_funding_plan: '公表された資金計画', public_statement: '当事者の説明', issuer_assessment: '会社・提案者の判断', documented_process: '公表された経緯', documented_condition: '公表された条件', observed_outcome: '結果の確認', reported_by_target: '対象会社が受領・公表', buyer_retrospective_statement: '買い手による事後説明', official_acknowledgment_after_media_report: '報道後の会社確認'});
const ROLES = Object.freeze({observed_failure_mechanism: '結果原本の直接の不成立要件', post_event_exchange_synthesis: '取引所の事後整理・因果認定と別', disclosed_execution_condition: '公表された実施条件', disclosed_conditional_risk: '仮定の中止条件・実際の失敗と別'});
const badge = text => `<span class="mbo-badge mbo-badge-muted">${esc(text)}</span>`;
const empty = text => `<p class="mbo-empty">${esc(text)}</p>`;
const date = value => value ? safeText(value, 40) : '未確認';
const classification = item => CLASSIFICATIONS[item?.transaction_class] || ['other', item?.transaction_class || '分類未確認'];
const displayNote = text => Object.entries(FACTORS).reduce((note, [id, label]) => note.replaceAll(id, label), safeText(text, 1000).replace(/\bfactor_ids\b/g, '表示した論点'));
const list = values => array(values).length ? `<ul class="mbo-list">${values.map(value => `<li>${esc(value, 1000)}</li>`).join('')}</ul>` : '<p class="mbo-muted">この保存版では確認していません。</p>';

export function validateCaseData(data) {
  if (!data || data.schema_version !== 1 || !Array.isArray(data.cases) || !data.sources || typeof data.sources !== 'object' || Array.isArray(data.sources)) throw Error('過去事例の保存データ形式を確認できませんでした。');
  return data;
}

export function caseSubset(data, {query = '', result = 'all'} = {}) {
  validateCaseData(data);
  const words = safeText(query, 100).normalize('NFKC').toLocaleLowerCase('ja-JP').trim().split(/\s+/).filter(Boolean);
  return data.cases.filter(item => item && typeof item === 'object').filter(item => {
    const text = `${item.name || ''} ${item.code || ''} ${item.actors || ''} ${array(item.factor_ids).map(id => FACTORS[id] || id).join(' ')}`.normalize('NFKC').toLocaleLowerCase('ja-JP');
    return words.every(word => text.includes(word)) && (result === 'all' || classification(item)[0] === result);
  });
}

function sourceLink(data, id, locator = '') {
  const source = record(data.sources[id]), url = safeHttpsUrl(source.url);
  const title = `${source.title || id || '資料未確認'} · 公表 ${date(source.public_at)} · ${locator || source.locator || '位置未確認'}`;
  return url ? `<a href="${esc(url, 2048)}" target="_blank" rel="noopener noreferrer">${esc(title, 700)} ↗</a>` : `<span>${esc(title, 700)}（安全な出所リンク未登録）</span>`;
}

function sourceLinks(data, ids, locator = '') {
  return array(ids).map(id => `<small class="mbo-case-source">${sourceLink(data, id, locator)}</small>`).join('');
}

function observations(data, values, title) {
  return `<article class="mbo-panel"><h3>${esc(title)}</h3>${array(values).length ? values.map(value => `<div class="mbo-evidence"><p>${esc(value?.text, 1200)}</p><p>${badge(PHASES[value?.availability_phase] || value?.availability_phase || '判明時点未確認')}${badge(KINDS[value?.evidence_kind] || '当事者資料の説明')}${value?.evidence_role ? badge(ROLES[value.evidence_role] || value.evidence_role) : ''}</p>${sourceLinks(data, value?.source_ids, value?.locator)}</div>`).join('') : '<p class="mbo-muted">この保存版では確認していません。</p>'}</article>`;
}

function sourceIds(item) {
  const ids = new Set();
  const visit = value => {
    if (!value || typeof value !== 'object') return;
    for (const [key, entry] of Object.entries(value)) {
      if (key.endsWith('source_ids')) array(entry).forEach(id => { if (typeof id === 'string') ids.add(id); });
      else if (Array.isArray(entry)) entry.forEach(visit);
      else if (entry && typeof entry === 'object') visit(entry);
    }
  };
  visit(item);
  return [...ids];
}

export function renderCaseDetail(data, item, lessons = {}) {
  validateCaseData(data);
  if (!item) return empty('一覧の企業名を選ぶと、公表理由・結果・根拠資料を確認できます。');
  const outcome = record(item.outcome), before = record(item.preannouncement_independent_evidence), sources = sourceIds(item);
  const actualEvents = [['later_confirmation_publication_date', '後続資料での結果・取得確認'], ['mbo_tob_result_date', item.census ? '取引結果公表' : 'TOB結果公表'], ['mbo_failure_announcement_date', 'MBO不成立公表'], ['first_result_date', '初回TOB結果公表'], ['retry_announcement_date', '再実施公表'], ['retry_result_date', '再TOB結果公表'], ['retry_settlement_confirmed_date', '再TOB決済確認'], ['subsequent_tob_result_date', '別買収者のTOB結果'], ['actual_delisting_date', '上場廃止（実績）']].filter(([key]) => outcome[key]);
  const plannedEvents = [['planned_shareholder_meeting_date', '株主総会（予定）'], ['planned_delisting_date', '上場廃止（予定・未完了）']].filter(([key]) => outcome[key]);
  const rows = [...actualEvents.map(([key, title]) => `<dt>${esc(title)}</dt><dd>${esc(date(outcome[key]))}</dd>`), ...plannedEvents.map(([key, title]) => `<dt>${esc(title)}</dt><dd>${esc(date(outcome[key]))} · 保存基準日時点の予定</dd>`)].join('');
  return `<article class="mbo-case-detail" aria-label="${esc(item.name)}の過去事例"><div class="mbo-section-head"><h2 tabindex="-1" data-case-heading>${esc(item.name)} <small>${esc(item.code)}</small></h2>${badge(classification(item)[1])}</div>${item.research_role_note ? `<p class="mbo-notice">${esc(item.research_role_note)}</p>` : ''}${item.period_caution ? `<p class="mbo-notice">${esc(item.period_caution)}</p>` : ''}
    <p class="mbo-muted">関与者（公表資料）：${esc(item.actors, 600)}</p>
    <div class="mbo-detail-grid"><article class="mbo-panel"><h3>公表と結果の時系列</h3><dl class="mbo-definition"><dt>${item.census ? '確認した公式公表（初報探索は全件未実施）' : '最初の公式確認'}</dt><dd>${esc(date(item.first_official_disclosure_date))}${sourceLinks(data, item.first_date_source_ids, item.census?.announcement_locator)}</dd><dt>${item.census?.scope_class === 'mbo_equivalent_no_tob' ? '非TOB非公開化の公表' : '正式MBOの公表'}</dt><dd>${item.first_formal_mbo_announcement_date ? esc(date(item.first_formal_mbo_announcement_date)) + sourceLinks(data, item.formal_date_source_ids, item.formal_date_locator) : item.census ? '正式公表日の原本確認待ち' : '正式MBOの実施公表なし'}</dd>${rows}</dl><p>${esc(outcome.summary, 1200)}</p>${sourceLinks(data, outcome.source_ids, outcome.locator)}${sourceLinks(data, outcome.delisting_source_ids, outcome.delisting_locator)}<p class="mbo-muted">確認基準日 ${esc(date(outcome.reviewed_as_of || data.as_of))}。予定日を完了実績には数えていません。</p></article>
    <article class="mbo-panel"><h3>現評価への反映</h3>${list(lessons[item.code])}<p>${array(item.factor_ids).map(id => badge(FACTORS[id] || id)).join('')}</p><p class="mbo-muted">${esc(displayNote(item.factor_mapping_note || '論点の参照タグです。効果・重み・発生確率を示しません。'), 600)}</p></article></div>
    <div class="mbo-detail-grid">${observations(data, item.public_motives, item.first_formal_mbo_announcement_date ? (item.census?.scope_class === 'mbo_equivalent_no_tob' ? '公表された非公開化の理由' : '公表されたMBOの理由') : '公表された提案・比較方針')}${observations(data, item.observed_obstacles, '障害・争点として確認したこと')}${observations(data, item.observed_enabling_conditions, '成立条件・後続取引で確認したこと')}</div>
    <article class="mbo-panel"><h3>公表前に予測できた情報か</h3><p>${esc(before.reason || '初報前の独立資料による事前予測は未確認です。', 1000)}</p><dl class="mbo-definition"><dt>初報より前の独立資料</dt><dd>${before.independent_source_verified === true ? '独立資料の確認あり（予測精度は未検証）' : '未確認・事前予測の実績には未採用'}</dd><dt>正式MBO公表より前</dt><dd>${before.official_pre_formal_source_verified === true ? '報道後の公式な検討確認あり。初報前の独立予測とは区別。' : 'この保存版では独立の事前材料を確認していません。'}</dd></dl>${array(item.pre_formal_signals).map(signal => `<p>${esc(signal.text, 1000)}</p>${sourceLinks(data, signal.source_ids, signal.locator)}`).join('')}</article>
    <article class="mbo-panel"><h3>分類するときの注意</h3>${list(array(item.classification_cautions).map(displayNote))}</article>
    <details class="mbo-case-sources"><summary>一次資料 ${sources.length}件・原文の短い引用</summary>${sources.map(id => { const source = record(data.sources[id]); return `<article class="mbo-evidence"><strong>${esc(source.title || id)}</strong><p class="mbo-muted">${esc(source.issuer || '公表主体未確認')} · 公表 ${esc(date(source.public_at))} · ${esc(source.locator || '位置未確認')}</p>${source.short_quote ? `<blockquote>${esc(source.short_quote, 400)}</blockquote>` : '<p class="mbo-muted">この資料の原文引用は未登録です。</p>'}${sourceLink(data, id)}</article>`; }).join('')}</details></article>`;
}

export function renderMboCases(data, lessons = {}, {query = '', result = 'all', selectedCase = ''} = {}) {
  validateCaseData(data);
  const items = caseSubset(data, {query, result});
  const selected = items.find(item => item.case_id === selectedCase) || null;
  const rows = items.map(item => `<tr><td><button type="button" class="mbo-company-button" data-mbo-case="${esc(item.case_id)}">${esc(item.name)}</button><small>${esc(item.code)}${item.research_role_note ? ' · 着想源の参考事例' : item.period_caution ? ' · 2020年公表の補助例' : ''}</small></td><td>${esc(date(item.first_official_disclosure_date))}<small>正式MBO ${item.first_formal_mbo_announcement_date ? esc(date(item.first_formal_mbo_announcement_date)) : '実施公表なし'}</small></td><td>${esc(classification(item)[1])}<small>${esc(item.outcome?.summary, 400)}</small></td><td>${esc(array(item.public_motives).map(value => value?.text || '').join(' / '), 200)}</td><td>${esc(array(lessons[item.code]).slice(0, 2).join(' / '), 240) || array(item.factor_ids).map(id => esc(FACTORS[id] || id)).join(' / ')}</td></tr>`).join('');
  return `<div class="mbo-cases"><div class="mbo-section-head"><div><h2>過去事例から評価項目を確認する</h2><p class="mbo-muted">ケース集は${esc(data.as_of)}の保存版です。週次の候補・株価データとは更新時点が異なります。</p></div></div><p class="mbo-notice">${esc(data.selection_method || '論点比較のために選んだ事例です。')} 発生頻度・成立率・予測精度は未検証です。公表理由は当事者の説明として扱います。</p>
    <div class="mbo-filters"><label>企業・コード・論点<input data-case-query type="search" autocomplete="off" maxlength="100" value="${esc(query, 100)}" placeholder="企業名・コード・資金など"></label><label>結果・取引の分類<select data-case-result>${[['all', 'すべて'], ['succeeded', '当初のMBO成立'], ['retry', '初回不成立・再TOB成立'], ['different', 'MBO不成立・別買収へ'], ['funding', '創業家提案・資金未達']].map(([value, title]) => `<option value="${value}"${result === value ? ' selected' : ''}>${esc(title)}</option>`).join('')}</select></label></div>
    <p class="mbo-muted" data-case-count>${items.length}社表示 / 保存版 ${data.cases.length}社 · ${Object.keys(data.sources).length}件の一次資料</p><div data-case-table>${items.length ? `<div class="mbo-table-wrap" tabindex="0" role="region" aria-label="過去事例の比較"><table><thead><tr>${['企業', '最初の公式確認', '結果・取引の分類', '公表された理由', '現評価への反映'].map(title => `<th scope="col">${title}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div>` : empty('条件に合う過去事例はありません。')}</div>
    <div data-case-detail>${renderCaseDetail(data, selected, lessons)}</div><details class="mbo-case-sources"><summary>調査範囲と限界</summary><p>${esc(data.scope, 1000)}</p>${list(data.inference_limits)}${Object.entries(record(data.unrepresented_or_unconfirmed_factors)).map(([key, text]) => `<p>${esc(FACTORS[key] || key)}：${esc(text, 1000)}</p>`).join('')}</details></div>`;
}

export function mountMboCases(host, {data, lessons = {}, census = null} = {}) {
  validateCaseData(data);
  if (census) {
    const merged = {...data, sources: {...data.sources, ...census.sources}};
    const referenceCases = [...data.cases.filter(item => !item.first_formal_mbo_announcement_date || item.first_formal_mbo_announcement_date < census.start_date), ...array(census.references)];
    const referenceHtml = `<details class="mbo-case-sources"><summary>期間外・正式公表前の参考事例（${referenceCases.length}件）</summary>${referenceCases.map(item => renderCaseDetail(merged, item, lessons)).join('')}</details>`;
    return mountMboCensus(host, {data: census, referenceHtml,
      renderDetail: item => {
        const detailed = data.cases.filter(old => old.code === item.code && old.first_formal_mbo_announcement_date);
        return renderCaseDetail(merged, item, lessons) + (detailed.length ? `<details class="mbo-case-sources"><summary>同社の個別詳細調査・初報や後続取引（台帳の件数と別）</summary><p class="mbo-muted">以前の詳細調査です。初回不成立から再実施までをまとめた事例も含むため、選択中のエピソードの結果とは分けてご覧ください。</p>${detailed.map(old => renderCaseDetail(merged, old, lessons)).join('')}</details>` : '');
      }});
  }
  const state = {query: '', result: 'all', selectedCase: ''};
  let destroyed = false;
  const render = () => { if (!destroyed) host.innerHTML = renderMboCases(data, lessons, state); };
  const update = event => {
    if (destroyed) return;
    const query = event.target.closest?.('[data-case-query]'), result = event.target.closest?.('[data-case-result]');
    if (query) state.query = safeText(query.value, 100);
    else if (result) state.result = safeText(result.value, 30);
    else return;
    // Replace only results while typing so the input focus and caret survive.
    const markup = renderMboCases(data, lessons, state), template = host.ownerDocument?.createElement?.('template');
    if (template?.content) {
      template.innerHTML = markup;
      for (const selector of ['[data-case-count]', '[data-case-table]', '[data-case-detail]']) {
        const target = host.querySelector(selector), next = template.content.querySelector(selector);
        if (target && next) target.innerHTML = next.innerHTML;
      }
    } else render();
  };
  const click = event => {
    const button = event.target.closest?.('[data-mbo-case]');
    if (!button || destroyed) return;
    state.selectedCase = button.dataset.mboCase;
    const item = caseSubset(data, state).find(item => item.case_id === state.selectedCase);
    const detail = host.querySelector('[data-case-detail]');
    if (detail) { detail.innerHTML = renderCaseDetail(data, item, lessons); detail.querySelector?.('[data-case-heading]')?.focus(); }
  };
  host.addEventListener('input', update);
  host.addEventListener('change', update);
  host.addEventListener('click', click);
  render();
  return {getState: () => ({...state}), destroy() { destroyed = true; host.removeEventListener('input', update); host.removeEventListener('change', update); host.removeEventListener('click', click); }};
}
