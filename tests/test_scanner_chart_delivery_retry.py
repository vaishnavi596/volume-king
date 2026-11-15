"""Regression for Scanner WebView local delivery after failed JavaScript dispatch."""
import unittest
from pathlib import Path


class ScannerChartDeliveryRetryTests(unittest.TestCase):
    def test_pending_candles_are_retried_without_network_request(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        body=source.split("    async def sync_visible_chart():",1)[1].split("    async def scanner_fast_signal_loop():",1)[0]
        self.assertIn("if tv_pending[0] is not None:",body)
        self.assertIn("push_chart_data()",body)
        self.assertIn("if tv_pending[0] is not None:return",body)
        self.assertIn("if tv_pending[0] is None:",body)
        self.assertIn("chart_delivery_identity[0]=identity",body)
        self.assertNotIn("get_market_data(",body)
        self.assertNotIn("dhan_feed.intraday(",body)

    def test_failed_js_call_retains_pending_payload(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        body=source.split("    def push_chart_data():",1)[1].split("    def tv_started(e):",1)[0]
        self.assertIn("except Exception as exc:",body)
        self.assertIn("return",body.split("except Exception as exc:",1)[1])
        self.assertIn("tv_pending[0] is pending",body)


if __name__=="__main__":
    unittest.main()
