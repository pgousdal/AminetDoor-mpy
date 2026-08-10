# Changelog

## 1.0.1 — Version Reporting Fix

- Fixed stale version reporting in the live Mystic door banner; the main menu
  and About header now use the canonical runtime version source.
- Removed duplicated version metadata from diagnostic tooling and strengthened
  release validation to exercise the rendered headers and runtime User-Agent.
- Added regression coverage that rejects stale hardcoded version banners.
- This patch release contains no new product features.

## 1.0.0 — M1.7 Release Readiness

- Aligned user, installation, licensing, and milestone documentation with the
  complete implemented feature set and confirmed live Mystic operation.
- Normalized runtime and diagnostic version reporting to 1.0.0.
- Added deterministic release validation and a manual release checklist.
- Added no major functional scope; this release prepares the mature M1.6 door
  for its first stable release.

## M1.5 Package of the Day

- Added a deterministic daily spotlight sourced from the existing Recent feed.
- Reuses the current README reader and cache without adding another endpoint.

## M1.6 Favorites

- Added per-user local JSON bookmarks with atomic writes and Favorites lightbar
  management.
- Favorites use Mystic's `getuser(0)` identity and fail open on storage errors.

## M1.3 Quick Path

- Added `J` in Browse to jump directly to validated Aminet category paths.
- Quick Path reuses Browse retrieval, architecture filtering, and existing
  hierarchy semantics.

## M1.4 Resilient Browse

- Browse root and catalog parents no longer depend on Aminet's `/tree` endpoint.
- Catalog leaves continue to load live, architecture-filtered package listings.

## M1.2 Local README cache

- Added a bounded JSON cache for package README text with a 24-hour default TTL.
- Cache writes are atomic; corrupt entries are ignored and stale entries can
  serve during transient network failures.
- Made cache path resolution Mystic `.mpy` safe and fail open on filesystem
  configuration or permission errors.

## Transient Aminet backend failures

- Added bounded retries for HTTP 502, 503, and 504 responses with concise
  final outage messages and developer-only attempt diagnostics.
- Recent now reports feed transport and parse details in `DEBUG_NETWORK` mode;
  malformed feeds are distinct from HTTP failures and valid empty feeds.

## M1.1 Architecture filtering

- Added SysOp-configured architecture filtering for Browse package listings
  and Search, defaulting to `m68k-amigaos` plus `generic`.
- Uses Aminet's verified Advanced Search `arch[]` fields; the complete Browse
  category tree and unfiltered Recent RSS behavior remain unchanged.

## Mystic-native ESC navigation

- ESC is now presented as the primary Back/Cancel/Menu key across menus, selectors, Search
  input, README pages, About, and pause/error screens.
- Q remains the compatible alias wherever ESC performs the same action.
- Search and numbered input use a small Mystic-native `getkey()` line reader
  so Escape, Enter, Backspace, and bounded printable input are explicit.
- Centralized navigation preserves Mystic's live-tested Escape (`"\\x1b"`) and
  extended arrow (`("H", True)` / `("P", True)`) representations.

## Network diagnostics

- Aligned the standalone urllib probe with production User-Agent, headers,
  timeout, response limit, and verified SSL context.
- Added runtime, CA-path, proxy-key, and detailed exception diagnostics behind
  `DEBUG_NETWORK`.
- Added portable verified CA-bundle fallback and classified TLS/DNS/timeout,
  refusal, generic network, and HTTP failures.

## M1

- Added read-only Browse navigation for Aminet categories and package lists.
- Added bounded keyword Search using Aminet's public `/search?query=` form.
- Reused the lightbar selector and existing README reader for both modes.
- Added stdlib HTML parsing, offline fixtures, and browse/search documentation.
- Live Mystic validation remains pending.

## M1 Fix

- Fixed Browse child-category parsing for Aminet's direct relative links such
  as `game/shoot`; root links still use `tree?path=`.
- Added safe same-host category URL normalization and clearer markup failures.
- Verified live Browse, Search, and README probes from the development host.

## M0.2

- Added a configurable lightbar result selector, defaulting to `lightbar`.
- Added Mystic-native extended Up/Down handling and a scrolling result viewport.
- Retained multi-digit numbered compatibility mode with safe fallback behavior.
- Polished the About screen and expanded offline selector tests.
- Live Mystic validation remains pending.

## 0.1.0 — M0

Initial functional delivery.

- Mystic Python 3 `.mpy` implementation
- Recent Aminet uploads via RSS feed (`https://aminet.net/feed`)
- numbered selection from the recent-uploads list
- plain-text README retrieval and paged reader
- dependency-free HTTP using `urllib`, feed parsing using `xml.etree`
- error handling and documentation
