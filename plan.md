# plan.md — Yash-Awasthi (profile repository)

Consolidated plan for the GitHub profile repository. There was no prior plan
file; this replaces the implicit backlog in the README and in
`.github/city.py` comments. Scope is deliberately narrow: the artefact is a
41-line README plus one generator and two SVG assets. The work is therefore
**claim integrity, build determinism and reader-facing craft**, not features.

Generated 2026-11-24. Evidence base: `README.md` (41 lines), `assets/city-dark.svg`
(143 KB), `assets/city-light.svg` (129 KB), `.github/city.py` (267 lines),
`.github/workflows/contrib-city.yml`, and cross-checks against the README of
Nexus, FinScrape, AdapFit, PocketDesk, KeyRouter, CaseFiles, Ping, LobIQ and
RISC-VInjection.

**Order:** corrective → preventive → perfective → widening → depth → enterprise.

**Hierarchy:** Phase → Major (M#.#) → Minor (m#.#.#) → Subtask. One subtask = one

**Done tasks stay.** A finished subtask becomes `- [x]` in place with one evidence line under it (`verified-here: <command> → <result>`). Nothing is ever removed from this list.
PR = one command that proves it.

**Tag (exactly one):** `[C]` corrective · `[P]` preventive · `[F]` perfective ·
`[W]` widening · `[D]` depth · `[E]` enterprise.

**Method anchors:** `writing-docs` §1 (every claim has a source), `design-ux`
§1/§5 (first screen, hierarchy, accessibility), `devops-cloud` §8 (pinned,
reproducible automation), `data-ml` §8 (measured numbers only),
`security-operations` §5 (third-party images and unpinned actions).

---

## 0. Verified ground truth

| Fact | Measured | Claimed | Source |
|---|---|---|---|
| README size | 49 lines | — | `wc -l` |
| Sections | header image, 4 badge links, 1 para, experience (2 roles), project table (9 projects), stack icons, certifications, city image | — | `README.md` |
| Live links | portfolio, LinkedIn, resume PDF, email, 3 live demos (Nexus, FinScrape, LobIQ) | all present | `README.md:3-26` |
| Generated assets | 2 SVGs, 272 KB total, regenerated daily | — | `assets/`, workflow `cron: 0 0 * * *` |
| Generator | `.github/city.py`, 267 lines, stdlib only, GitHub GraphQL | — | `city.py:1-35` |
| Workflow actions | `actions/checkout@11d5960a…` pinned by SHA with `# v4.4.0` (was `@v4`), `contents: write`, cron + manual | — | `contrib-city.yml` |
| Bot commits | daily commit to `assets/` when the diff is non-empty | — | `contrib-city.yml:24-27` |
| External images | capsule-render, shields.io ×4, skillicons.dev, raw.githubusercontent | 6 third-party hosts | `README.md` |
| Provider count | profile says "17 providers"; `Nexus/apps/api/src/lib/provider-keys.ts` `DRIVER_FACTORIES` names **39 providers** a key can be added for (`packages/llm/src/drivers/index.ts` defines 43 driver classes, 4 of them local/self-hosted entry points) | "17 providers" | `awk '/^const DRIVER_FACTORIES/,/^};/' Nexus/apps/api/src/lib/provider-keys.ts \| grep -cE '^  [a-z0-9_]+:'` → 39 |
| FinScrape claim | profile says "LoRA-tuned ModernBERT" | ModernBERT appears nowhere in FinScrape's tree; `docs/BACKFILL.md:82` says "No LoRA was published"; the classifier is Laya (`scripts/laya_train/train.py`, base `convaiinnovations/laya`) | `README.md:23`, `FinScrape/README.md` |
| Alt text | present on header, stack icons, city image, and on all 4 badge links (`![Portfolio](…)` etc. — the badge alt is the label) | — | `README.md:3-5` |

Invariants:

1. **Every claim is verifiable in one click.** A number in this README must match the repository it describes, or it is removed.
2. **No private data.** No phone number, no address, no employer-only links, no API keys; the public email is the contact.
3. **The city asset is generated, never hand-edited.** `assets/*.svg` are outputs of `city.py`.
4. **The daily job must not fail silently.** A missed run leaves a stale image with no signal today.
5. **Accessibility is not optional.** Every image has an `alt`; colour is not the only carrier of meaning; the page is readable with images blocked.

---

## Phase 1 — Corrective

### M1.1 Claim integrity across the nine projects

**Why:** the profile is the entry point to every repository, and two claims do
not match their own READMEs ("17 providers" vs eight named and "and more";
"LoRA-tuned ModernBERT" absent from FinScrape's README). A reader who checks
once stops trusting the rest.
**Done when:** every project line can be checked against that project's README in
under a minute, and a mismatch fails a check.

- [x] Rewrite each project row to one verifiable sentence, quoting the number only where the project's own README states it. `[C]`
  - verified-here: `grep -nE 'KeyRouter|Ping' README.md` → KeyRouter row now says "OpenAI- or Anthropic-style" and expiring `sk-gw-` keys (KeyRouter/README.md:3,5); Ping row now says gesture-keyed PAKE on P-256 + AES-256-GCM over BLE (Ping/README.md:45,152,156), replacing the narrower "ECDH" wording. The other 7 rows matched their repository README as written.
- [x] Nexus row: replace "17 providers" with the number the Nexus README or code supports, or drop the count. `[C]`
  - verified-here: `awk '/^const DRIVER_FACTORIES/,/^};/' Nexus/apps/api/src/lib/provider-keys.ts \| grep -cE '^  [a-z0-9_]+:'` → 39; the README row now reads "39 providers behind one streaming API". The plan's earlier "9 distinct providers" figure was a partial grep and is corrected in §0.
- [x] FinScrape row: confirm the LoRA/ModernBERT claim in FinScrape's tree; if unverified, remove it. `[C]`
  - verified-here: `grep -rniE "modernbert" --exclude-dir=.venv FinScrape` → no match anywhere in the tree; `FinScrape/docs/BACKFILL.md:82` says "No LoRA was published". Row now says "Laya (a small fine-tuned classifier), the LLM and keywords" (`FinScrape/README.md:33`) and keeps `$0/month` (`FinScrape/README.md:8`).
- [x] Verify each live link returns 200 and serves the expected product (Nexus, FinScrape, LobIQ, portfolio, resume PDF). `[C]`
  - verified-here: `for u in <5 urls>; do curl -s -o /dev/null -w "%{http_code}" -m 25 -L "$u"; done` → portfolio 200, resume PDF 200 (`application/pdf`, 58,916 B), winfin.pages.dev 200 (`<title>FinScrape — See what moves markets…`), yash-awasthi.github.io/LobIQ/ 200 (`<title>LobIQ demo reports`), nexus-iosc.onrender.com 200 after **45.8 s** cold start (Render free tier; SPA, no `<title>`, `apple-mobile-web-app-title` = Nexus). LinkedIn returns 999 to `curl` (bot wall, not a 404) → needs-verify: 2026-11-23 li-at-909a62293 | M4.2 needs the Nexus cold-start note.
- [x] Add `scripts/check_claims.py`: for each row, the expected snippet in the target repo's README; non-zero exit on drift. `[C]`
  - verified-here: `python3 scripts/check_claims.py` → `9 rows, 0 problem(s)` exit 0; with the Nexus row edited to "42 providers" → `FAIL Nexus: row claims 42 providers, apps/api/src/lib/provider-keys.ts has 39`, exit 1. Sibling checkouts are used when present, else `raw.githubusercontent.com/.../HEAD/<path>` (fallback proven by re-pointing `ROOT` at `scripts/`). Local interpreter on this box is `FinScrape/.venv/Scripts/python.exe` (3.14.8): no `python`/`python3` is on PATH.

### M1.2 Fix the broken or unverifiable presentation bits

- [x] Every badge link gets `alt` text that says where it goes; today the icons are decorative URLs. `[C]`
  - verified-here: `grep -oE '!\[[^]]*\]' README.md` → `![Portfolio — yash-portfolio-nine-navy.vercel.app]`, `![LinkedIn — linkedin.com/in/yash-vaibhav-awasthi]`, `![Resume — PDF on the portfolio site]`, `![Email — yashvaibhav.job@gmail.com]`. Plan corrected: the badges did already carry short alt text (`![Portfolio](…)`) — Appendix C's "badges carry no alt" was wrong; the gap was that the alt named the label, not the destination.
- [x] The header uses a third-party renderer with a URL-encoded name and no fallback; add a plain `<h1>`-equivalent text line so the page degrades if capsule-render is down. `[C]`
  - verified-here: `head -8 README.md` → the banner is now decorative (`alt="Gradient banner"`) and is followed by real text `# Yash Vaibhav Awasthi` and the tagline `Software engineer · backends, AI systems, mobile apps`; with images blocked the name and tagline still render. `wc -l < README.md` → 45 (was 41).
- [x] `skillicons.dev` and `shields.io` are single points of failure; state the fallback (a text list) and use it in `alt`. `[C]`
  - verified-here: `sed -n '/### Stack/,/<picture>/p' README.md` → a visible `**Stack:** TypeScript · Python · … · Three.js` line (14 names, same order as the `?i=` list) now precedes the icon strip, which is marked decorative with `alt=""`.
  - deviation: the stack list is adjacent visible text rather than stuffed into the image `alt`, so a screen reader announces the stack once instead of twice. Badges keep destination-bearing alt (m1.2.1); their label text is still readable with images blocked because the link text is the badge. Host-down behaviour is recorded in m2.3.1.
- [x] The city `<picture>` points at `master` on `raw.githubusercontent`; confirm the default branch name and add the matching repo-relative path. `[C]`
  - verified-here: `curl -s https://api.github.com/repos/Yash-Awasthi/Yash-Awasthi | grep default_branch` → `master`; `curl -sL https://github.com/Yash-Awasthi | grep -oE 'srcset="[^"]*city-dark[^"]*"'` → `https://raw.githubusercontent.com/Yash-Awasthi/Yash-Awasthi/master/assets/city-dark.svg` (the branch in the README is the one GitHub resolves).
  - deviation: no repo-relative path added — a profile README resolves relative URLs against `github.com/<user>/`, and `curl -o /dev/null -w '%{http_code}' https://github.com/Yash-Awasthi/assets/city-light.svg` → **404**, while the raw URL → 200. The absolute `raw.githubusercontent.com/.../master/...` form stays, so a default-branch rename is caught by the m1.1 link check and m2.1 CI, not by a silent 404.

### M1.3 Pin the automation

- [x] `actions/checkout@v4` → commit SHA with a `# v4.x.y` comment. `[C]`
  - verified-here: `grep -nE 'uses:' .github/workflows/contrib-city.yml` → `actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0`; the SHA is the tag commit per `curl -s https://api.github.com/repos/actions/checkout/git/refs/tags/v4.4.0 | grep sha`.
- [x] Replace the hand-rolled commit step with `git commit -m ...` plus `git push` guarded on `git diff --cached --quiet` (already) and add `--force-with-lease`-free safety: fail if the branch moved. `[C]`
  - verified-here: the Commit step now exits 0 on an unchanged `assets/`, commits otherwise, and compares `HEAD~1` with a freshly fetched `origin/$GITHUB_REF_NAME` before `::error::` + exit 1. Rehearsed in a scratch bare repo (`/tmp/gtest`): unchanged → CASE1 exit 0; a second clone pushed first → CASE2 `git rev-parse HEAD~1` `bdafac1…` ≠ `origin/master` `3172dc2…` → guard fires; no competing push → CASE3 parent matches, push succeeds. Workflow still parses (`yaml.safe_load` → jobs: ['generate']).
- [x] Add `permissions: contents: write` only on the job that needs it, and `actions: read` elsewhere. `[C]`
  - verified-here: `python3 -c "import yaml; …"` over the workflow → workflow-level `{'contents': 'read'}`, job `generate` `{'contents': 'write'}`, `jobs: ['generate']`. Nothing else needs `actions: read` today; the read default is what a future `check` job (m2.1) inherits.
- [x] Add `timeout-minutes` and a `concurrency` group so a manual run cannot race the cron. `[C]`
  - verified-here: `yaml.safe_load` → `concurrency: {'group': 'contrib-city', 'cancel-in-progress': True}`, `timeout-minutes: 10` (timeout was already there; the race was the missing concurrency group).

### M1.4 The generator has no failure path

**Why:** `city.py` calls the GraphQL API with `urllib` and writes both SVGs. On a
rate limit, an auth failure or a partial response, today's behaviour decides
whether the committed image is stale, empty, or mangled.
**Done when:** a failed fetch leaves the previous asset untouched and the job goes red.

- [x] Treat any non-200, `errors` payload or empty calendar as a failure: exit non-zero, write nothing. `[C]`
  - verified-here: `python3 -m unittest discover -s tests` → `Ran 7 tests … OK` (6 of them error against the old `fetch`: `FAILED (errors=6)` with the change stashed); end to end `GITHUB_TOKEN=not-a-real-token python3 .github/city.py Yash-Awasthi` → `city.py: GraphQL HTTP 401 Unauthorized (assets left untouched)`, exit 1, `sha1sum -c` → both SVGs `OK`.
- [x] Write to a temp path and `os.replace` both files only after both render successfully, so a crash cannot leave one theme updated and the other stale. `[C]`
  - verified-here: `python3 -m unittest discover -s tests` → `Ran 10 tests … OK` (the 3 `WriteTest` cases error against the old inline write: `FAILED (errors=3)` with the change stashed). `write_assets` renders both themes into memory, stages each through `tempfile.mkstemp(dir=assets)` and only then `os.replace`es both; a render that raises on the second theme leaves both files byte-identical, and no `.city-*` temp survives.
- [x] Log the contribution total and the date range rendered, so a silently empty year is visible in the job log. `[C]`
  - verified-here: `python3 -m unittest discover -s tests` → `Ran 11 tests … OK` (the `SummaryTest` case errors without it); `city.summary([[('2026-11-01',2),('2026-11-02',0)],[('2026-11-03',5)]])` → `7 contributions, 2026-11-01 to 2026-11-03, 2 weeks`, which `__main__` prints as `city.py: <summary>` before any file is written, so a zero/low year shows in the job log.
- [x] Add `--year` and `--out` flags so the script can be run locally without touching `assets/`. `[C]`
  - verified-here: `python3 -m unittest discover -s tests` → `Ran 14 tests … OK` (3 CLI/year cases error without it); real run `GITHUB_TOKEN=$(gh auth token) python3 .github/city.py Yash-Awasthi --out /tmp/cityout` → `city.py: 3470 contributions, 2025-11-23 to 2026-11-24, 53 weeks`, exit 0, two SVGs in `/tmp/cityout`, `git status --porcelain assets` empty. `--year 2026 --out /tmp/cityout26` → `3470 contributions, 2026-01-01 to 2026-11-24, 48 weeks`, different bytes (`md5 c717bf9a…` vs `fd7c05f2…`): 5 all-2025 empty weeks collapsed into the one leading river, so the width is unchanged at 946 and the 2025 stretch held 0 contributions.

---

## Phase 2 — Preventive

### M2.1 A CI that guards the page

- [x] Workflow `check`: markdown lint, `check_claims.py`, link check on every external URL (with a weekly run for the network ones), and a size budget on `assets/*.svg`. `[P]`
  - verified-here: `npx --yes markdownlint-cli2@0.16.0 "README.md"` → `Summary: 0 error(s)` (`.markdownlint-cli2.jsonc` allows the banner/`<picture>` HTML and long badge URLs; README headings moved to `## Experience`, `## Projects`, `## Stack`, `## Certifications` to clear MD001/MD036); `python3 scripts/check_page.py` → `0 problem(s)` (143,082 B + 129,218 B under a 200,000 B budget); `python3 scripts/check_links.py` → 22 URLs, `0 problem(s)`, LinkedIn reported `999 (bot wall)` rather than failed; with one URL changed to `…/LobIQ/nope-404.html` → `FAIL 404`, exit 1. `.github/workflows/check.yml` parses (`jobs: ['static', 'links']`, workflow `contents: read`, checkout pinned, `links` gated to schedule/dispatch).
- [x] Fail when the README exceeds a line budget (currently 41; a profile page that grows into a résumé loses the reader). `[P]`
  - verified-here: `python3 scripts/check_page.py` → `ok   lines README.md 50 (budget 60)`, `0 problem(s)`; with 15 blank lines appended → `FAIL README.md is 65 lines, over the 60-line budget`, exit 1. (The script counts the unterminated last line, so it reports 50 where `wc -l` reports 49.)
- [x] Fail on a raw `<img>` without `alt`, and on a link without a destination. `[P]`
  - verified-here: `python3 scripts/check_page.py` → `ok   alt   7 images, every link has a destination`, `0 problem(s)`; appending `<img src="…">`, `[nowhere]()` and `![](…)` → three `FAIL` lines and exit 1. An empty `alt=""` is accepted on purpose: the icon strip is decorative because the stack is also written as text (m1.2.3).
- [ ] Verify the two SVG themes declare the same viewBox and dimensions, so dark/light do not jump. `[P]`

### M2.2 Determinism of the city

- [ ] Render the same contribution data twice and assert byte-identical SVG (the script uses `zlib`; confirm no timestamps, no random ids, no dict-order dependence). `[P]`
- [ ] Add a committed fixture JSON (the calendar payload) and a test that renders from it, so the generator is testable without the network. `[P]`
- [ ] Golden-hash the fixture render; a visual change needs an intentional update. `[P]`
- [ ] Assert the SVG contains no `<script>`, no external `href`, and no `<image>` — GitHub sanitises, but a generated asset must not rely on that. `[P]`

### M2.3 Third-party dependency policy

- [ ] List the six external hosts with what breaks if each goes down, in a short `docs/DEPENDENCIES.md`. `[P]`
- [ ] Pin the image URLs' parameters (`theme`, `perline`, sizes) so an upstream default change cannot silently alter the page. `[P]`
- [ ] Replace anything with a self-hosted equivalent where cost is zero (e.g. generate the header locally as a static SVG). `[P]`
- [ ] Check the third-party hosts' terms allow hotlinking from a profile page; record the finding. `[P]`

### M2.4 Privacy and safety

- [ ] Confirm no personal data beyond the public email, city and employer names; add a rule in `docs/` about what never goes on the profile. `[P]`
- [ ] The resume PDF is a live third-party URL; add a check that it exists and that it contains no phone number or address (open it, read the header block). `[P]`
- [ ] Add `SECURITY.md` (contact, no bug bounty, response window) because the profile invites contact. `[P]`

---

## Phase 3 — Perfective

### M3.1 The table becomes data

**Why:** the project table and the badge row are hand-typed, so a link and its label
can diverge and a claim change is a text edit.
**Done when:** both render from one file.

- **m3.1.1 Data**
  - [ ] Move the project table's data to `projects.json` (name, repo, one-line claim, live URL, claim source) and generate the table; a claim change becomes a data edit. `[F]`
  - [ ] Generate the badge row from the same data so a link and its label cannot diverge. `[F]`
- **m3.1.2 Checks**
  - [ ] A check that every `live URL` in `projects.json` answers 200 within 10 s, and that every claim has a `source` field. `[F]`

### M3.2 The city asset

**Why:** the two SVGs are 272 KB combined and carry no accessible text; `city.py`
is 267 lines in one file.
**Done when:** each SVG is under 100 KB with `<title>`/`<desc>`, and the generator is
three modules.

- **m3.2.1 Size and accessibility**
  - [ ] Cut SVG size: target under 100 KB each with path simplification and shared defs. `[F]`
  - [ ] Add `<title>` and `<desc>` to both SVGs so a screen reader announces the year and total, not "image". `[F]`
- **m3.2.2 Generator shape**
  - [ ] Reduce `city.py`'s 267 lines into render, layout and theme modules; the SVG writing stays pure functions over the fixture. `[F]`

### M3.3 Automation hygiene

**Why:** the workflow runs a floating `python3` on a cron that is more frequent than
the data changes.
**Done when:** versions are pinned and the cadence matches the data.

- **m3.3.1 Pinning**
  - [ ] Node/Python versions for the workflow pinned explicitly (no floating `python3`), with the version in `docs/`. `[F]`
- **m3.3.2 Cadence**
  - [ ] Replace the daily cron with a schedule that matches the data's update rate and add `workflow_dispatch` with a `--year` input. `[F]`

---

## Phase 4 — Widening

### M4.1 Freshness without manual edits

**Why:** the page claims to be current but only the city image changes.
**Done when:** the "now" section is generated from a real source.

- **m4.1.1 Now**
  - [ ] Add a "What I am working on now" section, generated from the most recently pushed public repository, so the page stays current without manual edits. `[W]`
- **m4.1.2 Writing**
  - [ ] Add a compact "Selected writing" or "Notes" section only if real posts exist; never placeholder links. `[W]`

### M4.2 Live surfaces

**Why:** three demo links exist and none is checked.
**Done when:** every demo link is verified and its cold-start state is visible.

- **m4.2.1 Demo links**
  - [ ] Add per-project demo links that are checked automatically, and mark any that are cold-starting (Render free tier) with a note. `[W]`
- **m4.2.2 Growth**
  - [ ] Add an "archive" section for older projects, collapsed, so the main table stays short as the portfolio grows. `[W]`
  - [ ] Add a machine-readable `profile.json` (projects, links, stack) so the table, badges and a future personal site all read one source. `[W]`

---

## Phase 5 — Depth

### M5.1 First-screen craft

Method: `design-ux` §1 — the page has one screen above the fold; judge that
screen, not the whole file.

- [ ] Screenshot the rendered profile at 360/768/1440 in light and dark, into `docs/screenshots/before/`. `[D]`
- [ ] Above the fold: name, one sentence, three links. Measure what is actually visible at 360×640 and move anything that pushes the sentence out. `[D]`
- [ ] Type and spacing consistency across sections; no section uses a different heading level for the same weight. `[D]`
- [ ] Table at 360 px: two columns fit; verify no horizontal scroll and that long project names wrap cleanly. `[D]`
- [ ] Colour: the four badge colours and the city theme agree; check contrast of badge text at 4.5:1. `[D]`

### M5.2 The city as a data graphic

- [ ] Every building height maps to a stated quantity (contributions per day) and the legend says so; today the mapping is implicit. `[D]`
- [ ] Add a text alternative with the same information: total contributions, longest streak, busiest month, rendered as one line under the image. `[D]`
- [ ] Colour-blind check on the six levels: the ramp must be distinguishable in the most common deficiency, or a pattern/label added. `[D]`
- [ ] Reduced-motion: if any animation exists in the SVG, gate it behind `prefers-reduced-motion`. `[D]`

### M5.3 Claim audit depth

- [ ] For each of the nine projects, record the exact file and line that supports the profile sentence; store it in `projects.json` as `claim_source`. `[D]`
- [ ] Re-audit quarterly with a checklist: number, live link, licence, last commit date. `[D]`
- [ ] Remove any project that has not been touched in a year and has no live demo, or move it to the archive section with the date. `[D]`

---

## Phase 6 — Enterprise (profile as a maintained artefact)

### M6.1 Cadence and provenance

**Why:** nobody knows when the profile was last reviewed, and a stale SVG cannot be
identified from the file itself.
**Done when:** a review date is recorded and the asset names its generator.

- **m6.1.1 Review cadence**
  - [ ] Ownership and cadence: a quarterly review with a recorded date, and the reviewer checklist in `docs/REVIEW.md`. `[E]`
- **m6.1.2 Generator provenance**
  - [ ] Release discipline for the generator: tags, a changelog, and a note in the job log naming the script commit that produced the current assets. `[E]`
  - [ ] Embedded provenance: the SVG carries a comment with generator version, data range and commit, so a stale image can be identified from the file alone. `[E]`

### M6.2 Failure and accessibility

**Why:** the job can fail silently and accessibility is asserted, not tested.
**Done when:** a failed run is visible and the claim is scoped.

- **m6.2.1 Runbook**
  - [ ] Runbook: cron job failed, GraphQL rate-limited, an external image host is down, a live demo is offline, a claim is disputed. `[E]`
- **m6.2.2 Accessibility statement**
  - [ ] What is verified (alt text, contrast, text alternative) and what is not (screen-reader testing on every platform). `[E]`

### M6.3 Succession

**Why:** the profile only makes sense with the owner's memory.
**Done when:** someone else can update it from the files.

- **m6.3.1 Handover**
  - [ ] The README, `projects.json` and the scripts are enough for someone else to update the profile without the owner's memory. `[E]`

---

## 7. Execution model: waves, effort, exit gates

Effort: **S** ≤ 1 day, **M** 2–3 days.

| Wave | Days | Objective | Majors | Effort | Gate |
|---|---|---|---|---|---|
| **W0** | 1–2 | Claim integrity, links, pinned automation, a failure path | M1.1–M1.4 | M+S+S+S | every claim names its source; no external link 404s; the workflow pins its actions by SHA; a failed run opens an issue or fails loudly |
| **W1** | 2–3 | CI, determinism, third-party policy, privacy | M2.1–M2.4 | M+S+S+S | CI regenerates the assets and diffs them; `city.py` is deterministic from a fixture; the host list is documented |
| **W2** | 3–4 | Data-driven table, city size/accessibility, automation hygiene | M3.1–M3.3 | M+M+S | `projects.json` is the only source; each SVG < 100 KB with title/desc; versions pinned |
| **W3** | 4–5 | Freshness, live surfaces, machine-readable profile | M4.1–M4.2 | M+S | demo links checked automatically; `profile.json` exists |
| **W4** | 5–6 | First-screen craft, city as a data graphic, claim depth | M5.1–M5.3 | M+M+S | each claim has a click-path a stranger can follow |
| **W5** | quarter | Cadence, provenance, runbook, succession | M6.1–M6.3 | S×3 | a stale asset identifies itself; a second person updates it |

Wave rules: W0 is one afternoon of work and removes the only claims that could be
called wrong. W1's determinism test is what makes W2's generator split safe.

---

## 8. Dependencies and the critical path

```
M1.1 (claims)        → M5.3 (claim depth)
M1.3 (pinned actions)→ M2.1 (CI guard)         → M3.3 (hygiene)
M1.4 (failure path)  → M6.2 (runbook)
M2.2 (determinism)   → M3.2 (city refactor)
M3.1 (projects.json) → M4.2 (profile.json)
```

Critical path: **M1.1 → M3.1 → M4.2**. The profile is a claim surface; making the
claims data is what lets every later surface share one source.

Do not start: M3.2 before M2.2 (refactoring the generator without a determinism test);
M4.x before M1.1 (adding surfaces on top of unverified claims widens the problem).

---

## 9. Verification harness (commands that exist today)

| Purpose | Command | Status |
|---|---|---|
| Generate city assets | `python3 .github/city.py <user> [--year YYYY] [--out DIR]` (stdlib only; 14 tests in `tests/test_city.py`) | exists |
| Daily refresh | `.github/workflows/contrib-city.yml` (`cron: "0 0 * * *"`, `contents: write`, `actions/checkout` pinned by SHA to v4.4.0) | exists; action pinned |
| **Claim audit** | `python3 scripts/check_claims.py` (add `--links` to fetch every live URL) | exists (M1.1) |
| **Any test** | `python3 -m unittest discover -s tests` (stdlib only; offline) | exists (M1.4: 14 tests) |
| **Page guards** | `python3 scripts/check_page.py` (size budget; alt/line/viewBox next) | exists (M2.1) |
| **CI** | `.github/workflows/check.yml` — lint, tests, claims, page guards on push; link check weekly | exists (M2.1) |
| **Determinism check** | — | **missing** (M2.2) |
| **Link check** | `python3 scripts/check_links.py` (network; weekly job) | exists (M2.1) |
| **Claim audit** | — | **missing** (M1.1) |

---

## 10. Risk register

| # | Risk | Prob | Impact | Detection | Mitigation |
|---|---|---|---|---|---|
| R1 | "17 providers" and "LoRA-tuned ModernBERT" are unverifiable as phrased | High | Credibility | claim audit (M1.1) | name the measured number (9 providers) or cite the repo |
| R2 | Daily job fails silently, leaving a stale image | Med | Wrong impression | no failure path | M1.4 |
| R3 | Actions pinned by tag (`@v4`), not SHA | Med | Supply chain | `contrib-city.yml:16` | M1.3 |
| R4 | 272 KB of SVG on a mobile profile view | Med | Slow first paint | file size | M3.2 |
| R5 | Six third-party image hosts can change or die | Med | Broken header | no check | M2.3 |
| R6 | Table and badge text typed by hand | High | Divergence | manual | M3.1 |
| R7 | No `alt` on some badges | Low | Accessibility | `README.md` audit | M1.2 |
| R8 | Demo links on free tiers cold-start | Certain | "offline" impression | unchecked | M4.2 |
| R9 | Generator untested, 267 lines | Med | Silent SVG corruption | none | M2.2 |
| R10 | No recorded review date | High | Staleness | none | M6.1 |

---

## 11. PR batching and rollback

| Batch | Contents | Rollback |
|---|---|---|
| B1 | claim fixes + source fields | revert README |
| B2 | action pinning + failure path | revert workflow |
| B3 | determinism fixture + check | revert |
| B4 | `projects.json` + generated table/badges | revert; table returns to hand-written |
| B5 | city size/accessibility + generator split | revert assets |

Rollback rules: generated assets are replaced only with their producer command; a
claim that cannot be sourced is deleted, not softened.

---

## 12. Progress metrics

| Metric | Now (measured) | W1 | W3 | How measured |
|---|---|---|---|---|
| README lines | 49 | 40–60 | 60–90 | `wc -l` |
| Claims with a source field | unknown | 100% | 100% | `projects.json` |
| Provider count claim | "17" vs 9 named in Nexus | exact | exact | claim audit |
| SVG size | 143 KB + 129 KB | same | < 100 KB each | `ls -l assets` |
| Third-party hosts | 6 | documented | documented | host list |
| Tests | 14 (`tests/test_city.py`) | ≥1 (determinism) | + link check | `python3 -m unittest discover -s tests` |
| Actions pinned by SHA | 1 of 1 | 1 | 1 | workflow |

---

## Appendix A — Blocked on the owner

- Which projects stay on the front table versus the archive, and whether the archive section should exist at all.
- The exact provider count for Nexus (repo-level truth decides; the profile follows).
- Whether the resume PDF may be regenerated or must stay as published.
- Whether to self-host the header image (removes one third-party dependency).
- Licence choice for this repository (none today); a `LICENSE` for the generator and assets.

## Appendix B — Definition of done

1. Every claim on the page has a `claim_source` in `projects.json`, and `check_claims.py` passes.
2. Links checked, images have `alt`, both SVG themes regenerate byte-identically from the committed fixture.
3. The daily job fails loudly and leaves the previous assets untouched on any error.
4. The page is readable with images blocked and with a screen reader: name, sentence, links, and a text alternative for the city.
5. No private data anywhere in the tree or the published resume.

## Appendix C — Evidence ledger

| Claim | Command | Result | Status |
|---|---|---|---|
| README is 49 lines | `wc -l < README.md` | 49 | verified-here |
| Two SVGs, 272 KB | `ls -l assets` | 143,082 + 129,218 B | verified-here |
| `city.py` 267 lines, stdlib only | `wc -l .github/city.py`, `grep '^import'` | json, math, os, sys, urllib.request | verified-here |
| `actions/checkout@v4` by tag, `contents: write`, daily cron | `grep -nE 'uses\|cron\|contents:' .github/workflows/contrib-city.yml` | now SHA-pinned `# v4.4.0` / write / `0 0 * * *` | verified-here |
| Nine distinct providers named in Nexus | `awk '/^const DRIVER_FACTORIES/,/^};/' Nexus/apps/api/src/lib/provider-keys.ts \| grep -cE '^  [a-z0-9_]+:'` | 39 | verified-here |
| "17 providers" | `README.md:20` | was stale; row now says 39 | verified-here |
| "LoRA-tuned ModernBERT" | `grep -rniE "modernbert" --exclude-dir=.venv FinScrape`; absent from `FinScrape/README.md` | no match in tree; row now says "Laya (a small fine-tuned classifier)" | verified-here |
| Alt text on badges | inspected `<img>` tags | the four badges carried label-only alt (`![Portfolio](…)`); now each names its destination | verified-here |

## 13. Journal

- 2026-11-23 m1.1.1 [x] project rows rewritten to repo-backed sentences (KeyRouter provider style, Ping PAKE/AES) | proof: `grep -nE 'KeyRouter|Ping' README.md` → both rows now quote their own README | next: m1.1.2
- 2026-11-23 m1.1.2 [x] Nexus "17 providers" → 39, the count of `DRIVER_FACTORIES` | proof: `awk '/^const DRIVER_FACTORIES/,/^};/' Nexus/apps/api/src/lib/provider-keys.ts \| grep -cE '^  [a-z0-9_]+:'` → 39 | next: m1.1.3
- 2026-11-23 m1.1.3 [x] FinScrape "LoRA-tuned ModernBERT" removed; row quotes FinScrape's own README | proof: `grep -rniE "modernbert" --exclude-dir=.venv FinScrape` → no match; `grep -n "fine-tuned classifier" FinScrape/README.md` → :33 | next: m1.1.4
- 2026-11-23 m1.1.4 [x] five live links checked | proof: `curl -s -o /dev/null -w "%{http_code}" -m 25 -L <url>` → 200 ×5 (Nexus 45.8 s cold start) | next: m1.1.5
- 2026-11-23 m1.1.5 [x] `scripts/check_claims.py` guards all 9 rows | proof: `python3 scripts/check_claims.py` → `9 rows, 0 problem(s)`; with "42 providers" → exit 1 | next: m1.2.1
- 2026-11-23 m1.2.1 [x] badge alt text names the destination | proof: `grep -oE '!\[[^]]*\]' README.md` → 4 alts with host/mailbox | next: m1.2.2
- 2026-11-23 m1.2.2 [x] name and tagline are real text, banner decorative | proof: `head -8 README.md` → `# Yash Vaibhav Awasthi` + tagline; `wc -l < README.md` → 45 | next: m1.2.3
- 2026-11-23 m1.2.3 [x] stack has a visible text fallback; icon strip decorative (`alt=""`) | proof: `sed -n '/### Stack/,/<picture>/p' README.md` → `**Stack:** …` line + `alt=""`; `wc -l` → 47 | deviation: text list instead of repeating it in alt | next: m1.2.4
- 2026-11-23 m1.2.4 [x] default branch confirmed `master`; city `<picture>` URL verified as the one GitHub serves | proof: `curl -s api.github.com/repos/Yash-Awasthi/Yash-Awasthi \| grep default_branch` → master; relative path would 404 | deviation: absolute raw URL kept | next: m1.3.1
- 2026-11-23 m1.3.1 [x] checkout pinned by SHA with version comment | proof: `grep -nE 'uses:' .github/workflows/contrib-city.yml` → `actions/checkout@11d5960a… # v4.4.0` | next: m1.3.2
- 2026-11-23 m1.3.2 [x] commit step refuses to push when the branch moved | proof: scratch-repo rehearsal of the step → CASE1 exit 0, CASE2 guard fires (HEAD~1 ≠ origin/master), CASE3 push ok | next: m1.3.3
- 2026-11-23 m1.3.3 [x] least-privilege default, write only on the generating job | proof: `yaml.safe_load` → workflow `contents: read`, job `generate` `contents: write` | next: m1.3.4
- 2026-11-23 m1.3.4 [x] `concurrency: contrib-city` added (timeout was already 10) | proof: `yaml.safe_load` → concurrency + timeout-minutes 10 | next: m1.4.1
- 2026-11-23 m1.4.1 [x] bad fetch (HTTP error, non-200, `errors`, empty calendar) fails instead of rendering | proof: `python3 -m unittest discover -s tests` → 7 OK (6 fail on the old code); live 401 → exit 1, SVGs unchanged | next: m1.4.2
- 2026-11-23 m1.4.2 [x] both themes staged and swapped together | proof: `python3 -m unittest discover -s tests` → 10 OK; 3 WriteTest cases error on the old code | next: m1.4.3
- 2026-11-23 m1.4.3 [x] job log names total, date range and week count | proof: `python3 -m unittest discover -s tests` → 11 OK; `city.summary(...)` → `7 contributions, 2026-11-01 to 2026-11-03, 2 weeks` | next: m1.4.4
- 2026-11-23 m1.4.4 [x] `--year` and `--out` flags; real render runs into a temp dir | proof: `unittest discover` → 14 OK; `city.py Yash-Awasthi --out /tmp/cityout` → 3470 contributions, 2025-11-23 to 2026-11-24, 53 weeks, assets untouched | next: m2.1.1
- 2026-11-23 m2.1.1 [x] `check.yml` (lint, tests, claims, size) + weekly link job | proof: markdownlint 0 errors, `check_page.py` 0 problems, `check_links.py` 22 URLs 0 problems (broken URL → exit 1) | next: m2.1.2
- 2026-11-23 m2.1.2 [x] README line budget of 60 enforced | proof: `check_page.py` → `lines README.md 50 (budget 60)`; 65 lines → exit 1 | next: m2.1.3
- 2026-11-23 m2.1.3 [x] every `<img>` needs `alt`, every link a destination | proof: `check_page.py` → `ok alt 7 images`; injected `<img>` without alt / `[x]()` / `![]()` → 3 FAIL, exit 1 | next: m2.1.4
