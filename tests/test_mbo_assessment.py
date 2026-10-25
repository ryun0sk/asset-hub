"""Evidence and workflow invariants; all companies and source text are fictional."""
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from backend.mbo import assessment, core
from backend.mbo.__main__ import demo, write_csv
from backend.mbo_dashboard import sanitize_bundle, query_response


TODAY = date.today().isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()


def evidence(**changes):
    return {'record_id': 'rec-test', 'factor_id': 'transformation', 'dimension': 'motive',
            'state': 'supported', 'evidence_type': 'public_fact', 'speaker': 'company',
            'quote': '架空の事業転換計画', 'interpretation': 'MBO意向までは確認していない',
            'as_of': TODAY, 'valid_until': TOMORROW, 'public_at': YESTERDAY,
            'observed_at': TODAY, 'ready_at': TODAY, 'source_id': 'demo-facts',
            'document_id': 'doc-test', 'locator': '架空資料1頁', 'reviewer': '検証担当',
            'quality_status': 'verified', **changes}


def assess(rows=None, reviews=None, events=None, facts=None, valuation=None):
    return assessment.evaluate_assessment(facts or {}, valuation or {}, rows or [], reviews or [], events or [], TODAY)


def axis(result, identifier):
    return next(a for a in result['axes'] if a['id'] == identifier)


class EvidenceStatesTests(unittest.TestCase):
    def test_census_execution_checks_do_not_follow_from_owner_ratio_or_positive_cashflow(self):
        result = assess(facts={'owner_ratio': {'quality_status': 'verified', 'value': '0.8'},
                               'operating_cfo': {'quality_status': 'verified', 'value': '100'},
                               'capex': {'quality_status': 'verified', 'value': '1'}})
        states = {f['factor_id']: f['state'] for a in result['axes'] for f in a['factors']}
        for key in ['tender_feasibility', 'execution_conditions', 'price_acceptability']:
            self.assertEqual(states[key], 'unknown')
        self.assertNotIn('score', result)

    def test_tender_path_support_needs_named_parties_and_terms(self):
        row = evidence(factor_id='tender_feasibility', dimension='execution')
        with self.assertRaisesRegex(ValueError, '応募経路'):
            assessment.validate_assessment(row)
        assessment.validate_assessment({**row, 'agreement_parties': '架空応募株主',
                                        'agreement_terms': '下限・応募合意・担保解除の確認範囲'})
        self.assertEqual(axis(assess([{**row, 'evidence_type': 'analyst_hypothesis'}]), 'execution')['state'], 'unknown')

    def test_census_checks_do_not_accept_an_analyst_opinion_as_party_confirmation(self):
        for factor, dimension in [('tender_feasibility', 'execution'), ('execution_conditions', 'execution'),
                                  ('price_acceptability', 'obstacles')]:
            result = assess([evidence(factor_id=factor, dimension=dimension, speaker='analyst')])
            self.assertEqual(axis(result, dimension)['state'], 'unknown')
            self.assertFalse(axis(result, dimension)['evidence'][0]['usable_for_candidate'])

    def test_missing_is_unknown_not_contradicted_and_no_score_exists(self):
        result = assess()
        self.assertTrue(all(a['state'] == 'unknown' for a in result['axes']))
        self.assertEqual(result['information']['unresolved_count'], len(assessment.FACTORS))
        self.assertNotIn('score', result)
        self.assertEqual(result['workflow']['state'], 'awaiting')

    def test_hypothesis_or_scenario_cannot_establish_company_motive(self):
        for kind in ['analyst_hypothesis', 'own_scenario', 'post_announcement']:
            result = assess([evidence(evidence_type=kind)])
            self.assertEqual(axis(result, 'motive')['state'], 'unknown')
            self.assertFalse(axis(result, 'motive')['evidence'][0]['usable_for_candidate'])

    def test_shareholder_proposal_is_not_management_intent(self):
        result = assess([evidence(speaker='shareholder')])
        self.assertEqual(axis(result, 'motive')['state'], 'unknown')
        self.assertIn('会社・経営陣', axis(result, 'motive')['evidence'][0]['exclusion_reason'])

    def test_public_fact_needs_fresh_reviewed_source_and_effective_date(self):
        for change in [{'quality_status': 'pending'}, {'valid_until': YESTERDAY}, {'as_of': TOMORROW}]:
            self.assertEqual(axis(assess([evidence(**change)]), 'motive')['state'], 'unknown')
        self.assertEqual(axis(assess([evidence()]), 'motive')['state'], 'supported')

    def test_opposite_evidence_is_conflict_not_last_import_wins(self):
        rows = [evidence(), evidence(record_id='rec-other', source_id='source-other', state='contradicted')]
        result = assess(rows)
        self.assertEqual(axis(result, 'motive')['state'], 'conflicting')
        self.assertEqual(assess(list(reversed(rows))), result)

    def test_new_date_does_not_erase_valid_opposing_source(self):
        rows = [evidence(as_of=YESTERDAY), evidence(record_id='rec-later', source_id='source-later', state='contradicted')]
        self.assertEqual(axis(assess(rows), 'motive')['state'], 'conflicting')

    def test_funding_agreement_needs_named_parties_and_terms(self):
        row = evidence(factor_id='funding_commitment', dimension='execution')
        with self.assertRaisesRegex(ValueError, 'agreement_parties'):
            assessment.validate_assessment(row)
        row.update(agreement_parties='架空銀行と買収者', agreement_terms='金額・条件は架空原本2頁')
        assessment.validate_assessment(row)
        self.assertEqual(axis(assess([{**row, 'speaker': 'shareholder'}]), 'execution')['state'], 'unknown')

    def test_shareholder_view_on_listing_is_not_company_policy(self):
        row = evidence(factor_id='listing_benefits', dimension='obstacles', speaker='shareholder')
        self.assertEqual(axis(assess([row]), 'obstacles')['state'], 'unknown')

    def test_multiple_sources_do_not_inflate_confirmed_factor_count(self):
        rows = [evidence(), evidence(record_id='rec-other', source_id='source-other')]
        self.assertEqual(assess(rows)['information']['verified_count'], 1)

    def test_after_announcement_explanation_is_event_research(self):
        event = {'announced_at': YESTERDAY, 'event_type': 'mbo', 'status': 'withdrawn'}
        result = assess([evidence()], events=[event])
        self.assertEqual(result['workflow']['state'], 'event')
        self.assertEqual(axis(result, 'motive')['state'], 'unknown')
        self.assertEqual(axis(result, 'motive')['evidence'][0]['evidence_type'], 'post_announcement')

    def test_timezone_cannot_move_post_event_evidence_to_previous_day(self):
        event = {'announced_at': TODAY + 'T00:00:00+09:00', 'event_type': 'mbo', 'status': 'announced'}
        row = evidence(public_at=YESTERDAY + 'T16:00:00Z')
        result = assess([row], events=[event])
        self.assertFalse(axis(result, 'motive')['evidence'][0]['usable_for_candidate'])

    def test_financial_plausibility_does_not_promote_to_monitor(self):
        facts = {k: {'value': v, 'quality_status': 'verified'} for k, v in
                 [('owner_ratio', '.8'), ('operating_cfo', '100'), ('capex', '1')]}
        result = assess(facts=facts, valuation={'lbo': {'status': 'ok'}})
        self.assertEqual(result['workflow']['state'], 'research')
        self.assertEqual(axis(result, 'execution')['state'], 'unknown')
        self.assertEqual(axis(result, 'motive')['state'], 'unknown')

    def test_manual_monitor_requires_trigger_and_review_date(self):
        row = {'state': 'monitor', 'as_of': TODAY, 'next_review_at': TOMORROW, 'watch_trigger': ''}
        with self.assertRaisesRegex(ValueError, 'watch_trigger'):
            assessment.validate_review(row)
        row.update(watch_trigger='次回決算', reason='根拠を確認', quality_status='verified', ready_at=TODAY,
                   record_id='review-1', reviewer='担当者', basis_record_ids='["rec-test"]')
        assessment.validate_review(row)
        self.assertEqual(assess([evidence()], reviews=[row])['workflow']['state'], 'monitor')
        row['next_review_at'] = YESTERDAY
        self.assertEqual(assess(reviews=[row])['workflow']['state'], 'awaiting')

    def test_monitor_downgrades_when_its_evidence_expires_or_conflicts(self):
        review = {'state': 'monitor', 'as_of': YESTERDAY, 'next_review_at': TOMORROW,
                  'watch_trigger': '決算', 'reason': '確認', 'quality_status': 'verified',
                  'ready_at': TODAY, 'record_id': 'review-1', 'basis_record_ids': ['rec-test']}
        self.assertEqual(assess([evidence()], reviews=[review])['workflow']['state'], 'monitor')
        for rows in [[evidence(valid_until=YESTERDAY)],
                     [evidence(), evidence(record_id='rec-negative', source_id='source-negative', state='contradicted')]]:
            result = assess(rows, reviews=[review])
            self.assertEqual(result['workflow']['state'], 'awaiting')
            self.assertIn('失効・訂正・矛盾', result['workflow']['reason'])

    def test_contradictory_manual_decisions_cannot_silently_promote(self):
        row = {'state': 'monitor', 'as_of': TODAY, 'next_review_at': TOMORROW, 'watch_trigger': '決算',
               'reason': '確認', 'quality_status': 'verified', 'ready_at': TODAY, 'record_id': 'review-1'}
        result = assess(reviews=[row, {**row, 'state': 'deferred', 'record_id': 'review-2'}])
        self.assertEqual(result['workflow']['state'], 'awaiting')
        self.assertIn('矛盾', result['workflow']['reason'])

    def test_new_work_queue_does_not_sort_by_retired_points(self):
        def company(code, priority):
            return {'security_id': code, 'code': code, 'name': code, 'status': 'pending',
                    'priority': priority, 'mbo_assessment': assess()}
        payload = {'schema_version': 1, 'run_id': 'run-test', 'companies': [company('B', 4), company('A', 0)]}
        result = query_response('/api/mbo/candidates', {}, status_reader=lambda: {},
                                runs_reader=lambda: {}, snapshot_reader=lambda _: payload)
        self.assertEqual([c['code'] for c in result['items']], ['A', 'B'])


class EvidenceImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.base = Path(self.temp.name) / 'db'
        demo(self.base)

    def tearDown(self):
        self.temp.cleanup()

    def import_row(self, row, kind='assessments'):
        directory = Path(self.temp.name) / ('import-' + str(len(list(Path(self.temp.name).iterdir()))))
        directory.mkdir()
        allowed = {k: v for k, v in row.items() if k in core.HEADERS[kind]}
        write_csv(directory / (kind + '.csv'), [allowed], core.HEADERS[kind])
        return core.import_bundle(directory, self.base, demo=True)

    def test_import_correction_dto_and_frozen_history(self):
        original = core.read_snapshot(self.base)
        old_path = self.base / 'published' / original['run_id'] / 'snapshot.json'
        old_digest = core.digest(old_path.read_bytes())
        row = evidence(code='DEMO1', exchange='DEMO')
        self.import_row(row)
        core.build(TODAY, self.base)
        snapshot = core.read_snapshot(self.base)
        company = next(c for c in snapshot['companies'] if c['code'] == 'DEMO1')
        self.assertEqual(axis(company['mbo_assessment'], 'motive')['state'], 'supported')
        conn = core.connection(self.base)
        try:
            prior = core.records(conn, 'assessments')[0]
        finally:
            conn.close()
        self.import_row({**row, 'state': 'contradicted', 'supersedes': prior['record_id'], 'correction_reason': '誤読訂正'})
        core.build(TODAY, self.base)
        revised = core.read_snapshot(self.base)
        company = next(c for c in revised['companies'] if c['code'] == 'DEMO1')
        self.assertEqual(axis(company['mbo_assessment'], 'motive')['state'], 'contradicted')
        self.assertEqual(core.digest(old_path.read_bytes()), old_digest)
        self.assertEqual(original['companies'][0]['valuation'], revised['companies'][0]['valuation'])
        run = core.read_runs(self.base)['items'][0]
        result = sanitize_bundle({'schema_version': 1, 'runs': [run], 'snapshots': {run['run_id']: revised},
                                  'latest_run_id': run['run_id']})
        projected = result['snapshots'][run['run_id']]['companies'][0]['mbo_assessment']
        self.assertEqual(projected, company['mbo_assessment'])

    def test_future_source_never_appears_in_current_axis(self):
        self.import_row(evidence(code='DEMO1', exchange='DEMO', public_at=TOMORROW))
        core.build(TODAY, self.base)
        company = core.read_snapshot(self.base)['companies'][0]
        self.assertEqual(axis(company['mbo_assessment'], 'motive')['state'], 'unknown')

    def test_first_report_stays_cutoff_after_formal_announcement_update(self):
        conn = core.connection(self.base)
        try:
            # DEMO3 already has a formal announcement dated today. Append an
            # earlier report to prove that latest event state cannot erase it.
            existing = next(r for r in core.records(conn, 'events') if r['code'] == 'DEMO3')
        finally:
            conn.close()
        self.import_row({**existing, 'status': 'reported', 'announced_at': YESTERDAY}, 'events')
        self.import_row(evidence(code='DEMO3', exchange='DEMO', public_at=YESTERDAY))
        core.build(TODAY, self.base)
        company = next(c for c in core.read_snapshot(self.base)['companies'] if c['code'] == 'DEMO3')
        self.assertEqual(axis(company['mbo_assessment'], 'motive')['evidence'][0]['evidence_type'], 'post_announcement')

    def test_unsupported_factor_and_unattributed_source_are_rejected(self):
        for change in [{'factor_id': 'founder_age'}, {'speaker': ''}, {'quote': ''}]:
            with self.assertRaises(ValueError):
                self.import_row(evidence(code='DEMO1', exchange='DEMO', **change))


if __name__ == '__main__':
    unittest.main()
