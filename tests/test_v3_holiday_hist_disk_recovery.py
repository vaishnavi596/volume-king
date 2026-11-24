"""Strict closed-session HIST disk persistence; no fake Dhan live quotes."""
import ast
import pathlib
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT=pathlib.Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/"src"))
from snapshot_store import SnapshotStore

IST=timezone(timedelta(hours=5,minutes=30))
def hist():
    start=int(datetime(2026,11,23,9,15,tzinfo=IST).timestamp())
    return {"source":"Dhan","price":None,"bars":[
        [start+i*60,25000+i,25003+i,24998+i,25001+i,10+i]
        for i in range(40)],"_scanner_timeframe":"1m",
        "freshness":"historical_unverified","live_verified":False}

class ClosedSessionHistoryPersistence(unittest.TestCase):
    def test_reboot_restores_dhan_candles_without_fake_price(self):
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d)/"snapshots.json"
            store=SnapshotStore(path)
            self.assertTrue(store.put("market",("Dhan","NIFTY","1m","7d"),hist()))
            reopened=SnapshotStore(path)
            saved=reopened.get("market","Dhan","NIFTY","1m","7d")
            self.assertEqual(len(saved["bars"]),40)
            self.assertIsNone(saved["price"])
            self.assertEqual(saved["_scanner_timeframe"],"1m")
            self.assertFalse(saved["live_verified"])
            self.assertNotIn("NIFTY",reopened.latest_markets())
            self.assertIsNone(reopened.get("market","Dhan","NIFTY","3m","7d"))
            self.assertIsNone(reopened.get("market","Yahoo Finance","NIFTY","1m","7d"))

    def test_malformed_and_fake_history_must_not_persist(self):
        with tempfile.TemporaryDirectory() as d:
            store=SnapshotStore(pathlib.Path(d)/"snapshots.json")
            for changes in (
                {"source":"Yahoo Finance"},{"live_verified":True},
                {"freshness":"verified_live"},{"_scanner_timeframe":"5m"},
                {"bars":hist()["bars"][:4]},
                {"bars":[dict() for _ in range(40)]},
                {"price":True},
            ):
                if changes.get("_scanner_timeframe")=="5m":
                    # Correctly stamped 5m history is allowed when actual
                    # 5m bars exist; only mismatched lookup must be rejected.
                    continue
                row=dict(hist(),**changes)
                self.assertFalse(store.put("market",("Dhan","NIFTY","1m","7d"),row),changes)

    def test_historical_source_is_filtered_from_quote_cache(self):
        with tempfile.TemporaryDirectory() as d:
            store=SnapshotStore(pathlib.Path(d)/"snapshots.json")
            candles=hist()
            self.assertTrue(store.put("market",("Dhan","RELIANCE","1m","7d"),candles))
            quotes=store.latest_markets()
            self.assertNotIn("RELIANCE",quotes)
            self.assertEqual(store.get("market","Dhan","RELIANCE","1m","7d")["price"],None)

    def test_main_reopens_exact_history_without_provider_call(self):
        source=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="shared_history"]
        self.assertEqual(len(nodes),1)
        body=ast.get_source_segment(source,nodes[0])
        self.assertIn('market_store.get("market","Dhan",sym,tf,saved_range)',body)
        self.assertIn('saved.get("_scanner_timeframe")==tf',body)
        self.assertIn('live_verified=False',body)

if __name__=="__main__":
    unittest.main()
