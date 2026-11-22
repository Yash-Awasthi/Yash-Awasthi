#!/usr/bin/env python3
"""Pin every claim_source to a line number, once, from the code it cites.

A claim that names only a file can drift inside that file without anyone
noticing; a claim that names a line cannot. Run this after a repo's prose moves
and before check_claims.py, which then holds the line:

    python3 scripts/pin_claims.py --write    # fill in / refresh every `line`
    python3 scripts/pin_claims.py --check    # exit 1 if any pinned line is wrong

Which line is pinned: the first line of the cited file that holds one of the
claim's own snippets (`any[]`), or the `const NAME` line for a `count` claim.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_claims import PROJECTS, read, repo_name  # noqa: E402


def line_of(text: str, c: dict) -> tuple[int, str] | tuple[None, str]:
    """The 1-based line that backs this entry, in the order the claim is written."""
    lines = text.splitlines()
    for token in c.get("any", []):
        for n, line in enumerate(lines, 1):
            if token in line:
                return n, token
    name = c.get("count")
    if name:
        for n, line in enumerate(lines, 1):
            if f"const {name}" in line:
                return n, f"const {name}"
    return None, ""


def pin(data: dict, write: bool) -> int:
    problems, pinned = [], 0
    for p in data["projects"] + data.get("archive", []):
        target = repo_name(p["repo"])
        for c in p.get("claim_source", []):
            text = read(target, c["file"])
            if text is None:
                problems.append(f"{p['name']}: cannot read {target}/{c['file']}")
                continue
            found, _ = line_of(text, c)
            if found is None:
                problems.append(f"{p['name']}: no line in {c['file']} holds {c.get('any') or c.get('count')!r}")
                continue
            if write:
                c["line"] = found
            elif c.get("line") != found:
                problems.append(f"{p['name']}: {c['file']} line {c.get('line')} is not where the claim lives (now {found})")
            pinned += 1
    if write and not problems:
        PROJECTS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for problem in problems:
        print(f"FAIL {problem}")
    print(f"{pinned} claim(s) {'pinned' if write else 'verified'}, {len(problems)} problem(s)")
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="fill in every claim_source line")
    group.add_argument("--check", action="store_true", help="exit 1 when a pinned line is stale")
    args = ap.parse_args()
    return pin(json.loads(PROJECTS.read_text(encoding="utf-8")), args.write)


if __name__ == "__main__":
    sys.exit(main())
