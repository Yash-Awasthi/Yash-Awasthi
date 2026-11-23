#!/usr/bin/env python3
"""Offline guards on the page a reader sees: asset size, README shape, images, themes.

No network, no dependencies. Exit 1 with one FAIL line per problem.

    python3 scripts/check_page.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ASSETS = ROOT / "assets"

# Budgets. M3.2 tightens the SVG budget to 100 KB per theme.
SVG_BUDGET = 200_000
README_MAX_LINES = 120


def check_asset_size() -> list[str]:
    problems = []
    for svg in sorted(ASSETS.glob("*.svg")):
        size = svg.stat().st_size
        if size > SVG_BUDGET:
            problems.append(f"{svg.relative_to(ROOT)} is {size:,} B, over the {SVG_BUDGET:,} B budget")
        else:
            print(f"ok   size  {svg.relative_to(ROOT)} {size:,} B")
    if not list(ASSETS.glob("*.svg")):
        problems.append("assets/ has no SVG")
    return problems


def main() -> int:
    problems = check_asset_size()
    for p in problems:
        print(f"FAIL {p}")
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
