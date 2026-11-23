"""Tests for scripts/check_claims.py: the rules that guard every claim in projects.json."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_claims():
    spec = importlib.util.spec_from_file_location("check_claims", ROOT / "scripts" / "check_claims.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


claims = load_claims()


class BudgetTest(unittest.TestCase):
    def test_a_normal_live_url_must_answer_in_ten_seconds(self):
        self.assertEqual(claims.budget_for({"live": "https://x.example"}), 10.0)

    def test_a_documented_cold_start_gets_the_longer_budget(self):
        self.assertEqual(claims.budget_for({"cold_start": True}), 120.0)

    def test_the_shipped_data_only_exempts_documented_cold_starts(self):
        for p in claims.load()["projects"]:
            if p.get("cold_start"):
                self.assertTrue(p.get("cold_start_note"), f"{p['name']} has no cold_start_note")


class SourceTest(unittest.TestCase):
    def test_a_claim_without_a_source_fails(self):
        self.assertTrue(claims.check_source({"name": "X"}))
        self.assertTrue(claims.check_source({"name": "X", "claim_source": []}))

    def test_a_source_entry_needs_a_file_and_something_to_look_for(self):
        self.assertTrue(claims.check_source({"name": "X", "claim_source": [{"any": ["y"]}]}))
        self.assertTrue(claims.check_source({"name": "X", "claim_source": [{"file": "README.md"}]}))
        self.assertEqual(claims.check_source(
            {"name": "X", "claim_source": [{"file": "README.md", "any": ["y"]}]}), [])

    def test_every_shipped_project_is_sourced(self):
        data = claims.load()
        for p in data["projects"]:
            self.assertEqual(claims.check_source(p), [], p["name"])
            self.assertTrue(p["claim"], p["name"])


class LiveUrlTest(unittest.TestCase):
    def test_only_projects_with_a_live_url_are_checked(self):
        for p in claims.load()["projects"]:
            if p.get("live"):
                self.assertTrue(p["live"].startswith("https://"), p["name"])


if __name__ == "__main__":
    unittest.main()
