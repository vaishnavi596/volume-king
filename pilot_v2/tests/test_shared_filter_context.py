"""Source-safe cross-screen factor consistency test for V2."""
import ast
import sys
import unittest
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from shared_filter_context import shared_filter_context
from evidence_inbox import DeviceEvidenceInbox
from feed_inbox import DeviceFeedInbox
from watchlist_parity import watchlist_row
from dashboard_parity import index_card_model


def factor(direction):
    return {"direction": direction, "source": "dhan",
            "observed_at": 100, "eligible": True}


class SharedFilterContextTest(unittest.TestCase):
    def test_wait_is_same_across_screens(self):
        e = DeviceEvidenceInbox()
        q = DeviceFeedInbox()
        row = watchlist_row("TCS", q, e, selected_equities=("TCS",))
        ctx = shared_filter_context(e.filters, "TCS", "3m",
                                    selected_equities=("TCS",))
        self.assertEqual(row["filter_text"], ctx["compact"])
        self.assertEqual(ctx["coverage"], 0)
        self.assertEqual(ctx["sixth"], ("", ""))
        self.assertFalse(ctx["live_verified"])
        idx = index_card_model("NIFTY", q, e)
        self.assertEqual(idx["filters"], shared_filter_context(e.filters, "NIFTY", "1m")["rows"])

    def test_partial_source_gated_independent_timeframes(self):
        e = DeviceEvidenceInbox()
        e.filters.accept_available("TCS", "3m", 1,
                                   {"candle_trend": factor("bullish")},
                                   allowed_symbols=("TCS",), trusted_transport=True)
        ctx = shared_filter_context(e.filters, "TCS", "3m",
                                    selected_equities=("TCS", "INFY"))
        self.assertEqual(ctx["coverage"], 1)
        self.assertEqual(ctx["rows"][4][1], "BULLISH HIST")
        self.assertEqual(ctx["rows"][0][1], "WAIT")
        self.assertEqual(shared_filter_context(e.filters, "TCS", "1m",
                         selected_equities=("TCS",))["coverage"], 0)
        self.assertEqual(shared_filter_context(e.filters, "INFY", "3m",
                         selected_equities=("TCS", "INFY"))["coverage"], 0)
        with self.assertRaises(ValueError):
            e.filters.accept_available("TCS", "3m", 2,
                {"pcr": factor("bearish")}, allowed_symbols=("TCS",),
                trusted_transport=False)
        self.assertEqual(ctx["sixth"], ("", ""))

    def test_reject_roster_and_invalid_timeframe(self):
        e = DeviceEvidenceInbox()
        for symbol, tf, roster in (("TCS", "3m", ()),
                                   ("TCS", "10m", ("TCS",)),
                                   ("NIFTY", "1m", ("NIFTY",)),
                                   ("TCS", "3m", ("TCS", "TCS")),
                                   ("TCS", "3m", tuple("S"+str(i) for i in range(71)))):
            with self.assertRaises(ValueError):
                shared_filter_context(e.filters, symbol, tf,
                                      selected_equities=roster)

    def test_actual_wiring_all_four_views(self):
        for name in ("main.py", "watchlist_parity.py", "dashboard_parity.py"):
            s = (SRC / name).read_text()
            ast.parse(s)
            self.assertIn("shared_filter_context", s)
            self.assertNotIn("ServerAngelFeed(", s)
            self.assertNotIn("get_yahoo(", s)
        m = (SRC / "main.py").read_text()
        self.assertIn('filter_evidence, item["symbol"], "3m"', m)
        self.assertIn('filter_evidence, scanner[0].symbol, scanner[0].timeframe', m)
        self.assertIn('card["factor_coverage"]', m)

if __name__ == "__main__":
    unittest.main()
