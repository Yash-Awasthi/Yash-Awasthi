#!/usr/bin/env python3
"""Keep the README's "Now" line current from the repository I last pushed to.

    python3 scripts/gen_now.py --write   # refresh now.json from the GitHub API
    python3 scripts/gen_now.py --check   # exit 1 if now.json is missing or stale

The API call is public (a token is used when `GITHUB_TOKEN` is set, which raises the
rate limit). `gen_readme.py` renders the README block from `now.json`, so the page is
never hand-edited and CI can verify it offline.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOW = ROOT / "now.json"
STALE_DAYS = 30


def load() -> dict:
    return json.loads(NOW.read_text(encoding="utf-8"))


def fetch_repos(user: str) -> list[dict]:
    url = f"https://api.github.com/users/{user}/repos?per_page=100&sort=pushed&direction=desc"
    req = urllib.request.Request(url, headers={"User-Agent": "gen_now/1",
                                              "Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 - fixed host
            return json.loads(r.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        raise SystemExit(f"gen_now.py: cannot read {url}: {e}")


def pick(repos: list[dict], user: str) -> dict:
    """The most recently pushed repository that is mine and is not this profile page."""
    for repo in repos:
        if repo.get("fork") or repo.get("archived"):
            continue
        if repo["name"].lower() == user.lower():
            continue
        return repo
    raise SystemExit("gen_now.py: no eligible repository")


def record(repo: dict, user: str, today: str) -> dict:
    return {
        "user": user,
        "repo": repo["name"],
        "url": repo["html_url"],
        "description": (repo.get("description") or "").strip(),
        "language": (repo.get("language") or "").strip(),
        "pushed_at": (repo.get("pushed_at") or "")[:10],
        "fetched_at": today,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="refresh now.json")
    group.add_argument("--check", action="store_true", help="exit 1 if now.json is missing or stale")
    ap.add_argument("--user", default="Yash-Awasthi", help="GitHub login (default: Yash-Awasthi)")
    args = ap.parse_args()

    if args.check:
        if not NOW.exists():
            print("FAIL now.json is missing; run python3 scripts/gen_now.py --write")
            return 1
        data = load()
        missing = [k for k in ("repo", "url", "pushed_at", "fetched_at") if not data.get(k)]
        age = (date.today() - date.fromisoformat(data["fetched_at"])).days if data.get("fetched_at") else 10 ** 6
        if missing:
            print(f"FAIL now.json is missing {missing}")
            return 1
        if age > STALE_DAYS:
            print(f"FAIL now.json was fetched {age} days ago (budget {STALE_DAYS}); the daily job should refresh it")
            return 1
        print(f"ok   now   {data['repo']} pushed {data['pushed_at']}, snapshot {age} day(s) old")
        return 0

    today = datetime.now(timezone.utc).date().isoformat()
    data = record(pick(fetch_repos(args.user), args.user), args.user, today)
    NOW.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote now.json: {data['repo']} pushed {data['pushed_at']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
