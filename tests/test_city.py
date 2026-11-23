"""Tests for .github/city.py, run offline: python3 -m unittest discover -s tests

The generator decides whether the committed SVGs are replaced, so its failure
paths are the interesting part: a bad fetch must raise and must not render.
"""
from __future__ import annotations

import importlib.util
import io
import json
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
        real = city.urllib.request.urlopen
        city.urllib.request.urlopen = FakeUrlopen(**kw)
        try:
            return city.fetch("someone", "token")
        finally:
            city.urllib.request.urlopen = real

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
        real_render, calls = city.render, []

        def render_then_fail(weeks, theme):
            calls.append(theme)
            if len(calls) == 2:
                raise RuntimeError("theme 2 exploded")
            return real_render(weeks, theme)

        city.render = render_then_fail
        try:
            with self.assertRaises(RuntimeError):
                city.write_assets(self.WEEKS, self.dir)
        finally:
            city.render = real_render
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


if __name__ == "__main__":
    unittest.main()
