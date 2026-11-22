# Review

Who reviews this page, how often, and what the last pass found. The date in the
table below is what `scripts/check_page.py` reads: a review older than 100 days is a
failure, so "I will get to it" cannot pass CI.

- **Owner:** Yash Vaibhav Awasthi (sole maintainer of this repository).
- **Cadence:** quarterly — January, April, July and October, the same months as the
  [claim audit](AUDIT.md) workflow (`0 7 1 */3 *`). The next scheduled run is
  **2027-01-01**.
- **Time:** about 30 minutes: three commands, then read what they print.

## What a reviewer does

1. `python3 scripts/pin_claims.py --check` — every claim still sits on the line it cites.
2. `python3 scripts/check_claims.py --links` — every snippet and every live URL still answers.
3. `python3 scripts/audit_claims.py --links --fail-on-stale` — the table: number, live
   link, licence, last commit date; anything stale is archived or dropped.
4. Look at the page on a phone and on a desktop, light and dark:
   `python3 scripts/shoot_profile.py --out docs/screenshots/review-YYYY-MM-DD`.
5. Confirm the city matches the contribution calendar, and that the caption under it
   states the same total as the image (`python3 scripts/check_page.py` does this).
6. Record the pass in the table below: date, reviewer, what changed, what was left.

How to make each of those changes — a claim, a project, an archive entry, a
re-render — is in [the handover page](HANDOVER.md).

Anything that needs a decision rather than an edit — a project to retire, a claim to
soften, a licence to add in another repository — is written down here and in
`plan.md` under `needs-verify`, not left in the reviewer's head.

## Passes

| Date | Reviewer | Result | Notes |
|:--|:--|:--|:--|
| 2026-11-24 | Yash Vaibhav Awasthi | pass | First recorded pass. 20 claims pinned to file+line, 11 projects audited with 0 stale (oldest push 33 days), 3 live demos answering (Nexus 45.8 s cold start, within its 120 s exemption). Page checked at 360/768/1440 in light and dark. Left open: five repositories carry no licence (AdapFit, CaseFiles, RISC-VInjection, sign-setu, ToolkitArchive) — recorded as `needs-verify`. |

## Escalation

- A live demo that stops answering is removed from its claim within one review; the
  project stays in the table only if the claim describes work, not availability.
- A disputed claim is answered by the `claim_source` line, not by argument: if the
  pinned line no longer supports the sentence, the sentence changes that day.
- A generator bug that changes the rendering is a version bump (`docs/CHANGELOG.md`),
  not an edit in place, so the images on disk keep naming the release that drew them.
