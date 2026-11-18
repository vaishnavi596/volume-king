"""Synthetic V2 app evidence inbox integration, no Oracle/Dhan connection."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(ROOT))
from evidence_inbox import DeviceEvidenceInbox
from option_evidence import OptionEvidenceError
from filter_evidence import FilterEvidenceError


def bars(end=200):
    return [
        {"timestamp": 100, "open": 100, "high": 104, "low": 99,
         "close": 102, "volume": 3, "completed": True},
        {"timestamp": end, "open": 102, "high": 106, "low": 101,
         "close": 103, "volume": 4, "completed": True},
    ]


def factor(t=200, direction="bullish"):
    return {"direction": direction, "source": "dhan",
            "observed_at": t, "eligible": True}


def metrics(symbol="NIFTY", revision=1, observed=400):
    return {"symbol": symbol, "expiry": "2026-11-26", "revision": revision,
            "observed_at": observed, "source": "dhan", "ce_oi": 100,
            "pe_oi": 120, "pcr": 1.2, "max_pain": 25000, "eligible": True}


class EvidenceInboxTests(unittest.TestCase):
    def setUp(self):
        self.inbox = DeviceEvidenceInbox()

    def test_candle_and_option_factors_independent_and_sixth_blank(self):
        x = self.inbox
        self.assertTrue(x.apply_candles("NIFTY", "1m", 1, bars(), trusted_transport=True))
        self.assertTrue(x.apply_candle_trend(
            "NIFTY", "1m", 1, factor(), trusted_transport=True))
        x.apply_expiries("NIFTY", 1, ["2026-11-26"],
                         trusted_transport=True)
        x.select_expiry("NIFTY", "2026-11-26")
        x.apply_options(metrics(), trusted_transport=True)
        x.apply_option_factors("NIFTY", "1m", 1, {"pcr": factor(400)},
                               trusted_transport=True)
        rows = x.filters.rows("NIFTY", "1m")
        self.assertEqual([value for _, value in rows[:5]],
                         ["WAIT", "WAIT", "WAIT", "BULLISH HIST", "BULLISH HIST"])
        self.assertEqual(rows[5], ("", ""))
        self.assertEqual(x.filters.rows("NIFTY", "3m")[4][1], "WAIT")

    def test_denied_untrusted_or_unselected_evidence_preserves_last_good(self):
        x = self.inbox
        x.apply_candles("TCS", "3m", 1, bars(),
                        selected_equities=("TCS",), trusted_transport=True)
        x.apply_candle_trend("TCS", "3m", 1, factor(),
                             selected_equities=("TCS",), trusted_transport=True)
        with self.assertRaises(ValueError):
            x.apply_candles("TCS", "3m", 2, bars(300),
                            selected_equities=("TCS",), trusted_transport=False)
        with self.assertRaises(FilterEvidenceError):
            x.apply_candle_trend("TCS", "3m", 2, factor(300),
                                 selected_equities=("TCS",), trusted_transport=False)
        with self.assertRaises(ValueError):
            x.apply_candles("TCS", "3m", 2, bars(300), trusted_transport=True)
        self.assertEqual(x.candles.view("TCS", "3m",
                                      selected_equities=("TCS",))["count"], 2)
        self.assertEqual(x.filters.rows("TCS", "3m", selected_equities=("TCS",))[4][1],
                         "BULLISH HIST")

    def test_option_revisions_expiry_change_and_failed_join_keep_candle(self):
        x = self.inbox
        x.apply_candles("NIFTY", "1m", 1, bars(), trusted_transport=True)
        x.apply_candle_trend("NIFTY", "1m", 1, factor(),
                             trusted_transport=True)
        x.apply_expiries("NIFTY", 1, ["2026-11-26", "2026-12-03"],
                         trusted_transport=True)
        x.select_expiry("NIFTY", "2026-11-26")
        x.apply_options(metrics(), trusted_transport=True)
        with self.assertRaises(FilterEvidenceError):
            x.apply_option_factors("NIFTY", "1m", 1, {"pcr": factor(401)},
                                   trusted_transport=True)
        self.assertEqual(x.filters.rows("NIFTY", "1m")[4][1], "BULLISH HIST")
        x.apply_option_factors("NIFTY", "1m", 1, {"pcr": factor(400)},
                               trusted_transport=True)
        with self.assertRaises(OptionEvidenceError):
            x.select_expiry("NIFTY", "2026-12-31")
        self.assertEqual(x.filters.rows("NIFTY", "1m")[3][1], "BULLISH HIST")
        x.select_expiry("NIFTY", "2026-12-03")
        self.assertEqual(x.filters.rows("NIFTY", "1m")[3][1], "WAIT")
        self.assertEqual(x.filters.rows("NIFTY", "1m")[4][1], "BULLISH HIST")

    def test_removed_roster_cannot_expose_old_equity_evidence(self):
        x = self.inbox
        with self.assertRaises(ValueError):
            x.allowed(("TCS", "TCS"))
        x.apply_candles("TCS", "3m", 1, bars(),
                        selected_equities=("TCS",), trusted_transport=True)
        x.apply_candle_trend("TCS", "3m", 1, factor(),
                             selected_equities=("TCS",), trusted_transport=True)
        x.forget_removed(())
        self.assertEqual(x.candles.view("TCS", "3m",
                                       selected_equities=("TCS",))["status"], "WAIT")
        self.assertEqual(x.filters.rows("TCS", "3m",
                                        selected_equities=("TCS",))[4][1], "WAIT")
        self.assertEqual(x.filters.rows("NIFTY", "1m")[4][1], "WAIT")

    def test_flet_source_uses_one_inbox_for_ui_and_removal(self):
        src = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn("evidence_inbox = DeviceEvidenceInbox()", src)
        self.assertIn("candle_history = evidence_inbox.candles", src)
        self.assertIn("filter_evidence = evidence_inbox.filters", src)
        self.assertIn("option_evidence = evidence_inbox.options", src)
        self.assertIn("expiry_choices = evidence_inbox.expiries", src)
        self.assertIn("evidence_inbox.forget_removed(state.selected)", src)


if __name__ == "__main__":
    unittest.main()
