import unittest
from datetime import datetime, timezone, timedelta
from scanner_engine import analyze

IST = timezone(timedelta(hours=5, minutes=30))


def bars(last_clock, last_volume, n=40):
    end = datetime(2026, 11, 26, last_clock[0], last_clock[1], tzinfo=IST)
    out = []
    price = 100.0
    for i in range(n):
        ts = int((end - timedelta(minutes=n - 1 - i)).timestamp())
        price += 0.1
        out.append([ts, price, price + 0.2, price - 0.2, price + 0.05, 1_700_000.0])
    out[-1][5] = last_volume
    return out


def vol(rows):
    res = analyze(rows, selected=["Volume"], timeframe="1m")
    return [v for v in res["votes"] if v["name"] == "Volume"][0]


class PostCloseVolumeBar(unittest.TestCase):
    def test_post_close_print_not_used(self):
        v = vol(bars((15, 30), 2249.0))
        self.assertIn("1700000", v["detail"])  # regular bar compared, not 2249
        self.assertNotIn("Volume 2249", v["detail"])

    def test_regular_last_bar_unchanged(self):
        v = vol(bars((15, 29), 2249.0))
        self.assertIn("Volume 2249", v["detail"])


if __name__ == "__main__":
    unittest.main()
