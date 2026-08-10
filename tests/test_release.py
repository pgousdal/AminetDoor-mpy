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
        self.assertIn('VERSION = "1.0.0"', source)
        self.assertEqual(release_check.EXPECTED_VERSION, "1.0.0")
        self.assertEqual(release_check.check_metadata(ROOT), [])

    def test_release_check_reports_missing_required_file(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = release_check.check_metadata(pathlib.Path(directory))
        self.assertIn("missing required file: aminetdoor.mpy", errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
