"""Dashboard three independent index-card to Scanner 1m app routing."""
import ast
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(ROOT))
from app_state import LocalWatchlists
from scanner_state import ScannerSelection, choose, INDEXES, ScannerError


class IndexChartRoutingTests(unittest.TestCase):
    def test_three_indexes_always_selectable_with_one_minute(self):
        state = LocalWatchlists()
        state.add(0, "TCS")
        for index in INDEXES:
            with self.subTest(index=index):
                chosen = choose(ScannerSelection("TCS", "3m"), state,
                                symbol=index, timeframe="1m")
                self.assertEqual((chosen.symbol, chosen.timeframe), (index, "1m"))
        with self.assertRaises(ScannerError):
            choose(ScannerSelection(), state, symbol="UNKNOWN", timeframe="1m")

    def test_real_dashboard_button_uses_local_scanner_without_server(self):
        s = (ROOT / "main.py").read_text(encoding="utf-8")
        ast.parse(s)
        self.assertIn("def open_index_chart(symbol):", s)
        self.assertIn("if symbol not in INDEXES:", s)
        self.assertIn("scanner[0] = choose(scanner[0], state, symbol=symbol,", s)
        self.assertIn('timeframe="1m"', s)
        self.assertIn('ft.TextButton("1m Chart",', s)
        self.assertIn('open_index_chart(symbol)', s)
        self.assertIn("if save_scanner() else", s)
        self.assertEqual(s.count("ft.NavigationDestination("), 3)
        self.assertNotIn("ServerAngelFeed(", s)
        self.assertNotIn("get_yahoo(", s)

if __name__ == "__main__":
    unittest.main()
