# AminetDoor

**AminetDoor M0 / v0.1.0** is a small Aminet reader written as a Mystic BBS
Python 3 (`.mpy`) script.

## M0 features

- Recent Aminet uploads, fetched from Aminet's RSS feed
- Numbered selection from the recent-uploads list
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

Main menu:

```text
R  Recent uploads
A  About
Q  Quit
```

README reader:

```text
N  Next page
P  Previous page
Q  Return to recent-uploads list
```

## Data source

M0 uses Aminet's public RSS feed at:

```text
https://aminet.net/feed
```

and fetches the matching plain-text `.readme` file for a selected package
directly from `https://aminet.net/<path>.readme`. No scraping of Aminet's
HTML pages is performed in M0; RSS/XML is used because it is far more stable
to parse than HTML that can change layout at any time.

## Scope

M0 intentionally stays small. It does not yet include category Browse,
keyword Search, architecture filtering, local README caching, a "package of
the day" random spotlight, or screenshot rendering. Those are good M1
candidates -- see `docs/M0.md`.

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
