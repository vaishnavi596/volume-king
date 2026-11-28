import unittest, sys
sys.path.insert(0, "backend")
import clone_signal_runner as r


class B258(unittest.TestCase):
    def test_weight_follows_edge(self):
        row = r._gate_row(200, 115, 51.7)   # hit 57.5, low ~50.6, edge 5.8
        self.assertTrue(row["eligible"])
        self.assertAlmostEqual(row["weight"], 0.58, places=2)
        self.assertEqual(r._gate_row(10, 9, 50.0)["weight"], 0.0)  # too few samples

    def test_super_five_uses_one_minute(self):
        src = open("src/main.py", encoding="utf-8").read()
        self.assertNotIn('five_engine_chips(row["symbol"],display_timeframe="5m")', src)
        self.assertNotIn('else "5m")),', src.split("def paper_trading_center")[1][:900])


if __name__ == "__main__":
    unittest.main()
