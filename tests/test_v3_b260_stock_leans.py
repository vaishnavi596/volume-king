import io, sys, time, unittest
from unittest import mock
sys.path[:0] = ["src", "backend"]
import clone_signal_runner as r

HEAD = "SEM_INSTRUMENT_NAME,SEM_TRADING_SYMBOL,SEM_EXM_EXCH_ID,SEM_EXPIRY_DATE,SEM_SMST_SECURITY_ID,SEM_LOT_UNITS\n"


class StockFutures(unittest.TestCase):
    def test_parse_includes_roster_stock_futures_only(self):
        rows = HEAD + ("FUTSTK,RELIANCE-Dec2026-FUT,NSE,2026-12-30,111,500\n"
                       "FUTSTK,RELIANCE-Jan2027-FUT,NSE,2027-01-27,112,500\n"
                       "FUTSTK,NOTINROSTER-Dec2026-FUT,NSE,2026-12-30,113,100\n"
                       "FUTIDX,NIFTY-Dec2026-FUT,NSE,2026-12-30,114,65\n")
        out = r.parse_future_contracts(io.StringIO(rows), "2026-11-28")
        self.assertEqual(out["RELIANCE"][3], "2026-12-30")      # nearest expiry wins
        self.assertNotIn("NOTINROSTER", out)
        self.assertIn("NIFTY", out)

    def test_roster_has_51_names(self):
        self.assertEqual(len(r.STOCK_ROSTER), 51)

    def test_stock_refresh_rotates_and_never_touches_index_ledger_keys(self):
        r.STOCK_STATE.update(fut={}, news={}, cursor=0)
        base = 1_700_000_000.0
        bars = [[int(base + 60 * i), 100 + 0.1 * i, 100.2 + 0.1 * i, 99.9 + 0.1 * i, 100 + 0.1 * i, 100] for i in range(120)]
        futures = {n: ["NSE_FNO", 1, 100, "2026-12-30"] for n in r.STOCK_ROSTER}
        calls = []

        def fake_post(path, body, key, timeout=25):
            calls.append(body["underlying"])
            return {"bars": bars, "oi": None}
        with mock.patch.object(r, "post", fake_post), \
             mock.patch.object(r, "FUTURES_FILE", mock.Mock(exists=lambda: True,
                                                            read_text=lambda encoding=None: __import__("json").dumps({"futures": futures}))), \
             mock.patch.object(r, "v3_news_cue", None):
            r.stock_refresh("k", base + 7200, "2026-11-28")
            first = list(calls)
            r.stock_refresh("k", base + 7260, "2026-11-28")
        self.assertEqual(len(first), r.STOCK_FUT_PER_CYCLE)
        self.assertEqual(len(set(calls)), 2 * r.STOCK_FUT_PER_CYCLE)       # second call moved on
        self.assertTrue(r.STOCK_STATE["fut"])
        row = next(iter(r.STOCK_STATE["fut"].values()))
        self.assertIn(row["lean"], ("BULLISH", "BEARISH", "NEUTRAL"))
        self.assertFalse(set(r.STOCK_STATE["fut"]) & set(r.SYMBOLS))


class GatewayRoute(unittest.TestCase):
    def test_gateway_accepts_roster_underlying_and_uses_futstk(self):
        src = open("backend/clone_v2_gateway.py", encoding="utf-8").read()
        self.assertIn('"FUTSTK"', src)
        self.assertIn('re.fullmatch(r"[A-Z0-9&-]{1,20}", body.underlying)', src)


if __name__ == "__main__":
    unittest.main()
