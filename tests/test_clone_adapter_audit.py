"""Clone adapter joint audit: page context, refresh separation, index availability.

No phone/Oracle credentials, synthetic LIVE prices, or broker requests.
"""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAIN=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
GATEWAY=(ROOT/"backend"/"clone_v2_gateway.py").read_text(encoding="utf-8")
CLIENT=(ROOT/"src"/"clone_v2_gateway.py").read_text(encoding="utf-8")

def block(start,end):
    return MAIN.split(start,1)[1].split(end,1)[0]


class CloneAdapterAudit(unittest.TestCase):
    def test_all_sources_compile(self):
        for name,content in (("main",MAIN),("gateway",GATEWAY),("client",CLIENT)):
            with self.subTest(name=name):
                ast.parse(content)

    def test_dashboard_index_one_minute_not_scanner_or_superfive_five_minute(self):
        page=block("    def dashboard_index_analysis():","    def dashboard_market_indices():")
        market=block("    def dashboard_market_indices():","    def dashboard():")
        self.assertIn('defaults=("NIFTY","BANKNIFTY","SENSEX")',page)
        self.assertIn('shared_history(sym,"1m")',page)
        self.assertIn('dashboard_hist_agreement(index_name,index_history)',market)
        self.assertIn('dashboard_hist_agreement(sym,candle_data)',page)
        shared=block("    def dashboard_hist_agreement(sym,history):",
                     "    def dashboard_index_analysis():")
        self.assertIn('historical_vote_agreement(history,"1m")',shared)
        self.assertIn('timeframe="1m"',shared)
        home=block("    def dashboard():","    search=ft.TextField(")
        self.assertIn("Dashboard index candles: 1m",home)
        self.assertIn("Scanner has independent timeframe",home)
        superfive=block("    def super_five_card():","    async def retry_failed_symbol(")
        self.assertIn('timeframe_spec("5m")',superfive)
        self.assertIn('rows=(\n',superfive)

    def test_scanner_watchlist_chart_settings_are_isolated(self):
        self.assertIn('scanner_intervals=(["1m","2m","3m","5m","10m","15m","30m","1h"]',MAIN)
        self.assertIn('watch_three_minute_signal(sym)',MAIN)
        self.assertIn('chart_snapshots[(sym,selected_tf,generation)]',MAIN)
        self.assertIn('if tf not in ("1m","2m","3m","5m","10m","15m","30m","1h"):',MAIN)
        self.assertIn('def oracle_assessment_context(symbol,surface="overview"):',MAIN)
        self.assertIn('timeframe=scan_tf.value if scan_tf.value in ("1m","3m","5m") else None',MAIN)
        self.assertIn('if surface=="chart":',MAIN)
        self.assertIn('timeframe=None',MAIN)
        self.assertIn('value="Dhan"',MAIN)

    def test_sensex_source_mapped_but_provider_can_omit_price(self):
        self.assertIn('"SENSEX": ("IDX_I", 51)',GATEWAY)
        self.assertIn('"unavailable": [s for s in symbols if s not in quotes]',GATEWAY)
        self.assertIn('names = ("NIFTY", "BANKNIFTY", "SENSEX")',CLIENT)
        market=block("    async def refresh_dhan_index_quotes(force=False):",
                     "    manual_quote_last_attempt=")
        self.assertIn('missing_indices=[sym for sym in ("NIFTY","BANKNIFTY","SENSEX")',market)
        self.assertIn('await asyncio.sleep(1.1)',market)
        self.assertIn('dhan_feed.quote,missing_symbol',market)
        self.assertIn('Dhan index LTP unavailable:',market)
        self.assertIn('provider_status="provider_data_unavailable"',market)
        self.assertIn('index_refresh_busy[0]=False',market)
        self.assertIn('now-index_last_attempt[0]<60',market)
        self.assertNotIn('asyncio.gather(',market)

    def test_equity_and_index_share_safe_provider_cooldown(self):
        adapter=ast.parse(CLIENT)
        nodes=[n for n in ast.walk(adapter) if isinstance(n,ast.FunctionDef)
               and n.name=="_fetch"]
        self.assertEqual(len(nodes),1)
        source=ast.get_source_segment(CLIENT,nodes[0])
        # Real Dhan provider 429 retains 30s; gateway-only 2s pacing must
        # not be mislabeled as a 30s provider quota ban.
        self.assertIn('cooldown_seconds = 2 if "quote lane paced" in str(exc) else 30',source)
        self.assertIn('time.monotonic() + cooldown_seconds',source)
        self.assertIn('"/dhan/selected-ltp-batch"',source)
        self.assertIn('"/dhan/index-ltp-batch"',source)
        self.assertIn('max(self._cooldowns.get(route, 0.0), until)',source)

    def test_gateway_provider_errors_keep_throttle_and_auth_distinct(self):
        gateway_tree=ast.parse(GATEWAY)
        helpers=[n for n in ast.walk(gateway_tree)
                 if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
                 and n.name=="provider_read_error"]
        self.assertEqual(len(helpers),1)
        helper=ast.get_source_segment(GATEWAY,helpers[0])
        self.assertIn("isinstance(exc, DhanRateLimitError)",helper)
        self.assertIn("quota_error(exc)",helper)
        quota=next(n for n in ast.walk(gateway_tree) if isinstance(n,ast.FunctionDef) and n.name=="quota_error")
        body=ast.get_source_segment(GATEWAY,quota)
        self.assertIn('stage, seconds = "PROVIDER_QUOTA", 30',body)
        self.assertIn('HTTPException(429',body)
        self.assertIn('"Retry-After": str(seconds)',body)
        self.assertIn("HTTPException(\n                424",helper)
        self.assertIn("HTTPException(502, unavailable_message)",helper)
        for route,reason in (("market_candles","Clone Dhan candles unavailable"),
                             ("market_option_expiries","Clone Dhan option expiry unavailable"),
                             ("market_option_chain","Clone Dhan option chain unavailable")):
            nodes=[n for n in ast.walk(gateway_tree)
                   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==route]
            self.assertEqual(len(nodes),1)
            source=ast.get_source_segment(GATEWAY,nodes[0])
            self.assertIn('provider_read_error(exc, "'+reason+'")',source)

    def test_scroll_is_not_network_poll_or_page_navigation(self):
        callback=block("    def remember_scroll(e):","    body=ft.Column(")
        self.assertIn('last_scroll_monotonic[0]=time.monotonic()',callback)
        self.assertNotIn('request_view_refresh(',callback)
        self.assertNotIn('get_market_data(',callback)
        self.assertNotIn('select(',callback)
        flusher=block("    async def flush_view_refresh():","    def request_view_refresh(i):")
        self.assertIn('refresh_target[0]==0 and current[0]==0',flusher)
        self.assertIn('time.monotonic()-last_scroll_monotonic[0]<1.0',flusher)
        self.assertIn('await asyncio.sleep(.25)',flusher)
        self.assertIn('target=refresh_target[0]',flusher)

    def test_old_settings_preserved_not_mislabelled(self):
        self.assertIn('sym=prefs.get(key,defaults[slot])',MAIN)
        self.assertIn('last_page',MAIN)
        self.assertIn('prefs.get("chart_timeframe","1m")',MAIN)
        self.assertIn('scan_tf=ft.Dropdown(',MAIN)
        self.assertNotIn("SENSEX price=0",MAIN)


if __name__=="__main__":
    unittest.main()
