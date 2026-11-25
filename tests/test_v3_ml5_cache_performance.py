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

    def test_incremental_migration_restart_and_eviction(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"cache.json"
            payload=lambda n: dict(items=[dict(title=str(n),url="u",published=1,source="s")],fetched=n)
            old=SnapshotStore(path,max_entries=3)
            self.assertTrue(old.put("news",("a",),payload(1)))
            original=path.read_bytes()
            s=SnapshotStore(path,max_entries=3,incremental=True)
            self.assertEqual(s.get("news","a"),payload(1))
            for n in range(2,5):
                self.assertTrue(s.put("news",(str(n),),payload(n)))
            self.assertEqual(path.read_bytes(),original)
            self.assertIsNone(s.get("news","a"))
            self.assertTrue(s.put("news",("4",),payload(4)))
            self.assertEqual(s.diagnostics()["unchanged_writes_skipped"],1)
            self.assertEqual(s.diagnostics()["storage_backend"],"sqlite_incremental")
            restored=SnapshotStore(path,max_entries=3,incremental=True)
            self.assertEqual(restored.get("news","4"),payload(4))
            self.assertIsNone(restored.get("news","a"))
            self.assertFalse(restored.diagnostics()["restored_cache_live_proof"])
            with sqlite3.connect(str(s.db_path)) as db:
                self.assertEqual(db.execute("SELECT count(*) FROM snapshots").fetchone()[0],3)

    def test_incremental_roster_scaling(self):
        with tempfile.TemporaryDirectory() as d:
            for count in (5,34,51,70):
                s=SnapshotStore(Path(d)/("cache%d.json"%count),incremental=True)
                for n in range(count):
                    for frame in ("1m","3m","5m"):
                        row=dict(source="Dhan",price=100,quote_timestamp=1000,
                                 bars=[[900,99,101,98,100,10]],live_verified=False)
                        self.assertTrue(s.put("market",("Dhan",str(n),frame,"5d"),row))
                self.assertEqual(s.diagnostics()["entries"],count*3)
                self.assertEqual(s.diagnostics()["write_count"],count*3)
                self.assertEqual(SnapshotStore(s.path,incremental=True).diagnostics()["restored_entries"],count*3)

    def test_incremental_corrupt_db_preserves_legacy(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"cache.json"
            old=SnapshotStore(path)
            row=dict(items=[dict(title="t",url="u",published=1,source="s")],fetched=1)
            self.assertTrue(old.put("news",("a",),row))
            original=path.read_bytes()
            Path(str(path)+".sqlite3").write_bytes(b"not a sqlite database")
            s=SnapshotStore(path,incremental=True)
            self.assertEqual(s.get("news","a"),row)
            self.assertEqual(s.diagnostics()["fallback_reason"],"sqlite_restore_failed")
            self.assertTrue(s.put("news",("b",),row))
            self.assertEqual(path.read_bytes(),original)
            self.assertGreater(s.diagnostics()["physical_storage_bytes"],0)

    def test_incremental_physical_bytes_and_concurrent_writes(self):
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"cache.json"
            s=SnapshotStore(path,incremental=True)
            row=dict(items=[dict(title="t",url="u",published=1,source="s")],fetched=1)
            with ThreadPoolExecutor(max_workers=4) as pool:
                self.assertTrue(all(pool.map(lambda n:s.put("news",(str(n),),row),range(70))))
            self.assertEqual(s.diagnostics()["entries"],70)
            self.assertGreater(s.diagnostics()["physical_storage_bytes"],0)
            self.assertEqual(SnapshotStore(path,incremental=True).diagnostics()["restored_entries"],70)

    def test_cache_latency_telemetry(self):
        with tempfile.TemporaryDirectory() as d:
            s=SnapshotStore(Path(d)/"cache.json",incremental=True)
            row=dict(items=[dict(title="t",url="u",published=1,source="s")],fetched=1)
            self.assertTrue(s.put("news",("a",),row))
            self.assertEqual(s.get("news","a"),row)
            self.assertIsNone(s.get("news","missing"))
            stats=s.diagnostics()
            self.assertEqual(stats["read_count"],2)
            self.assertGreaterEqual(stats["read_max_ms"],stats["read_last_ms"])
            self.assertGreaterEqual(stats["write_lock_wait_max_ms"],stats["write_lock_wait_last_ms"])
            self.assertGreaterEqual(stats["write_lock_wait_last_ms"],0)
            self.assertEqual(stats["write_count"],1)
