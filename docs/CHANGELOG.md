# Changelog

For the contribution-city generator (`scripts/citykit/` + `.github/city.py`) and the
profile tooling around it. The version in a tag matches the version the SVGs carry in
their provenance comment (`<!-- citykit 1.0.0 · data … · commit … -->`), so a file on
disk names the release that drew it.

## 1.0.0 — 2026-11-24

The first tagged release. Everything before it was a single script edited in place,
so nothing older is reconstructable from a tag.

### Added

- `stats.py`: total, longest streak and busiest month for the same calendar the
  drawing uses, written to `assets/city-stats.json` and rendered as one line under
  the image (`<!-- city:start/end -->`).
- A legend line inside both SVGs stating that a tower is one day and its height the
  contributions of that day, and that a river is a run of quiet weeks.
- `<desc>` carries the same sentence as the visible caption, so alt text and captions
  cannot disagree.
- Provenance comment in every SVG: generator version, data range, commit.
- `@media (prefers-reduced-motion: reduce)` — every animation stops, and buildings
  that start hidden are made visible.
- Guards: `scripts/pin_claims.py` (claims pinned to a file **and** a line),
  `scripts/audit_claims.py` (quarterly number, live link, licence and last-commit audit).
- `docs/AUDIT.md`, `docs/CI.md`, `docs/DEPENDENCIES.md`, `docs/PRIVACY.md`.

### Changed

- `PAD_B` 56 → 76 to give the legend its own band; viewBox height 349 → 369.
- Badge colours moved into the city's water/leaf ramp and made to pass 4.5:1 against
  white text (LinkedIn was 3.89:1).
- README's banner is 120 px tall instead of 200.

### Known limits

- Each tower's colour is a colour channel; the ramp is distinguishable under
  simulated deuteranopia (adjacent ΔE ≥ 14.7), but height is the primary encoding.
- The 360 × 640 first screen cannot hold the name, the sentence and the badges at
  once on GitHub; the measurements are in `plan.md` (M5.1.2).

## Releasing

1. Change the drawing or the tooling.
2. Bump `__version__` in `scripts/citykit/__init__.py` and add a section here.
3. Re-render (`GITHUB_TOKEN=… python3 .github/city.py`) so the assets carry the new
   version, then `python3 scripts/gen_readme.py --write`.
4. Commit, then tag: `git tag city-v1.0.0 && git push origin city-v1.0.0`.
