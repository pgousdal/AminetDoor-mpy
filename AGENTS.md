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
  cookies, search/Browse caching, or mirror operations. The configured local
  README-text cache is the exception for this milestone.
- Cache only bounded README text as JSON; never cache archives, HTML, RSS, or
  executable content.
- Favorites are per-user local JSON data; storage failure must never disable
  core Browse, Search, Recent, or README functionality.
- Use Mystic's documented `bbs.getuser(0)` record for per-user identity; do not
  guess user fields or write arbitrary data into Mystic's native user record.
- Architecture filtering is SysOp configuration in `aminetdoor.mpy`; it must
  use verified Aminet metadata or form fields, not filename inference.
- The inline Aminet category catalog is navigation-only; package listings must
  remain live and the catalog should be updated deliberately against Aminet's
  public Browse tree.
- Package of the Day must use the existing Recent candidate pool and stable
  date/path hashing; do not infer architecture or add another endpoint.

## Mystic Python Runtime Compatibility

Mystic `.mpy` execution must not assume normal script globals such as
`__file__` are available.

Runtime filesystem locations must use explicit configuration or Mystic-
confirmed runtime facilities. Optional features such as caches must fail open:
cache/filesystem failure must never prevent core door functionality.

## Mystic Door Navigation Standard

- ESC     Back / Cancel / Menu / Exit the current context
- Q       Alias for ESC where appropriate

- Up/Down Move selection
- Enter   Select / Open

- B       Back one hierarchy level, where applicable
- R       Return to root, where applicable
- S       Search / New search, where applicable
- J       Jump directly to a validated category path, where applicable

ESC is the primary navigation convention.

AminetDoor should behave like a native Mystic interface wherever practical.

Q is retained as a convenient BBS-door compatibility alias where ESC performs
Back/Cancel/Exit.

A caller must never become trapped in a selector, text-input field, pager,
About screen, error screen, or other interactive state because ESC is ignored.

Where both Q and ESC are available, they must perform the same semantic action
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
