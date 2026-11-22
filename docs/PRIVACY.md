# What may and may not appear on the profile

The profile at `github.com/Yash-Awasthi` is public and indexed. These are the
rules the page is held to; `scripts/check_privacy.py` enforces the mechanical ones.

## Allowed — deliberate, public, already on a CV

| Item | Where it appears | Why it is allowed |
|---|---|---|
| Full name | `README.md` heading | The profile is a public professional identity. |
| Public email `yashvaibhav.job@gmail.com` | Badge link, `mailto:` | Chosen contact channel, published on purpose. |
| LinkedIn profile URL | Badge link | Public professional profile. |
| City/university and CGPA | Bio line | Public record, already in the resume. |
| Employer and internship names, dates | Experience section | Public employment history. |
| Project repositories and demos | Project table | The subject of the page. |

## Never

1. **Phone numbers** — no phone number in the README, the assets, or the PDF. A
   profile is scraped; a phone number there is a permanent spam target.
2. **Home address or locality below city level** — city-level is fine, a street
   or a pin code is not.
3. **Government identifiers** — no Aadhaar, PAN, passport, driving licence,
   employee numbers, roll numbers.
4. **Private keys, tokens, API keys, session cookies** — and no screenshot that
   contains one.
5. **Other people's personal data** — no colleague, referee or family contact
   details without their consent; no student data from the school platform.
6. **Unpublished employer internals** — no architecture detail, screenshots or
   names of customers from a role that has not shipped publicly.
7. **Medical or financial detail** — no health data, salary, bank details, or
   anything from the AdapFit user domain.

## How the rules are enforced

- `scripts/check_privacy.py` scans `README.md` and the committed assets for
  phone-number shapes, street addresses, and key/token shapes, and fails the
  `check` workflow. It also checks the published resume PDF for the same.
- `scripts/check_page.py` keeps every image's `alt` and every link's destination
  explicit, so nothing is smuggled in as an opaque badge URL.
- A change that adds personal data must also change this file in the same
  commit, with the reason.

If something private is already published, the order is: remove it, force the
cache to refresh (edit the file again or bump the branch), then rotate whatever
was exposed.
