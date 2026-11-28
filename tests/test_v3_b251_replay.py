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
