#!/usr/bin/env python3
"""Focused tests for release metadata and validation logic."""

import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "release_check", ROOT / "scripts" / "release_check.py")
release_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_check)


class ReleaseMetadataTests(unittest.TestCase):
    def test_runtime_and_release_versions_are_canonical(self):
        source = (ROOT / "aminetdoor.mpy").read_text(encoding="utf-8")
        self.assertIn('VERSION = "1.0.1"', source)
        self.assertEqual(release_check.EXPECTED_VERSION, "1.0.1")
        self.assertEqual(release_check.check_metadata(ROOT), [])

    def test_release_check_reports_missing_required_file(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = release_check.check_metadata(pathlib.Path(directory))
        self.assertIn("missing required file: aminetdoor.mpy", errors)

    def test_release_check_rejects_stale_rendered_header(self):
        source = (ROOT / "aminetdoor.mpy").read_text(encoding="utf-8")
        source = source.replace(
            'return "|11 AminetDoor |07v%s  |08-  Aminet from your BBS" % VERSION',
            'return "|11 AminetDoor |07v0.1.0  |08-  Aminet from your BBS"')
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            for relative_path in release_check.REQUIRED_FILES:
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("1.0.1", encoding="utf-8")
            (root / "aminetdoor.mpy").write_text(source, encoding="utf-8")
            errors = release_check.check_metadata(root)
        self.assertIn("main-menu header does not render v1.0.1", errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
