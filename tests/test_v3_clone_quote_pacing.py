"""V3 Clone quote lane: offline-only 429 and minimum pacing assertions."""
import time
import unittest
import pathlib
import sys
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from clone_v2_gateway import CloneDhanReadOnly
from server_feed import FeedError


class OfflineGateway:
    connected = True
    def __init__(self):
        self.calls = []
        self.raise_paced = False
    def market_quotes(self, symbols):
        self.calls.append((tuple(symbols), time.monotonic()))
        if self.raise_paced:
            raise FeedError("Clone Dhan quote lane paced; retry later")
        return {name: 100.0 for name in symbols}
    def disconnect(self):
        self.connected = False


class CloneQuotePacingTests(unittest.TestCase):
    def test_equity_then_index_has_gateway_safe_spacing(self):
        gateway = OfflineGateway()
        feed = CloneDhanReadOnly(gateway)
        a = feed._fetch(["RELIANCE"])
        b = feed.index_batch_quotes()
        self.assertEqual(a["RELIANCE"], 100.0)
        self.assertEqual(set(b), {"NIFTY","BANKNIFTY","SENSEX"})
        self.assertEqual(len(gateway.calls), 2)
        self.assertGreaterEqual(gateway.calls[1][1] - gateway.calls[0][1], 1.05)

    def test_429_blocks_immediate_retries_across_index_and_equity(self):
        gateway = OfflineGateway()
        gateway.raise_paced = True
        feed = CloneDhanReadOnly(gateway)
        with self.assertRaisesRegex(FeedError,"paced"):
            feed.index_batch_quotes()
        self.assertGreater(feed.cooldown_remaining("/dhan/index-ltp-batch"), 25)
        with self.assertRaisesRegex(FeedError,"cooldown active"):
            feed._fetch(["RELIANCE"])
        self.assertEqual(len(gateway.calls), 1)

    def test_unverified_quotes_preserve_dhan_source(self):
        gateway = OfflineGateway()
        feed = CloneDhanReadOnly(gateway)
        rows = feed.index_batch_quotes()
        self.assertTrue(all(row["source"] == "Dhan"
                            and row["live_verified"] is False
                            and row["quote_timestamp"] is None
                            for row in rows.values()))


if __name__ == "__main__":
    unittest.main()
