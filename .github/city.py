"""Render the last year of contributions as an oblique 3D city (light and dark SVGs).

The drawing lives in `scripts/citykit/`: `source` fetches and validates the calendar,
`layout` turns weeks into columns, `theme` holds the palettes, `draw` writes the SVG
and `assets` swaps both files in atomically. This file is the command line.

    python3 .github/city.py <login> [--year YYYY] [--out DIR]
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from citykit import (THEMES, FetchError, __version__, caption, fetch,  # noqa: E402
                     filter_year, layout, parse_calendar, render, stats, summary,
                     unsafe_refs, write_assets)

__all__ = ["THEMES", "FetchError", "caption", "fetch", "filter_year", "layout", "parse_calendar",
           "render", "stats", "summary", "unsafe_refs", "write_assets"]


def commit_sha() -> str:
    """The commit that produced the current assets, so a stale SVG can be identified."""
    env = os.environ.get("GITHUB_SHA", "").strip()
    if env:
        return env[:7]
    try:
        import subprocess

        out = subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], capture_output=True,
                             text=True, check=True, cwd=Path(__file__).resolve().parents[1])
        return out.stdout.strip() or "unknown"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("user", nargs="?", help="GitHub login to render (default: $GITHUB_USER)")
    ap.add_argument("--year", type=int, help="render only this calendar year")
    ap.add_argument("--out", default="assets", help="output directory for the two SVGs (default: assets)")
    args = ap.parse_args()
    user = args.user or os.environ.get("GITHUB_USER")
    if not user:
        ap.error("no user given; pass one or set GITHUB_USER")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        ap.error("GITHUB_TOKEN is not set")
    try:
        weeks = fetch(user, token)
        if args.year:
            weeks = filter_year(weeks, args.year)
    except FetchError as e:
        print(f"city.py: {e} (assets left untouched)", file=sys.stderr)
        return 1
    days = sorted(d for w in weeks for d, _ in w)
    provenance = f"citykit {__version__} · data {days[0]}..{days[-1]} · commit {commit_sha()}"
    print(f"city.py: {summary(weeks)}")
    print(f"city.py: {provenance}")
    write_assets(weeks, args.out, provenance)
    return 0


if __name__ == "__main__":
    sys.exit(main())
