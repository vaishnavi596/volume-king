"""Source regression for all Dhan quote writers, without provider I/O."""
import ast
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from clone_smart_refresh_priority import accept_newer_dhan_quote
MAIN=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(MAIN)

def fn(name):
    nodes=[x for x in ast.walk(TREE)
           if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name==name]
    assert len(nodes)==1,(name,len(nodes))
    return ast.get_source_segment(MAIN,nodes[0])

class SharedQuoteWriterAudit(unittest.TestCase):
    def test_login_regular_batch_and_historical_preflight_share_guard(self):
        self.assertIn("accept_newer_dhan_quote(quotes.get(symbol),candidate)",fn("check_clone_v2_connection"))
        self.assertIn("accept_newer_dhan_quote(quotes.get(ticker),snapshot)",fn("refresh_watch_batch"))
        self.assertIn("accept_newer_dhan_quote(quotes.get(ticker),snapshot)",fn("refresh_market"))

    def test_out_of_order_timestamp_cannot_roll_back_price(self):
        newer={"source":"Dhan","price":120,"quote_timestamp":1800000020}
        self.assertFalse(accept_newer_dhan_quote(newer,{"source":"Dhan","price":119,"quote_timestamp":1800000010}))
        self.assertFalse(accept_newer_dhan_quote(newer,{"source":"Dhan","price":119,"quote_timestamp":None}))
        self.assertFalse(accept_newer_dhan_quote(newer,{"source":"Dhan","price":-1}))
        self.assertTrue(accept_newer_dhan_quote(newer,{"source":"Dhan","price":121,"quote_timestamp":1800000030}))

    def test_market_close_history_cannot_declare_live_quote(self):
        source=fn("refresh_market")
        self.assertNotIn('live_verified=True',source.split("Historical preflight cannot overwrite a newer LTP.",1)[1].split("if current[0] == 4:",1)[0])

if __name__=="__main__":
    unittest.main()
