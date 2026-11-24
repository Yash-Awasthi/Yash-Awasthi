"""The numbers the picture is made of, stated in words so the drawing has a text twin."""
from __future__ import annotations

from datetime import date, timedelta


MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def stats(weeks):
    """Total, longest streak and busiest month for the same calendar the city draws."""
    days = sorted((d, n) for w in weeks for d, n in w)
    total = sum(n for _, n in days)
    best, run, best_end = 0, 0, None
    prev = None
    for d, n in days:
        step = date.fromisoformat(d)
        if n and prev is not None and (step - prev).days == 1:
            run += 1
        elif n:
            run = 1
        else:
            run = 0
        if run > best:
            best, best_end = run, step
        prev = step
    months = {}
    for d, n in days:
        months[d[:7]] = months.get(d[:7], 0) + n
    month, peak = max(months.items(), key=lambda kv: kv[1])
    return {
        "total": total,
        "first": days[0][0],
        "last": days[-1][0],
        "weeks": len(weeks),
        "peak_day": max(days, key=lambda dn: dn[1]),
        "streak": best,
        "streak_end": best_end.isoformat() if best_end else None,
        "best_month": month,
        "best_month_count": peak,
        "active_days": sum(1 for _, n in days if n),
    }


def caption(s):
    """One line under the image: the same facts the towers and rivers carry."""
    month = f"{MONTHS[int(s['best_month'][5:]) - 1]} {s['best_month'][:4]}"
    streak = f"{s['streak']} days to {s['streak_end']}" if s["streak"] else "no streak"
    return (f"{s['total']:,} contributions on {s['active_days']} active days, "
            f"{s['first']} to {s['last']} · longest streak {streak} · "
            f"busiest month {month} ({s['best_month_count']:,})")
