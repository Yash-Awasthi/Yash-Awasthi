#!/usr/bin/env python3
"""Check every claim in projects.json against the repository it describes.

`projects.json` is the source of truth for the profile table, and every project
carries `claim_source`: the file in its own repository and the snippet that backs
the claim. This script verifies those snippets and exits non-zero when a claim
has drifted from its repository, so a mismatch fails CI instead of shipping.

    python3 scripts/check_claims.py            # snippets only, no network
    python3 scripts/check_claims.py --links    # also fetch every live URL

Sibling checkouts are used when present (``../Nexus``, ``../FinScrape``, …);
otherwise the file is fetched from ``raw.githubusercontent.com`` on the default
branch, so the check works from a fresh clone in CI.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects.json"
OWNER = "Yash-Awasthi"


def load() -> dict:
    return json.loads(PROJECTS.read_text(encoding="utf-8"))


def repo_name(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def read(target: str, path: str) -> str | None:
    local = ROOT.parent / target / path
    if local.is_file():
        return local.read_text(encoding="utf-8", errors="replace")
    url = f"https://raw.githubusercontent.com/{OWNER}/{target}/HEAD/{path}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:  # noqa: S310 - fixed host
            return r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None


def count_entries(text: str, name: str) -> int:
    """Count the keys of a `const NAME: … = { … };` object literal."""
    start = text.find(f"const {name}")
    if start < 0:
        return -1
    end = text.find("\n};", start)
    if end < 0:
        return -1
    return len(re.findall(r"^  [a-z0-9_]+:", text[start:end], re.MULTILINE))


def check_project(p: dict) -> list[str]:
    name = p["name"]
    if not p.get("claim"):
        return [f"{name}: no claim"]
    if not p.get("claim_source"):
        return [f"{name}: claim has no claim_source"]
    target = repo_name(p["repo"])
    problems = []
    for c in p["claim_source"]:
        text = read(target, c["file"])
        if text is None:
            problems.append(f"{name}: cannot read {target}/{c['file']}")
            continue
        if "count" in c:
            claimed = re.search(r"(\d+) providers", p["claim"])
            actual = count_entries(text, c["count"])
            if actual < 0:
                problems.append(f"{name}: {c['count']} not found in {c['file']}")
            elif not claimed:
                problems.append(f"{name}: claim states no provider count")
            elif int(claimed.group(1)) != actual:
                problems.append(f"{name}: claim says {claimed.group(1)} providers, {c['file']} has {actual}")
            continue
        missing = [s for s in c.get("any", []) if s not in text]
        if missing:
            problems.append(f"{name}: {target}/{c['file']} lacks {missing!r}")
    return problems


def head_ok(url: str, budget: float) -> tuple[bool, str, bool]:
    """Fetch the URL and decide whether it answered inside `budget` seconds (one retry)."""
    import time

    last, elapsed, slow = "", 0.0, False
    for _ in range(2):
        req = urllib.request.Request(url, headers={"User-Agent": "check_claims/1"})
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=budget) as r:  # noqa: S310 - data URLs
                elapsed = time.monotonic() - t0
                slow = elapsed > budget
                return r.status == 200 and not slow, f"{r.status} in {elapsed:.1f}s", slow
        except urllib.error.HTTPError as e:
            return False, str(e.code), False
        except (urllib.error.URLError, TimeoutError) as e:
            last = repr(e)
    return False, last, True


LIVE_BUDGET = 10.0       # every live URL must answer inside 10 s
COLD_START_BUDGET = 120.0  # a free-tier app that sleeps: measured 45.8 s on Render


def budget_for(p: dict) -> float:
    """10 s is the contract; a documented free-tier app that sleeps gets the cold-start budget."""
    return COLD_START_BUDGET if p.get("cold_start") else LIVE_BUDGET


def check_source(p: dict) -> list[str]:
    """Every claim carries a machine-checkable source."""
    name = p["name"]
    srcs = p.get("claim_source")
    if not srcs:
        return [f"{name}: no claim_source"]
    problems = []
    for c in srcs:
        if not c.get("file"):
            problems.append(f"{name}: a claim_source entry has no file")
        elif not (c.get("any") or c.get("count")):
            problems.append(f"{name}: claim_source {c['file']} has neither any[] nor count")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--links", action="store_true", help="also fetch every live URL")
    args = ap.parse_args()

    data = load()
    problems = []
    for p in data["projects"]:
        problems += check_project(p)
        problems += check_source(p)
    for link in data["profile"]["links"]:
        url = link["url"]
        if not url.startswith(("http://", "https://", "mailto:")):
            problems.append(f"profile link {link['label']}: {url!r} is not a destination")
        if not link.get("alt"):
            problems.append(f"profile link {link['label']}: no alt text")

    if args.links:
        for p in data["projects"]:
            if not p.get("live"):
                continue
            budget = budget_for(p)
            ok, detail, _ = head_ok(p["live"], budget)
            print(f"{'ok  ' if ok else 'FAIL'} live  {p['name']:16} {detail:>14}  {p['live']}")
            if not ok:
                problems.append(f"{p['name']}: live URL {p['live']} -> {detail} (budget {budget:.0f}s)")

    for p in problems:
        print(f"FAIL {p}")
    print(f"{len(data['projects'])} projects, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
