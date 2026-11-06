"""Vote percentage contract: directional votes only, no trade probability."""
import unittest
from test_audit import start


class StrengthBarTests(unittest.TestCase):
    def test_vote_percentage(self):
        _, v = start({"scanner_live": False})
        calc = v["signal_percentages"]
        self.assertEqual(calc({"votes": [{"vote": 1}]*6 + [{"vote": -1}]*2}), (75, 25, 8))
        self.assertEqual(calc({"votes": [{"vote": 1}]*8}), (100, 0, 8))
        self.assertIsNone(calc({"votes": [{"vote": 0}, {"vote": None}]}))

    def test_all_watchlists_render_without_signal_data(self):
        _, v = start({"scanner_live": False})
        for index in range(5):
            v["active_watch"][0] = index
            v["fill_watch"]()


if __name__ == "__main__":
    unittest.main()
