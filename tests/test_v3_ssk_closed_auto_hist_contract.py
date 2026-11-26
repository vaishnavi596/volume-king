import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1].joinpath("src", "main.py").read_text(encoding="utf-8")


class SskClosedAutoHistContract(unittest.TestCase):
    def test_once_per_generation_and_gated(self):
        start = SRC.index("ssk_closed_auto_hist_generation[0]!=provider_generation[0]")
        block = SRC[start - 500:start + 400]
        for needle in ("clone_v2_gateway.connected", "not dhan_feed.connected",
                       "not refresh_hours()", "app_active[0]", "refresh_all_dhan_quotes()"):
            self.assertIn(needle, block)
        self.assertIn("ssk_closed_auto_hist_generation[0]=provider_generation[0]", block)


if __name__ == "__main__":
    unittest.main()


class ClosedIndexSnapshotContract(unittest.TestCase):
    def test_snapshot_is_unverified_and_never_activates_live_feed(self):
        start = SRC.index("async def closed_session_index_snapshot(generation):")
        end = SRC.index("async def check_clone_v2_market_quotes():")
        body = SRC[start:end]
        self.assertIn('"live_verified":False', body)
        self.assertIn("paced_market_quotes", body)
        self.assertIn("accept_newer_dhan_quote", body)
        self.assertNotIn("activate_with_quote", body)
        self.assertIn("closed_index_snapshot_generation[0]==generation", body)
        self.assertGreaterEqual(SRC.count("closed_session_index_snapshot"), 3)  # def, poll branch, repair action
