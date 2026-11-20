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
        self.assertIn('historical_vote_agreement(index_history,"1m")',market)
        home=block("    def dashboard():","    search=ft.TextField(")
        self.assertIn("Dashboard index candles: 1m",home)
        self.assertIn("Scanner has independent timeframe",home)
        superfive=block("    def super_five_card():","    async def retry_failed_symbol(")
        self.assertIn('timeframe_spec("5m")',superfive)
        self.assertIn('rows=(\n',superfive)

    def test_scanner_watchlist_chart_settings_are_isolated(self):
        self.assertIn('scanner_intervals=(["1m","2m","3m","5m","15m","1h"]',MAIN)
        self.assertIn('watch_three_minute_signal(sym)',MAIN)
        self.assertIn('chart_snapshots[(sym,selected_tf,generation)]',MAIN)
        self.assertIn('if tf not in ("1m","2m","3m","5m","15m","1h"):',MAIN)
        self.assertIn('def oracle_assessment_context(symbol,surface="overview"):',MAIN)
        self.assertIn('timeframe=scan_tf.value if scan_tf.value in ("1m","3m","5m") else None',MAIN)
        self.assertIn('if surface=="chart":',MAIN)
        self.assertIn('timeframe=None',MAIN)
        self.assertIn('value="Dhan"',MAIN)

    def test_sensex_source_mapped_but_provider_can_omit_price(self):
        self.assertIn('"SENSEX": ("BSE_I", 51)',GATEWAY)
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
        self.assertIn('prefs.get("chart_timeframe","5m")',MAIN)
        self.assertIn('scan_tf=ft.Dropdown(',MAIN)
        self.assertNotIn("SENSEX price=0",MAIN)


if __name__=="__main__":
    unittest.main()
