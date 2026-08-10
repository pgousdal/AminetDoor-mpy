#!/usr/bin/env python3
"""Deterministic, dependency-free release-readiness checks."""

import argparse
import compileall
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_VERSION = "1.0.0"
REQUIRED_FILES = (
    "aminetdoor.mpy",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "SECURITY.md",
    "AGENTS.md",
    "docs/INSTALL.md",
    "docs/LICENSING.md",
    "docs/RELEASE.md",
    "tests/test_helpers.py",
)


def check_metadata(root=ROOT):
    """Return human-readable metadata errors without modifying the tree."""
    errors = []
    for relative_path in REQUIRED_FILES:
        if not (root / relative_path).is_file():
            errors.append("missing required file: %s" % relative_path)

    source_path = root / "aminetdoor.mpy"
    if source_path.is_file():
        source = source_path.read_text(encoding="utf-8")
        match = re.search(r'^VERSION = "([^"]+)"$', source, re.MULTILINE)
        if not match:
            errors.append("aminetdoor.mpy has no canonical VERSION assignment")
        elif match.group(1) != EXPECTED_VERSION:
            errors.append("runtime version is %s, expected %s" %
                          (match.group(1), EXPECTED_VERSION))

    for relative_path in ("README.md", "CHANGELOG.md"):
        path = root / relative_path
        if path.is_file() and EXPECTED_VERSION not in path.read_text(encoding="utf-8"):
            errors.append("%s does not mention %s" %
                          (relative_path, EXPECTED_VERSION))

    diagnostic = root / "scripts/check_aminet.py"
    if diagnostic.is_file():
        text = diagnostic.read_text(encoding="utf-8")
        if "AminetDoor/%s" % EXPECTED_VERSION not in text:
            errors.append("diagnostic User-Agent version is inconsistent")

    for relative_path in ("README.md", "docs/INSTALL.md", "docs/M1.md"):
        path = root / relative_path
        if path.is_file() and "Mystic validation: pending" in path.read_text(
                encoding="utf-8"):
            errors.append("%s still says Mystic validation is pending" % relative_path)
    return errors


def run_command(command):
    print("+ %s" % " ".join(command))
    return subprocess.run(command, cwd=str(ROOT)).returncode == 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-only", action="store_true",
                        help="skip tests and compilation")
    args = parser.parse_args(argv)

    errors = check_metadata()
    if errors:
        for error in errors:
            print("ERROR: %s" % error, file=sys.stderr)
        return 1
    print("metadata: OK (v%s)" % EXPECTED_VERSION)

    if args.metadata_only:
        return 0
    tests_ok = run_command([
        sys.executable, "-m", "unittest", "discover", "-s", "tests",
        "-p", "test_*.py", "-v",
    ])
    compile_ok = compileall.compile_file(
        str(ROOT / "aminetdoor.mpy"), quiet=1, force=True)
    for directory in (ROOT / "scripts", ROOT / "tests"):
        compile_ok = compileall.compile_dir(
            str(directory), quiet=1, force=True) and compile_ok
    print("compileall: %s" % ("OK" if compile_ok else "FAILED"))
    return 0 if tests_ok and compile_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
