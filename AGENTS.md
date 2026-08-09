# AGENTS.md

## Project

AminetDoor is a small Mystic BBS Python 3 door for browsing Aminet.

## Runtime constraints

- Keep `aminetdoor.mpy` dependency-free outside Mystic and Python stdlib.
- Do not require `requests` or any third-party HTML-parsing library. RSS/XML
  uses `xml.etree.ElementTree`; M1 Browse/Search HTML uses the stdlib
  `html.parser.HTMLParser` only.
- Preserve a usable 80x25 interface.
- Network calls must have finite timeouts.
- Avoid raw exception tracebacks in the caller-facing BBS session.
- Keep API/feed behavior testable without live-network tests.
- Do not perform uploads, edits, or any write operation against Aminet.
- Treat all remote HTML as untrusted input and bound response reads.
- Keep Browse/Search read-only; do not add downloads, uploads, credentials,
  cookies, caching, or mirror operations.

## Validation

Run:

```bash
python3 tests/test_helpers.py
```

The test harness injects a tiny `mystic_bbs` stub and loads `aminetdoor.mpy`
without entering the interactive main loop. Network calls are mocked; there
are no live-network tests.
