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


def check_images_and_links() -> list[str]:
    """Every image states what it is, and every link goes somewhere."""
    text = README.read_text(encoding="utf-8")
    problems = []
    for m in re.finditer(r"<img\b[^>]*>", text):
        tag = m.group(0)
        if not re.search(r"\balt=", tag):
            problems.append(f"<img> without alt: {tag[:80]}")
    for m in re.finditer(r"!\[([^\]]*)\]\(([^)]*)\)", text):
        alt, src = m.group(1), m.group(2)
        if not alt.strip():
            problems.append(f"markdown image without alt text: {src[:80]}")
        if not src.strip():
            problems.append("markdown image without a source")
    for m in re.finditer(r"\[([^\]]*)\]\(\s*\)", text):
        problems.append(f"link without a destination: [{m.group(1)}]()")
    for m in re.finditer(r"<a\b[^>]*href\s*=\s*[\"']\s*[\"']", text):
        problems.append(f"anchor without a destination: {m.group(0)[:80]}")
    if not problems:
        imgs = len(re.findall(r"<img\b[^>]*>", text)) + len(re.findall(r"!\[", text))
        print(f"ok   alt   {imgs} images, every link has a destination")
    return problems


def check_theme_geometry() -> list[str]:
    """The dark and light SVGs must agree on their box, or the page jumps between themes."""
    boxes = {}
    for svg in sorted(ASSETS.glob("*.svg")):
        tag = re.search(r"<svg\b[^>]*>", svg.read_text(encoding="utf-8"))
        if not tag:
            return [f"{svg.name} has no <svg> tag"]
        boxes[svg.name] = {
            attr: re.search(rf'\b{attr}="([^"]+)"', tag.group(0)) for attr in ("viewBox", "width", "height")
        }
        if not boxes[svg.name]["viewBox"]:
            return [f"{svg.name} declares no viewBox"]
    if len(boxes) < 2:
        return ["expected one SVG per theme in assets/"]
    ref_name, ref = next(iter(boxes.items()))
    problems = []
    for name, box in boxes.items():
        for attr in ("viewBox", "width", "height"):
            a = ref[attr].group(1) if ref[attr] else None
            b = box[attr].group(1) if box[attr] else None
            if a != b:
                problems.append(f"{name} {attr}={b!r} differs from {ref_name} {attr}={a!r}")
    if not problems:
        print(f"ok   box   {', '.join(boxes)} share viewBox {ref['viewBox'].group(1)}")
    return problems


def main() -> int:
    problems = check_asset_size() + check_readme_lines() + check_images_and_links() + check_theme_geometry()
    for p in problems:
        print(f"FAIL {p}")
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
