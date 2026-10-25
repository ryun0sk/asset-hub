"""Validate and combine reviewed MBO episodes; never infer motives from keywords."""
from pathlib import Path
from collections import Counter
from datetime import date
import json
import re

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'research/themes/mbo-evaluation/2026-10-18/census-2021-2026'
AS_OF = '2026-10-18'
EXPECTED_TSE = {2021: 17, 2022: 11, 2023: 17, 2024: 18, 2025: 31}
MOTIVES = {
    'growth_investment': '成長投資・海外展開', 'restructuring': '事業再編・収益構造の改革',
    'succession': '経営承継・経営体制', 'listing_cost': '上場維持の負担',
    'sponsor_resources': 'スポンサーの人材・資金・支援', 'market_valuation': '市場評価・資本政策',
    'long_term_governance': '中長期の経営・意思決定', 'other': 'その他の公表動機',
}
OBSTACLES = {
    'tender_shortfall': '応募下限未達', 'price_disagreement': '買付価格・価値評価の不一致',
    'competing_bid': '競合する買収・資本政策', 'funding': '資金調達・返済条件',
    'approval': '許認可・実施前提条件', 'operating_risk': '事業・投資の不確実性', 'other': 'その他の障害',
    'market_price_above_offer': '市場株価が買付価格を上回る（株主の意図は未確認）',
}
FACTOR_MAP = {
    'growth_investment': ['transformation'], 'restructuring': ['transformation'],
    'succession': ['succession'], 'listing_cost': ['listing_tradeoff'],
    'sponsor_resources': ['management_alignment'],
    'market_valuation': ['listing_tradeoff'],
    'long_term_governance': ['management_alignment', 'listing_tradeoff'],
    'tender_shortfall': ['tender_feasibility'], 'price_disagreement': ['price_acceptability'],
    'competing_bid': ['competing_policy'], 'funding': ['funding_capacity', 'funding_commitment'],
    'approval': ['execution_conditions'], 'operating_risk': ['operating_uncertainty'],
}

def verified(value):
    return value in {'verified', 'primary_verified', 'confirmed', 'verified_primary',
                     'verified_primary_public_rationale', 'verified_primary_later_confirmation',
                     'verified_exchange', 'verified_exchange_delisting',
                     'verified_issuer_original', 'verified_existing_issuer_original', 'verified_exchange_list',
                     'verified_company_original', 'verified_company_original_body',
                     'verified_issuer_body', 'verified_body', 'verified_existing_case_source',
                     'verified_issuer_tender_result', 'verified_original_tob_failed', 'open_at_cutoff',
                     'verified_issuer_delisting_completed', 'verified_issuer_result_and_settlement',
                     'verified_buyer_investment_completed'}

def checked_date(value, label, *, cutoff=None):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError(label + ': ISO形式の日付が必要')
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ValueError(label + ': 存在しない日付') from None
    if cutoff is not None and value > cutoff:
        raise ValueError(label + ': 基準日より未来の実績・資料')
    return value


def observations(row, kind, source_map):
    result = []
    for entry in row.get(kind, []):
        ids = entry.get('source_ids') or ([entry['source_id']] if entry.get('source_id') else [])
        if not ids or any(key not in source_map for key in ids) or not entry.get('locator') or not entry.get('text'):
            raise ValueError(f'{row["episode_id"]}: {kind}の原本・位置・本文が不足')
        dates = [source_map[key].get('public_at') for key in ids]
        phase = ('unknown' if any(day is None for day in dates) else
                 'at_announcement' if row.get('announcement_date') and
                 all(day == row['announcement_date'] for day in dates) else
                 'before_formal_announcement' if row.get('announcement_date') and
                 all(day < row['announcement_date'] for day in dates) else 'after_announcement')
        category = entry.get('category', 'other')
        if category not in (MOTIVES if kind == 'motives' else OBSTACLES):
            raise ValueError(f'{row["episode_id"]}: 未定義の分類 {category}')
        result.append({'text': entry['text'], 'source_ids': ids, 'locator': entry['locator'],
                       'evidence_kind': entry.get('evidence_kind') or ('public_statement' if kind == 'motives' else 'documented_process'),
                       'evidence_role': entry.get('evidence_role'),
                       'availability_phase': phase, 'category': category})
    return result

def build():
    rows, exclusions, notes, candidate_checks = [], [], [], []
    for path in sorted(FOLDER.glob('years-*.json')):
        data = json.loads(path.read_text())
        if not isinstance(data.get('episodes'), list):
            raise ValueError(f'{path.name}: episodesが必要')
        rows.extend(data['episodes'])
        exclusions.extend(data.get('exclusions', []))
        candidate_checks.extend(data.get('candidate_checks', []))
        notes.extend(data.get('coverage_notes', []))
    extra = json.loads((FOLDER / 'root-boundary-checks.json').read_text())
    exclusions.extend(extra.get('exclusions', []))
    notes.extend(extra.get('coverage_notes', []))
    sources, cases, seen = {}, [], set()
    for original in rows:
        row = dict(original)
        eid = row['episode_id']
        if eid in seen:
            raise ValueError('episode_id重複: ' + eid)
        seen.add(eid)
        ann = row.get('announcement_date')
        if ann:
            checked_date(ann, eid + ': announcement_date', cutoff=AS_OF)
            if ann < '2021-01-01':
                raise ValueError(eid + ': 期間外の正式公表日')
        for key in ('result_date', 'delisting_date'):
            if row.get(key) is not None:
                checked_date(row[key], eid + ': ' + key, cutoff=AS_OF)
        if row.get('planned_delisting_date') is not None:
            checked_date(row['planned_delisting_date'], eid + ': planned_delisting_date')
        for source in row.get('sources', []):
            sid = source['source_id']
            normalized = {**source, 'source_type': 'primary_company_or_buyer_or_exchange'}
            if sid in sources:
                prior = sources[sid]
                if prior.get('url') != source.get('url') or prior.get('public_at') != source.get('public_at'):
                    raise ValueError('source_idの原本が衝突: ' + sid)
                # One exchange page may cite several company rows. Citation
                # locations belong to observations, not document identity.
                locations = sorted(set(prior.get('locators', [prior.get('locator', '')]) + [source.get('locator', '')]) - {''})
                normalized = {**prior, 'locators': locations, 'locator': ' / '.join(locations)}
            if source.get('public_at') is not None:
                checked_date(source['public_at'], eid + ': source.public_at', cutoff=AS_OF)
            if not source.get('url', '').startswith('https://'):
                raise ValueError(eid + ': HTTPS原本URLが必要')
            sources[sid] = normalized
        motives = observations(row, 'motives', sources)
        obstacles = observations(row, 'obstacles', sources)
        status = row.get('outcome_status', 'unknown')
        if status not in {'succeeded', 'failed', 'withdrawn', 'ongoing', 'unknown'}:
            raise ValueError(eid + ': 結果分類が不明: ' + status)
        checks = row.get('verification', {})
        if verified(checks.get('motive')) and not motives:
            raise ValueError(eid + ': 理由確認済みなのに本文なし')
        if ann and not verified(checks.get('announcement')):
            raise ValueError(eid + ': 未確認日付を確定欄へ設定')
        ann_ids = row.get('announcement_source_ids') or ([row['announcement_source_id']] if row.get('announcement_source_id') else [])
        result_ids = row.get('result_source_ids') or ([row['result_source_id']] if row.get('result_source_id') else [])
        if not ann_ids and ann:
            ann_ids = [s['source_id'] for s in row.get('sources', []) if s.get('public_at') == ann]
        if not ann_ids and ann:
            ann_ids = [s['source_id'] for s in row.get('sources', []) if s.get('discovery_document_type') in {'tender_offer_statement', 'position_statement'}][:1]
        for sid in [*ann_ids, *result_ids]:
            if sid not in sources:
                raise ValueError(eid + ': 未定義の結果・日付原本')
        if ann and (not ann_ids or not row.get('announcement_locator')):
            raise ValueError(eid + ': 正式公表日の根拠位置が不足')
        actual_delisting = row.get('delisting_date')
        if actual_delisting and actual_delisting > AS_OF:
            raise ValueError(eid + ': 将来の上場廃止を実績欄へ設定')
        cats = list(dict.fromkeys(m['category'] for m in motives))
        ocats = list(dict.fromkeys(o['category'] for o in obstacles))
        summary = row.get('outcome_note') or row.get('followup_note') or {
            'succeeded': '当該エピソードの成立を確認。上場廃止の完了は別欄で確認。',
            'failed': '当該エピソードは不成立。再試行や別買収とは区別。',
            'withdrawn': '当該エピソードは撤回・中止。', 'ongoing': '基準日時点で進行中。後日の結果を織り込まない。',
            'unknown': '結果の原本確認が未完了。',
        }[status]
        case = {'case_id': eid, 'code': str(row['code']), 'name': row['name'],
                'first_official_disclosure_date': ann, 'first_formal_mbo_announcement_date': ann,
                'first_date_source_ids': ann_ids, 'formal_date_source_ids': ann_ids,
                'formal_date_locator': row.get('announcement_locator'), 'transaction_class': 'census_' + status,
                'actors': row.get('actors') or '各原本の買付者・経営陣の記載を参照',
                'factor_ids': sorted({f for cat in cats + ocats for f in FACTOR_MAP.get(cat, [])}),
                'public_motives': motives, 'observed_obstacles': obstacles, 'observed_enabling_conditions': [],
                'outcome': {'mbo_tob_status': status, 'summary': summary, 'source_ids': result_ids,
                            'locator': row.get('result_locator'), 'result_kind': row.get('result_kind'),
                            'reviewed_as_of': AS_OF, 'delisting_status': 'completed' if actual_delisting else 'unconfirmed_or_not_completed'},
                'preannouncement_independent_evidence': {'independent_source_verified': False,
                    'reason': '本台帳は公表後の原本による事例分析。初報前の独立した予測根拠を全社で復元したものではない。'},
                'classification_cautions': row.get('cautions', []),
                'factor_mapping_note': '表示した論点は調査項目の参照。事後の理由を予測力の実証や加点に変換していない。',
                'census': {'year': int(ann[:4]) if ann else row.get('candidate_announcement_year') or row.get('discovery', {}).get('year'),
                           'verification': checks, 'status': status, 'motive_categories': cats,
                           'obstacle_categories': ocats, 'market': row.get('market'),
                           'is_tse': row.get('is_tse'), 'announcement_locator': row.get('announcement_locator')},
                }
        case['census']['market'] = row.get('market') or row.get('listing_market')
        case['transaction_method'] = row.get('transaction_method') or row.get('transaction_type')
        case['census']['verification_raw'] = dict(checks)
        case['census']['verification'] = {key: 'verified' if verified(value) else value for key, value in checks.items()}
        delisting_ids = row.get('delisting_source_ids') or ([row['delisting_source_id']] if row.get('delisting_source_id') else [])
        case['outcome']['delisting_source_ids'] = delisting_ids
        case['outcome']['delisting_locator'] = row.get('delisting_locator')
        case['outcome']['transaction_status'] = status
        case['census']['scope_class'] = 'formal_mbo'
        if case['transaction_method'] == 'management_led_share_consolidation_without_tob':
            case['census']['scope_class'] = 'mbo_equivalent_no_tob'
            case['transaction_class'] = 'census_equivalent_' + status
            case['outcome']['mbo_tob_status'] = 'not_applicable'
            case['outcome']['transaction_status'] = status
        elif row.get('result_kind') == 'delisting_observed':
            case['transaction_class'] = 'census_completion_observed'
            case['outcome']['mbo_tob_status'] = 'unknown'
            case['outcome']['tob_result_evidence'] = 'unconfirmed'
            case['outcome']['completion_evidence'] = 'exchange_delisting'
            case['outcome']['summary'] = '非公開化完了を取引所資料で確認。TOB結果原本そのものは未確認。' + (row.get('followup_note') or '')
            case['classification_cautions'] = [*case['classification_cautions'], '非公開化完了は取引所一覧で確認。TOB結果原本そのものは未確認であり、上場廃止日をTOB結果日としていない。']
        if actual_delisting:
            case['outcome']['actual_delisting_date'] = actual_delisting
        if row.get('planned_delisting_date'):
            case['outcome']['planned_delisting_date'] = row['planned_delisting_date']
        if row.get('result_date') and case['outcome']['mbo_tob_status'] != 'not_applicable':
            if row.get('result_kind') in {None, 'tob_result_notice'}:
                case['outcome']['mbo_tob_result_date'] = row['result_date']
            elif row.get('result_kind') in {'tob_result_faq', 'investment_completion_notice'}:
                case['outcome']['later_confirmation_publication_date'] = row['result_date']
        cases.append(case)
    # Preserve vetted report/formal-announcement boundaries using an exact
    # episode key. Never replace a failed first attempt with a later outcome.
    legacy = json.loads((FOLDER.parent / 'cases-research.json').read_text())
    supplement = json.loads((FOLDER.parent / 'inforich-supplement.json').read_text())
    legacy_cases = legacy['cases'] + [supplement['case']]
    legacy_sources = {**legacy['sources'], **supplement['sources']}
    def referenced(value):
        if isinstance(value, list):
            return {key for entry in value for key in referenced(entry)}
        if isinstance(value, dict):
            return {key for name, entry in value.items() for key in (entry if name.endswith('source_ids') else referenced(entry))}
        return set()
    for case in cases:
        matches = [c for c in legacy_cases if (c['code'], c['first_formal_mbo_announcement_date']) ==
                   (case['code'], case['first_formal_mbo_announcement_date'])]
        if len(matches) > 1:
            raise ValueError('旧詳細のエピソードキーが重複')
        if matches:
            for key in ['first_official_disclosure_date', 'first_date_source_ids',
                        'preannouncement_independent_evidence', 'pre_formal_signals']:
                if key in matches[0]:
                    case[key] = matches[0][key]
            for sid in referenced(case):
                if sid not in sources:
                    sources[sid] = legacy_sources[sid]
        if case['code'] == '9338':
            case['aliases'] = ['インフォリッチ']
    # Duplicate same-company same-date rows must be resolved explicitly, never silently dropped.
    keys = [(c['code'], c['first_formal_mbo_announcement_date']) for c in cases if c['first_formal_mbo_announcement_date']]
    if len(keys) != len(set(keys)):
        raise ValueError('同社・同日エピソードが重複。二段階買付けと再試行を確認してください')
    cases.sort(key=lambda c: (c['first_formal_mbo_announcement_date'] or '', c['case_id']), reverse=True)
    counts = {key: sum(verified(c['census']['verification'].get(key)) for c in cases) for key in ['announcement', 'motive', 'outcome']}
    yearly = []
    for year in range(2021, 2027):
        selected = [c for c in cases if c['census']['year'] == year]
        tse = [c for c in selected if c['census']['is_tse'] is True]
        yearly.append({'year': year, 'episodes': len(selected), 'companies': len({c['code'] for c in selected}),
                       'announcement_verified': sum(verified(c['census']['verification'].get('announcement')) for c in selected),
                       'motive_verified': sum(verified(c['census']['verification'].get('motive')) for c in selected),
                       'tse_episodes': len(tse), 'tse_benchmark': EXPECTED_TSE.get(year),
                       'formal_mbo': sum(c['census']['scope_class'] == 'formal_mbo' for c in selected),
                       'equivalent_no_tob': sum(c['census']['scope_class'] == 'mbo_equivalent_no_tob' for c in selected),
                       'tse_formal_mbo': sum(c['census']['scope_class'] == 'formal_mbo' for c in tse),
                       'tse_equivalent_no_tob': sum(c['census']['scope_class'] == 'mbo_equivalent_no_tob' for c in tse),
                       'market_unconfirmed': sum(c['census']['is_tse'] is None for c in selected)})
    data = {'schema_version': 1, 'collection_kind': 'census', 'as_of': AS_OF, 'start_date': '2021-01-01',
            'coverage_complete': False,
            'coverage_summary': '東証・名証を中心に年別件数と原本を照合。全国の完全捕捉は未確認で、TOKYO PRO Market等の一部の個別取引・過年度撤回履歴に確認余地がある。',
            'cases': cases, 'sources': sources, 'exclusions': exclusions, 'candidate_checks': candidate_checks, 'coverage_notes': notes,
            'company_count': len({c['code'] for c in cases}), 'verified': counts, 'yearly': yearly,
            'source_count': len({s['url'] for s in sources.values()}),
            'outcomes': dict(Counter(c['census']['status'] for c in cases)),
            'motive_labels': MOTIVES, 'obstacle_labels': OBSTACLES,
            'motive_counts': {cat: sum(verified(c['census']['verification'].get('motive')) and cat in c['census']['motive_categories'] for c in cases) for cat in MOTIVES},
            'obstacle_counts': {cat: sum(cat in c['census']['obstacle_categories'] for c in cases) for cat in OBSTACLES},
            'cautions': ['母集団は正式公表された非公開化MBO。全上場企業や未公表の意向を調べた母集団ではない。',
                         '各理由は公表した当事者の説明。複数分類があり、理由件数は合計しても案件総数に一致しない。',
                         '動機の頻度は予測力・因果効果を示さない。初報前の非MBO比較群と予測精度の校正は別工程。']}
    if (FOLDER / 'references.json').exists():
        reference = json.loads((FOLDER / 'references.json').read_text())
        data['references'] = reference['cases']
        for sid, source in reference['sources'].items():
            if sid in data['sources'] and any(data['sources'][sid].get(key) != source.get(key) for key in ('url', 'public_at')):
                raise ValueError('参考資料のsource_idが衝突: ' + sid)
            data['sources'][sid] = source
    # Legacy and reference documents are also part of the exported evidence.
    for sid, source in data['sources'].items():
        if not source.get('url', '').startswith('https://'):
            raise ValueError(sid + ': HTTPS原本URLが必要')
        if source.get('public_at') is not None:
            checked_date(source['public_at'], sid + ': source.public_at', cutoff=AS_OF)
    gap_path = FOLDER / 'scope-gap-candidates.json'
    data['scope_gap_candidates'] = json.loads(gap_path.read_text()) if gap_path.exists() else []
    (FOLDER / 'census.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    literal = json.dumps(data, ensure_ascii=False, indent=2).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    (ROOT / 'web/mbo-census-data.js').write_text('// Generated by scripts/build_mbo_census.py from reviewed episode ledgers.\nexport const MBO_CENSUS_DATA = ' + literal + ';\n')
    print(json.dumps({'episodes': len(cases), 'companies': data['company_count'], 'verified': counts, 'sources': data['source_count']}, ensure_ascii=False))

if __name__ == '__main__':
    build()
