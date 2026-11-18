"""V2 offline Watchlist compact V1-style row parity, no provider calls."""
import sys
import unittest
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from feed_inbox import DeviceFeedInbox
from evidence_inbox import DeviceEvidenceInbox
from watchlist_parity import watchlist_row, watchlist_rows


def quote_snapshot(revision, prices):
    return {"protocol": "botking-v2-readonly", "schema_version": 1,
            "source": "dhan", "freshness": "unverified",
            "live_orders_enabled": False, "revision": revision,
            "quotes": {sym: {"price": p, "freshness": "unverified",
                             "live_verified": False, "revision": revision}
                       for sym, p in prices.items()}}


def bars():
    return [
        {"timestamp": 100, "open": 100, "high": 102, "low": 99,
         "close": 101, "volume": 2, "completed": True},
        {"timestamp": 200, "open": 101, "high": 103, "low": 100,
         "close": 102, "volume": 3, "completed": True},
    ]


class WatchlistParityTests(unittest.TestCase):
    def setUp(self):
        self.q = DeviceFeedInbox()
        self.e = DeviceEvidenceInbox()

    def test_selected_equity_only_three_minute_wait_and_blank_sixth(self):
        row = watchlist_row("TCS", self.q, self.e, selected_equities=("TCS",))
        self.assertEqual(row["price"], "WAIT")
        self.assertEqual(row["candle"], "3m candles WAIT")
        self.assertIn("5 filters WAIT", row["filter_text"])
        self.assertEqual(row["sixth"], ("", ""))
        self.assertTrue(row["historical_only"])
        for sym in ("NIFTY", "INFY"):
            with self.subTest(symbol=sym), self.assertRaises(ValueError):
                watchlist_row(sym, self.q, self.e, selected_equities=("TCS",))

    def test_last_good_quote_candles_and_independent_selected_rows(self):
        self.q.apply_feed("quotes", quote_snapshot(1, {"TCS": 100}), ("TCS", "INFY"))
        self.e.apply_candles("TCS", "3m", 1, bars(),
                             selected_equities=("TCS", "INFY"), trusted_transport=True)
        row = watchlist_row("TCS", self.q, self.e, selected_equities=("TCS", "INFY"))
        self.assertEqual(row["price"], "100.00 HIST")
        self.assertEqual(row["candle"], "2 completed 3m candles HIST")
        self.q.apply_feed("quotes", quote_snapshot(2, {}), ("TCS", "INFY"))
        self.assertEqual(watchlist_row("TCS", self.q, self.e,
                         selected_equities=("TCS", "INFY"))["price"], "100.00 HIST")
        self.assertEqual(watchlist_row("INFY", self.q, self.e,
                         selected_equities=("TCS", "INFY"))["price"], "WAIT")

    def test_group_order_and_duplicate_roster_fail_closed(self):
        roster = ("TCS", "INFY")
        rows = watchlist_rows(["INFY", "TCS"], self.q, self.e,
                              selected_equities=roster)
        self.assertEqual(tuple(row["symbol"] for row in rows), ("INFY", "TCS"))
        with self.assertRaises(ValueError):
            watchlist_rows(["TCS", "TCS"], self.q, self.e, selected_equities=roster)
        with self.assertRaises(ValueError):
            watchlist_row("TCS", self.q, self.e, selected_equities=("TCS", "TCS"))

    def test_watchlist_chart_button_routes_selected_equity_to_3m_scanner(self):
        src = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertIn("def open_watchlist_chart(symbol):", src)
        self.assertIn("scanner[0] = choose(scanner[0], state, symbol=symbol,", src)
        self.assertIn('timeframe="3m"', src)
        self.assertIn('ft.TextButton("Chart",', src)
        self.assertIn("open_watchlist_chart(item)", src)
        self.assertIn("page.navigation_bar.selected_index = 0", src)
        self.assertIn("except ScannerError:", src)
        self.assertNotIn("ServerAngelFeed(", src)
        self.assertNotIn("get_yahoo(", src)

    def test_flet_row_is_compact_and_uses_current_selected_roster(self):
        src = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertIn("watchlist_rows(", src)
        self.assertIn("filtered_watchlist_symbols(state.groups[group[0]], watch_search[0])", src)
        self.assertIn("quote_view, evidence_inbox,", src)
        self.assertIn("on_submit=apply_search", src)
        self.assertIn("selected_equities=state.selected", src)
        self.assertIn('ft.Text(row["candle"]', src)
        self.assertIn('ft.Text(row["filter_text"]', src)
        self.assertIn('on_click=lambda e, item=row["symbol"]: remove(e, item)', src)


if __name__ == "__main__":
    unittest.main()
