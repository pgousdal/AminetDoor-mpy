# Release checklist

Use this checklist for AminetDoor v1.0.1. Publishing remains a manual SysOp or
maintainer action; the release checker does not use credentials or modify
GitHub.

- [ ] Run `python3 scripts/release_check.py` (tests, compilation, and metadata).
- [ ] Run any configured lint, formatting, or static checks; none are currently
  configured in this repository.
- [ ] Review the complete diff and confirm the working tree contains only
  intended release changes.
- [ ] Launch `aminetdoor.mpy` on a live Mystic BBS at an 80x25 terminal size.
- [ ] Verify Recent, Browse, Search, and Package of the Day.
- [ ] Verify architecture-filtered Browse and Search package listings.
- [ ] Verify README viewing and next/previous/ESC navigation.
- [ ] Add, reload, and remove a Favorite; confirm per-user persistence.
- [ ] Exercise a transient network failure and verify bounded retries, friendly
  errors, and stale README fallback where cached content exists.
- [ ] Verify ESC/Q cleanly exits each interactive context and returns to Mystic.
- [ ] Verify the About/runtime display reports v1.0.1.
- [ ] Update and review `CHANGELOG.md`.
- [ ] Commit the final release changes.
- [ ] Create the annotated tag: `git tag -a v1.0.1 -m "AminetDoor v1.0.1"`.
- [ ] Push the commit and tag, then create the GitHub release manually.
