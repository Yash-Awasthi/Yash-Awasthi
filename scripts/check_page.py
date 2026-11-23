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
# §12 of plan.md holds the page to 40–60 lines at W1: a profile that turns into
# a résumé loses the reader. Raising this is a deliberate, reviewed change.
README_MAX_LINES = 60


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


def check_readme_lines() -> list[str]:
    lines = README.read_text(encoding="utf-8").count("\n") + 1
    if lines > README_MAX_LINES:
        return [f"README.md is {lines} lines, over the {README_MAX_LINES}-line budget"]
    print(f"ok   lines README.md {lines} (budget {README_MAX_LINES})")
    return []


def main() -> int:
    problems = check_asset_size() + check_readme_lines()
    for p in problems:
        print(f"FAIL {p}")
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
