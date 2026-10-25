"""Fictional data exercises availability, capital updates and local path safety."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import contextlib
import io
import os
import unittest

from backend.mbo import core


def fact(metric, value='100', **updates):
    row = {
        'metric': metric, 'value': value, 'unit': 'JPY', 'currency': 'JPY',
        'fact_kind': 'actual', 'period_start': '2025-04-01', 'period_end': '2026-03-31',
        'consolidation': 'consolidated', 'public_at': '2026-05-15',
        'observed_at': '2026-05-15T11:00:00+09:00',
        'ready_at': '2026-05-15T12:00:00+09:00', 'quality_status': 'verified',
        'share_basis': 'post-split-2025',
    }
    if metric == 'shares_diluted':
        row['unit'] = 'shares'
    elif metric == 'owner_ratio':
        row['unit'] = 'ratio'
    row.update(updates)
    return row


class MboTimeTest(unittest.TestCase):
    def test_build_today_uses_jst_even_when_host_date_is_previous_day(self):
        class HostDate(date):
            @classmethod
            def today(cls):
                return cls(2026, 10, 24)
        with TemporaryDirectory() as temporary, \
                patch.object(core, 'date', HostDate), \
                patch.object(core, 'now', return_value='2026-10-24T16:00:00+00:00'):
            with self.assertRaises(FileNotFoundError):
                core.build('2026-10-25', Path(temporary) / 'empty')
            with self.assertRaisesRegex(ValueError, '今日以前'):
                core.build('2026-10-26', Path(temporary) / 'future')

    def test_cli_default_as_of_uses_jst_even_when_host_date_is_previous_day(self):
        from backend.mbo import __main__ as cli
        class HostDate(date):
            @classmethod
            def today(cls):
                return cls(2026, 10, 24)
        with patch.object(cli, 'date', HostDate), \
                patch.object(core, 'now', return_value='2026-10-24T16:00:00+00:00'), \
                patch.object(core, 'build', return_value={}) as build, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['build']), 0)
        self.assertEqual(build.call_args.args[0], '2026-10-25')

    def test_latest_compares_instants_not_iso_lexicography(self):
        old = fact('ebit', '100', public_at='2026-10-18T09:00:00+09:00', observed_at='2026-10-18T10:00:00+09:00')
        new = fact('ebit', '200', public_at='2026-10-18T01:00:00+00:00', observed_at='2026-10-18T10:01:00+09:00')
        self.assertEqual(core.latest([new, old], lambda r: r['metric'])[0]['value'], '200')

    def test_utc_day_boundary_cannot_leak_into_previous_jst_day(self):
        row = {'public_at': '2026-10-18T23:00:00+00:00',
               'observed_at': '2026-10-18T23:00:00+00:00',
               'ready_at': '2026-10-18T23:00:00+00:00'}
        self.assertFalse(core.visible(row, '2026-10-18'))
        self.assertTrue(core.visible(row, '2026-10-19'))
        self.assertEqual(core.day(row['public_at']), date(2026, 10, 19))

    def test_all_availability_fields_gate_a_record(self):
        for field in ('public_at', 'observed_at', 'ready_at'):
            row = dict(public_at='2026-10-01', observed_at='2026-10-01', ready_at='2026-10-01')
            row[field] = '2026-10-20T00:00:00+09:00'
            self.assertFalse(core.visible(row, '2026-10-18'), field)
        self.assertFalse(core.visible({'as_of': '2026-10-19'}, '2026-10-18'))
        self.assertFalse(core.visible({'published_at': '2026-10-19'}, '2026-10-18'))

    def test_date_only_information_is_available_at_day_end(self):
        self.assertFalse(core.visible({'public_at': '2026-10-18'}, '2026-10-18T12:00:00+09:00'))
        self.assertTrue(core.visible({'public_at': '2026-10-18'}, '2026-10-18'))
        for bad in (None, 'bad', '2026-02-30', '2026-10-18T12:00:00'):
            with self.assertRaises(ValueError):
                core.iso(bad, 'date')

    def test_later_issuance_and_owner_update_use_the_latest_point_in_time(self):
        rows = [fact('ebit'), fact('capex'), fact('shares_diluted', '100'), fact('owner_ratio', '.2')]
        rows.extend([
            fact('shares_diluted', '200', period_end='2026-09-30', public_at='2026-10-01', consolidation='standalone'),
            fact('owner_ratio', '.1', period_end='2026-09-30', public_at='2026-10-01', consolidation='standalone'),
        ])
        result, _ = core._fact_set(rows, '2026-10-18')
        self.assertEqual(result['shares_diluted']['value'], '200')
        self.assertEqual(result['owner_ratio']['value'], '.1')
        self.assertEqual(result['ebit']['period_end'], '2026-03-31')
        self.assertEqual(result['capex']['quality_status'], 'verified')

    def test_future_observed_update_does_not_hide_earlier_valid_shares(self):
        rows = [fact('ebit'), fact('shares_diluted', '100'),
                fact('shares_diluted', '200', period_end='2026-09-30', public_at='2026-10-01', observed_at='2026-10-20')]
        result, _ = core._fact_set(rows, '2026-10-18')
        self.assertEqual(result['shares_diluted']['value'], '100')

    def test_same_instant_share_conflict_is_not_silently_selected(self):
        rows = [fact('ebit'),
                fact('shares_diluted', '100', public_at='2026-10-18T09:00:00+09:00'),
                fact('shares_diluted', '200', public_at='2026-10-18T00:00:00+00:00')]
        result, _ = core._fact_set(rows, '2026-10-18')
        self.assertEqual(result['shares_diluted']['quality_status'], 'conflicting')
        rows[-1]['value'] = '100.0'
        result, _ = core._fact_set(rows, '2026-10-18')
        self.assertEqual(result['shares_diluted']['quality_status'], 'verified')
        rows[-1]['share_basis'] = 'different-basis'
        result, _ = core._fact_set(rows, '2026-10-18')
        self.assertEqual(result['shares_diluted']['quality_status'], 'conflicting')

    def test_financial_flows_still_require_one_period(self):
        rows = [fact('ebit'), fact('capex', period_start='2025-03-15')]
        result, _ = core._fact_set(rows, '2026-10-18')
        self.assertEqual(result['ebit']['quality_status'], 'pending')
        self.assertEqual(result['capex']['quality_status'], 'pending')


class MboLocalPathTest(unittest.TestCase):
    def test_temp_directory_system_alias_works_but_user_symlink_does_not(self):
        with TemporaryDirectory() as directory:
            canonical = core.reject_symlinks(directory)
            self.assertEqual(canonical, Path(directory).resolve())
            original = Path(directory) / 'original.txt'
            original.write_text('fictional')
            link = Path(directory) / 'user-link.txt'
            link.symlink_to(original)
            with self.assertRaises(ValueError):
                core.read_input(link)
            self.assertEqual(core.read_input(original, Path(directory)), b'fictional')

    def test_only_known_system_alias_targets_are_allowed(self):
        for alias, target in (('/tmp', '/private/tmp'), ('/var', '/private/var')):
            if os.path.islink(alias):
                actual = os.path.normpath(os.path.join('/', os.readlink(alias)))
                if actual == target:
                    self.assertEqual(core.reject_symlinks(alias), Path(target))

    def test_nonexistent_input_raises_file_not_found(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                core.read_input(Path(directory) / 'absent.csv')


if __name__ == '__main__':
    unittest.main()
