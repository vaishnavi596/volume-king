"""Read-only source contract: prevent silent SENSEX segment drift.

This is NOT a Dhan entitlement/live-price verification. A future mapping
change must update the contract intentionally with instrument-master evidence.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "backend" / "clone_v2_gateway.py"
FEED = ROOT / "backend" / "dhan_feed.py"


def configured_indices():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "indices" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("Gateway index mapping not found")


class CloneIndexMappingContract(unittest.TestCase):
    def test_three_dashboard_indices_have_distinct_security_ids(self):
        indices = configured_indices()
        self.assertEqual(set(indices), {"NIFTY", "BANKNIFTY", "SENSEX"})
        self.assertEqual(len(set(indices.values())), 3)
        self.assertEqual(indices["NIFTY"], ("IDX_I", 13))
        self.assertEqual(indices["BANKNIFTY"], ("IDX_I", 25))

    def test_sensex_current_source_contract_requires_provider_confirmation(self):
        # Records current code, not a claim that Dhan accepts this segment.
        self.assertEqual(configured_indices()["SENSEX"], ("IDX_I", 51))
        self.assertIn('"BSE_I"', FEED.read_text(encoding="utf-8"))
        self.assertIn('"IDX_I"', FEED.read_text(encoding="utf-8"))

    def test_registry_cannot_silently_override_index_mapping(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("known = dict(registry)", source)
        self.assertIn("known.update(indices)", source)
        self.assertIn("option_known = dict(known)", source)

    def test_quote_provider_pacing_and_candle_hash_are_source_only(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("time.sleep(spacing_remaining)", source)
        self.assertIn("X-BotKing-429-Stage", source)
        self.assertIn("normalized_bars_sha256", source)


if __name__ == "__main__":
    unittest.main()
