#!/usr/bin/env python3
"""Offline guards on the page a reader sees: asset size, README shape, images, themes.

No network, no dependencies. Exit 1 with one FAIL line per problem.

    python3 scripts/check_page.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ASSETS = ROOT / "assets"

# Budgets. M3.2 tightened the SVG budget to 100 KiB per theme; both assets sat at
# 94,237 B and 84,777 B on 2026-11-23, so the slack is real, not accidental.
SVG_BUDGET = 102_400
# §12 of plan.md: 40–60 lines at W1, 60–90 at W2. The collapsed archive (M4.2.2)
# and the generated Now line are why this moved; raising it again is a reviewed change.
README_MAX_LINES = 80


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
    problems = []
    for svg in sorted(ASSETS.glob("*.svg")):
        tag = re.search(r"<svg\b[^>]*>", svg.read_text(encoding="utf-8"))
        if not tag:
            problems.append(f"{svg.name} has no <svg> tag")
            continue
        box = {attr: re.search(rf'\b{attr}="([^"]+)"', tag.group(0))
               for attr in ("viewBox", "width", "height")}
        if not box["viewBox"]:
            problems.append(f"{svg.name} declares no viewBox")
        if svg.name.startswith("city-"):
            boxes[svg.name] = box
    if len(boxes) < 2:
        return problems + ["expected one SVG per theme in assets/"]
    ref_name, ref = next(iter(boxes.items()))
    for name, box in boxes.items():
        for attr in ("viewBox", "width", "height"):
            a = ref[attr].group(1) if ref[attr] else None
            b = box[attr].group(1) if box[attr] else None
            if a != b:
                problems.append(f"{name} {attr}={b!r} differs from {ref_name} {attr}={a!r}")
    if not problems:
        print(f"ok   box   {', '.join(boxes)} share viewBox {ref['viewBox'].group(1)}")
    return problems


def load_city():
    import importlib.util

    spec = importlib.util.spec_from_file_location("city", ROOT / ".github" / "city.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_asset_safety() -> list[str]:
    """The generated SVGs must be inert: no script, no foreign object, no external href."""
    city = load_city()
    problems = []
    for svg in sorted(ASSETS.glob("*.svg")):
        problems += [f"{svg.name} {p}" for p in city.unsafe_refs(svg.read_text(encoding="utf-8"))]
    if not problems:
        print("ok   inert  no script, no external href, no <image>")
    return problems


PLACEHOLDERS = ("coming soon", "todo", "tbd", "lorem ipsum", "placeholder", "example.com",
                "your-name", "yourname")


def contrast_on_white(hex_colour: str) -> float:
    """WCAG 2.1 relative contrast of white text on `hex_colour`."""
    def channel(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(int(hex_colour[i:i + 2], 16)) for i in (1, 3, 5))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return (1.05) / (luminance + 0.05)


BADGE_MIN_CONTRAST = 4.5  # WCAG AA for normal text


def check_badge_contrast() -> list[str]:
    """White badge text must stay readable on every badge colour (M5.1)."""
    data = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
    problems, seen = [], []
    for link in data["profile"]["links"]:
        ratio = contrast_on_white("#" + link["color"])
        seen.append(f"{link['label']} {ratio:.2f}:1")
        if ratio < BADGE_MIN_CONTRAST:
            problems.append(f"badge {link['label']} #{link['color']} is {ratio:.2f}:1 on white text, "
                            f"under {BADGE_MIN_CONTRAST}:1")
    if not problems:
        print(f"ok   a11y  {len(seen)} badge colours, contrast {' / '.join(seen)}")
    return problems


def check_no_placeholders() -> list[str]:
    """Sections exist because the content does, never to fill a gap (M4.1.2)."""
    text = README.read_text(encoding="utf-8").lower()
    problems = [f"README.md contains the placeholder {word!r}" for word in PLACEHOLDERS if word in text]
    problems += [f"README.md links to a bare {m!r}" for m in re.findall(r"\]\((\#[^)]*|)\)", text)]
    if not problems:
        print("ok   text  no placeholders, no empty link targets")
    return problems


def check_accessible_names() -> list[str]:
    """A screen reader should hear the year and the total, not "image" (M3.2.2)."""
    problems, totals = [], {}
    for svg in sorted(ASSETS.glob("city-*.svg")):
        text = svg.read_text(encoding="utf-8")
        # The city also carries a <title> per building, so ask for the SVG-level one by id.
        title = re.search(r'<title id="ct"[^>]*>([^<]*)</title>', text) or re.search(r'<title[^>]*>([^<]*)</title>', text)
        desc = re.search(r'<desc id="cd"[^>]*>([^<]*)</desc>', text) or re.search(r'<desc[^>]*>([^<]*)</desc>', text)
        if not title:
            problems.append(f"{svg.name} has no <title>")
        if not desc:
            problems.append(f"{svg.name} has no <desc>")
        if not title or not desc:
            continue
        total = re.search(r"([\d,]+) contributions", title.group(1) + " " + desc.group(1))
        if not total:
            problems.append(f"{svg.name} <title>/<desc> states no contribution total")
            continue
        totals[svg.name] = total.group(1)
        if not re.search(r"\d{4}", title.group(1)):
            problems.append(f"{svg.name} <title> states no year")
        bounds = re.search(r"\d{4}-\d{2}-\d{2} to \d{4}-\d{2}-\d{2}", desc.group(1))
        if not bounds:
            problems.append(f"{svg.name} <desc> states no date range")
        if not re.search(r'aria-labelledby="ct cd"', text):
            problems.append(f"{svg.name} does not point aria-labelledby at its title and desc")
    if len(set(totals.values())) > 1:
        problems.append(f"themes disagree on the total: {totals}")
    if not problems:
        print(f"ok   a11y  {', '.join(f'{k} {v}' for k, v in totals.items())} with title, desc, dates")
    return problems


def check_city_encoder() -> list[str]:
    """The drawing says what its geometry means, and it stops moving when asked (M5.2)."""
    problems, notes = [], []
    caption = re.search(r"<!-- city:start -->\n(.*?)\n<!-- city:end -->",
                        README.read_text(encoding="utf-8"), re.S)
    if not caption:
        problems.append("README.md has no <!-- city:start --> … <!-- city:end --> caption")
    for svg in sorted(ASSETS.glob("city-*.svg")):
        text = svg.read_text(encoding="utf-8")
        if "Each tower is one day" not in text:
            problems.append(f"{svg.name} has no legend stating what a tower's height means")
        if "prefers-reduced-motion:reduce" not in text:
            problems.append(f"{svg.name} animates without a prefers-reduced-motion rule")
        if caption:
            title = re.search(r'<title id="ct"[^>]*>([^<]*)</title>', text)
            stated = re.search(r"([\d,]+) contributions", caption.group(1))
            if title and stated and stated.group(1) not in title.group(1):
                problems.append(f"{svg.name} title says {title.group(1)!r} but the caption under it "
                                f"says {stated.group(1)} contributions")
            notes.append(svg.name)
    if not problems and caption:
        print(f"ok   image legend in {len(notes)} themes, reduced-motion rule present, "
              f"caption matches the title total")
    return problems


PROVENANCE = re.compile(r"<!-- citykit (\d+\.\d+\.\d+) · data (\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2}) "
                          r"· commit ([0-9a-f]{7}|unknown) -->")


def check_provenance() -> list[str]:
    """A stale image must name the generator, its data range and the commit (M6.1.2)."""
    problems, found = [], {}
    for svg in sorted(ASSETS.glob("city-*.svg")):
        match = PROVENANCE.search(svg.read_text(encoding="utf-8"))
        if not match:
            problems.append(f"{svg.name} carries no `citykit <version> · data <first>..<last> · commit <sha>` comment")
            continue
        version, first, last, commit = match.groups()
        found[svg.name] = f"v{version} {first}..{last} at {commit}"
        title = re.search(r'<title id="ct"[^>]*>([^<]*)</title>', svg.read_text(encoding="utf-8"))
        if title and first[:4] not in title.group(1):
            problems.append(f"{svg.name} provenance says data starts {first} but the title says {title.group(1)!r}")
    if len(set(v.split(' at ')[0] for v in found.values())) > 1:
        problems.append(f"the two themes disagree on their data range: {found}")
    if not problems:
        print(f"ok   prov  {', '.join(f'{k} {v}' for k, v in found.items())}")
    return problems


REVIEW = ROOT / "docs" / "REVIEW.md"
REVIEW_MAX_DAYS = 100


def check_review_freshness(today=None) -> list[str]:
    """A recorded review date is only worth having if it has to be current (M6.1.1)."""
    from datetime import date

    text = REVIEW.read_text(encoding="utf-8")
    dates = re.findall(r"^\| (\d{4}-\d{2}-\d{2}) \|", text, re.MULTILINE)
    if not dates:
        return ["docs/REVIEW.md records no review date (expected a | YYYY-MM-DD | row in Passes)"]
    last = max(date.fromisoformat(d) for d in dates)
    age = ((today or date.today()) - last).days
    if age > REVIEW_MAX_DAYS:
        return [f"the last review was {age} days ago ({last}); docs/REVIEW.md allows {REVIEW_MAX_DAYS}"]
    print(f"ok   review  last pass {last} ({age} day(s) ago, budget {REVIEW_MAX_DAYS})")
    return []


def check_hosts_documented() -> list[str]:
    """A new external host is a new dependency; docs/DEPENDENCIES.md must name it."""
    from urllib.parse import urlparse

    text = README.read_text(encoding="utf-8")
    urls = re.findall(r'(?:href|src)="(https?://[^"]+)"', text)
    urls += re.findall(r'srcset="(https?://[^"]+)"', text)
    urls += re.findall(r"\]\((https?://[^)]+)\)", text)
    documented = (ROOT / "docs" / "DEPENDENCIES.md").read_text(encoding="utf-8")
    hosts = sorted({urlparse(u).netloc for u in urls})
    problems = [f"{h} is used by README.md but not listed in docs/DEPENDENCIES.md"
                for h in hosts if h not in documented]
    if not problems:
        print(f"ok   hosts {len(hosts)} hosts, {len(urls)} URLs, all documented")
    return problems


def main() -> int:
    problems = (check_asset_size() + check_readme_lines() + check_images_and_links()
                + check_theme_geometry() + check_asset_safety() + check_accessible_names()
                + check_no_placeholders() + check_badge_contrast() + check_city_encoder() + check_provenance() + check_review_freshness()
                + check_hosts_documented())
    for p in problems:
        print(f"FAIL {p}")
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
