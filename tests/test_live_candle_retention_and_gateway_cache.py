import sys, unittest
from datetime import datetime, timezone, timedelta
sys.path.insert(0, "src")
from candle_retention import retain_candle_history

IST = timezone(timedelta(hours=5, minutes=30))

def bars(start, n):
    return [[start + 60 * i, 100.0, 101.0, 99.0, 100.5, 10.0] for i in range(n)]

class RetentionTest(unittest.TestCase):
    def test_live_completed_list_replaces_prior_with_forming_bar(self):
        old = {"source": "Dhan", "_scanner_timeframe": "1m", "bars": bars(1000000, 41)}
        new = {"source": "Dhan", "_scanner_timeframe": "1m", "bars": bars(1000000, 40),
               "live_verified": True, "historical": False, "freshness": "exchange_verified"}
        out = retain_candle_history(new, old)
        self.assertTrue(out["live_verified"])
        self.assertEqual(len(out["bars"]), 40)
        self.assertNotIn("_candle_retained", out)

    def test_unqualified_older_window_still_retained(self):
        old = {"source": "Dhan", "_scanner_timeframe": "1m", "bars": bars(1000000, 41)}
        new = {"source": "Dhan", "_scanner_timeframe": "1m", "bars": bars(1000000, 40),
               "live_verified": False, "historical": True, "freshness": "historical_unverified"}
        self.assertTrue(retain_candle_history(new, old).get("_candle_retained"))

    def test_live_but_two_frames_behind_still_retained(self):
        old = {"source": "Dhan", "_scanner_timeframe": "1m", "bars": bars(1000000, 42)}
        new = {"source": "Dhan", "_scanner_timeframe": "1m", "bars": bars(1000000, 40),
               "live_verified": True, "historical": False, "freshness": "exchange_verified"}
        self.assertTrue(retain_candle_history(new, old).get("_candle_retained"))

class GatewayCacheSource(unittest.TestCase):
    def test_cache_rule_present(self):
        src = open("backend/clone_v2_gateway.py").read()
        self.assertIn("candle_cache_current(cached, body.interval, body.to_date)", src)
        self.assertIn("(time.monotonic(), payload, time.time())", src)

    def test_cache_rule_behaviour(self):
        src = open("backend/clone_v2_gateway.py").read()
        start = src.index("    def candle_cache_current")
        end = src.index("\n    candle_cache_max_entries") if False else src.index("    candle_cache_lock", start) if False else None
        block = src[start:src.index("        return True\n", src.index("last = entry[1]", start)) + len("        return True\n")]
        import textwrap, time
        ns = {"time": time, "datetime": datetime, "timezone": timezone, "timedelta": timedelta}
        exec(textwrap.dedent(block), ns)
        f = ns["candle_cache_current"]
        day = datetime(2026, 11, 27, tzinfo=IST)
        t = lambda h, m, s: day.replace(hour=h, minute=m, second=s).timestamp()
        # fetched 11:42:30, asked 11:42:50 -> same bar, reusable
        e = (0, {"last_candle_timestamp": t(11, 42, 0)}, t(11, 42, 30))
        self.assertTrue(f(e, 1, day.date(), now=t(11, 42, 50)))
        # asked 11:43:10 -> a bar closed since the fetch, refetch
        self.assertFalse(f(e, 1, day.date(), now=t(11, 43, 10)))
        # asked 11:43:01 (inside grace) -> still reusable
        self.assertTrue(f(e, 1, day.date(), now=t(11, 43, 1)))
        # after hours plain TTL applies
        self.assertTrue(f(e, 1, day.date(), now=t(16, 30, 0)))
        # a historical window is untouched
        self.assertTrue(f(e, 1, (day - timedelta(days=1)).date(), now=t(11, 43, 30)))

if __name__ == "__main__":
    unittest.main()
