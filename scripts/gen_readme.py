#!/usr/bin/env python3
"""Render the README's project table from projects.json, so a claim is a data edit.

    python3 scripts/gen_readme.py --write   # rewrite the block in README.md
    python3 scripts/gen_readme.py --check   # exit 1 if README.md has drifted

The generated block sits between `<!-- projects:start -->` and
`<!-- projects:end -->`. Everything outside those markers is hand-written.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
PROJECTS = ROOT / "projects.json"
START = "<!-- projects:start -->"
END = "<!-- projects:end -->"


def load() -> dict:
    return json.loads(PROJECTS.read_text(encoding="utf-8"))


def render_table(projects: list[dict]) -> str:
    lines = ["| Project | What it does |", "|:--|:--|"]
    for p in projects:
        cell = p["claim"]
        if p.get("live"):
            cell += f' [Live]({p["live"]})'
        lines.append(f'| [**{p["name"]}**]({p["repo"]}) | {cell} |')
    return "\n".join(lines)


def render_block(data: dict) -> str:
    return f"{START}\n{render_table(data['projects'])}\n{END}"


def replace_block(readme: str, block: str) -> str:
    start = readme.find(START)
    end = readme.find(END)
    if start < 0 or end < 0 or end < start:
        raise SystemExit(f"README.md has no {START} … {END} block; add the markers once, by hand")
    return readme[:start] + block + readme[end + len(END):]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="rewrite the block in README.md")
    group.add_argument("--check", action="store_true", help="exit 1 when README.md differs from the data")
    args = ap.parse_args()

    data = load()
    readme = README.read_text(encoding="utf-8")
    expected = replace_block(readme, render_block(data))

    if args.check:
        if readme != expected:
            print("FAIL README.md is not what projects.json renders; run python3 scripts/gen_readme.py --write")
            return 1
        print(f"ok   table {len(data['projects'])} projects, README.md matches projects.json")
        return 0

    README.write_text(expected, encoding="utf-8", newline="\n")
    print(f"wrote {len(data['projects'])} projects into README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
