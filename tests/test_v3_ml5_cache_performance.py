import tempfile
import unittest
from pathlib import Path
from snapshot_store import SnapshotStore

class ML5CachePerformanceTests(unittest.TestCase):
    def test_independent_clocks_and_unchanged_write(self):
        with tempfile.TemporaryDirectory() as d:
            s=SnapshotStore(Path(d)/"cache.json")
            key=("Dhan","NIFTY","1m","5d")
            row=dict(source="Dhan",price=100,quote_timestamp=1000,
                     bars=[[900,99,101,98,100,10]],live_verified=False)
            self.assertTrue(s.put("market",key,row))
            self.assertTrue(s.put("market",key,row))
            self.assertEqual(s.diagnostics()["write_count"],1)
            self.assertEqual(s.diagnostics()["unchanged_writes_skipped"],1)
            newer=dict(row,price=90,quote_timestamp=950,bars=[[960,99,101,98,100,10]])
            self.assertTrue(s.put("market",key,newer))
            got=s.get("market",*key)
            self.assertEqual(got["price"],100)
            self.assertEqual(got["quote_timestamp"],1000)
            self.assertEqual(got["bars"][-1][0],960)
            self.assertFalse(got["live_verified"])
    def test_capacity_warning(self):
        with tempfile.TemporaryDirectory() as d:
            s=SnapshotStore(Path(d)/"cache.json",max_entries=5)
            for n in range(4):
                self.assertTrue(s.put("news",(str(n),),dict(items=[dict(title="t",url="u",published=1,source="s")],fetched=1)))
            self.assertTrue(s.diagnostics()["capacity_warning"])
