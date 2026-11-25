import tempfile
import unittest
from pathlib import Path
from snapshot_store import SnapshotStore

class ML5CacheTests(unittest.TestCase):
    def test_last_good_context_restore_and_identity(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"cache.json"
            s=SnapshotStore(path)
            a=dict(source="Dhan",historical=True,live_verified=False,
                freshness="historical_unverified",symbol="NIFTY",timeframe="1m",
                timestamp=1800000000,count=40,votes=[])
            o=dict(source="dhan",symbol="NIFTY",expiry="2026-12-01",signal_eligible=False)
            self.assertTrue(s.put("analysis_last_good",("Dhan","NIFTY","1m"),a))
            self.assertFalse(s.put("analysis_last_good",("Dhan","NIFTY","3m"),a))
            self.assertFalse(s.put("analysis_last_good",("Dhan","NIFTY","1m"),dict(a,timestamp=1700000000)))
            self.assertTrue(s.put("option_context_last_good",("Dhan","NIFTY","2026-12-01"),o))
            self.assertFalse(s.put("option_context_last_good",("Dhan","NIFTY","2026-12-01"),dict(o,signal_eligible=True)))
            r=SnapshotStore(path)
            self.assertEqual(r.get("analysis_last_good","Dhan","NIFTY","1m"),a)
            self.assertEqual(r.get("option_context_last_good","Dhan","NIFTY","2026-12-01"),o)
            self.assertEqual(r.diagnostics()["restored_entries"],2)
            self.assertFalse(r.diagnostics()["restored_cache_live_proof"])
    def test_capacity_and_eviction(self):
        with tempfile.TemporaryDirectory() as d:
            s=SnapshotStore(Path(d)/"cache.json",max_entries=2)
            for sym in ("A","B","C"):
                self.assertTrue(s.put("news",(sym,),dict(items=[dict(title="t",url="u",published=1,source="s")],fetched=1)))
            self.assertEqual(s.diagnostics()["entries"],2)
            self.assertEqual(s.diagnostics()["evicted_since_start"],1)
            self.assertEqual(SnapshotStore(Path(d)/"other").diagnostics()["max_entries"],1200)
