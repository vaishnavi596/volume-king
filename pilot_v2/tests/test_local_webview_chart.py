"""No-network HTML candidate for future optional Android WebView acceptance."""
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from candle_history import LocalCandleHistory, CandleEvidenceError
from local_webview_chart import historical_chart_html


def two_bars():
    return [
        {"timestamp": 100, "open": 100, "high": 105, "low": 99,
         "close": 103, "volume": 100, "completed": True},
        {"timestamp": 200, "open": 103, "high": 106, "low": 101,
         "close": 102, "volume": 150, "completed": True},
    ]


class LocalWebViewHTMLContract(unittest.TestCase):
    def setUp(self):
        self.cache = LocalCandleHistory()

    def test_wait_without_source_is_never_fake_chart(self):
        self.assertIsNone(historical_chart_html(
            self.cache, "TCS", "3m", selected_equities=("TCS",)))
        self.assertIsNone(historical_chart_html(
            self.cache, "TCS", "3m", selected_equities=()))

    def test_svg_uses_only_retained_candles_and_no_external_assets(self):
        self.cache.accept("TCS", "3m", 1, two_bars(), allowed_symbols=("TCS",))
        html = historical_chart_html(
            self.cache, "TCS", "3m", selected_equities=("TCS",))
        for item in ("<svg", "<rect", "<line", "TCS", "HIST / unverified",
                     "Content-Security-Policy", "not LIVE"):
            self.assertIn(item, html)
        for forbidden in ("https://", "http://", "<script", "fetch(", "WebSocket",
                          "device_bearer", "access_token", "LIVE VERIFIED"):
            self.assertNotIn(forbidden, html)
        line = historical_chart_html(
            self.cache, "TCS", "3m", selected_equities=("TCS",), style="Line")
        self.assertIn("<polyline", line)
        self.assertNotIn("<rect", line)

    def test_invalid_symbol_style_limit_and_incomplete_candles_fail_closed(self):
        for symbol in ("<script>", "tcs", "TCS/", ""):
            with self.subTest(symbol=symbol), self.assertRaises(ValueError):
                historical_chart_html(
                    self.cache, symbol, "3m", selected_equities=(symbol,))
        for value in (0, 71, True, 14):
            with self.subTest(window=value), self.assertRaises(ValueError):
                historical_chart_html(
                    self.cache, "TCS", "3m", selected_equities=("TCS",), limit=value)
        with self.assertRaises(ValueError):
            historical_chart_html(self.cache, "TCS", "3m",
                                  selected_equities=("TCS",), style="TradingView")
        self.cache.accept("TCS", "3m", 1, two_bars(), allowed_symbols=("TCS",))
        invalid = [dict(b) for b in two_bars()]
        invalid[-1]["completed"] = False
        with self.assertRaises(CandleEvidenceError):
            self.cache.accept("TCS", "3m", 2, invalid, allowed_symbols=("TCS",))
        self.assertIn("HIST / unverified", historical_chart_html(
            self.cache, "TCS", "3m", selected_equities=("TCS",)))


if __name__ == "__main__":
    unittest.main()
