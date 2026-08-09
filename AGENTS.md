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

## Mystic Door Navigation Standard

- Up/Down: move selection
- Enter: activate/open
- Esc: back / cancel / exit the current screen
- Q: same semantic action as Esc
- B: one hierarchical level back, where applicable
- R: return to root, where applicable
- S: search/new search, where applicable

Esc must never leave the caller trapped in an input prompt, pager, selector,
About screen, error screen, pause screen, or other interactive state.

Where both Q and Esc are available, they must perform the same semantic action
unless a screen has a clearly documented exceptional reason.

Mystic `getkey()` returns Escape as `"\\x1b"` (or integer 27 in compatible
bindings); this is the live-tested representation used by the door. Mystic
extended arrows remain `("H", True)` for Up and `("P", True)` for Down. Do
not replace these mappings with generic ANSI parsing.

## Validation

Run:

```bash
python3 tests/test_helpers.py
```

The test harness injects a tiny `mystic_bbs` stub and loads `aminetdoor.mpy`
without entering the interactive main loop. Network calls are mocked; there
are no live-network tests.
