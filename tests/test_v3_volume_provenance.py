"""FT2 regression: truthful Dhan candle volume readiness, no invented vote."""
import unittest
from datetime import datetime, timedelta, timezone

from scanner_engine import analyze


def fixture(last_volume, prior_volume=100):
    ist = timezone(timedelta(hours=5, minutes=30))
    start = (datetime.now(ist).replace(hour=10, minute=0,
                                      second=0, microsecond=0)
             - timedelta(days=2)).timestamp()
    bars = []
    for i in range(40):
        op = 25000.0 + i
        bars.append([start + 60*i, op, op+2, op-1, op+1,
                     last_volume if i == 39 else prior_volume])
    return bars


class VolumeProvenanceTests(unittest.TestCase):
    def test_zero_last_bar_stays_wait_with_exact_reason(self):
        result = analyze(fixture(0), selected=["Volume"], timeframe="1m")
        self.assertEqual(result["volume_input_status"], "ZERO_LAST_BAR_VOLUME")
        self.assertEqual(result["votes"][0]["vote"], None)
        self.assertIn("ZERO_LAST_BAR_VOLUME", result["votes"][0]["detail"])

    def test_empty_baseline_does_not_invent_volume(self):
        result = analyze(fixture(100, prior_volume=0),
                         selected=["Volume"], timeframe="1m")
        self.assertEqual(result["volume_input_status"], "NO_BASELINE_VOLUME")
        self.assertIsNone(result["votes"][0]["vote"])

    def test_real_positive_volume_keeps_existing_filter_math(self):
        result = analyze(fixture(1000), selected=["Volume"], timeframe="1m")
        self.assertEqual(result["volume_input_status"], "OK")
        self.assertEqual(result["votes"][0]["vote"], 1)


if __name__ == "__main__":
    unittest.main()
