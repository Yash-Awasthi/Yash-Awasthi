#!/usr/bin/env python3
"""Fetch every external URL the README points at and fail on a broken one.

This is the network half of the CI guard (scripts/check_claims.py is the offline
half). It runs on the weekly schedule, not on every push.

    python3 scripts/check_links.py

Hosts that refuse non-browser clients (LinkedIn answers `999`) are reported as
`blocked` and do not fail the run; every other non-2xx/3xx does.
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
TIMEOUT = 60
BOT_WALLED = ("linkedin.com",)
UA = "Mozilla/5.0 (compatible; profile-link-check/1)"


def urls(readme: str) -> list[str]:
    import re

    found = re.findall(r'(?:href|src)="(https?://[^"]+)"', readme)
    found += re.findall(r'srcset="(https?://[^"]+)"', readme)
    found += re.findall(r"\]\((https?://[^)]+)\)", readme)
    return sorted(dict.fromkeys(found))


def fetch(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # noqa: S310 - README URLs
            return r.status < 400, str(r.status)
    except urllib.error.HTTPError as e:
        blocked = e.code in (403, 429, 999) and any(h in url for h in BOT_WALLED)
        return blocked, f"{e.code} (bot wall)" if blocked else str(e.code)
    except (urllib.error.URLError, TimeoutError) as e:
        return False, repr(e)


def main() -> int:
    readme = README.read_text(encoding="utf-8")
    problems = []
    for url in urls(readme):
        ok, status = fetch(url)
        print(f"{'ok  ' if ok else 'FAIL'} {status:>14}  {url}")
        if not ok:
            problems.append(f"{url} -> {status}")
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
