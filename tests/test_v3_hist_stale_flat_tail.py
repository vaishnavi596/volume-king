import unittest
from historical_session_window import drop_stale_flat_tail, historical_regular_session_bars

IST = 19800
DAY = 20000


def base(n, step=60):
    t0 = DAY * 86400 - IST + (9 * 60 + 15) * 60
    return [[t0 + i * step, 100 + i * .1, 100.3 + i * .1, 99.9 + i * .1, 100.1 + i * .1, 50.0 + i] for i in range(n)]


def frozen(rows, count, vol=2249.0):
    out = [list(r) for r in rows]
    out[-1][5] = vol                      # last real bar carries the repeated volume
    for _ in range(count):
        out.append([out[-1][0] + 60, 100.0, 100.0, 100.0, 100.0, vol])
    return out


class StaleTailTests(unittest.TestCase):
    def test_1m_frozen_run_then_closing_print_is_cut(self):
        rows = frozen(base(360), 6)
        rows.append([rows[-1][0] + 60, 100.0, 100.0, 99.0, 99.0, 2249.0])   # closing print
        out = drop_stale_flat_tail(rows, "1m")
        self.assertEqual(len(out), 360)
        self.assertEqual(out, [list(r) for r in rows[:360]])

    def test_5m_two_frozen_bars_then_close(self):
        rows = frozen(base(70, 300), 2)
        rows.append([rows[-1][0] + 300, 100.0, 101.0, 100.0, 101.0, 2249.0])
        self.assertEqual(len(drop_stale_flat_tail(rows, "5m")), 70)

    def test_single_flat_bar_is_kept(self):
        rows = frozen(base(60), 1)
        self.assertEqual(len(drop_stale_flat_tail(rows, "1m")), 61)

    def test_real_flat_zero_volume_is_kept(self):
        rows = [list(r) for r in base(60)]
        for _ in range(4):
            rows.append([rows[-1][0] + 60, 100.0, 100.0, 100.0, 100.0, 0.0])
        self.assertEqual(len(drop_stale_flat_tail(rows, "1m")), 64)

    def test_frozen_run_in_the_middle_is_kept(self):
        rows = frozen(base(40), 3)
        t = rows[-1][0]
        for i in range(1, 11):
            rows.append([t + 60 * i, 101.0 + i * .1, 101.4 + i * .1, 100.9 + i * .1, 101.2 + i * .1, 70.0 + i])
        self.assertEqual(len(drop_stale_flat_tail(rows, "1m")), len(rows))

    def test_never_cuts_below_30_bars_and_input_not_mutated(self):
        rows = frozen(base(20), 4)
        snapshot = [list(r) for r in rows]
        self.assertEqual(len(drop_stale_flat_tail(rows, "1m")), len(rows))
        self.assertEqual(rows, snapshot)

    def test_combined_wrapper_cuts_after_close_bar_and_frozen_tail(self):
        rows = frozen(base(360), 4)
        rows.append([DAY * 86400 - IST + (18 * 60 + 43) * 60, 99.0, 99.0, 99.0, 99.0, 0.0])
        out = historical_regular_session_bars(rows, "1m")
        self.assertEqual(len(out), 360)

    def test_unsupported_timeframe_untouched(self):
        rows = frozen(base(60), 5)
        self.assertEqual(len(drop_stale_flat_tail(rows, "15m")), len(rows))


if __name__ == "__main__":
    unittest.main()
