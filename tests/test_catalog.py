"""README rows name their own research target, not linked related themes."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/build_catalog.py'
spec = importlib.util.spec_from_file_location('build_catalog', SCRIPT)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class CatalogTitleTests(unittest.TestCase):
    def test_related_archive_does_not_override_its_own_row_title(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'README.md').write_text(
                '| Current review | 2026-11-06 | [report](research/themes/current/2026-11-06/report.md) | '
                '[related](research/themes/ranking/2026-10-18/report.md) |\n'
                '| Future ranking | 2026-10-18 | [report](research/themes/ranking/2026-10-18/report.md) | '
                '[older](research/themes/ranking/2026-10-01/README.md) |\n', encoding='utf-8')
            with patch.object(catalog, 'ROOT', root):
                titles = catalog.root_titles()
        self.assertEqual(titles['research/themes/current'], 'Current review')
        self.assertEqual(titles['research/themes/ranking'], 'Future ranking')
        self.assertEqual(titles['research/themes/ranking/2026-10-18'], 'Future ranking')
        self.assertEqual(titles['research/themes/ranking/2026-10-01'], 'Future ranking')


if __name__ == '__main__':
    unittest.main()
