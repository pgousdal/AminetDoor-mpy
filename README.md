# AminetDoor

AminetDoor v1.0.0 is a read-only Aminet browser and search door for Mystic
BBS. It is a single Python 3 `.mpy` script, uses only the Python standard
library, and has been validated in a live Mystic BBS installation.

## Features

- Recent uploads from Aminet's RSS feed
- Category Browse that remains navigable without Aminet's `/tree` page
- Keyword Search and SysOp-configured architecture filtering for Browse/Search
- Deterministic Package of the Day drawn from the current Recent feed
- Per-user Favorites based on Mystic's documented `bbs.getuser(0)` identity
- Paged package description/README viewing for an 80x25 terminal
- Bounded local JSON caching of README text, with stale-cache fallback for
  transient network failures
- Classified network errors, finite 10-second request timeouts, bounded reads,
  and two retries for HTTP 502/503/504 responses

## Requirements and installation

AminetDoor requires Mystic BBS with embedded Python 3.6 or newer and
standard-library HTTPS support. It has no third-party Python dependencies.

Copy `aminetdoor.mpy` to the active Mystic theme's script directory or
Mystic's default script directory, then add this menu command:

```text
Command: GZ
Data:    aminetdoor
```

Mystic supplies the `mystic_bbs` module and resolves the omitted `.mpy`
extension. See [docs/INSTALL.md](docs/INSTALL.md) for deployment and
troubleshooting details.

## Configuration

Configuration constants are near the top of `aminetdoor.mpy`. Common choices
are:

```python
ARCHITECTURE_FILTER = ("m68k-amigaos", "generic")
RESULT_SELECTOR = "lightbar"       # or "numbered"
CACHE_ENABLED = True
CACHE_DIR = "cache/readme"
CACHE_MAX_AGE_SECONDS = 86400
USER_DATA_DIR = "data/users"
```

Set `ARCHITECTURE_FILTER = None` for unfiltered Browse and Search results.
Recent stays unfiltered because its feed lacks reliable architecture metadata.
Relative storage paths use Mystic's process working directory; absolute paths
are recommended when that directory is not stable.

Favorites are stored as per-user local JSON under `USER_DATA_DIR/favorites`.
README cache entries are bounded JSON containing text only. Storage failures
fail open: Favorites may become unavailable and cache operations are bypassed,
while Browse, Search, Recent, and README fetching continue. A stale README can
be served when a refresh encounters a transient network failure. Archives,
HTML, RSS, credentials, cookies, and executable content are never cached.

## Controls

Arrow keys move, Enter selects, and ESC goes back, cancels, or exits the
current context. Q is an ESC-compatible alias. Main-menu keys are `R` Recent,
`B` Browse, `S` Search, `P` Package of the Day, `F` Favorites, and `A` About.
Browse also supports `B` (parent), `R` (root), and `J` (validated category
path). The README reader uses `N` and `P` for paging. Favorites can be toggled
with `F` in package contexts and removed with `D` in the Favorites screen.

## Network and scope

Aminet responses are treated as untrusted input and bounded before parsing.
RSS/XML uses `xml.etree.ElementTree`; Browse/Search HTML uses
`html.parser.HTMLParser`. All Aminet operations are read-only.

Intentional non-goals include downloads, uploads, Aminet accounts, credentials,
cookies, archive or HTML caching, mirrors, screenshots, and caller-selectable
architecture settings. The inline category catalog is navigation data only;
package listings and metadata remain live.

## Validation and release status

Version 1.0.0 represents the first stable release. Automated tests are
offline and mock network calls; the door has also been operated successfully
under Mystic BBS. Run the complete release gate with:

```bash
python3 scripts/release_check.py
```

See [docs/RELEASE.md](docs/RELEASE.md) for the release checklist.

## Licensing

AminetDoor source code is MIT licensed. Package descriptions, README text, and
metadata retrieved from Aminet remain the property of their respective authors
and are not relicensed by AminetDoor. See
[docs/LICENSING.md](docs/LICENSING.md).
