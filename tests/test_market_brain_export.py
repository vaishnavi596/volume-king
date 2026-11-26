import datetime as dt
import unittest

from market_brain.export_external import parse_fred, parse_yahoo
from market_brain.export_history import SPAN_DAYS, valid_rows, windows


class ExportHelpers(unittest.TestCase):
    def test_windows_respect_server_span_and_cover_range_without_overlap(self):
        today = dt.date(2026, 11, 26)
        ws = windows(today, 365)
        for a, b in ws:
            self.assertLessEqual((b - a).days, SPAN_DAYS)
        for (a1, _), (_, b2) in zip(ws, ws[1:]):
            self.assertEqual(b2, a1 - dt.timedelta(days=1))
        self.assertEqual(ws[0][1], today)
        self.assertEqual(ws[-1][0], today - dt.timedelta(days=365))

    def test_bad_rows_are_dropped(self):
        good = [1700000000, 10.0, 11.0, 9.0, 10.5, 100]
        bad = [[1700000300, 10, 9, 11, 10, 1], [0, 1, 1, 1, 1, 1], "x", [1, 2, 3]]
        self.assertEqual(valid_rows([good] + bad), [good])

    def test_parsers_skip_missing_values(self):
        y = {"chart": {"result": [{"timestamp": [1700000000, 1700086400],
                                    "indicators": {"quote": [{"close": [100.0, None]}]}}]}}
        self.assertEqual(len(parse_yahoo(y)), 1)
        self.assertEqual(parse_fred("DATE,V\n2026-11-23,4.92\n2026-11-24,.\n"), [("2026-11-23", 4.92)])


if __name__ == "__main__":
    unittest.main()
