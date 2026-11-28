import json, math, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
sys.path[:0] = ["src", "backend"]
IST = timezone(timedelta(hours=5, minutes=30))


def session(day="2026-11-26", n=375):
    start = datetime.fromisoformat(day + "T09:15:00").replace(tzinfo=IST).timestamp()
    bars = []
    for i in range(n):
        base = 100 + 3 * math.sin(i / 25) + i * 0.01
        o, c = base, base + 0.15 * math.sin(i / 3)
        bars.append([int(start + 60 * i), round(o, 2), round(max(o, c) + 0.1, 2), round(min(o, c) - 0.1, 2), round(c, 2), 1000 + i])
    return bars, datetime.fromisoformat(day + "T16:00:00").replace(tzinfo=IST).timestamp()


class BoxTable(unittest.TestCase):
    def test_row_has_t_c_m_from_one_minute_bars(self):
        import box_table
        bars, now = session()
        row = box_table.build_row(bars, now)
        self.assertGreater(row["bars"], 300)
        self.assertIsNotNone(row["T"]); self.assertAlmostEqual(row["T"]["b"] + row["T"]["s"], 100, delta=1)
        self.assertIsNotNone(row["C"])
        self.assertIn("h30", row["M"])

    def test_no_bars_gives_empty_boxes_not_errors(self):
        import box_table
        row = box_table.build_row([], 1_700_000_000)
        self.assertIsNone(row["T"]); self.assertIsNone(row["C"]); self.assertIsNone(row["M"])
        self.assertEqual(box_table.build_row(None, 1_700_000_000)["bars"], 0)

    def test_overlays_f_n_o(self):
        import box_table
        bars, now = session()
        row = box_table.build_row(bars, now, fut={"bullish": 60, "bearish": 40, "buildup": "LONG_BUILDUP"},
                                  news={"bullish": 70, "bearish": 30, "n": 9}, oi={"bullish": 40, "bearish": 60, "expiry": "2026-12-29"})
        self.assertEqual((row["F"]["b"], row["N"]["b"], row["O"]["b"]), (60, 70, 40))
        self.assertEqual(box_table.build_row(bars, now, news={"n": 5, "bullish": None})["N"], {"n": 5, "dir": None})


class RunnerRefresh(unittest.TestCase):
    def test_box_refresh_writes_a_table_with_all_54(self):
        import clone_signal_runner as r
        bars, now = session()
        with tempfile.TemporaryDirectory() as d:
            out_file = Path(d) / "boxes.json"
            r.BOX_STATE.update(rows={}, cursor=0, oi={}, oi_cursor=0)
            r.STOCK_STATE.update(fut={"INFY": {"bullish": 55, "bearish": 45, "day": "2026-11-26"}}, news={}, cursor=0)

            def fake_post(path, body, key, timeout=25):
                return {"bars": bars, "normalized_bars_sha256": None}
            with mock.patch.object(r, "BOX_FILE", out_file), mock.patch.object(r, "post", fake_post), \
                 mock.patch.object(r, "with_integrity", lambda x: x), \
                 mock.patch.object(r, "oi_snapshot", lambda k, s, t, c: {"bullish": 45, "bearish": 55, "expiry": "2026-12-29", "pcr": 0.9}):
                res = r.box_refresh("k", now, "2026-11-26", False, {"oi_lean": {"NIFTY": {"bullish": 30, "bearish": 70}}})
            table = json.loads(out_file.read_text())
        self.assertEqual(table["count"], 54)
        self.assertEqual(table["box_base"], "1m")
        self.assertEqual(table["rows"]["NIFTY"]["O"]["b"], 30)          # index O comes from the index OI lean
        self.assertEqual(table["rows"]["INFY"]["F"]["b"], 55)
        self.assertGreater(res["with_T"], 3)
        self.assertLess(len(json.dumps(table)), 120000)


class Wiring(unittest.TestCase):
    def test_gateway_route_and_installer(self):
        gw = open("backend/clone_v2_gateway.py", encoding="utf-8").read()
        self.assertIn('"/clone-v2/snapshot/boxes"', gw)
        ins = open("ops/install_server_away_20261127.sh", encoding="utf-8").read()
        for name in ("box_table.py", "five_engine.py", "analysis_quality.py", "historical_session_window.py", "filter_wiring_audit.py"):
            self.assertIn(name, ins)


if __name__ == "__main__":
    unittest.main()
