import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'archive_snapshots.py'
spec = importlib.util.spec_from_file_location('archive_snapshots', SCRIPT)
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


def write(base, files):
    for name, text in files.items():
        path = base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')


class ArchiveSnapshotTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write(self.root, {
            'research/companies/1111-a/2026-09-05/report.md': 'old',
            'research/companies/1111-a/2026-09-05/working/raw.json': 'local only',
            'research/companies/1111-a/2026-09-05/.DS_Store': 'x',
            'research/companies/1111-a/2026-10-03/report.md': 'new',
            'research/themes/solo/2026-09-05/README.md': 'only version',
        })
        self.patch = patch.multiple(archive, ROOT=self.root, RESEARCH=self.root / 'research', MANIFEST=self.root / 'research/archive-manifest.json')
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_only_older_versions_are_archives_and_local_files_are_skipped(self):
        self.assertEqual(archive.archived_folders(), ['research/companies/1111-a/2026-09-05'])
        self.assertEqual(archive.snapshot_files('research/companies/1111-a/2026-09-05'), ['report.md'])

    def test_unrecorded_changed_missing_and_added_files_are_reported(self):
        self.assertEqual(archive.problems(archive.load()), [('research/companies/1111-a/2026-09-05', None, 'archive is not recorded; run --write')])
        archive.main(['--write'])
        manifest = archive.load()
        self.assertEqual(archive.problems(manifest), [])
        folder = self.root / 'research/companies/1111-a/2026-09-05'
        (folder / 'report.md').write_text('edited', encoding='utf-8')
        (folder / 'extra.md').write_text('new file', encoding='utf-8')
        self.assertEqual(archive.problems(manifest), [
            ('research/companies/1111-a/2026-09-05', 'report.md', 'changed'),
            ('research/companies/1111-a/2026-09-05', 'extra.md', 'added after the archive was recorded'),
        ])
        (folder / 'report.md').unlink()
        self.assertIn(('research/companies/1111-a/2026-09-05', 'report.md', 'missing'), archive.problems(manifest))
        with self.assertRaises(SystemExit):
            archive.main(['--check'])

    def test_write_keeps_recorded_hashes(self):
        archive.main(['--write'])
        before = archive.load()
        (self.root / 'research/companies/1111-a/2026-09-05/report.md').write_text('edited', encoding='utf-8')
        with self.assertRaises(SystemExit):
            archive.main(['--write'])
        self.assertEqual(archive.load(), before)

    def test_restore_puts_committed_content_back(self):
        config = ['-c', 'user.name=t', '-c', 'user.email=t@example.com', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null']
        git = lambda *args: subprocess.run(['git', *config, *args], cwd=self.root, check=True, capture_output=True)
        git('init', '-q')
        git('add', '-A')
        git('commit', '-qm', 'snapshot')
        archive.main(['--write'])
        folder = self.root / 'research/companies/1111-a/2026-09-05'
        (folder / 'report.md').write_text('edited', encoding='utf-8')
        archive.main(['--restore'])
        self.assertEqual((folder / 'report.md').read_text(encoding='utf-8'), 'old')
        # A deleted archive folder comes back whole and restore reports success.
        shutil.rmtree(folder)
        archive.main(['--restore'])
        self.assertEqual((folder / 'report.md').read_text(encoding='utf-8'), 'old')
        self.assertEqual(archive.problems(archive.load()), [])

    def test_a_folder_with_only_local_files_does_not_archive_the_current_version(self):
        write(self.root, {'research/companies/1111-a/2026-11-01/working/raw.json': 'in progress'})
        self.assertEqual(archive.archived_folders(), ['research/companies/1111-a/2026-09-05'])


class RepositoryArchivesTest(unittest.TestCase):
    def test_repository_archives_match_the_manifest(self):
        self.assertEqual(archive.problems(archive.load()), [])


if __name__ == '__main__':
    unittest.main()
