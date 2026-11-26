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
