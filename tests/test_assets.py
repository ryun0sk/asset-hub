import io
import json
import math
import shutil
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from backend import assets
from backend.assets import (CARRY_FORWARD_CLASSES, CLASS_LABELS, CLASSES, STATE_OBJECT, asset_document, asset_payload,
                            build_state, gcloud_session, load_sources, push, template, validate_accounts,
                            validate_snapshot)
from backend.paths import ROOT
from backend.storage import Conflict, GCSDocument, LocalDocument

FIXTURES = Path(__file__).resolve().parent / 'fixtures/assets'
TODAY = date(2026, 10, 4)
NOW = datetime(2026, 10, 4, 1, 0, tzinfo=timezone.utc)
ACCOUNT_IDS = {'mizuho', 'rakuten-bank', 'smbc', 'bitflyer', 'binance', 'sbi-tokutei', 'sbi-nisa', 'daiwa', 'private-equity'}
CONFIG = {'project': 'asset-hub-test', 'project_number': '123456', 'account': 'owner@example.com',
          'region': 'asia-northeast1', 'service': 'asset-hub'}


def read_fixture(relative):
    return json.loads((FIXTURES / relative).read_text(encoding='utf-8'))


ACCOUNTS = validate_accounts(read_fixture('accounts.json'))


def position(**changes):
    row = {'account': 'sbi-tokutei', 'class': 'stock', 'market': 'JP', 'symbol': '285A', 'name': 'キオクシア',
           'quantity': 100, 'valueJpy': 650000, 'costJpy': 400000}
    row.update(changes)
    return row


DEFAULT = object()


def snapshot(positions=DEFAULT, **changes):
    data = {'version': 1, 'date': '2026-10-04', 'positions': [position()] if positions is DEFAULT else positions}
    data.update(changes)
    return data


def check(data, filename_date='2026-10-04', today=TODAY):
    return validate_snapshot(data, ACCOUNTS, filename_date=filename_date, today=today)


def rejects(test, data, *fragments, filename_date='2026-10-04'):
    with test.assertRaises(ValueError) as caught:
        check(data, filename_date=filename_date)
    for fragment in fragments:
        test.assertIn(fragment, str(caught.exception))


class AccountsTest(unittest.TestCase):
    def test_fixture_accounts_validate_and_unknown_keys_are_ignored(self):
        data = read_fixture('accounts.json')
        self.assertEqual(data['_note'], 'テスト用のダミー値')
        self.assertEqual(set(ACCOUNTS), ACCOUNT_IDS)
        self.assertEqual(ACCOUNTS['sbi-nisa']['label'], 'SBI証券 NISA')
        self.assertEqual(ACCOUNTS['sbi-nisa']['institution'], 'SBI証券')
        self.assertEqual(ACCOUNTS['private-equity']['defaultClass'], 'private')
        self.assertEqual(set(ACCOUNTS['mizuho']), {'id', 'institution', 'label', 'defaultClass', 'currency', 'readGuide'})
        account = dict(data['accounts'][0], extra='ignored')
        del account['readGuide']
        validated = validate_accounts({'accounts': [account]})
        self.assertEqual(set(validated['mizuho']), {'id', 'institution', 'label', 'defaultClass', 'currency'})

    def test_each_account_rule_names_the_field(self):
        first = read_fixture('accounts.json')['accounts'][0]
        cases = [({'id': 'Mizuho'}, 'accounts[0].id'), ({'id': 'a'}, 'accounts[0].id'), ({'id': '-abc'}, 'accounts[0].id'),
                 ({'id': 'a' * 41}, 'accounts[0].id'), ({'id': None}, 'accounts[0].id'),
                 ({'institution': ''}, 'institution'), ({'label': '  '}, 'label'), ({'label': None}, 'label'),
                 ({'defaultClass': 'equity'}, 'defaultClass'), ({'defaultClass': None}, 'defaultClass'),
                 ({'currency': 'jpy'}, 'currency'), ({'currency': 'JPYY'}, 'currency'), ({'currency': None}, 'currency'),
                 ({'readGuide': 5}, 'readGuide')]
        for changes, fragment in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError) as caught:
                validate_accounts({'accounts': [dict(first, **changes)]})
            self.assertIn(fragment, str(caught.exception))
            self.assertIn('accounts.json', str(caught.exception))
        for data in [{'accounts': []}, {}, [], {'accounts': 'x'}, {'accounts': [first, dict(first)]},
                     {'version': 2, 'accounts': [first]}, {'accounts': ['x']}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_accounts(data)
        with self.assertRaises(ValueError) as caught:
            validate_accounts({'accounts': [first, dict(first, label='other')]})
        self.assertIn('重複', str(caught.exception))
        self.assertEqual(set(validate_accounts({'version': 1, 'accounts': [first]})), {'mizuho'})


class SnapshotTest(unittest.TestCase):
    def test_valid_snapshot_drops_unknown_keys_and_null_optionals(self):
        data = snapshot([position(extra='ignored', quantity=None, costJpy=None, market=None)], _note='dummy', other=1,
                        recordedAt='2026-10-04T10:00:00Z', source='screenshot')
        result, warnings = check(data)
        self.assertEqual(warnings, [])
        self.assertEqual(set(result), {'version', 'date', 'recordedAt', 'source', 'positions', 'notes'})
        self.assertEqual(result['positions'], [{'account': 'sbi-tokutei', 'class': 'stock', 'symbol': '285A',
                                                'name': 'キオクシア', 'valueJpy': 650000}])
        self.assertEqual(result['notes'], [])
        self.assertEqual(result['recordedAt'], '2026-10-04T10:00:00Z')

    def test_version_and_date_rules(self):
        for version in [2, '1', True, None]:
            rejects(self, snapshot(version=version), 'version')
        for day in ['2026/10/04', '2026-10-4', '2026-02-30', '', None, 20261004]:
            rejects(self, snapshot(date=day), 'date', filename_date=None)
        rejects(self, snapshot(date='2026-10-03'), 'ファイル名と一致しません')
        rejects(self, snapshot(date='2026-10-05'), '未来の日付', filename_date='2026-10-05')
        with self.assertRaises(ValueError):
            validate_snapshot(snapshot(date='2999-01-01'), ACCOUNTS)
        result, _ = check(snapshot(date='2026-10-03'), filename_date='2026-10-03')
        self.assertEqual(result['date'], '2026-10-03')
        result, _ = check(snapshot(), filename_date=None)
        self.assertEqual(result['date'], '2026-10-04')

    def test_recorded_at_source_and_notes(self):
        rejects(self, snapshot(recordedAt='yesterday'), 'recordedAt')
        rejects(self, snapshot(recordedAt=12345), 'recordedAt')
        rejects(self, snapshot(source=7), 'source')
        rejects(self, snapshot(notes='memo'), 'notes')
        rejects(self, snapshot(notes=[1]), 'notes')
        result, _ = check(snapshot(recordedAt='2026-10-04T10:05:00+09:00', notes=['a', 'b']))
        self.assertEqual(result['notes'], ['a', 'b'])
        self.assertEqual(check(snapshot(notes=None))[0]['notes'], [])

    def test_position_rules_name_the_row_and_field(self):
        cases = [({'account': 'unknown'}, 'account'), ({'account': None}, 'account'),
                 ({'class': 'equity'}, 'class'), ({'market': 'EU'}, 'market'),
                 ({'symbol': '預り金'}, 'symbol'), ({'symbol': ''}, 'symbol'), ({'symbol': 'A' * 33}, 'symbol'),
                 ({'symbol': 'with space'}, 'symbol'), ({'symbol': None}, 'symbol'),
                 ({'name': ''}, 'name'), ({'name': None}, 'name'),
                 ({'valueJpy': None}, 'valueJpy'), ({'valueJpy': -1}, 'valueJpy'), ({'valueJpy': 1.5}, 'valueJpy'),
                 ({'valueJpy': True}, 'valueJpy'), ({'valueJpy': '100'}, 'valueJpy'),
                 ({'costJpy': -1}, 'costJpy'), ({'costJpy': 1.5}, 'costJpy'), ({'costJpy': True}, 'costJpy'),
                 ({'quantity': 0}, 'quantity'), ({'quantity': -1}, 'quantity'), ({'quantity': True}, 'quantity'),
                 ({'quantity': 'x'}, 'quantity'), ({'quantity': math.inf}, 'quantity'),
                 ({'currency': 'usd'}, 'currency'), ({'currency': 'US'}, 'currency'), ({'currency': 'A' * 11}, 'currency'),
                 ({'nativeAmount': 'x'}, 'nativeAmount'), ({'nativeAmount': math.nan}, 'nativeAmount'),
                 ({'nativeAmount': True}, 'nativeAmount'),
                 ({'carryForward': 'yes'}, 'carryForward'), ({'carryForward': True}, 'carryForward')]
        for changes, fragment in cases:
            with self.subTest(changes=changes):
                rejects(self, snapshot([position(**changes)]), 'snapshots/2026-10-04.json: positions[0].' + fragment)
        rejects(self, snapshot([position(), 'x']), 'positions[1]')
        for rows in [[], {}, None, 'x']:
            rejects(self, snapshot(rows), 'positions')
        missing = snapshot()
        del missing['positions']
        rejects(self, missing, 'positions')
        with self.assertRaises(ValueError) as caught:
            check(snapshot([position(valueJpy=None)]))
        self.assertIn('未入力', str(caught.exception))
        self.assertIn('sbi-tokutei/285A', str(caught.exception))

    def test_accepted_optional_values(self):
        private = {'account': 'private-equity', 'class': 'private', 'symbol': 'PRIVATE-A', 'name': 'A社', 'valueJpy': 100,
                   'carryForward': True}
        rows = [position(valueJpy=0), position(symbol='AAPL', market='US', currency='USD', nativeAmount=2345.67, quantity=10.5),
                {'account': 'bitflyer', 'class': 'crypto', 'symbol': 'BTC', 'name': 'BTC', 'quantity': 0.0123, 'valueJpy': 1,
                 'currency': 'BTC', 'nativeAmount': -0.5},
                private, dict(private, symbol='PRIVATE-B', carryForward=False)]
        result, _ = check(snapshot(rows))
        self.assertEqual(result['positions'][0]['valueJpy'], 0)
        self.assertEqual(result['positions'][1]['nativeAmount'], 2345.67)
        self.assertNotIn('market', result['positions'][2])
        self.assertIs(result['positions'][3]['carryForward'], True)
        self.assertNotIn('carryForward', result['positions'][4])
        self.assertTrue(all(p['class'] in CLASSES for p in result['positions']))

    def test_duplicates_and_zero_total(self):
        rejects(self, snapshot([position(), position(valueJpy=1)]), 'positions[1]', '重複', 'sbi-tokutei/stock/285A')
        rows = [position(), {'account': 'sbi-tokutei', 'class': 'cash', 'symbol': 'JPY', 'name': '預り金', 'valueJpy': 1},
                {'account': 'bitflyer', 'class': 'cash', 'symbol': 'JPY', 'name': '日本円', 'valueJpy': 1}]
        self.assertEqual(len(check(snapshot(rows))[0]['positions']), 3)
        rejects(self, snapshot([position(valueJpy=0)]), '合計が 0')

    def test_weekday_is_only_a_warning(self):
        result, warnings = check(snapshot(date='2026-10-01'), filename_date='2026-10-01')
        self.assertEqual(result['date'], '2026-10-01')
        self.assertEqual(len(warnings), 1)
        self.assertIn('土日ではありません', warnings[0])
        self.assertIn('木曜日', warnings[0])
        self.assertIn('snapshots/2026-10-01.json', warnings[0])
        self.assertEqual(check(snapshot(date='2026-10-03'), filename_date='2026-10-03')[1], [])


class BuildTest(unittest.TestCase):
    def test_build_sorts_dates_and_drops_null_fields(self):
        later = {'version': 1, 'date': '2026-10-04', 'recordedAt': '2026-10-04T10:00:00+09:00',
                 'positions': [dict(position(), costJpy=None, extra='x')], 'notes': ['memo']}
        earlier = {'version': 1, 'date': '2026-09-27', 'positions': [position(valueJpy=1)], 'notes': []}
        state = build_state(ACCOUNTS, [later, earlier], NOW)
        self.assertEqual([s['date'] for s in state['snapshots']], ['2026-09-27', '2026-10-04'])
        self.assertEqual(state['latestDate'], '2026-10-04')
        self.assertEqual(state['builtAt'], NOW.isoformat())
        self.assertEqual(state['version'], 1)
        self.assertEqual([a['id'] for a in state['accounts']], list(ACCOUNTS))
        last = state['snapshots'][1]
        self.assertEqual(set(last), {'date', 'recordedAt', 'positions', 'notes'})
        self.assertEqual(set(last['positions'][0]), {'account', 'class', 'market', 'symbol', 'name', 'quantity', 'valueJpy'})
        self.assertEqual(set(state['snapshots'][0]), {'date', 'positions'})
        self.assertTrue(json.dumps(state))

    def test_build_rejects_duplicate_dates_and_allows_no_snapshots(self):
        one = {'version': 1, 'date': '2026-10-04', 'positions': [position()], 'notes': []}
        with self.assertRaises(ValueError) as caught:
            build_state(ACCOUNTS, [one, dict(one)], NOW)
        self.assertIn('2026-10-04', str(caught.exception))
        empty = build_state(ACCOUNTS, [], NOW)
        self.assertEqual((empty['snapshots'], empty['latestDate']), ([], None))


class TemplateTest(unittest.TestCase):
    def test_previous_values_are_blanked_except_carry_forward_classes(self):
        previous, _ = validate_snapshot(read_fixture('snapshots/2026-10-04.json'), ACCOUNTS, '2026-10-04', TODAY)
        draft = template('2026-10-11', ACCOUNTS, previous)
        self.assertEqual((draft['version'], draft['date'], draft['source'], draft['notes']), (1, '2026-10-11', 'screenshot', []))
        self.assertEqual(len(draft['positions']), len(previous['positions']))
        by_key = {(p['account'], p['symbol']): p for p in draft['positions']}
        apple = by_key[('sbi-tokutei', 'AAPL')]
        self.assertIsNone(apple['valueJpy'])
        self.assertIsNone(apple['quantity'])
        self.assertIsNone(apple['nativeAmount'])
        self.assertEqual((apple['costJpy'], apple['currency'], apple['market']), (300000, 'USD', 'US'))
        cash = by_key[('mizuho', 'JPY')]
        self.assertIsNone(cash['valueJpy'])
        self.assertNotIn('quantity', cash)
        private = by_key[('private-equity', 'PRIVATE-A')]
        self.assertEqual(private['valueJpy'], 1000000)
        self.assertIs(private['carryForward'], True)
        self.assertEqual(CARRY_FORWARD_CLASSES, ('private',))
        with self.assertRaises(ValueError) as caught:
            validate_snapshot(draft, ACCOUNTS, '2026-10-11', date(2026, 10, 11))
        self.assertIn('未入力', str(caught.exception))

    def test_without_previous_one_row_per_account(self):
        draft = template('2026-10-04', ACCOUNTS, None)
        self.assertEqual([p['account'] for p in draft['positions']], list(ACCOUNTS))
        self.assertEqual([p['class'] for p in draft['positions']], [a['defaultClass'] for a in ACCOUNTS.values()])
        self.assertEqual(draft['positions'][0], {'account': 'mizuho', 'class': 'cash', 'symbol': 'JPY', 'name': 'みずほ銀行',
                                                 'quantity': None, 'valueJpy': None})
        self.assertIsNone(draft['positions'][5]['symbol'])
        with self.assertRaises(ValueError):
            template('2026-13-01', ACCOUNTS, None)


class DocumentTest(unittest.TestCase):
    def test_local_default_path_and_environment_overrides(self):
        with patch.dict('os.environ', {'ASSET_ASSETS_DIR': '', 'ASSET_ASSETS_LOCAL_PATH': ''}):
            document = asset_document(None)
            self.assertIsInstance(document, LocalDocument)
            self.assertEqual(document.path, ROOT / 'data/private/assets/state.json')
        with patch.dict('os.environ', {'ASSET_ASSETS_DIR': '/tmp/assets-x', 'ASSET_ASSETS_LOCAL_PATH': ''}):
            self.assertEqual(asset_document(None).path, Path('/tmp/assets-x/state.json'))
        with patch.dict('os.environ', {'ASSET_ASSETS_DIR': 'other', 'ASSET_ASSETS_LOCAL_PATH': 'foo/state.json'}):
            self.assertEqual(asset_document(None).path, ROOT / 'foo/state.json')
            self.assertEqual(assets.assets_dir(), ROOT / 'other')

    def test_gcs_document_uses_the_given_session(self):
        session = Mock()
        document = asset_document('bucket', writable=True, session=session)
        self.assertIsInstance(document, GCSDocument)
        self.assertIs(document.session, session)
        self.assertEqual((document.bucket, document.name), ('bucket', STATE_OBJECT))
        self.assertEqual(STATE_OBJECT, 'assets/state.json')

    def test_payload_shape(self):
        document = Mock()
        document.read.return_value = ({}, 0)
        self.assertEqual(asset_payload(document), {'state': None, 'status': {'status': 'not_configured', 'pushedAt': None}})
        state = build_state(ACCOUNTS, [], NOW)
        document.read.return_value = ({'state': state, 'pushedAt': '2026-10-04T01:00:00+00:00'}, 5)
        payload = asset_payload(document)
        self.assertEqual(set(payload), {'state', 'status'})
        self.assertEqual(payload['state'], state)
        self.assertEqual(payload['status'], {'status': 'ok', 'pushedAt': '2026-10-04T01:00:00+00:00'})


def response(status=200, generation=None, body=None):
    result = Mock()
    result.status_code = status
    result.headers = {'x-goog-generation': str(generation)} if generation is not None else {}
    result.json.return_value = body or {}
    result.raise_for_status.return_value = None
    return result


class PushTest(unittest.TestCase):
    def setUp(self):
        self.state = build_state(ACCOUNTS, [], NOW)
        self.session = Mock()
        self.document = GCSDocument('bucket', STATE_OBJECT, writable=True, session=self.session)

    def test_push_writes_with_generation_match(self):
        self.session.get.return_value = response(200, 7, {'state': {}})
        self.session.post.return_value = response(200)
        self.assertEqual(push(self.document, self.state, NOW), NOW.isoformat())
        call = self.session.post.call_args
        self.assertEqual(call.kwargs['params'], {'uploadType': 'media', 'name': 'assets/state.json', 'ifGenerationMatch': 7})
        self.assertIn('/b/bucket/o', call.args[0])
        body = json.loads(call.kwargs['data'])
        self.assertEqual(set(body), {'state', 'pushedAt'})
        self.assertEqual(body['state'], self.state)
        self.assertEqual(body['pushedAt'], NOW.isoformat())

    def test_missing_object_is_created_with_generation_zero(self):
        self.session.get.return_value = response(404)
        self.session.post.return_value = response(200)
        push(self.document, self.state, NOW)
        self.assertEqual(self.session.post.call_args.kwargs['params']['ifGenerationMatch'], 0)

    def test_conflict_rereads_and_retries_once(self):
        self.session.get.side_effect = [response(200, 7), response(200, 8)]
        self.session.post.side_effect = [response(412), response(200)]
        push(self.document, self.state, NOW)
        self.assertEqual(self.session.get.call_count, 2)
        self.assertEqual([c.kwargs['params']['ifGenerationMatch'] for c in self.session.post.call_args_list], [7, 8])

    def test_second_conflict_is_raised(self):
        self.session.get.side_effect = [response(200, 7), response(200, 8), response(200, 9)]
        self.session.post.return_value = response(412)
        with self.assertRaises(Conflict):
            push(self.document, self.state, NOW)
        self.assertEqual(self.session.post.call_count, 2)


class GcloudSessionTest(unittest.TestCase):
    def test_token_from_gcloud_becomes_a_bearer_header(self):
        session = Mock()
        session.headers = {}
        fake = types.SimpleNamespace(Session=Mock(return_value=session))
        with patch.dict(sys.modules, {'requests': fake}), \
                patch('subprocess.check_output', return_value='tok-123\n') as output:
            self.assertIs(gcloud_session('owner@example.com'), session)
            self.assertEqual(output.call_args.args[0],
                             ['gcloud', 'auth', 'print-access-token', '--account=owner@example.com'])
            self.assertEqual(session.headers, {'Authorization': 'Bearer tok-123'})
            gcloud_session(None)
            self.assertEqual(output.call_args.args[0], ['gcloud', 'auth', 'print-access-token'])
        with patch.dict(sys.modules, {'requests': fake}), patch('subprocess.check_output', return_value='\n'):
            with self.assertRaises(ValueError):
                gcloud_session('owner@example.com')


class FixtureTest(unittest.TestCase):
    def test_fixtures_validate_build_and_cover_mover_cases(self):
        accounts, snapshots, warnings = load_sources(FIXTURES, today=TODAY)
        self.assertEqual(warnings, [])
        self.assertEqual(set(accounts), ACCOUNT_IDS)
        self.assertEqual([s['date'] for s in snapshots], ['2026-09-20', '2026-09-27', '2026-10-04'])
        state = build_state(accounts, snapshots, NOW)
        self.assertEqual(state['latestDate'], '2026-10-04')
        for name in ['accounts.json', 'snapshots/2026-09-20.json', 'snapshots/2026-09-27.json', 'snapshots/2026-10-04.json']:
            self.assertEqual(read_fixture(name)['_note'], 'テスト用のダミー値')
        symbols = [{(p['account'], p['symbol']) for p in s['positions']} for s in state['snapshots']]
        self.assertIn(('sbi-nisa', '523A'), symbols[1])
        self.assertNotIn(('sbi-nisa', '523A'), symbols[2])
        self.assertNotIn(('sbi-tokutei', '4062'), symbols[1])
        self.assertIn(('sbi-tokutei', '4062'), symbols[2])
        last = {(p['account'], p['symbol']): p for p in state['snapshots'][2]['positions']}
        self.assertIs(last[('private-equity', 'PRIVATE-A')]['carryForward'], True)
        self.assertEqual(last[('sbi-tokutei', 'AAPL')]['currency'], 'USD')
        self.assertEqual(last[('sbi-nisa', 'EMAXIS-SLIM-ALL')]['class'], 'fund')
        self.assertEqual(last[('sbi-tokutei', 'JPY')]['class'], 'cash')
        classes = {p['class'] for s in state['snapshots'] for p in s['positions']}
        self.assertEqual(classes, {'stock', 'fund', 'crypto', 'cash', 'private'})
        self.assertEqual(set(CLASS_LABELS), set(CLASSES))
        self.assertEqual(sum(p['valueJpy'] for p in state['snapshots'][2]['positions']), 8888824)


class CLITest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name) / 'assets'
        shutil.copytree(FIXTURES, self.directory)
        patcher = patch.dict('os.environ', {'ASSET_ASSETS_DIR': str(self.directory), 'ASSET_ASSETS_LOCAL_PATH': '',
                                            'ASSET_ASSETS_MIRROR': '', 'ASSET_STATE_BUCKET': ''})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.temp.cleanup)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = assets.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def break_snapshot(self):
        path = self.directory / 'snapshots/2026-10-04.json'
        data = json.loads(path.read_text())
        data['positions'][0]['valueJpy'] = None
        path.write_text(json.dumps(data))

    def test_validate_reports_summary_or_exit_code_one(self):
        code, out, err = self.run_cli('validate')
        self.assertEqual((code, err), (0, ''))
        self.assertEqual(json.loads(out), {'assetsValidate': 'ok', 'snapshots': 3, 'latestDate': '2026-10-04', 'warnings': 0})
        self.break_snapshot()
        code, out, err = self.run_cli('validate')
        self.assertEqual((code, out), (1, ''))
        self.assertIn('snapshots/2026-10-04.json: positions[0].valueJpy', err)
        shutil.rmtree(self.directory / 'snapshots')
        self.assertEqual(json.loads(self.run_cli('validate')[1])['snapshots'], 0)
        (self.directory / 'accounts.json').unlink()
        code, _, err = self.run_cli('validate')
        self.assertEqual(code, 1)
        self.assertIn('accounts.json', err)

    def test_weekday_warning_goes_to_stderr_without_failing(self):
        source = self.directory / 'snapshots/2026-10-04.json'
        data = json.loads(source.read_text())
        data['date'] = '2026-10-01'
        (self.directory / 'snapshots/2026-10-01.json').write_text(json.dumps(data))
        source.unlink()
        code, out, err = self.run_cli('validate')
        self.assertEqual(code, 0)
        self.assertIn('土日ではありません', err)
        self.assertEqual(json.loads(out)['warnings'], 1)

    def test_build_writes_local_state_and_mirror(self):
        mirror = Path(self.temp.name) / 'mirror'
        with patch.dict('os.environ', {'ASSET_ASSETS_MIRROR': str(mirror)}):
            code, out, err = self.run_cli('build')
        self.assertEqual((code, err), (0, ''))
        result = json.loads(out)
        self.assertEqual((result['assetsBuild'], result['latestDate'], result['snapshots'], result['mirrored']),
                         ('ok', '2026-10-04', 3, 5))
        self.assertEqual(result['path'], str(self.directory / 'state.json'))
        payload = asset_payload(asset_document(None))
        self.assertEqual(payload['status'], {'status': 'ok', 'pushedAt': None})
        self.assertEqual(payload['state']['latestDate'], '2026-10-04')
        self.assertEqual(len(payload['state']['snapshots']), 3)
        self.assertEqual(sorted(p.relative_to(mirror).as_posix() for p in mirror.rglob('*.json')),
                         ['accounts.json', 'snapshots/2026-09-20.json', 'snapshots/2026-09-27.json',
                          'snapshots/2026-10-04.json', 'state.json'])
        self.assertEqual(self.run_cli('build')[0], 0)  # a second build replaces the previous revision
        elsewhere = Path(self.temp.name) / 'elsewhere/state.json'
        other_mirror = Path(self.temp.name) / 'mirror2'
        with patch.dict('os.environ', {'ASSET_ASSETS_LOCAL_PATH': str(elsewhere), 'ASSET_ASSETS_MIRROR': str(other_mirror)}):
            code, out, _ = self.run_cli('build')
        self.assertEqual((code, json.loads(out)['mirrored'], json.loads(out)['path']), (0, 5, str(elsewhere)))
        self.assertTrue(elsewhere.is_file())
        self.assertEqual(json.loads((other_mirror / 'state.json').read_text())['state']['latestDate'], '2026-10-04')
        self.break_snapshot()
        code, _, err = self.run_cli('build')
        self.assertEqual(code, 1)
        self.assertIn('valueJpy', err)
        self.assertEqual(asset_payload(asset_document(None))['state']['latestDate'], '2026-10-04')

    def test_template_creates_a_draft_and_refuses_to_overwrite(self):
        code, out, err = self.run_cli('template', '--date', '2026-10-11')
        self.assertEqual((code, err), (0, ''))
        target = self.directory / 'snapshots/2026-10-11.json'
        self.assertEqual(out.splitlines()[0], str(target))
        self.assertEqual(json.loads(out.splitlines()[1]), {'assetsTemplate': 'ok', 'date': '2026-10-11',
                                                           'basedOn': '2026-10-04', 'positions': 14})
        draft = json.loads(target.read_text())
        self.assertEqual(draft['date'], '2026-10-11')
        self.assertIsNone(draft['positions'][0]['valueJpy'])
        self.assertTrue(draft['positions'][-1]['carryForward'])
        code, _, err = self.run_cli('template', '--date', '2026-10-11')
        self.assertEqual(code, 1)
        self.assertIn('--force', err)
        self.assertEqual(self.run_cli('template', '--date', '2026-10-11', '--force')[0], 0)
        self.assertEqual(self.run_cli('template', '--date', '2026-10-32')[0], 1)
        # The draft itself does not validate until the nulls are filled in.
        self.assertEqual(self.run_cli('validate')[0], 1)
        shutil.rmtree(self.directory / 'snapshots')
        code, out, _ = self.run_cli('template', '--date', '2026-10-04')
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.splitlines()[1])['positions'], 9)

    def test_push_resolves_bucket_and_account_then_writes_once(self):
        session = Mock()
        instance = Mock()
        instance.read.return_value = ({}, 3)
        with patch.object(assets, 'gcloud_session', return_value=session) as token, \
                patch.object(assets, 'GCSDocument', return_value=instance) as gcs, \
                patch('infra.common.load_config', side_effect=AssertionError('config must not be read')):
            code, out, err = self.run_cli('push', '--bucket', 'explicit', '--account', 'me@example.com')
            self.assertEqual((code, err), (0, ''))
            gcs.assert_called_once_with('explicit', STATE_OBJECT, writable=True, session=session)
            token.assert_called_once_with('me@example.com')
            value, generation = instance.write.call_args.args
            self.assertEqual(generation, 3)
            self.assertEqual(set(value), {'state', 'pushedAt'})
            self.assertEqual(value['state']['latestDate'], '2026-10-04')
            result = json.loads(out)
            self.assertEqual((result['assetsPush'], result['bucket'], result['object'], result['latestDate']),
                             ('ok', 'explicit', STATE_OBJECT, '2026-10-04'))
            with patch.dict('os.environ', {'ASSET_STATE_BUCKET': 'from-env'}):
                self.assertEqual(self.run_cli('push', '--account', 'me@example.com')[0], 0)
            self.assertEqual(gcs.call_args.args[0], 'from-env')
        with patch.object(assets, 'gcloud_session', return_value=session) as token, \
                patch.object(assets, 'GCSDocument', return_value=instance) as gcs, \
                patch('infra.common.load_config', return_value=CONFIG):
            self.assertEqual(self.run_cli('push')[0], 0)
            self.assertEqual(gcs.call_args.args[0], 'asset-hub-test-asset-state')
            token.assert_called_once_with('owner@example.com')
            with patch.dict('os.environ', {'ASSET_STATE_BUCKET': 'from-env'}):
                self.run_cli('push')
            self.assertEqual(gcs.call_args.args[0], 'from-env')

    def test_push_stops_before_any_network_call_when_sources_are_invalid(self):
        self.break_snapshot()
        with patch.object(assets, 'gcloud_session') as token, patch.object(assets, 'GCSDocument') as gcs:
            code, out, err = self.run_cli('push', '--bucket', 'b', '--account', 'a')
        self.assertEqual((code, out), (1, ''))
        self.assertIn('valueJpy', err)
        token.assert_not_called()
        gcs.assert_not_called()

    def test_push_conflict_twice_exits_one(self):
        instance = Mock()
        instance.read.return_value = ({}, 3)
        instance.write.side_effect = Conflict()
        with patch.object(assets, 'gcloud_session', return_value=Mock()), patch.object(assets, 'GCSDocument', return_value=instance):
            code, out, err = self.run_cli('push', '--bucket', 'b', '--account', 'a')
        self.assertEqual((code, out), (1, ''))
        self.assertIn('再実行', err)
        self.assertEqual(instance.write.call_count, 2)


if __name__ == '__main__':
    unittest.main()
