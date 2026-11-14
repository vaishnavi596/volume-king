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
        self.assertIn('Price change unavailable • reference unverified', source)
        self.assertIn('signal_direction=("Bullish" if signal_counts[0]>signal_counts[1]', source)

    def test_dhan_equity_quote_poll_runs_every_30_seconds(self):
        source = SOURCE.read_text(encoding="utf-8")
        body = source.split("    async def dhan_quote_poll():", 1)[1].split("    async def watch_visible_tick():", 1)[0]
        self.assertIn("await asyncio.sleep(30)", body)
        self.assertNotIn("await asyncio.sleep(180)", body)
        self.assertIn("await refresh_watch_batch()", body)
        self.assertIn('remaining=dhan_feed.cooldown_remaining("/v2/snapshot")', body)
        self.assertIn("if remaining==0:", body)
        self.assertIn("Dhan snapshot cooling down", body)
        self.assertIn("last valid prices retained", body)

    def test_dhan_history_scans_equities_before_index(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('symbols=([equities[0],"NIFTY"]+equities[1:]) if equities else ["NIFTY"]', source)
        self.assertIn("Dhan quote refresh • every 30 sec while foreground", source)
        self.assertIn("exchange timestamp unverified", source)

    def test_scanner_chart_cache_respects_timeframe_and_scan_generation(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('saved_chart.get("_scanner_timeframe") != (scan_tf.value or "5m")', source)
        self.assertIn('saved_chart.get("_scanner_generation") != scan_generation[0]', source)
        self.assertIn('if prefs.get("source")!="Dhan":\n                quotes[sym]=hist', source)

    def test_cooldown_path_also_reports_unattempted(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('+" symbols not attempted"', source)
        self.assertIn('Dhan historical scan paused: HTTP 429 / cooldown', source)


if __name__ == "__main__":
    unittest.main()
