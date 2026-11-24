"""Tests for .github/city.py, run offline: python3 -m unittest discover -s tests

The generator decides whether the committed SVGs are replaced, so its failure
paths are the interesting part: a bad fetch must raise and must not render.
"""
from __future__ import annotations

import importlib.util
import io
import json
import re
import unittest
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_city():
    spec = importlib.util.spec_from_file_location("city", ROOT / ".github" / "city.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


city = load_city()
# The generator is a package (scripts/citykit) behind a thin CLI; patch the real call site.
source = importlib.import_module("citykit.source")
assets = importlib.import_module("citykit.assets")


def payload(days):
    """A GraphQL payload whose single week holds `days` as (date, count) pairs."""
    return {"data": {"user": {"contributionsCollection": {"contributionCalendar": {"weeks": [
        {"contributionDays": [{"date": d, "contributionCount": n} for d, n in days]}
    ]}}}}}


class Response(io.BytesIO):
    def __init__(self, body: bytes, status: int = 200):
        super().__init__(body)
        self.status = status


class FakeUrlopen:
    def __init__(self, body: bytes = b"", status: int = 200, error: Exception | None = None):
        self.body, self.status, self.error = body, status, error

    def __call__(self, req, timeout=None):
        if self.error:
            raise self.error
        return Response(self.body, self.status)


class FetchTest(unittest.TestCase):
    def run_fetch(self, **kw):
        real = source.urllib.request.urlopen
        source.urllib.request.urlopen = FakeUrlopen(**kw)
        try:
            return city.fetch("someone", "token")
        finally:
            source.urllib.request.urlopen = real

    def test_http_error_becomes_fetch_error(self):
        err = urllib.error.HTTPError("u", 401, "Unauthorized", {}, None)
        with self.assertRaises(city.FetchError):
            self.run_fetch(error=err)

    def test_network_error_becomes_fetch_error(self):
        with self.assertRaises(city.FetchError):
            self.run_fetch(error=urllib.error.URLError("no route"))

    def test_non_200_becomes_fetch_error(self):
        with self.assertRaises(city.FetchError):
            self.run_fetch(body=json.dumps(payload([("2026-11-01", 3)])).encode(), status=502)

    def test_graphql_errors_become_fetch_error(self):
        body = json.dumps({"errors": [{"message": "rate limited"}], "data": None}).encode()
        with self.assertRaises(city.FetchError):
            self.run_fetch(body=body)

    def test_empty_calendar_becomes_fetch_error(self):
        with self.assertRaises(city.FetchError):
            self.run_fetch(body=json.dumps(payload([("2026-11-01", 0)])).encode())

    def test_a_sha256_digest_of_nothing_is_not_rendered(self):
        with self.assertRaises(city.FetchError):
            city.parse_calendar({"data": {"user": None}})

    def test_valid_payload_is_parsed(self):
        weeks = self.run_fetch(body=json.dumps(payload([("2026-11-01", 3)])).encode())
        self.assertEqual(weeks, [[("2026-11-01", 3)]])


class WriteTest(unittest.TestCase):
    WEEKS = [[("2026-11-0%d" % (d + 1), d) for d in range(7)]]

    def setUp(self):
        import tempfile
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_both_themes_are_written(self):
        written = city.write_assets(self.WEEKS, self.dir)
        names = sorted(p.name for p in Path(self.dir).iterdir())
        self.assertEqual(names, ["city-dark.svg", "city-light.svg"])
        self.assertEqual(len(written), 2)

    def test_a_render_crash_leaves_the_previous_assets_untouched(self):
        city.write_assets(self.WEEKS, self.dir)
        before = {p.name: p.read_bytes() for p in Path(self.dir).iterdir()}
        real_render, calls = assets.render, []

        def render_then_fail(weeks, theme):
            calls.append(theme)
            if len(calls) == 2:
                raise RuntimeError("theme 2 exploded")
            return real_render(weeks, theme)

        assets.render = render_then_fail
        try:
            with self.assertRaises(RuntimeError):
                city.write_assets(self.WEEKS, self.dir)
        finally:
            assets.render = real_render
        after = {p.name: p.read_bytes() for p in Path(self.dir).iterdir()}
        self.assertEqual(before, after, "a failed render must not replace either theme")

    def test_no_temp_files_are_left_behind(self):
        city.write_assets(self.WEEKS, self.dir)
        self.assertFalse([p for p in Path(self.dir).iterdir() if p.name.startswith(".city-")])


class SummaryTest(unittest.TestCase):
    def test_summary_names_total_and_range(self):
        weeks = [[("2026-11-01", 2), ("2026-11-02", 0)], [("2026-11-03", 5)]]
        self.assertEqual(city.summary(weeks),
                         "7 contributions, 2026-11-01 to 2026-11-03, 2 weeks")


class YearAndCliTest(unittest.TestCase):
    WEEKS = [[("2025-12-30", 1), ("2026-01-01", 4)], [("2026-01-04", 2)]]

    def test_filter_year_drops_other_years(self):
        self.assertEqual(city.filter_year(self.WEEKS, 2026),
                         [[("2026-01-01", 4)], [("2026-01-04", 2)]])

    def test_filter_year_refuses_a_year_with_nothing_in_it(self):
        with self.assertRaises(city.FetchError):
            city.filter_year(self.WEEKS, 2024)

    def test_cli_offers_year_and_out(self):
        import subprocess, sys
        out = subprocess.run([sys.executable, str(ROOT / ".github" / "city.py"), "--help"],
                             capture_output=True, text=True, check=True)
        self.assertIn("--year", out.stdout)
        self.assertIn("--out", out.stdout)
        self.assertIn("$GITHUB_USER", out.stdout)  # the positional user's default


class DeterminismTest(unittest.TestCase):
    """The same calendar must always produce the same bytes, in this process and any other."""

    WEEKS = [[("2026-11-%02d" % (d + 1), (d * 3) % 7) for d in range(7)],
             [("2026-11-%02d" % (d + 8), 0 if d % 2 else d) for d in range(7)],
             [("2026-11-%02d" % (d + 15), d * 2) for d in range(7)]]

    def test_two_renders_are_byte_identical(self):
        for theme in city.THEMES:
            self.assertEqual(city.render(self.WEEKS, theme), city.render(self.WEEKS, theme), theme)

    def test_a_separate_process_agrees_under_another_hash_seed(self):
        import hashlib, json, os, subprocess, sys, tempfile
        digest = []
        for seed in ("0", "12345"):
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
                json.dump(self.WEEKS, fh)
                path = fh.name
            code = (
                "import hashlib, importlib.util, json, sys;"
                f"spec=importlib.util.spec_from_file_location('city', {str(ROOT / '.github' / 'city.py')!r});"
                "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
                f"weeks=json.load(open({path!r}));"
                "print(hashlib.sha256(''.join(m.render(weeks,t) for t in m.THEMES).encode()).hexdigest())"
            )
            env = dict(os.environ, PYTHONHASHSEED=seed)
            out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, check=True)
            digest.append(out.stdout.strip())
            os.unlink(path)
        self.assertEqual(digest[0], digest[1])
        self.assertEqual(len(digest[0]), 64)


FIXTURE = ROOT / "tests" / "fixtures" / "calendar.json"
GOLDEN = ROOT / "tests" / "fixtures" / "golden.json"


class FixtureTest(unittest.TestCase):
    """The generator must render from a committed payload, without the network."""

    def setUp(self):
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_parses_into_weeks(self):
        weeks = city.parse_calendar(self.payload)
        self.assertEqual(len(weeks), 53)
        self.assertEqual(weeks[0][0][0], "2025-11-23")
        self.assertGreater(sum(n for w in weeks for _, n in w), 0)

    def test_both_themes_render_from_the_fixture(self):
        weeks = city.parse_calendar(self.payload)
        for theme in city.THEMES:
            svg = city.render(weeks, theme)
            self.assertTrue(svg.startswith("<svg"))
            self.assertTrue(svg.rstrip().endswith("</svg>"))


class GoldenTest(unittest.TestCase):
    """A pixel change from the committed fixture has to be an intentional commit."""

    def test_fixture_render_matches_the_committed_hash(self):
        import hashlib, os
        weeks = city.parse_calendar(json.loads(FIXTURE.read_text(encoding="utf-8")))
        actual = {theme: hashlib.sha256(city.render(weeks, theme).encode()).hexdigest()
                  for theme in city.THEMES}
        if os.environ.get("UPDATE_GOLDEN") == "1":
            GOLDEN.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        stored = json.loads(GOLDEN.read_text(encoding="utf-8"))
        self.assertEqual(actual, stored,
                         "rendered output changed; rerun with UPDATE_GOLDEN=1 only if that is intended")


class SafetyTest(unittest.TestCase):
    """The asset is generated, but it must still be inert on its own."""

    def test_fixture_output_holds_nothing_active(self):
        weeks = city.parse_calendar(json.loads(FIXTURE.read_text(encoding="utf-8")))
        for theme in city.THEMES:
            self.assertEqual(city.unsafe_refs(city.render(weeks, theme)), [], theme)

    def test_the_scanner_catches_what_it_claims_to(self):
        self.assertTrue(city.unsafe_refs('<svg><script>alert(1)</script></svg>'))
        self.assertTrue(city.unsafe_refs('<svg><image href="https://x/y.png"/></svg>'))
        self.assertTrue(city.unsafe_refs('<svg><foreignObject></foreignObject></svg>'))
        self.assertTrue(city.unsafe_refs('<svg><use href="https://x/y.svg#a"/></svg>'))
        self.assertEqual(city.unsafe_refs('<svg><rect fill="url(#sky)"/></svg>'), [])


class AccessibleNameTest(unittest.TestCase):
    """A screen reader must hear the year and the total, not "image" (M3.2.2)."""

    def setUp(self):
        self.weeks = city.parse_calendar(json.loads(FIXTURE.read_text(encoding="utf-8")))
        self.total = sum(n for w in self.weeks for _, n in w)

    def test_each_theme_states_year_dates_and_total(self):
        for theme in city.THEMES:
            svg = city.render(self.weeks, theme)
            title = re.search(r"<title[^>]*>([^<]*)</title>", svg).group(1)
            desc = re.search(r"<desc[^>]*>([^<]*)</desc>", svg).group(1)
            self.assertIn(f"{self.total:,} contributions", title)
            first = self.weeks[0][0][0]
            last = self.weeks[-1][-1][0]
            self.assertIn(f"{first} to {last}", desc)

    def test_both_themes_declare_the_same_total(self):
        totals = {theme: re.search(r"([\d,]+) contributions", city.render(self.weeks, theme)).group(1)
                  for theme in city.THEMES}
        self.assertEqual(len(set(totals.values())), 1, totals)

    def test_the_svg_points_at_its_own_title_and_desc(self):
        svg = city.render(self.weeks, "dark")
        self.assertIn('aria-labelledby="ct cd"', svg)
        self.assertIn('id="ct"', svg)
        self.assertIn('id="cd"', svg)


if __name__ == "__main__":
    unittest.main()
