# AminetDoor

**AminetDoor M0.2 / v0.1.0** is a small Aminet reader written as a Mystic BBS
Python 3 (`.mpy`) script.

## Features

- Recent Aminet uploads, fetched from Aminet's RSS feed
- Browse Aminet's category hierarchy and package listings
- Search Aminet by package name or keyword
- Lightbar selection from the recent-uploads list
- Numbered selection compatibility mode
- Paged, terminal-friendly README reader (76-column wrapping, 16-line pages)
- Next / previous page navigation
- Graceful HTTP/feed/decoding error messages
- 10-second network timeout
- No API key
- No third-party Python packages

## Requirements

- Mystic BBS with embedded Python 3 configured
- Internet access to `https://aminet.net`
- Python standard library with HTTPS support

Mystic's Python module is imported as:

```python
import mystic_bbs as bbs
```

## Quick install

Copy:

```text
aminetdoor.mpy
```

to your Mystic theme's script directory, or the default script directory.

Create a Mystic menu entry:

```text
Command: GZ
Data:    aminetdoor
```

`GZ` executes a Python 3 Mystic script. Mystic will add `.mpy` when the
extension is omitted.

See `docs/INSTALL.md` for more detail.

## Controls

AminetDoor follows Mystic-native navigation conventions: arrow keys move, Enter
opens, and ESC returns or exits. Q is retained as an ESC-compatible alias.

Main menu:

```text
R  Recent uploads
A  About
Q  Return to BBS
```

Main menu also provides:

```text
B  Browse Aminet
S  Search Aminet
```

Browse follows Aminet's public category tree. Within Browse, `B` goes back one
level and `R` returns to the root. Search uses Aminet's public simple search
interface with a maximum query length of 60 characters. Both modes open the
same README reader as Recent.

Recent uploads (default lightbar selector):

```text
Up / Down  Move selection
Enter      Read selected package
ESC / Q    Return to the main menu
```

ESC acts as Back/Cancel throughout AminetDoor. It exits the main menu,
selectors, Search input, the README reader, About, and error/pause screens.

Set `RESULT_SELECTOR = "numbered"` near the top of `aminetdoor.mpy` to use
multi-digit numbered input instead. Invalid selector values safely fall back
to numbered mode. Lightbar Up/Down uses Mystic-native extended key handling;
the baseline layout remains 80x25.

README reader:

```text
N  Next page
P  Previous page
ESC / Q  Return to the package list
```

## Aminet endpoints

M0 uses Aminet's public RSS feed at:

```text
https://aminet.net/feed
```

and fetches the matching plain-text `.readme` file for a selected package
directly from `https://aminet.net/<path>.readme`. No scraping of Aminet's
HTML pages is performed in M0; RSS/XML is used because it is far more stable
to parse than HTML that can change layout at any time.

M1 Browse reads `GET https://aminet.net/tree` with the `path` query parameter
for category levels, then reads `GET https://aminet.net/<category-path>` for
leaf package listings. M1 Search reads `GET https://aminet.net/search` with
the `query` parameter and uses `page` only for later public result pages.
Responses are parsed with Python's standard-library `html.parser` and are
bounded before parsing.

## Scope

M1 intentionally stays read-only. It does not include architecture filtering,
local README caching, a "package of the day" random spotlight, screenshots,
downloads, uploads, or account functionality. See `docs/M1.md`.

Automated/offline validation: complete. Live Mystic validation: pending.

## Licensing

AminetDoor source code: MIT License.

Package descriptions and README text retrieved from Aminet remain the
property of their original authors and are not relicensed by AminetDoor's
MIT license. See `docs/LICENSING.md`.

## Project layout

```text
AminetDoor-mpy/
├── aminetdoor.mpy
├── README.md
├── CHANGELOG.md
├── LICENSE
├── AGENTS.md
├── SECURITY.md
├── docs/
│   ├── INSTALL.md
│   ├── LICENSING.md
│   └── M0.md
└── tests/
    └── test_helpers.py
```
