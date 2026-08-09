# Changelog

## M1

- Added read-only Browse navigation for Aminet categories and package lists.
- Added bounded keyword Search using Aminet's public `/search?query=` form.
- Reused the lightbar selector and existing README reader for both modes.
- Added stdlib HTML parsing, offline fixtures, and browse/search documentation.
- Live Mystic validation remains pending.

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
