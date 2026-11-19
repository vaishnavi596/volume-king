"""V2 Dhan historical cached-candle transport contracts: synthetic offline only."""
import json
import unittest
from urllib.error import HTTPError

from pilot_v2.oracle_dhan_cached_candles import (
    OracleDhanCachedCandleTransport, normalize_cached_bars)
from pilot_v2.oracle_evidence_lane import (
    DhanEvidenceBatch, RoundRobinDhanEvidenceTransport,
    OracleDhanEvidenceLane)
from pilot_v2.shared_read_budget import SharedReadBudget
from pilot_v2.internal_dhan_read_port import DhanReadUnavailable
from pilot_v2.unified_data_pipeline import PipelineUnavailable

KEY = "only-the-private-operator-can-supply-key-1234"
BASE = 1800000000 - (1800000000 % 180)
NOW = BASE + 1800


def minute_rows(count=12):
    result = []
    for i in range(count):
        price = 101.0 + i
        result.append([BASE + 60 * i, price, price + 2, price - 1,
                       price + 1, 100 + i])
    return result


def payload(*, interval="1m", symbol="NIFTY", rows=None):
    return {"source": "dhan", "symbol": symbol,
            "interval": interval, "freshness": "historical_unverified",
            "bars": minute_rows() if rows is None else rows,
            "live_orders_enabled": False}


class Reply:
    status = 200
    def __init__(self, url, data):
        self._url = url
        self._data = json.dumps(data).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def geturl(self):
        return self._url
    def read(self, count):
        return self._data[:count]


class Opener:
    def __init__(self, body, *, redirect=False, error=None):
        self.body = body
        self.redirect = redirect
        self.error = error
        self.calls = []
    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        url = request.full_url + "/redirect" if self.redirect else request.full_url
        return Reply(url, self.body)


class CachedDhanCandleTests(unittest.TestCase):
    def test_no_missing_minute_3m_aggregation_preserves_real_ohlcv(self):
        bars = normalize_cached_bars(minute_rows(12), timeframe="3m", now=NOW)
        self.assertEqual(len(bars), 4)
        first = bars[0]
        self.assertEqual(first["timestamp"], BASE)
        self.assertEqual(first["open"], 101)
        self.assertEqual(first["high"], 105)
        self.assertEqual(first["low"], 100)
        self.assertEqual(first["close"], 104)
        self.assertEqual(first["volume"], 303)
        self.assertIs(first["completed"], True)
        missing = [r for r in minute_rows(12) if r[0] != BASE + 60]
        self.assertEqual(len(normalize_cached_bars(
            missing, timeframe="3m", now=NOW)), 3)

    def test_3m_close_delay_rejects_open_bar_and_no_fake_gap_fill(self):
        self.assertEqual(len(normalize_cached_bars(
            minute_rows(12), timeframe="3m", now=BASE + 650)), 2)
        with self.assertRaises(ValueError):
            normalize_cached_bars(minute_rows(4), timeframe="3m", now=BASE + 650)
        with self.assertRaises(ValueError):
            normalize_cached_bars(
                [minute_rows()[0], minute_rows()[0]], timeframe="3m", now=NOW)
        tampered = minute_rows()
        tampered[3][2] = 1  # high below open
        with self.assertRaises(ValueError):
            normalize_cached_bars(tampered, timeframe="3m", now=NOW)

    def test_fixed_local_protected_dhan_history_and_no_fabricated_live(self):
        opener = Opener(payload())
        transport = OracleDhanCachedCandleTransport(
            pairing_key=KEY, symbol="NIFTY", timeframe="3m",
            opener=opener, clock=lambda: NOW)
        result = transport()
        self.assertEqual(result.source, "dhan")
        self.assertEqual(result.revision, 1)
        self.assertEqual(result.events[0]["timeframe"], "3m")
        self.assertEqual(len(result.events[0]["bars"]), 4)
        self.assertEqual(len(opener.calls), 1)
        req, timeout = opener.calls[0]
        self.assertEqual(req.full_url,
                         "http://127.0.0.1:8000/v2/candles/NIFTY/1")
        self.assertEqual(req.get_method(), "GET")
        self.assertEqual(req.get_header("X-botking-key"), KEY)
        self.assertNotIn("live_verified", str(result.events))
        self.assertEqual(transport().revision, 2)

    def test_untrusted_source_redirect_and_unsupported_symbols_fail_closed(self):
        for incorrect in (
            dict(payload(), source="mock"),
            dict(payload(), symbol="TCS"),
            dict(payload(), freshness="live"),
            dict(payload(), interval="5m"),
            dict(payload(), live_orders_enabled=True),
            dict(payload(), bars=[]),
        ):
            with self.subTest(item=str(incorrect)[:60]):
                transport = OracleDhanCachedCandleTransport(
                    pairing_key=KEY, symbol="NIFTY", opener=Opener(incorrect),
                    clock=lambda: NOW)
                with self.assertRaises(DhanReadUnavailable):
                    transport()
        transport = OracleDhanCachedCandleTransport(
            pairing_key=KEY, symbol="NIFTY",
            opener=Opener(payload(), redirect=True), clock=lambda: NOW)
        with self.assertRaises(DhanReadUnavailable):
            transport()
        for value in ("", "tcs", "NIFTY/../orders", None):
            with self.assertRaises(ValueError):
                OracleDhanCachedCandleTransport(pairing_key=KEY, symbol=value)

    def test_one_at_a_time_expiry_and_candle_producers_share_budget(self):
        calls = []

        def make(symbol):
            def collect():
                calls.append(symbol)
                return DhanEvidenceBatch("dhan", calls.count(symbol), NOW, [{
                    "kind": "expiries", "symbol": symbol,
                    "revision": calls.count(symbol),
                    "available": ["2026-11-26"]}])
            return collect

        mux = RoundRobinDhanEvidenceTransport([make("NIFTY"), make("SENSEX")])
        ticks = [100.0]
        budget = SharedReadBudget(monotonic=lambda: ticks[0])
        lane = OracleDhanEvidenceLane(
            transport=mux, read_budget=budget,
            monotonic=lambda: ticks[0], clock=lambda: NOW, cache_seconds=30)
        self.assertEqual(lane("master")["events"][0]["symbol"], "NIFTY")
        self.assertEqual(lane("delegate")["events"][0]["symbol"], "NIFTY")
        self.assertEqual(calls, ["NIFTY"])
        ticks[0] += 31
        self.assertEqual(lane("master")["events"][0]["symbol"], "SENSEX")
        self.assertEqual(calls, ["NIFTY", "SENSEX"])
        ticks[0] += 31
        self.assertEqual(lane("delegate")["events"][0]["symbol"], "NIFTY")
        self.assertEqual(calls, ["NIFTY", "SENSEX", "NIFTY"])


if __name__ == "__main__":
    unittest.main()
