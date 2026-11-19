"""One V2 atomic evidence staging contract; synthetic and no auth claim."""
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from evidence_inbox import DeviceEvidenceInbox
from app_evidence_batch import apply_staged_evidence_batch, EvidenceBatchError

IST = timezone(timedelta(hours=5, minutes=30))
T0 = int(datetime(2026, 11, 18, 9, 15, tzinfo=IST).timestamp())

def candles():
    return [
        {"timestamp": T0 + i * 60, "open": 100., "high": 102.,
         "low": 99., "close": 101., "volume": 7., "completed": True}
        for i in range(4)
    ]

class AppEvidenceBatchTests(unittest.TestCase):
    def setUp(self):
        self.e = DeviceEvidenceInbox()

    def test_two_events_atomic_same_holders(self):
        original = self.e.candles
        events = [
            {"kind": "candles", "symbol": "TCS", "timeframe": "1m",
             "revision": 1, "bars": candles()},
            {"kind": "expiries", "symbol": "TCS", "revision": 1,
             "available": ["2026-11-26", "2026-12-31"]},
        ]
        result = apply_staged_evidence_batch(
            self.e, events, selected_equities=("TCS",),
            trusted_transport=True)
        self.assertEqual(result["updated"], 2)
        self.assertIs(self.e.candles, original)
        self.assertEqual(self.e.candles.view(
            "TCS", "1m", selected_equities=("TCS",))["count"], 4)
        self.assertEqual(self.e.expiries.available(
            "TCS", selected_equities=("TCS",)),
            ("2026-11-26", "2026-12-31"))
        self.assertFalse(result["live_verified"])

    def test_failure_in_later_event_rolls_back_all_lanes(self):
        original = self.e.candles
        invalid = [
            {"kind": "candles", "symbol": "TCS", "timeframe": "1m",
             "revision": 1, "bars": candles()},
            {"kind": "expiries", "symbol": "TCS", "revision": 1,
             "available": ["2026-11-26", "2026-11-26"]},
        ]
        with self.assertRaises(ValueError):
            apply_staged_evidence_batch(
                self.e, invalid, selected_equities=("TCS",),
                trusted_transport=True)
        self.assertIs(self.e.candles, original)
        self.assertEqual(self.e.candles.view(
            "TCS", "1m", selected_equities=("TCS",))["status"], "WAIT")
        self.assertEqual(self.e.expiries.available(
            "TCS", selected_equities=("TCS",)), ())

    def test_roster_or_transport_and_payload_errors_fail_closed(self):
        event = {"kind": "candles", "symbol": "TCS", "timeframe": "1m",
                 "revision": 1, "bars": candles()}
        for events, roster, trust in [
            ([event], ("TCS",), False),
            ([event], (), True),
            ([dict(event, extra="x")], ("TCS",), True),
            ([dict(event, timeframe="60m")], ("TCS",), True),
            ([dict(event, symbol="NIFTY")], ("TCS",), False),
        ]:
            with self.subTest(events=events, roster=roster, trust=trust):
                with self.assertRaises(ValueError):
                    apply_staged_evidence_batch(
                        self.e, events, selected_equities=roster,
                        trusted_transport=trust)
        self.assertEqual(self.e.candles.view(
            "TCS", "1m", selected_equities=("TCS",))["status"], "WAIT")

    def test_do_not_claim_live_login_or_server_api(self):
        main = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertNotIn("apply_staged_evidence_batch(", main)
        self.assertNotIn("submit_order(", main)
        self.assertNotIn("ServerAngelFeed(", main)

if __name__ == "__main__":
    unittest.main()
