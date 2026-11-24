"""Regression checks for Dhan read-only activation after verified LTP."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from server_feed import ServerDhanReadOnly
from market_feed import FeedError


class DhanActivationTests(unittest.TestCase):
    def test_uses_verified_quote_without_second_network_call(self):
        feed = ServerDhanReadOnly()
        quote = {"source": "dhan", "symbol": "NIFTY", "ltp": 25030.35,
                 "live_orders_enabled": False}
        with patch.object(feed, "_call", side_effect=AssertionError("duplicate request")):
            feed.activate_verified("https://example.org", "test-pairing-key", quote)
        self.assertTrue(feed.connected)
        self.assertFalse(feed.historical_only)
        feed.disconnect()
        self.assertFalse(feed.connected)

    def test_historical_activation_requires_real_read_only_candles(self):
        feed = ServerDhanReadOnly()
        candles = {"source": "dhan", "symbol": "RELIANCE",
                   "live_orders_enabled": False,
                   "freshness": "historical_unverified",
                   "bars": [[1762500000, 100.0, 102.0, 99.0, 101.0, 500]]}
        feed.activate_historical_verified("https://example.org", "test-pairing-key", candles)
        self.assertTrue(feed.connected)
        self.assertTrue(feed.historical_only)
        feed.disconnect()
        self.assertFalse(feed.historical_only)
        for bad in (dict(candles, bars=[]),
                    dict(candles, live_orders_enabled=True),
                    dict(candles, freshness="live"),
                    dict(candles, symbol="NIFTY")):
            with self.subTest(bad=bad):
                with self.assertRaises(FeedError):
                    feed.activate_historical_verified("https://example.org", "test-pairing-key", bad)
                self.assertFalse(feed.connected)

    def test_historical_activation_rejects_malformed_ohlc(self):
        base = {"source": "dhan", "symbol": "RELIANCE",
                "live_orders_enabled": False, "freshness": "historical_unverified"}
        for bars in ([[1762500000, 100, 102, 99, 101]],
                     [[1762500000, 0, 102, 99, 101, 500]],
                     [[1762500000, 100, float("nan"), 99, 101, 500]],
                     [[1762500000, 100, True, 99, 101, 500]],
                     [[1762500000, 100, 102, 99, 101, "500"]],
                     [[1762500000, 100, 102, 99, 101, -1]],
                     [[1762500000, 100, 102, 99, 101, float("inf")]]):
            with self.subTest(bars=bars):
                feed = ServerDhanReadOnly()
                with self.assertRaises(FeedError):
                    feed.activate_historical_verified("https://example.org", "key", dict(base, bars=bars))
                self.assertFalse(feed.connected)

    def test_historical_activation_rejects_bad_order_and_price_geometry(self):
        base = {"source": "dhan", "symbol": "RELIANCE",
                "live_orders_enabled": False, "freshness": "historical_unverified"}
        valid = [1762500000, 100, 102, 99, 101, 500]
        for bars in (
            [[0, 100, 102, 99, 101, 500]],
            [[1762500000, 100, 100, 99, 101, 500]],
            [[1762500000, 100, 102, 101, 101, 500]],
            [valid, valid],
            [[1762500300, 100, 102, 99, 101, 500], valid],
        ):
            with self.subTest(bars=bars):
                feed = ServerDhanReadOnly()
                with self.assertRaises(FeedError):
                    feed.activate_historical_verified("https://example.org", "key", dict(base, bars=bars))
                self.assertFalse(feed.connected)

    def test_historical_only_contract_in_main(self):
        main = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        # Legacy V1 historical-only activation is no longer an Android login
        # fallback. The current Clone SSK requires real quote proof.
        self.assertIn("dhan_feed.activate_with_quote(proof)",main)
        self.assertIn('"freshness":"unverified" if quote else "historical_unverified"',main)
        self.assertNotIn("activate_historical_verified(endpoint,pairing_key,candles)",main)


    def test_index_batch_can_activate_login_after_individual_probe_failure(self):
        from server_feed import validated_login_index_batch
        prices={"NIFTY":25144.3,"BANKNIFTY":61034.1,"SENSEX":81592.45}
        batch={"source":"dhan","freshness":"unverified","live_orders_enabled":False,
               "quotes":{sym:{"symbol":sym,"source":"dhan","ltp":price}
                         for sym,price in prices.items()},"unavailable":[]}
        checked=validated_login_index_batch(batch)
        self.assertEqual(len(checked),3)
        self.assertEqual(checked["NIFTY"]["ltp"],25144.3)
        feed=ServerDhanReadOnly()
        with patch.object(feed,"_call",side_effect=AssertionError("extra quote request")):
            feed.activate_verified("https://example.org","test-pairing-key",checked["NIFTY"])
        self.assertTrue(feed.connected)
        self.assertFalse(feed.historical_only)

    def test_index_batch_login_fails_closed_on_missing_and_fake_data(self):
        from server_feed import validated_login_index_batch
        valid={"source":"dhan","freshness":"unverified","live_orders_enabled":False,
               "quotes":{"NIFTY":{"symbol":"NIFTY","source":"dhan","ltp":25144.3}},
               "unavailable":["BANKNIFTY","SENSEX"]}
        self.assertEqual(set(validated_login_index_batch(valid)),{"NIFTY"})
        invalids=[
            dict(valid,live_orders_enabled=True),
            dict(valid,quotes={},unavailable=["NIFTY","BANKNIFTY","SENSEX"]),
            dict(valid,quotes={"NIFTY":{"symbol":"NIFTY","source":"dhan","ltp":True}}),
            dict(valid,quotes={"NIFTY":{"symbol":"NIFTY","source":"dhan","ltp":float("nan")}}),
            dict(valid,unavailable=["NIFTY","SENSEX"]),
            dict(valid,unavailable=["BANKNIFTY"]),
            dict(valid,freshness="live"),
        ]
        for payload in invalids:
            with self.subTest(payload=payload),self.assertRaises(FeedError):
                validated_login_index_batch(payload)

    def test_index_login_fallback_is_before_historical_only_and_reuses_prices(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
        block=source.split('    async def check_clone_v2_connection():',1)[1].split('    def check_clone_v2_gateway(e):',1)[0]
        self.assertIn('dhan_feed.paced_market_quotes,request_symbols',block)
        # A verified equity quote may establish a partial connection even when
        # all index quotes are unavailable. Zero validated quotes must still fail.
        self.assertIn("if not proof:",block)
        self.assertNotIn('if "NIFTY" not in proof:',block)
        self.assertIn("dhan_feed.activate_with_quote(proof)",block)
        self.assertIn('login_bootstrap.finish(provider_generation[0],"indices",received_indices,3)',block)
        self.assertIn("if received_indices==3:",block)
        # A complete first index batch must not immediately repeat against Dhan.
        self.assertIn("index_last_attempt[0]=time.monotonic()",block)
        self.assertNotIn('page.run_task(refresh_dhan_index_quotes,True)',block)

    def test_rejects_unverified_or_live_order_responses(self):
        for quote in (
            {"source": "dhan", "symbol": "NIFTY", "ltp": 25030.35,
             "live_orders_enabled": True},
            {"source": "dhan", "symbol": "NIFTY", "ltp": 0,
             "live_orders_enabled": False},
            {"source": "dhan", "symbol": "BANKNIFTY", "ltp": 25030.35,
             "live_orders_enabled": False},
        ):
            with self.subTest(quote=quote):
                feed = ServerDhanReadOnly()
                with self.assertRaises(FeedError):
                    feed.activate_verified("https://example.org", "test-pairing-key", quote)
                self.assertFalse(feed.connected)


if __name__ == "__main__":
    unittest.main()
