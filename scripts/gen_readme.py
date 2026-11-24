#!/usr/bin/env python3
"""Render the README's project table and badge row from projects.json.

A claim becomes a data edit, and a link cannot drift from its label.

    python3 scripts/gen_readme.py --write   # rewrite the generated blocks
    python3 scripts/gen_readme.py --check   # exit 1 if README.md has drifted

Two generated blocks, each between markers; everything outside them is
hand-written:

    <!-- badges:start --> … <!-- badges:end -->
    <!-- projects:start --> … <!-- projects:end -->
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
PROJECTS = ROOT / "projects.json"
NOW = ROOT / "now.json"
BLOCKS = {
    "badges": ("<!-- badges:start -->", "<!-- badges:end -->"),
    "now": ("<!-- now:start -->", "<!-- now:end -->"),
    "projects": ("<!-- projects:start -->", "<!-- projects:end -->"),
}
NOW_DESCRIPTION_CHARS = 120


def load() -> dict:
    return json.loads(PROJECTS.read_text(encoding="utf-8"))


def render_table(projects: list[dict]) -> str:
    lines = ["| Project | What it does |", "|:--|:--|"]
    for p in projects:
        cell = p["claim"]
        if p.get("live"):
            # A sleeping free tier is visible to the reader, not a surprise click.
            label = "Live (cold start)" if p.get("cold_start") else "Live"
            cell += f' [{label}]({p["live"]})'
        lines.append(f'| [**{p["name"]}**]({p["repo"]}) | {cell} |')
    return "\n".join(lines)


def badge(link: dict) -> str:
    url = (f'https://img.shields.io/badge/{link["label"]}-{link["color"]}'
           f'?style=flat-square&logo={link["logo"]}&logoColor=white&labelColor=555')
    return f'[![{link["alt"]}]({url})]({link["url"]})'


def render_badges(links: list[dict]) -> str:
    return " ".join(badge(link) for link in links)


def render_now(now: dict) -> str:
    """"Now" is whatever the API says was pushed last; never a hand-typed claim."""
    line = f'**Now:** [**{now["repo"]}**]({now["url"]})'
    description = now.get("description", "").strip()
    prefix = f'{now["repo"]}: '
    if description.lower().startswith(prefix.lower()):  # the repo usually repeats its own name
        description = description[len(prefix):]
    if description:
        head = description.split(".")[0].strip()
        if len(head) > NOW_DESCRIPTION_CHARS:
            head = head[:NOW_DESCRIPTION_CHARS].rsplit(" ", 1)[0] + "…"
        line += f" — {head}."
    return line + f' Last push {now["pushed_at"]}.'


def render_block(kind: str, body: str) -> str:
    start, end = BLOCKS[kind]
    return f"{start}\n{body}\n{end}"


def replace_block(readme: str, kind: str, body: str) -> str:
    start_marker, end_marker = BLOCKS[kind]
    start = readme.find(start_marker)
    end = readme.find(end_marker)
    if start < 0 or end < 0 or end < start:
        raise SystemExit(f"README.md has no {start_marker} … {end_marker} block; add the markers once, by hand")
    return readme[:start] + render_block(kind, body) + readme[end + len(end_marker):]


def render_readme(readme: str, data: dict, now: dict) -> str:
    readme = replace_block(readme, "badges", render_badges(data["profile"]["links"]))
    readme = replace_block(readme, "now", render_now(now))
    return replace_block(readme, "projects", render_table(data["projects"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="rewrite the generated blocks in README.md")
    group.add_argument("--check", action="store_true", help="exit 1 when README.md differs from the data")
    args = ap.parse_args()

    data = load()
    now = json.loads(NOW.read_text(encoding="utf-8"))
    readme = README.read_text(encoding="utf-8")
    expected = render_readme(readme, data, now)

    if args.check:
        if readme != expected:
            print("FAIL README.md is not what projects.json renders; run python3 scripts/gen_readme.py --write")
            return 1
        print(f"ok   data {len(data['profile']['links'])} badges, {len(data['projects'])} projects, "
              f"now={now['repo']}, README.md matches")
        return 0

    README.write_text(expected, encoding="utf-8", newline="\n")
    print(f"wrote {len(data['profile']['links'])} badges and {len(data['projects'])} projects into README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
