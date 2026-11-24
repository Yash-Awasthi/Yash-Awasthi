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

from citykit import (THEMES, FetchError, fetch, filter_year, layout,  # noqa: E402
                     parse_calendar, render, summary, unsafe_refs, write_assets)

__all__ = ["THEMES", "FetchError", "fetch", "filter_year", "layout", "parse_calendar",
           "render", "summary", "unsafe_refs", "write_assets"]


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
    print(f"city.py: {summary(weeks)}")
    write_assets(weeks, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
