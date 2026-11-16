"""All 54 configured symbols reject malformed assessment filters at feed boundary.

No network, keys or broker market requests are made in this suite.
"""
import sys
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from server_feed import ServerDhanReadOnly, DHAN_VERIFIED_SYMBOLS, FeedError

IDS = ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")


def payload(symbol, bad_id=None):
    rows = [{"id": value, "status": "unavailable"} for value in IDS]
    if bad_id is not None:
        rows[0]["id"] = bad_id
    return {
        "symbol": symbol, "live_orders_enabled": False,
        "signal_eligible": False, "bullish_score": None, "bearish_score": None,
        "factors": {name: {"status": "unavailable"} for name in
                    ("news", "futures", "options", "candle")},
        "assessment_filters": rows,
    }


class AssessmentTransport54Tests(TestCase):
    def test_54_roster_allows_same_complete_placeholder_contract(self):
        self.assertEqual(len(DHAN_VERIFIED_SYMBOLS), 54)
        feed = ServerDhanReadOnly()
        for symbol in sorted(DHAN_VERIFIED_SYMBOLS):
            with self.subTest(symbol=symbol):
                with patch.object(feed, "_call", return_value=payload(symbol)) as call:
                    self.assertEqual(feed.assessment(symbol)["symbol"], symbol)
                    call.assert_called_once_with("/v2/assessment/" + symbol)

    def test_nonobject_assessment_payload_fails_as_feederror_for_every_symbol(self):
        feed = ServerDhanReadOnly()
        for symbol in sorted(DHAN_VERIFIED_SYMBOLS):
            for invalid in (None, [], "not configured", 200):
                with self.subTest(symbol=symbol, invalid=type(invalid).__name__):
                    with patch.object(feed, "_call", return_value=invalid):
                        with self.assertRaises(FeedError):
                            feed.assessment(symbol)

    def test_unhashable_filter_ids_fail_as_feederror_for_every_symbol(self):
        feed = ServerDhanReadOnly()
        for symbol in sorted(DHAN_VERIFIED_SYMBOLS):
            for wrong in ([], {"bad": 1}):
                with self.subTest(symbol=symbol, wrong=type(wrong).__name__):
                    with patch.object(feed, "_call", return_value=payload(symbol, wrong)):
                        with self.assertRaises(FeedError):
                            feed.assessment(symbol)


if __name__ == "__main__":
    main()
