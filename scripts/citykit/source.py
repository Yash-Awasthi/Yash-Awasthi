"""Where the numbers come from: fetch the calendar, and refuse anything doubtful."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import date


QUERY = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
weeks{contributionDays{date contributionCount}}}}}}"""


class FetchError(RuntimeError):
    """The contribution calendar could not be trusted, so nothing is rendered."""


def fetch(user, token):
    """Return the calendar's weeks, or raise FetchError rather than render a bad year."""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"u": user}}).encode(),
        headers={"Authorization": f"bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status, body = r.status, r.read()
    except urllib.error.HTTPError as e:
        raise FetchError(f"GraphQL HTTP {e.code} {e.reason}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise FetchError(f"GraphQL unreachable: {e}") from e
    if status != 200:
        raise FetchError(f"GraphQL HTTP {status}")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        raise FetchError(f"GraphQL response is not JSON: {e}") from e
    return parse_calendar(payload)


def parse_calendar(payload):
    """Weeks of (date, count) from a GraphQL payload; any doubt is a failure, not a blank city."""
    if payload.get("errors"):
        raise FetchError(f"GraphQL errors: {json.dumps(payload['errors'])[:300]}")
    try:
        cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        weeks = [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]]
                 for w in cal["weeks"]]
    except (KeyError, TypeError) as e:
        raise FetchError(f"unexpected GraphQL payload: missing {e}") from e
    if not weeks or not any(n for w in weeks for _, n in w):
        raise FetchError("contribution calendar is empty; keeping the previous assets")
    return weeks


def filter_year(weeks, year):
    """Keep only the days of `year`; a week that loses every day is dropped."""
    kept = []
    for w in weeks:
        days = [(d, n) for d, n in w if date.fromisoformat(d).year == year]
        if days:
            kept.append(days)
    if not any(n for w in kept for _, n in w):
        raise FetchError(f"no contributions recorded in {year}")
    return kept
