"""Rebuild the same local candidate inputs with the reviewed census checks."""
from pathlib import Path
from collections import Counter
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from backend.mbo import core
from backend.mbo.publish import export_dashboard

BASELINE = 'run-2026-10-18-3714ada8f872'
AS_OF = '2026-10-18'

def main():
    base = core.DEFAULT_DATA_DIR
    previous_path = base / 'published' / BASELINE / 'snapshot.json'
    before_hash = core.digest(previous_path.read_bytes())
    baseline = core.read_snapshot(base, BASELINE)
    current = core.read_snapshot(base)
    if current['run_id'] == BASELINE:
        result = core.build(AS_OF, base)
    else:
        assert current['as_of'] == AS_OF and current['rule_version'] == 'mbo-local-4-census-checks', 'Current changed; compare before rebuilding'
        result = {'run_id': current['run_id']}
    snapshot = core.read_snapshot(base, result['run_id'])
    assert core.digest(previous_path.read_bytes()) == before_hash
    old = {c['security_id']: c for c in baseline['companies']}
    assert set(old) == {c['security_id'] for c in snapshot['companies']}
    checks = ['tender_feasibility', 'execution_conditions', 'price_acceptability']
    for company in snapshot['companies']:
        prior = old[company['security_id']]
        for key in ['price', 'facts', 'valuation', 'events', 'status', 'review_notes']:
            assert company[key] == prior[key], (company['code'], key)
        factors = {f['factor_id']: f for a in company['mbo_assessment']['axes'] for f in a['factors']}
        assert all(factors[key]['state'] == 'unknown' and factors[key].get('criterion') for key in checks)
        assert company['mbo_assessment']['workflow'] == prior['mbo_assessment']['workflow']
    def manifest(run):
        return json.loads((base / 'runs' / run / 'manifest.json').read_text())
    assert manifest(BASELINE)['input_ids'] == manifest(result['run_id'])['input_ids']
    target = base / 'dashboard-results-census.json'
    exported = export_dashboard(base, target)
    summary = {'as_of': AS_OF, 'run_id': result['run_id'], 'baseline_run_id': BASELINE,
               'baseline_sha256': before_hash, 'rule_version': snapshot['rule_version'],
               'coverage': snapshot['coverage'], 'input_record_ids_unchanged': True,
               'prices_facts_valuations_events_unchanged': True, 'baseline_bytes_unchanged': True,
               'new_checks_unknown': checks,
               'workflow_counts': dict(Counter(c['mbo_assessment']['workflow']['state'] for c in snapshot['companies'])),
               'export': exported}
    Path(__file__).with_name('current-evaluation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False))

if __name__ == '__main__':
    main()
