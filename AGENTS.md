# AGENTS.md

## Project

AminetDoor is a small Mystic BBS Python 3 door for browsing Aminet.

## M0 constraints

- Keep `aminetdoor.mpy` dependency-free outside Mystic and Python stdlib.
- Do not require `requests` or any HTML-parsing library; use RSS/XML
  (`xml.etree.ElementTree`, stdlib) rather than scraping HTML pages.
- Preserve a usable 80x25 interface.
- Network calls must have finite timeouts.
- Avoid raw exception tracebacks in the caller-facing BBS session.
- Keep API/feed behavior testable without live-network tests.
- Do not perform uploads, edits, or any write operation against Aminet.

## Validation

Run:

```bash
python3 tests/test_helpers.py
```

The test harness injects a tiny `mystic_bbs` stub and loads `aminetdoor.mpy`
without entering the interactive main loop. Network calls are mocked; there
are no live-network tests.
