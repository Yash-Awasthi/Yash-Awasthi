# Security policy

This repository is a public GitHub profile: a README, a contribution-city
generator (`.github/city.py`), its committed SVG output, and the CI that guards
them. There is no server, no user data and no deployment of its own.

## Reporting a problem

Email **<yashvaibhav.job@gmail.com>** with the subject line `security: Yash-Awasthi`
and include the file or URL, what goes wrong, and the steps to reproduce.

Do not open a public issue for a security report.

## What is in scope

- `.github/city.py` and `scripts/citykit/` — the generator behind it (source,
  layout, theme, draw, assets). Anything that could make it write outside its
  output directory, follow a redirect to an unexpected host, or render untrusted
  strings into the SVG.
- `.github/workflows/*.yml` — anything that could run untrusted code with
  `contents: write`, or push to `master` without the checks passing.
- `scripts/*.py` — the CI checks themselves; a check that silently passes is a bug.
- The published assets — an SVG that embeds a script, an external `href` or an
  `<image>` reference.

## What is out of scope

- The projects linked from the README. Report those in their own repositories.
- Third-party hosts the page embeds or links (GitHub, shields.io, skillicons.dev,
  Vercel, Render, Cloudflare Pages, GitHub Pages); see `docs/DEPENDENCIES.md`.
- Anything that needs the owner's credentials or physical access.
- Reports produced only by an automated scanner with no working example.

## What to expect

| Stage | Window |
|---|---|
| Acknowledgement that the report arrived | 3 business days |
| First assessment (in scope, severity, plan) | 7 business days |
| Fix for a confirmed issue in scope | 30 days, or a public note saying why not |

There is no bug bounty and no monetary reward. If you want credit, say how you
would like to be named in the commit message and in this file's history.

## Supported versions

Only `master` is supported; the profile and its assets are regenerated from it
daily by `.github/workflows/contrib-city.yml`.

## Good practice already in place

- Every GitHub Action is pinned to a commit SHA with a version comment.
- Workflows default to `permissions: contents: read`; only the asset job asks for
  `contents: write`, and it refuses to push if the branch moved.
- Generated SVGs are asserted inert (no `<script>`, no `<foreignObject>`, no
  external `href`) by `scripts/check_page.py`.
- No personal data beyond the public email, city and employers; enforced by
  `scripts/check_privacy.py` and described in `docs/PRIVACY.md`.
