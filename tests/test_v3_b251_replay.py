import sys, unittest, random, calendar, datetime
sys.path[:0] = ["src", "backend"]
import clone_replay as r


def day_bars(day_offset, seed):
    random.seed(seed); c = 100
    base = calendar.timegm(datetime.datetime(2026, 11, 25, 3, 45).timetuple()) + day_offset * 86400
    out = []
    for i in range(375):
        c += random.uniform(-.3, .32)
        out.append((base + i * 60, c, c + .2, c - .2, c + .05, random.randint(50, 300)))
    return out


class Replay(unittest.TestCase):
    def test_split_days_and_replay_runs_clean(self):
        bars = day_bars(0, 1) + day_bars(1, 2)
        days = r.split_days(bars)
        self.assertEqual(len(days), 2)
        rep = {"horizons": {}, "windows": {}, "confluence": {}, "engine_dir": {},
               "engine": {"calls": 0, "errors": 0, "directional_ge3": 0}}
        for b in days.values():
            r.replay_day(b, rep)
        self.assertEqual(rep["engine"]["errors"], 0)
        self.assertGreater(rep["engine"]["calls"], 100)
        fin = r.finish(rep["horizons"])
        self.assertIn("30m", fin)
        self.assertTrue(0 <= fin["30m"]["hit_rate"] <= 100)

    def test_short_day_ignored(self):
        self.assertEqual(r.split_days(day_bars(0, 3)[:50]), {})

    def test_wiring(self):
        src = open("backend/clone_signal_runner.py", encoding="utf-8").read()
        self.assertIn('out["replay"]', src)
        inst = open("ops/install_server_away_20261127.sh", encoding="utf-8").read()
        self.assertIn("clone_replay.py", inst)
        upd = open("ops/botking_autoupdate.sh", encoding="utf-8").read()
        self.assertIn("replay;", upd)
        self.assertIn("no orders", open("backend/clone_replay.py", encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()


class OptionsPageLayout(unittest.TestCase):
    def test_buy_last_no_dummy(self):
        src = open("src/main.py", encoding="utf-8").read()
        a = src.index("    def options():")
        body = src[a:src.index("    # One Paper/Live selector", a)]
        self.assertNotIn("paper_trading_center()", body)
        self.assertNotIn("option_paper_action('SELL')", body)
        self.assertLess(body.index("Strategy Selector"), body.index("content.append(ticket_card())"))
        self.assertTrue(body.rstrip().endswith("return content"))
        self.assertTrue(body.index("content.append(ticket_card())") > body.index("server_paper_section(False)"))
        t = src[src.index("    def ticket_card():"):src.index("    option_chart_cache={}")]
        self.assertNotIn('sidebtn("SELL"', t)
        self.assertGreater(t.index("ticket_place"), t.index("tk_result"))


class ChartFilterMemory(unittest.TestCase):
    def test_per_symbol_filters_wired(self):
        src = open("src/main.py", encoding="utf-8").read()
        self.assertIn('prefs.setdefault("chart_filters_by_symbol",{})', src)
        self.assertIn("def chart_filter_panel(sym,bars):", src)
        self.assertIn("chart_filter_panel(symbol.value,", src)
        a = src.index("    def chart_filter_panel(sym,bars):")
        body = src[a:a + 2500]
        self.assertIn("for n in ALL_FILTERS", body)               # all 18, not 4
        self.assertIn("analyze([list(b) for b in bars]", body)    # same engine calculation
        self.assertIn("from scanner_engine import ema as _ema", src)
        # filters never touch the vote/scan state
        self.assertNotIn("scan_generation", body)
        self.assertNotIn("filter_selected", body)
