import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend"))
sys.path.append(str(ROOT / "src"))
import clone_signal_runner as r  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime(2026, 11, 26, 10, 31, 20, tzinfo=IST).timestamp()  # Thursday


def bars(width=60, n=40):
    last = datetime(2026, 11, 26, 10, 30, tzinfo=IST).timestamp()
    out, price = [], 100.0
    for i in range(n):
        t = int(last - (n - 1 - i) * width)
        price += 0.3 if i % 3 else -0.1
        out.append([t, price, price + 0.2, price - 0.2, price + 0.1, 1000.0 + i])
    return out


def response(b):
    import hashlib
    digest = hashlib.sha256(json.dumps(b, separators=(",", ":")).encode()).hexdigest()
    return r.with_integrity({"source": "dhan", "symbol": "NIFTY", "interval": "1m", "bars": b,
                             "candle_origin": "DHAN_INTRADAY_TIMESTAMP",
                             "normalized_bars_sha256": digest})


QUOTE = {"exchange_trade_timestamp": datetime(2026, 11, 26, 10, 31, 10, tzinfo=IST).timestamp(),
         "timestamp_origin": "DHAN_QUOTE_LAST_TRADE_TIME"}


class Runner(unittest.TestCase):
    def test_live_qualified_gets_votes(self):
        row = r.evaluate("NIFTY", "1m", response(bars()), QUOTE, NOW)
        self.assertEqual(row["state"], "LIVE_VERIFIED")
        self.assertGreaterEqual(row["directional"], 1)

    def test_no_quote_timestamp_stays_unqualified(self):
        row = r.evaluate("NIFTY", "1m", response(bars()), {"ltp": 1.0}, NOW)
        self.assertEqual(row["state"], "UNQUALIFIED")

    def test_stale_quote_stays_unqualified(self):
        old = dict(QUOTE, exchange_trade_timestamp=NOW - 400)
        row = r.evaluate("NIFTY", "1m", response(bars()), old, NOW)
        self.assertEqual(row["state"], "UNQUALIFIED")

    def test_digest_mismatch_is_not_live(self):
        resp = response(bars())
        resp["bars"][-1][4] += 5
        resp = r.with_integrity(resp)
        row = r.evaluate("NIFTY", "1m", resp, QUOTE, NOW)
        self.assertEqual(row["state"], "UNQUALIFIED")

    def test_closed_market_makes_no_requests(self):
        saturday = datetime(2026, 11, 28, 11, 0, tzinfo=IST).timestamp()
        out = r.cycle("k", saturday, 0, None)
        self.assertFalse(out["market_open"])
        self.assertEqual(out["symbols"], {})
        self.assertFalse(out["live_orders_enabled"])


if __name__ == "__main__":
    unittest.main()
