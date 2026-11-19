"""Offline contract tests for the Oracle V1 -> V2 internal read-only transport."""
import json
import unittest
from urllib.error import HTTPError

from pilot_v2.oracle_dhan_read_transport import OracleDhanReadTransport
from pilot_v2.internal_dhan_read_port import DhanRateLimited, DhanReadUnavailable, INDEXES


class Reply:
    status = 200
    def __init__(self, url, payload):
        self.url = url
        self.payload = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def geturl(self):
        return self.url
    def read(self, size):
        return self.payload[:size]


class Opener:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.calls = []
    def open(self, request, timeout):
        self.calls.append((request.full_url, request.get_method(), request.data, timeout))
        if self.error is not None:
            raise self.error
        return Reply(request.full_url, self.payload)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.key = "test-private-key-value-" * 3

    def test_indices_complete_and_only_local(self):
        symbols = INDEXES
        payload = {"source": "dhan", "live_orders_enabled": False,
                   "quotes": {s: {"ltp": 100.0} for s in symbols},
                   "unavailable": [], "freshness": "unverified"}
        opener = Opener(payload)
        bridge = OracleDhanReadTransport(pairing_key=self.key, opener=opener,
                                         clock=lambda: 1800000000.0)
        batch = bridge("indices", symbols)
        self.assertEqual(batch.symbols, symbols)
        self.assertEqual(batch.revision, 1)
        self.assertEqual(set(batch.rows), set(symbols))
        self.assertEqual(opener.calls[0][0], "http://127.0.0.1:8000/dhan/index-ltp-batch")
        self.assertEqual(opener.calls[0][1], "POST")

    def test_equities_only_requested(self):
        opener = Opener({"source": "dhan", "live_orders_enabled": False,
                         "quotes": {"TCS": 125.0}, "unavailable": []})
        bridge = OracleDhanReadTransport(pairing_key=self.key, opener=opener,
                                         clock=lambda: 1800000000.0)
        self.assertEqual(bridge("quotes", ("TCS",)).rows["TCS"]["price"], 125)
        self.assertEqual(json.loads(opener.calls[0][2]), {"symbols": ["TCS"]})

    def test_partial_or_fake_live_rejected(self):
        for payload in (
            {"source": "dhan", "live_orders_enabled": False,
             "quotes": {"TCS": 125}, "unavailable": ["INFY"]},
            {"source": "mock", "live_orders_enabled": False,
             "quotes": {"TCS": 125, "INFY": 200}, "unavailable": []},
            {"source": "dhan", "live_orders_enabled": True,
             "quotes": {"TCS": 125, "INFY": 200}, "unavailable": []},
        ):
            with self.subTest(payload=payload):
                b = OracleDhanReadTransport(pairing_key=self.key,
                    opener=Opener(payload), clock=lambda: 1800000000)
                with self.assertRaises(DhanReadUnavailable):
                    b("quotes", ("TCS", "INFY"))

    def test_429_and_guard(self):
        error = HTTPError("http://127.0.0.1:8000/dhan/index-ltp-batch",
                          429, "cooldown", {}, None)
        b = OracleDhanReadTransport(pairing_key=self.key, opener=Opener(error=error))
        with self.assertRaises(DhanRateLimited):
            b("indices", INDEXES)
        with self.assertRaises(DhanReadUnavailable):
            b("quotes", ("TCS", "TCS"))
        with self.assertRaises(DhanReadUnavailable):
            b("quotes", tuple("A" for _ in range(71)))


if __name__ == "__main__":
    unittest.main()
