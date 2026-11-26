import pathlib, unittest
SRC = (pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
BODY = SRC.split("    async def scan_closed_auto_hist():", 1)[1].split("    scan_live.on_change=auto_scan_changed", 1)[0]

class ScannerClosedAutoHist(unittest.TestCase):
    def test_runs_once_per_key_only_when_closed_and_scanner_open(self):
        for needle in ("current[0]!=3", "not scan_live.value", "regular_hours()",
                       "clone_v2_gateway.connected", "scan_closed_auto_done[0]==key",
                       "provider_generation[0],scan_symbol.value,scan_tf.value,scan_period.value"):
            self.assertIn(needle, BODY)

    def test_never_live_or_orders_and_started(self):
        for bad in ("activate_with_quote", "place_order", "live_orders", "token"):
            self.assertNotIn(bad, BODY)
        self.assertIn("page.run_task(scan_closed_auto_hist)", SRC)
