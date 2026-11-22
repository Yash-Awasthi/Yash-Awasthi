"""Tests for the page guards in scripts/check_page.py.

The guards read files in the repository, so the useful cases are the ones with a
date or a colour supplied by the test: the same code path CI takes, without a clock.
"""
from __future__ import annotations

import importlib.util
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_page():
    spec = importlib.util.spec_from_file_location("check_page", ROOT / "scripts" / "check_page.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


page = load_page()


class ReviewFreshnessTest(unittest.TestCase):
    """A review date that never expires is decoration (M6.1.1)."""

    def test_the_shipped_review_is_current(self):
        self.assertEqual(page.check_review_freshness(), [])

    def test_an_old_review_fails(self):
        stale = date.today() + timedelta(days=page.REVIEW_MAX_DAYS + 1)
        problems = page.check_review_freshness(stale)
        self.assertTrue(problems)
        self.assertIn("days ago", problems[0])

    def test_the_budget_is_a_quarter_not_a_year(self):
        self.assertLessEqual(page.REVIEW_MAX_DAYS, 100)


class ContrastTest(unittest.TestCase):
    """White badge text has to stay readable on the badge colour (M5.1.5)."""

    def test_black_and_white_are_the_extremes(self):
        self.assertAlmostEqual(page.contrast_on_white("#000000"), 21.0, places=1)
        self.assertAlmostEqual(page.contrast_on_white("#ffffff"), 1.0, places=2)

    def test_the_threshold_is_the_wcag_aa_value(self):
        self.assertEqual(page.BADGE_MIN_CONTRAST, 4.5)

    def test_every_shipped_badge_passes(self):
        self.assertEqual(page.check_badge_contrast(), [])


if __name__ == "__main__":
    unittest.main()
