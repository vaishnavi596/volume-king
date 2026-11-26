import unittest

from five_engine import (ContextualFiveEngineCache, EngineEvidence,
                         compose_snapshot, option_from_component)
from v3_option_oi_flow import oi_change_component, underlying_quote_live

NOW = 1795662000.0


def leg(oi, prev):
    return {"oi": float(oi), "previous_oi": float(prev), "volume": 10.0, "last_price": 5.0}


def chain(ce_delta=0, pe_delta=0, base=1000):
    rows = []
    for i, strike in enumerate((24900, 25000, 25100, 25200, 25300, 25400, 25500)):
        # put the whole delta on the ATM strike (index 3)
        cd = ce_delta if i == 3 else 0
        pd = pe_delta if i == 3 else 0
        rows.append({"strike": float(strike), "ce": leg(base + cd, base),
                     "pe": leg(base + pd, base)})
    return {"source": "dhan", "symbol": "NIFTY", "expiry": "2026-12-01",
            "freshness": "unverified", "signal_eligible": False, "pcr": 1.0,
            "max_pain": 25200.0,
            "atm_window": {"source": "dhan", "atm": 25200.0, "rows": rows,
                           "freshness": "unverified", "signal_eligible": False}}


def quote(**over):
    base = {"source": "Dhan", "symbol": "NIFTY", "cached": False,
            "timestamp_origin": "DHAN_QUOTE_LAST_TRADE_TIME",
            "freshness": "exchange_verified", "live_verified": True,
            "quote_timestamp": NOW - 5}
    base.update(over)
    return base


def build(metrics=None, q=None, **over):
    args = dict(quote=q if q is not None else quote(), symbol="NIFTY",
                timeframe="1m", generation=1, observed_at=NOW - 10, now=NOW)
    args.update(over)
    return oi_change_component(metrics if metrics is not None else chain(pe_delta=900), **args)


class OptionOiFlowTests(unittest.TestCase):
    def test_put_buildup_is_bullish_and_call_buildup_bearish(self):
        comp, _ = build(chain(pe_delta=900, ce_delta=100))
        self.assertEqual((comp["bias"], comp["bullish"], comp["bearish"]), ("BULLISH", 90, 10))
        comp, _ = build(chain(ce_delta=800, pe_delta=200))
        self.assertEqual((comp["bias"], comp["bullish"], comp["bearish"]), ("BEARISH", 20, 80))

    def test_unwinding_counts_for_opposite_side(self):
        comp, _ = build(chain(ce_delta=-600))  # call unwinding is bullish
        self.assertEqual(comp["bias"], "BULLISH")
        self.assertEqual(comp["bullish"], 100)

    def test_component_is_accepted_by_option_adapter(self):
        comp, _ = build()
        evidence = option_from_component(comp)
        self.assertTrue(evidence.eligible)
        self.assertEqual((evidence.bullish, evidence.bearish), (comp["bullish"], comp["bearish"]))
        self.assertEqual(evidence.timestamp, NOW - 10)

    def test_fail_closed_cases(self):
        small = chain(pe_delta=1)  # below 1% of window OI
        missing = chain(pe_delta=900)
        missing["atm_window"]["rows"][2]["pe"].pop("previous_oi")
        balanced = chain(pe_delta=500, ce_delta=500)
        cases = [
            build(small), build(missing), build(balanced),
            build(observed_at=NOW - 91), build(observed_at=NOW + 5),
            build(q=quote(quote_timestamp=NOW - 91)),
            build(q=quote(cached=True)),
            build(q=quote(timestamp_origin="LOCAL_CLOCK")),
            build(q=quote(freshness="historical_unverified")),
            build(q=quote(live_verified=False)),
            build(dict(chain(pe_delta=900), symbol="BANKNIFTY")),
            build(dict(chain(pe_delta=900), expiry="01-12-2026")),
            build(dict(chain(pe_delta=900), historical=True)),
            build(timeframe="15m"), build(generation=True), build(symbol="SENSEX"),
        ]
        for component, reason in cases:
            self.assertIsNone(component, reason)

    def test_not_a_directional_vote_without_measured_basis(self):
        comp, _ = build()
        for bad in (dict(comp, direction_basis="pcr"), dict(comp, bias="BEARISH"),
                    dict(comp, verified=False), dict(comp, source="Yahoo")):
            self.assertFalse(option_from_component(bad).eligible)

    def test_underlying_quote_live_requires_fresh_last_trade_time(self):
        self.assertTrue(underlying_quote_live(quote(), symbol="NIFTY", now=NOW))
        self.assertFalse(underlying_quote_live(None, symbol="NIFTY", now=NOW))
        self.assertFalse(underlying_quote_live(quote(), symbol="NIFTY", now=0))

    def test_third_engine_completes_quorum_and_stale_one_does_not(self):
        cache = ContextualFiveEngineCache()
        key = dict(symbol="NIFTY", timeframe="1m", generation=1)
        cache.publish(**key, snapshot=compose_snapshot(
            technical=EngineEvidence("technical", 80, 20, verified=True, timestamp=NOW - 30, source="Dhan"),
            candle=EngineEvidence("candle", 70, 30, verified=True, timestamp=NOW - 10, source="Dhan")))
        stale, _ = build(observed_at=NOW - 200)
        self.assertIsNone(stale)
        comp, _ = build()
        self.assertTrue(cache.publish_directional_components(**key, now=NOW, options=comp))
        combined = cache.peek(**key)["combined"]
        self.assertEqual((combined["state"], combined["coverage"]), ("BULLISH", 3))
        # contradictory live flag from a foreign producer is still rejected
        self.assertFalse(cache.publish_directional_components(
            **key, now=NOW, options=dict(comp, live_verified=False)))


if __name__ == "__main__":
    unittest.main()
