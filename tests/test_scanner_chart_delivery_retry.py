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


    def test_chart_guidance_is_compact_and_does_not_duplicate_settings_help(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        self.assertIn('parts.append(note("OHLC history • EMA 9/21 overlay • other filters: analysis only"))',source)
        self.assertNotIn("Chart/Analysis/Both is selected in Settings",source)
        self.assertIn('parts.append(tradingview_status)',source)

    def test_symbol_switch_resets_chart_identity_and_kicks_mounted_webview(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        chart=source.split("    def scanner_compact_chart():",1)[1].split("    def scanner_fast_signal_loop():",1)[0]
        self.assertIn("tv_history[0]=[];tv_js_view[0]=None",chart)
        self.assertIn("tv_mount_retries[0]=0",chart)
        self.assertIn("chart_delivery_identity[0]=None",chart)
        render=source.split("    def render_page(i):",1)[1].split("    # Keep the app chrome inside Android system insets",1)[0]
        self.assertIn("page.update()",render)
        self.assertIn("tv_booted[0]=True",render)
        self.assertIn("page.run_task(tv_load_widget)",render)

    def test_unready_webview_recovers_saved_candles_without_network(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        body=source.split("    async def sync_visible_chart():",1)[1].split("    async def scanner_fast_signal_loop():",1)[0]
        recovery=body.split("        if not tv_ready[0]:",1)[1].split("        # A failed JS delivery",1)[0]
        self.assertIn("tv_mount_retries[0]<2",recovery)
        self.assertIn("time.monotonic()-tv_last_html_load[0]>=6",recovery)
        self.assertIn("tradingview_widget_html(sym,",recovery)
        self.assertIn("view is tv_view[0] and context==tv_context[0]",recovery)
        self.assertNotIn("get_market_data(",recovery)
        self.assertNotIn("dhan_feed.intraday(",recovery)

if __name__=="__main__":
    unittest.main()
