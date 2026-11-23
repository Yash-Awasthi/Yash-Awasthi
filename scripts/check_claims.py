#!/usr/bin/env python3
"""Check every project row of README.md against the repository it describes.

Each row is a claim. This script holds the source of that claim — a file in the
target repository and a snippet that must appear in it — and exits non-zero when
a row and its repository disagree, so a drifting claim fails instead of shipping.

    python3 scripts/check_claims.py            # snippets only, no network
    python3 scripts/check_claims.py --links    # also HEAD every live URL

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
OWNER = "Yash-Awasthi"

# row name -> checks against the repository named in the row's link.
#   {"file": path in the target repo, "any": [snippets that must appear]}
#   {"file": path, "count": "DRIVER_FACTORIES"}, parsed against the row's "N providers"
CLAIMS: dict[str, dict] = {
    "Nexus": {
        "checks": [
            {"file": "apps/api/src/lib/provider-keys.ts", "count": "DRIVER_FACTORIES"},
            {"file": "README.md", "any": ["Council deliberation"]},
            {"file": "docs/FEATURES.md", "any": ["pgvector", "BM25"]},
        ]
    },
    "FinScrape": {
        "checks": [
            {"file": "README.md", "any": ["Laya (a small fine-tuned classifier)"]},
            {"file": "README.md", "any": ["$0%2Fmonth"]},
        ]
    },
    "AdapFit": {
        "checks": [
            {"file": "README.md", "any": ["personal baseline"]},
            {"file": "backend/app/services/daily_decision.py",
             "any": ["TRAIN", "REDUCE", "RECOVER", "REST"]},
        ]
    },
    "PocketDesk": {
        "checks": [
            {"file": "README.md", "any": ["60 fps"]},
            {"file": "README.md", "any": ["certificate pinning"]},
        ]
    },
    "KeyRouter": {
        "checks": [
            {"file": "README.md", "any": ["sk-gw-"]},
            {"file": "README.md", "any": ["Anthropic"]},
        ]
    },
    "CaseFiles": {
        "checks": [
            {"file": "README.md", "any": ["thirty sequential challenges"]},
            {"file": "README.md", "any": ["traced back to their owner"]},
        ]
    },
    "Ping": {
        "checks": [
            {"file": "README.md", "any": ["PAKE", "AES-256-GCM", "BLE"]},
        ]
    },
    "LobIQ": {
        "checks": [
            {"file": "README.md", "any": ["C++23", "TotalView-ITCH", "Polymarket"]},
        ]
    },
    "RISC-VInjection": {
        "checks": [
            {"file": "README.md", "any": ["binutils", "GCC"]},
            {"file": "docs/recognizer.md", "any": ["GIMPLE"]},
        ]
    },
}

ROW = re.compile(r"^\|\s*\[\*\*(?P<name>[^*]+)\*\*\]\((?P<url>https://github\.com/[^)]+)\)")
LIVE = re.compile(r"\[Live\]\((?P<url>[^)]+)\)")


def rows(readme: str) -> dict[str, dict]:
    found = {}
    for line in readme.splitlines():
        m = ROW.match(line)
        if not m:
            continue
        live = LIVE.search(line)
        found[m.group("name")] = {"url": m.group("url"), "live": live.group("url") if live else None}
    return found


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
    block = text[start:end]
    return len(re.findall(r"^  [a-z0-9_]+:", block, re.MULTILINE))


def check(name: str, row: dict, text_of) -> list[str]:
    problems = []
    spec = CLAIMS[name]
    for c in spec["checks"]:
        text = text_of(c["file"])
        if text is None:
            problems.append(f"{name}: cannot read {c['file']}")
            continue
        if "count" in c:
            claimed = re.search(r"(\d+) providers", row["line"])
            actual = count_entries(text, c["count"])
            if actual < 0:
                problems.append(f"{name}: {c['count']} not found in {c['file']}")
            elif not claimed:
                problems.append(f"{name}: row states no provider count")
            elif int(claimed.group(1)) != actual:
                problems.append(f"{name}: row claims {claimed.group(1)} providers, {c['file']} has {actual}")
            continue
        missing = [s for s in c["any"] if s not in text]
        if missing:
            problems.append(f"{name}: {c['file']} lacks {missing!r}")
    return problems


def head_ok(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "check_claims/1"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 - row URLs
            return r.status == 200, str(r.status)
    except urllib.error.HTTPError as e:
        return False, str(e.code)
    except (urllib.error.URLError, TimeoutError) as e:
        return False, repr(e)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--links", action="store_true", help="also fetch every live URL")
    args = ap.parse_args()

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    found = rows(readme)

    for name, row in found.items():
        row["line"] = next(ln for ln in readme.splitlines() if f"[**{name}**](" in ln)

    problems: list[str] = []
    for name in sorted(set(found) | set(CLAIMS)):
        if name not in found:
            problems.append(f"{name}: expected row missing from README.md")
        elif name not in CLAIMS:
            problems.append(f"{name}: row has no claim source in scripts/check_claims.py")
        else:
            target = found[name]["url"].rstrip("/").rsplit("/", 1)[-1]
            cache: dict[str, str | None] = {}

            def text_of(path: str, target=target, cache=cache) -> str | None:
                if path not in cache:
                    cache[path] = read(target, path)
                return cache[path]

            problems += check(name, found[name], text_of)

    if args.links:
        for name, row in sorted(found.items()):
            if not row["live"]:
                continue
            ok, status = head_ok(row["live"])
            print(f"{'ok  ' if ok else 'FAIL'} live  {name:16} {status:>6}  {row['live']}")
            if not ok:
                problems.append(f"{name}: live URL {row['live']} -> {status}")

    for p in problems:
        print(f"FAIL {p}")
    print(f"{len(found)} rows, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
