"""Re-evaluate the saved universe without changing prices or DCF assumptions.

--apply appends analyst workflow decisions and a new immutable run locally.
It never uploads, commits, fetches market data, or rewrites a historical run.
"""
from datetime import date
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from backend.mbo import core  # noqa: E402
from backend.mbo.__main__ import write_csv  # noqa: E402

AS_OF = '2026-10-18'
BASELINE = 'run-2026-10-18-2f4170da4bf7'
OUTPUT = Path(__file__).parent / 'current-evaluation.json'
REASONS = {
    '6459': ('買収後の事業範囲と借入内訳、実質所有関係を確認。旧単体CFからMBO余力を断定しない。', '買収後の決算・借入内訳・資本政策'),
    '7937': ('在庫と営業CFの変化、設備投資・経営陣の所有関係を確認。単年の負のCFでMBO不能とは判断しない。', '在庫・CF・所有関係の更新'),
    '4628': ('同一BS日の非支配持分、投資必要額と実質所有を確認。現金の多さだけではMBO意向不明。', '財務内訳・大株主・投資方針'),
    '5945': ('金融資産の回収可能性・本社建替え投資額・所有関係を確認。資産感応度は非公開化意向の証拠ではない。', '建替え予算・有価証券・資本政策'),
    '5982': ('株数・信託、設備投資と海外展開、実質所有を確認。LBO試算の成立は金融機関の合意とは別。', '設備投資・中間決算・大株主'),
    '7927': ('子会社売却後の利益・CF・株数を確認。売却益や旧連結利益をMBO適性へ転用しない。', '事業売却後の決算・株式数・資本政策'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--data-dir', type=Path, default=core.DEFAULT_DATA_DIR)
    args = parser.parse_args()
    baseline = core.read_snapshot(args.data_dir, BASELINE)
    current = core.read_snapshot(args.data_dir)
    previous_hash = core.digest(core.encode(baseline))
    old_by_id = {c['security_id']: c for c in baseline['companies']}
    for company in current['companies']:
        before = old_by_id.get(company['security_id'])
        if not before or any(before[k] != company[k] for k in ('facts', 'price', 'valuation', 'events')):
            raise ValueError('初回から金融データ・対象集合が変化。今回の保存版を使った再評価は停止します')
    decisions = []
    for company in baseline['companies']:
        if company['status'] == 'event':
            continue
        detailed = company['code'] in REASONS
        reason, trigger = REASONS.get(company['code'], (
            '財務・所有構造・動機・実行可能性の一次資料が未充足。旧優先度0は不適格ではなく未調査。',
            '通期財務・大株主・事業方針の一次取得'))
        decisions.append({'code': company['code'], 'exchange': company['exchange'],
                          'state': 'research' if detailed else 'awaiting', 'reason': reason,
                          'watch_trigger': trigger, 'as_of': AS_OF, 'next_review_at': '2026-10-25',
                          'public_at': AS_OF, 'source_id': 'mbo-evidence-review-20261018',
                          'locator': '独自調査判断/' + company['code'], 'quality_status': 'verified',
                          'reviewer': 'Codex（保存原本照合・Astra設計レビュー）', 'basis_record_ids': '[]'})
    plan = {'as_of': AS_OF, 'baseline_run_id': BASELINE, 'workflow_counts': {
        state: sum(r['state'] == state for r in decisions) for state in ['research', 'awaiting', 'monitor', 'deferred']},
        'financial_data_updated': False, 'mbo_probability_calibrated': False,
        'decisions': [{'code': r['code'], 'state': r['state'], 'reason': r['reason']} for r in decisions]}
    if not args.apply:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return
    if date.today().isoformat() != AS_OF:
        raise ValueError('保存時点以外の日に同日観測を装って実行できません。新しい日付版を作成してください')
    inbox = core.private_dir(ROOT / 'data/private/mbo-inbox/2026-10-18-evaluation')
    core.atomic(inbox / 'analyst-review.txt', core.encode(plan))
    write_csv(inbox / 'documents.csv', [{'source_id': 'mbo-evidence-review-20261018',
              'file': 'analyst-review.txt', 'title': '独自の調査作業判断（会社のMBO意向ではない）',
              'source_url': '', 'published_at': AS_OF}], core.HEADERS['documents'])
    write_csv(inbox / 'reviews.csv', decisions, core.HEADERS['reviews'])
    core.import_bundle(inbox, args.data_dir)
    result = core.build(AS_OF, args.data_dir)
    snapshot = core.read_snapshot(args.data_dir, result['run_id'])
    assert core.digest(core.encode(core.read_snapshot(args.data_dir, BASELINE))) == previous_hash
    for company in snapshot['companies']:
        before = old_by_id[company['security_id']]
        assert all(before[k] == company[k] for k in ('facts', 'price', 'valuation', 'events'))
    summary = {**plan, 'run_id': result['run_id'], 'rule_version': snapshot['rule_version'],
               'baseline_snapshot_unchanged': True, 'dcf_and_prices_unchanged': True,
               'companies': [{'code': c['code'], 'name': c['name'], 'assessment': c['mbo_assessment']}
                             for c in snapshot['companies']]}
    OUTPUT.write_bytes(core.encode(summary))
    print(json.dumps({k: v for k, v in summary.items() if k not in {'companies', 'decisions'}}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
