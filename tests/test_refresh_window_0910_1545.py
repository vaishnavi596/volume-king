"""BOT KING refresh begins 09:10 IST, ends 15:45, without false live signals."""
import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from v3_equity_session_calendar import regular_equity_hours, equity_refresh_window

MAIN=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(MAIN)
IST=timezone(timedelta(hours=5,minutes=30))

def get_local_function(name):
    matches=[n for n in ast.walk(TREE) if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len(matches)==1, (name,len(matches))
    module=ast.Module(body=[matches[0]],type_ignores=[])
    ns={"datetime":datetime,"timezone":timezone,"timedelta":timedelta,
        "regular_equity_hours":regular_equity_hours,"equity_refresh_window":equity_refresh_window}
    exec(compile(module,"<market-hours-isolated>","exec"),ns)
    return ns[name]

class RefreshWindow0910Tests(unittest.TestCase):
    def test_boundaries_and_weekend(self):
        refresh=get_local_function("refresh_hours")
        trading=get_local_function("regular_hours")
        monday=(2026,11,16)
        cases=[(9,9,False,False),(9,10,True,False),
               (9,14,True,False),(9,15,True,True),
               (15,29,True,True),(15,30,True,False),
               (15,44,True,False),(15,45,False,False)]
        for h,m,wanted_refresh,wanted_live in cases:
            with self.subTest(at=f"{h:02d}:{m:02d}"):
                value=datetime(*monday,h,m,tzinfo=IST)
                self.assertEqual(refresh(value),wanted_refresh)
                self.assertEqual(trading(value),wanted_live)
        saturday=datetime(2026,11,21,10,0,tzinfo=IST)
        self.assertFalse(refresh(saturday))
        self.assertFalse(trading(saturday))

    def test_pollers_and_manual_watchlist_use_wider_window(self):
        self.assertIn("app_active[0] and refresh_hours()",MAIN.split("    async def dhan_quote_poll():",1)[1].split("    # The Watchlist observes",1)[0])
        self.assertIn("app_active[0] and refresh_hours()",MAIN.split("    async def dhan_index_poll():",1)[1].split("    page.run_task(dhan_index_poll)",1)[0])
        watch=MAIN.split("    def watchlist():",1)[1].split("    symbol=ft.Dropdown(",1)[0]
        self.assertIn('ft.TextButton("Refresh data"',watch)
        self.assertNotIn("watch_countdown",watch)
        self.assertIn("if not force and not refresh_hours():",MAIN.split("    async def refresh_dhan_index_quotes(force=False):",1)[1].split("    manual_quote_last_attempt=",1)[0])

    def test_live_signal_eligibility_still_uses_exchange_session(self):
        self.assertIn('live_verified',MAIN)
        self.assertIn("market_open=regular_hours()",MAIN)
        self.assertIn('and regular_hours()',MAIN)
        self.assertNotIn("(9,10)<=(now.hour,now.minute)<(15,45)",ast.get_source_segment(MAIN,[n for n in ast.walk(TREE) if isinstance(n,ast.FunctionDef) and n.name=="regular_hours"][0]))

if __name__=="__main__":
    unittest.main()
