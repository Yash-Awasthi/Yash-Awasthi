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


def load_pin():
    spec = importlib.util.spec_from_file_location("pin_claims", ROOT / "scripts" / "pin_claims.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
        self.assertTrue(claims.check_source({"name": "X", "claim_source": [{"any": ["y"], "line": 1}]}))
        self.assertTrue(claims.check_source({"name": "X", "claim_source": [{"file": "README.md", "line": 1}]}))
        self.assertEqual(claims.check_source(
            {"name": "X", "claim_source": [{"file": "README.md", "any": ["y"], "line": 1}]}), [])

    def test_a_source_entry_without_a_pinned_line_fails(self):
        self.assertTrue(claims.check_source(
            {"name": "X", "claim_source": [{"file": "README.md", "any": ["y"]}]}))

    def test_every_shipped_project_is_sourced(self):
        data = claims.load()
        for p in data["projects"]:
            self.assertEqual(claims.check_source(p), [], p["name"])
            self.assertTrue(p["claim"], p["name"])


class LineTest(unittest.TestCase):
    """A claim that names a line cannot drift inside the file it cites (M5.3.1)."""

    TEXT = ("# title\nthe gateway mints sk-gw- keys\nthe vendor is Anthropic\n")

    def test_the_pinned_line_holds_the_snippet(self):
        self.assertTrue(claims.line_holds(self.TEXT, {"line": 2, "any": ["sk-gw-"]}))

    def test_a_moved_snippet_is_caught(self):
        self.assertFalse(claims.line_holds(self.TEXT, {"line": 1, "any": ["sk-gw-"]}))
        self.assertFalse(claims.line_holds(self.TEXT, {"line": 9, "any": ["sk-gw-"]}))

    def test_a_count_claim_pins_its_const_declaration(self):
        text = ("// x\nnconst DRIVER_FACTORIES = {\nn  a: 1,\nn};\nn")
        self.assertTrue(claims.line_holds(text, {"line": 2, "count": "DRIVER_FACTORIES"}))

    def test_every_shipped_entry_is_pinned(self):
        data = claims.load()
        for p in data["projects"] + data.get("archive", []):
            for c in p["claim_source"]:
                self.assertIsInstance(c.get("line"), int, f"{p['name']} {c['file']}")

    def test_the_pin_tool_finds_the_first_line_holding_a_snippet(self):
        pin = load_pin()
        self.assertEqual(pin.line_of(self.TEXT, {"any": ["Anthropic", "sk-gw-"]})[0], 3)
        self.assertEqual(pin.line_of(self.TEXT, {"any": ["nothing here"]}), (None, ""))


class LiveUrlTest(unittest.TestCase):
    def test_only_projects_with_a_live_url_are_checked(self):
        for p in claims.load()["projects"]:
            if p.get("live"):
                self.assertTrue(p["live"].startswith("https://"), p["name"])


if __name__ == "__main__":
    unittest.main()
