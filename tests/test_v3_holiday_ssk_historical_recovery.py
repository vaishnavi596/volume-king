"""Holiday history must not inherit the LIVE quote authorization gate."""
import ast
import pathlib
import unittest
from datetime import datetime

ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(SRC)
FUNCS={n.name: n for n in ast.walk(TREE) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def body(name):
    return ast.get_source_segment(SRC,FUNCS[name])

class HolidayHistorySourceGate(unittest.TestCase):
    def test_history_not_blocked_by_missing_ltp_if_ssk_and_closed(self):
        source=body("fetch_market_data_uncached")
        self.assertIn("closed_hist_gateway=(clone_v2_gateway.connected and not regular_hours())",source)
        self.assertIn("if not (dhan_feed.connected or closed_hist_gateway):",source)
        self.assertIn('dhan_feed.intraday(ticker,',source)
        gate=source.index("closed_hist_gateway=")
        self.assertLess(gate,source.index("dhan_feed.intraday(ticker,"))
        self.assertNotIn("dhan_feed.activate_with_quote(",source)

    def test_manual_scanner_can_request_closed_session_history_without_live(self):
        source=body("scan_market")
        self.assertIn("and allow_network",source)
        self.assertIn("and not (clone_v2_gateway.connected and not regular_hours())",source)
        self.assertIn("get_market_data,sym,interval,period",source)
        self.assertIn("if not allow_network and prefs.get(\"source\")==\"Dhan\":",source)

    def test_scanner_holiday_auto_selection_cache_only_independent_of_ltp(self):
        source=body("render_page")
        self.assertIn('if prefs.get("source")=="Dhan" and not refresh_hours():',source)
        self.assertIn("page.run_task(scan_market,False)",source)
        snippet=source.split('if prefs.get("source")=="Dhan" and not refresh_hours():',1)[1]
        self.assertLess(snippet.index("page.run_task(scan_market,False)"),1500)

    def test_open_market_does_not_bypass_real_quote_proof(self):
        login=body("check_clone_v2_connection")
        self.assertIn("if not regular_hours():",login)
        self.assertIn("dhan_feed.activate_with_quote(proof)",login)
        self.assertIn('if not proof:',login)
        self.assertIn("Clone B3 Dhan quote proof unavailable",login)

    def test_history_only_not_falsely_claimed_live(self):
        source=body("fetch_market_data_uncached")
        self.assertIn('"live_verified":False',source)
        self.assertIn('"historical_unverified"',source)

if __name__=="__main__":
    unittest.main()
