"""Evidence states for MBO research, deliberately without a probability score.

Historical cases generate questions; they do not estimate feature weights.
Financial context is kept separate from a company's intent and funding consent.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
import re

VERSION = 'mbo-evidence-2'
STATES = {'supported', 'contradicted', 'unknown', 'conflicting', 'not_applicable'}
EVIDENCE_TYPES = {'public_fact', 'analyst_hypothesis', 'own_scenario', 'post_announcement'}
SPEAKERS = {'company', 'management', 'shareholder', 'bidder', 'adviser', 'analyst'}
WORKFLOWS = {'awaiting', 'research', 'monitor', 'deferred'}
AXES = {'ownership': '所有・経営構造', 'motive': '非公開化を考える動機',
        'execution': '買収の実行可能性', 'obstacles': '障害・上場継続の利点'}
# State "supported" means that the named proposition is evidenced. In the
# obstacles dimension it means an obstacle is present, never a positive signal.
FACTORS = {
    'management_alignment': ('ownership', '経営陣の関与・実質所有関係'),
    'ownership_path': ('ownership', '株式取得・再出資の経路'),
    'transformation': ('motive', '事業転換・長期投資の必要性'),
    'succession': ('motive', '公表された承継・経営体制の検討'),
    'listing_tradeoff': ('motive', '非公開化の利点に関する公表説明'),
    'funding_capacity': ('execution', '買収規模に対する資金・返済余力'),
    'funding_commitment': ('execution', '資金提供・再出資の公表された合意'),
    'tender_feasibility': ('execution', '応募下限を満たす株主合意・自由処分の経路'),
    'execution_conditions': ('execution', '公表された実施前提条件の充足'),
    'shareholder_resistance': ('obstacles', '主要株主との条件不一致・反対'),
    'price_acceptability': ('obstacles', '買付価格・条件への異論'),
    'funding_gap': ('obstacles', '資金調達の不足・不成立'),
    'operating_uncertainty': ('obstacles', '投資負担・事業範囲・資金創出の不確実性'),
    'listing_benefits': ('obstacles', '会社が重視する上場継続の利点'),
    'competing_policy': ('obstacles', '競合する資本政策・契約制約'),
}
CRITERIA = {
    'tender_feasibility': '下限・既保有・不応募株・重複を除いた拘束的応募合意を照合し、解除条件や残余必要応募数を記録する。一般株主の応募予定だけでは到達を確認したことにしない。',
    'execution_conditions': '対象段階と条件ごとに未充足・充足・変更/放棄を確認する。条件の列挙や予定の公表だけを充足としない。',
    'price_acceptability': '誰が、どの版の価格・条件へ、いつ異論を表明したかを確認する。市場株価の買付価格超過だけでは異論と認定しない。障害命題のため根拠ありは異論ありを意味する。',
}


def _day(value):
    # Match core's JST normalization, including UTC or other offset timestamps.
    if len(value) == 10:
        return date.fromisoformat(value)
    moment = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if moment.tzinfo is None:
        raise ValueError('日時にはタイムゾーンが必要です')
    return moment.astimezone(timezone(timedelta(hours=9))).date()


def validate_assessment(row):
    if row['factor_id'] not in FACTORS:
        raise ValueError('factor_idが評価辞書にありません')
    if row['state'] not in STATES or row['evidence_type'] not in EVIDENCE_TYPES:
        raise ValueError('state/evidence_typeが不正です')
    if row['speaker'] not in SPEAKERS:
        raise ValueError('speakerの話者区分が不正です')
    if row['dimension'] != FACTORS[row['factor_id']][0]:
        raise ValueError('dimensionとfactor_idが一致しません')
    if _day(row['valid_until']) < _day(row['as_of']):
        raise ValueError('valid_untilはas_of以降にしてください')
    if row['state'] in {'supported', 'contradicted', 'conflicting'} and not row.get('quote'):
        raise ValueError('該当・反証・矛盾の判断には根拠原文quoteが必要です')
    if row['factor_id'] == 'funding_commitment' and row['state'] == 'supported':
        if not row.get('agreement_parties') or not row.get('agreement_terms'):
            raise ValueError('資金合意の確認にはagreement_parties/termsと原本位置が必要です')
    if row['factor_id'] == 'tender_feasibility' and row['state'] == 'supported':
        if not row.get('agreement_parties') or not row.get('agreement_terms'):
            raise ValueError('応募経路の確認にはagreement_parties/termsと原本位置が必要です')


def validate_review(row):
    if row['state'] not in WORKFLOWS:
        raise ValueError('作業状態はawaiting/research/monitor/deferredです')
    if _day(row['next_review_at']) < _day(row['as_of']):
        raise ValueError('next_review_atはas_of以降にしてください')
    if row['state'] == 'monitor' and not row.get('watch_trigger'):
        raise ValueError('monitorには次に確認する事象watch_triggerが必要です')
    try:
        basis = json.loads(row.get('basis_record_ids') or '[]')
    except (TypeError, ValueError):
        raise ValueError('basis_record_idsは根拠record IDのJSON配列です') from None
    if not isinstance(basis, list) or len(basis) > 50 or any(not isinstance(v, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', v) for v in basis):
        raise ValueError('basis_record_idsは50件以内の根拠record ID配列です')
    if row['state'] == 'monitor' and not basis:
        raise ValueError('monitorにはbasis_record_idsの根拠指定が必要です')
    row['basis_record_ids'] = basis


def _combine(states):
    effective = set(states) - {'unknown', 'not_applicable'}
    if 'conflicting' in effective or {'supported', 'contradicted'} <= effective:
        return 'conflicting'
    if effective:
        return next(iter(effective))
    return 'not_applicable' if states and set(states) == {'not_applicable'} else 'unknown'


def evaluate_assessment(facts, valuation, assessments, reviews, events, as_of):
    """Deterministic evidence grouping; no automatic promotion to monitoring.

    Missing motives/agreements do not imply unwillingness or infeasibility.
    A manually supplied hypothesis never turns into an evidenced public fact.
    """
    cutoff = _day(as_of)
    first_event = min((_day(e['announced_at']) for e in events), default=None)
    factors = {}
    for row in assessments:
        if _day(row['as_of']) <= cutoff:
            factors.setdefault(row['factor_id'], []).append(row)
    axes, verified, hypothesis, unresolved = [], 0, set(), 0
    usable_ids = {r['record_id'] for r in facts.values() if r.get('record_id') and
                  r.get('quality_status') == 'verified' and r.get('value') is not None}
    for dimension, label in AXES.items():
        evidence, factor_states, factor_details = [], [], []
        for factor_id, (axis, factor_label) in FACTORS.items():
            if axis != dimension:
                continue
            candidates = factors.get(factor_id, [])
            # New evidence from one source cannot erase a still-valid opposing
            # source. Corrections are already resolved explicitly by core.
            sources = {r['source_id'] for r in candidates}
            selected = [r for source in sorted(sources)
                        for r in candidates if r['source_id'] == source and
                        _day(r['as_of']) == max(_day(c['as_of']) for c in candidates if c['source_id'] == source)]
            effective = []
            for row in sorted(selected, key=lambda r: (r['source_id'], r['record_id'])):
                item = {key: row.get(key) for key in (
                    'record_id', 'factor_id', 'state', 'evidence_type', 'quote', 'interpretation',
                    'source_id', 'document_id', 'locator', 'public_at', 'observed_at', 'ready_at',
                    'quality_status', 'as_of', 'valid_until', 'reviewer', 'speaker', 'agreement_parties',
                    'agreement_terms', 'supersedes', 'correction_reason')}
                item['label'] = factor_label
                post = first_event is not None and _day(row['public_at']) >= first_event
                if post:
                    item['evidence_type'] = 'post_announcement'
                analyst_only = factor_id in CRITERIA and row['speaker'] == 'analyst'
                wrong_speaker = (analyst_only or (factor_id in {'transformation', 'succession', 'listing_tradeoff', 'listing_benefits'}
                                  and row['speaker'] not in {'company', 'management'}) or
                                 (factor_id == 'funding_commitment' and row['speaker'] not in {'company', 'management', 'bidder'}))
                eligible = (not wrong_speaker and row['quality_status'] == 'verified' and
                            item['evidence_type'] == 'public_fact' and
                            _day(row['valid_until']) >= cutoff)
                item['usable_for_candidate'] = eligible
                if not eligible:
                    item['exclusion_reason'] = ('分析者の説明であり当事者の合意・異論の確認ではない' if analyst_only else
                                                '会社・経営陣の説明ではない' if wrong_speaker else
                                                '案件公表以降の説明' if post or item['evidence_type'] == 'post_announcement'
                                                else '分析者の仮説・独自シナリオ' if item['evidence_type'] != 'public_fact'
                                                else '再確認期限超過' if _day(row['valid_until']) < cutoff
                                                else '原本・判断の確認待ち')
                evidence.append(item)
                if item['evidence_type'] in {'analyst_hypothesis', 'own_scenario'}:
                    hypothesis.add(factor_id)
                if eligible:
                    effective.append(row['state'])
            state = _combine(effective)
            if state in {'supported', 'contradicted', 'not_applicable'}:
                usable_ids.update(item['record_id'] for item in evidence if item['factor_id'] == factor_id and item['usable_for_candidate'])
            verified += state in {'supported', 'contradicted'}
            factor_states.append(state)
            detail = {'factor_id': factor_id, 'label': factor_label, 'state': state}
            if factor_id in CRITERIA:
                detail['criterion'] = CRITERIA[factor_id]
            factor_details.append(detail)
            unresolved += state in {'unknown', 'conflicting'}
        # Distinct positive propositions do not refute each other: a refuted
        # succession thesis must not erase an evidenced transformation need.
        present = set(factor_states)
        axis_state = ('conflicting' if 'conflicting' in present else 'supported' if 'supported' in present
                      else 'contradicted' if 'contradicted' in present else
                      'not_applicable' if present == {'not_applicable'} else 'unknown')
        axes.append({'id': dimension, 'label': label, 'state': axis_state,
                     'note': (f'{sum(s in {"supported", "contradicted", "not_applicable"} for s in factor_states)}/{len(factor_states)}論点を確認。' +
                              ('該当する材料と該当を否定する材料が別の論点に混在。軸全体の充足を意味しない。' if {'supported', 'contradicted'} <= present else '') +
                              ('障害材料あり。MBO不成立を断定しない。' if dimension == 'obstacles' and axis_state == 'supported'
                               else '背景論点の確認はMBO検討意思の確認とは別。未確認を否定しない。' if dimension == 'motive'
                               else '未確認は否定ではなく、全論点の確認完了も意味しない。')),
                     'factors': factor_details, 'evidence': evidence})

    known = [r for r in reviews if _day(r['as_of']) <= cutoff]
    latest_day = max((_day(r['as_of']) for r in known), default=None)
    decisions = [r for r in known if _day(r['as_of']) == latest_day]
    usable = [r for r in decisions if r['quality_status'] == 'verified' and _day(r['next_review_at']) >= cutoff]
    default_state = 'research' if facts else 'awaiting'
    workflow = {'state': default_state, 'label': '詳細調査中' if facts else '調査待ち',
                'reason': '監視・見送りの根拠確認は未完了。財務の有無はMBO適性の判定ではない。',
                'watch_trigger': None, 'next_review_at': None, 'reviewer': None}
    signatures = {(r['state'], r['reason'], r.get('watch_trigger'), r['next_review_at'], tuple(sorted(r.get('basis_record_ids', [])))) for r in usable}
    if len(signatures) == 1:
        row = max(usable, key=lambda r: (r['ready_at'], r['record_id']))
        basis = set(row.get('basis_record_ids') or [])
        if (row['state'] != 'monitor' or basis) and basis <= usable_ids:
            labels = {'awaiting': '調査待ち', 'research': '詳細調査中', 'monitor': '監視対象（手動選定）', 'deferred': '見送り（再確認予定あり）'}
            workflow = {key: row.get(key) for key in ('state', 'reason', 'watch_trigger', 'next_review_at', 'reviewer', 'basis_record_ids')}
            workflow['label'] = labels[row['state']]
        else:
            workflow['reason'] = '判断の根拠が失効・訂正・矛盾、または選択した財務から変化。監視・見送りを再確認。'
    elif len(signatures) > 1:
        workflow['reason'] = '同じ評価日の作業判断に矛盾。監視への昇格を保留。'
    if events:
        workflow = {**workflow, 'state': 'event', 'label': '公表済イベント研究',
                    'reason': '公表済み・報道済み案件を未発見候補の評価から分離。'}

    context = []
    def value(metric):
        fact = facts.get(metric, {})
        return Decimal(fact['value']) if fact.get('quality_status') == 'verified' and fact.get('value') is not None else None
    owner = value('owner_ratio')
    if owner is not None:
        context.append(f'確認できた経営陣・創業家持分 {owner * 100:.2f}%。実質所有の全体像・応募合意とは別。')
    cfo, capex = value('operating_cfo'), value('capex')
    if cfo is not None and capex is not None:
        context.append(f'営業CF−設備投資 {cfo - capex:,.0f}円（単年）。継続的な返済余力・MBO動機を保証しない。')
    if valuation.get('lbo', {}).get('status') == 'ok':
        context.append('独自LBO条件で価格を試算可能。融資承認・スポンサーの参加意思は未確認。')
    elif valuation.get('lbo', {}).get('status') == 'infeasible':
        context.append('今回の独自LBO条件では成立価格を算出できない。他の調達方法の不存在を意味しない。')
    return {'version': VERSION, 'validation_status': 'hypothesis_not_calibrated',
            'workflow': workflow, 'axes': axes,
            'information': {'verified_count': verified, 'hypothesis_count': len(hypothesis),
                            'unresolved_count': unresolved, 'coverage_label': '論点の確認件数。MBO確率・適性の点数ではない。'},
            'financial_context': context,
            'cautions': ['過去事例の原本に基づく論点整理。予測精度・発生確率・配点の有効性は未検証。',
                         '単年CF、現金余剰、保有比率20%による旧4点は、MBO有力度の順位に使用しない。',
                         '公表後の説明・分析者の仮説・独自資金試算を、事前に確認できた会社の意向に置き換えない。']}
