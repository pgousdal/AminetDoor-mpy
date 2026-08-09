# AminetDoor

**AminetDoor M0.2 / v0.1.0** is a small Aminet reader written as a Mystic BBS
Python 3 (`.mpy`) script.

## Features

- Recent Aminet uploads, fetched from Aminet's RSS feed
- Browse Aminet's category hierarchy and package listings
- Search Aminet by package name or keyword
- Architecture-aware Browse and Search, defaulting to 68k AmigaOS + generic
- Local README cache with 24-hour freshness and stale-on-transient fallback
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

Browse navigation uses an inline catalog mirroring Aminet's public category
tree, so temporary `/tree` outages do not disable category navigation. Package
listings remain live. Within Browse, `B` goes back one level, `R` returns to the
root, and `J` jumps directly to a category path such as `game/shoot`, `comm/net`,
or `dev/cross`. Search uses Aminet's public search interface with a maximum
query length of 60 characters. Both modes open the same README reader as Recent.

Architecture filtering is configured in `aminetdoor.mpy`:

```python
ARCHITECTURE_FILTER = ("m68k-amigaos", "generic")
```

The default targets classic 68k Amiga users while retaining architecture-
independent Aminet content. Set `ARCHITECTURE_FILTER = None` to show all
architectures. The filter applies to Browse package lists and Search; Recent
remains unfiltered because its RSS feed does not expose reliable architecture
metadata.

README text caching is configured in the same script:

```python
CACHE_ENABLED = True
CACHE_DIR = "cache/readme"  # relative to Mystic's process working directory
CACHE_MAX_AGE_SECONDS = 86400
```

Relative `CACHE_DIR` values use Mystic's process working directory; set an
absolute path when the deployment working directory is not stable. The cache
stores only bounded JSON README text and uses stale content if a refresh fails
at the network layer. Cache/filesystem failures bypass caching and continue
with the normal Aminet fetch. Cached package content remains subject to its
original authors' copyright and licensing terms.

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
for category levels. M1.1 package listings use Aminet's verified Advanced
Search form with `type=advanced`, `path[]`, `q_arch=AND`, and repeated
`arch[]` values. M1 Search uses the same Advanced Search architecture fields
when filtering is enabled; `ARCHITECTURE_FILTER = None` retains the original
simple `GET https://aminet.net/search?query=...` request. Responses are parsed
with Python's standard-library `html.parser` and are bounded before parsing.

## Scope

M1.2 intentionally stays read-only. It does not include interactive
architecture selection, package archive caching, a "package of the day"
random spotlight, screenshots, downloads, uploads, or account functionality.
See `docs/M1.md`.

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
