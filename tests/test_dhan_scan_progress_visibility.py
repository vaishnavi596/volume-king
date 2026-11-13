"""Guard scan progress wording when a first Dhan history failure aborts the cycle."""
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


class DhanScanProgressTests(unittest.TestCase):
    def test_first_history_failure_reports_unattempted_symbols(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('failed=1,state="Dhan historical feed unavailable • scan paused • 1 failed • "', source)
        self.assertIn('str(max(0,len(symbols)-1))+" not attempted • first error: "', source)
        self.assertIn('market_status="Dhan candle history unavailable', source)

    def test_missing_dhan_change_is_unavailable_not_neutral(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('else "Neutral" if valid_change else "Unavailable"', source)
        self.assertIn('Price direction unavailable • Dhan change/reference price not verified', source)
        self.assertIn('signal_direction=("Bullish" if signal_counts[0]>signal_counts[1]', source)

    def test_cooldown_path_also_reports_unattempted(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('+" symbols not attempted"', source)
        self.assertIn('Dhan historical scan paused: HTTP 429 / cooldown', source)


if __name__ == "__main__":
    unittest.main()
