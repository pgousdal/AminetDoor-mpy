#!/usr/bin/env python3
"""Deterministic, dependency-free release-readiness checks."""

import argparse
import compileall
import importlib.machinery
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import types


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_VERSION = "1.0.1"
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


def load_door(source_path):
    """Load the door with a minimal Mystic stub for runtime validation."""
    output = []
    stub = types.ModuleType("mystic_bbs")
    stub.write = lambda value="": output.append(value)
    stub.writeln = lambda value="": output.append(value)
    stub.getuser = lambda number: {"number": 1, "name": "release-check"}
    stub.getkey = lambda *args, **kwargs: ("Q", False)
    stub.onekey = lambda *args, **kwargs: "Q"
    previous = sys.modules.get("mystic_bbs")
    sys.modules["mystic_bbs"] = stub
    try:
        loader = importlib.machinery.SourceFileLoader(
            "aminetdoor_release_check", str(source_path))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        door = importlib.util.module_from_spec(spec)
        loader.exec_module(door)
    finally:
        if previous is None:
            del sys.modules["mystic_bbs"]
        else:
            sys.modules["mystic_bbs"] = previous
    return door, output


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
        try:
            door, output = load_door(source_path)
            door.heading("Main menu")
            rendered = "\n".join(output)
            expected_banner = "AminetDoor |07v%s" % EXPECTED_VERSION
            if expected_banner not in rendered:
                errors.append("main-menu header does not render v%s" %
                              EXPECTED_VERSION)
            output[:] = []
            door.about()
            if expected_banner not in "\n".join(output):
                errors.append("About header does not render v%s" %
                              EXPECTED_VERSION)
            if door.USER_AGENT != (
                    "AminetDoor/%s (Mystic BBS door; "
                    "https://github.com/pgousdal/AminetDoor-mpy)" %
                    EXPECTED_VERSION):
                errors.append("runtime User-Agent version is inconsistent")
        except Exception as exc:
            errors.append("could not validate runtime version surfaces: %s" % exc)

    for relative_path in ("README.md", "CHANGELOG.md"):
        path = root / relative_path
        if path.is_file() and EXPECTED_VERSION not in path.read_text(encoding="utf-8"):
            errors.append("%s does not mention %s" %
                          (relative_path, EXPECTED_VERSION))

    diagnostic = root / "scripts/check_aminet.py"
    if diagnostic.is_file():
        text = diagnostic.read_text(encoding="utf-8")
        if 'USER_AGENT = "AminetDoor/%s' not in text or "% VERSION" not in text:
            errors.append("diagnostic User-Agent does not derive from VERSION")

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
