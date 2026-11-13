"""Safety checks for server-owned Dhan quote continuity."""
from pathlib import Path
import unittest
SOURCE=(Path(__file__).resolve().parents[1]/"backend/server.py").read_text(encoding="utf-8")
class ServerOwnedSnapshotTests(unittest.TestCase):
    def test_ingest_opt_in_not_automatically_enabled(self):
        self.assertIn('os.environ.get("BOTKING_226_INGEST_ENABLED", "0") == "1"',SOURCE)
        self.assertIn('ingest_task = asyncio.create_task(ingest_quotes()) if ingest_enabled else None',SOURCE)
    def test_server_ingest_has_bounded_cadence_and_rate_limit_cooldown(self):
        self.assertIn('max(60, min(900, int(os.environ.get("BOTKING_226_INGEST_SECONDS", "90"))))',SOURCE)
        self.assertIn('if exc.status_code == 429:',SOURCE)
        self.assertIn('await asyncio.sleep(max(ingest_interval, 120))',SOURCE)
    def test_snapshot_reads_cache_without_upstream_request(self):
        endpoint=SOURCE.split('    @app.get("/v2/snapshot")',1)[1].split('    @app.post("/dhan/ltp-batch")',1)[0]
        self.assertIn('with snapshot_lock:',endpoint)
        self.assertIn('dict(snapshot_cache["quotes"])',endpoint)
        self.assertNotIn('DhanFeed(',endpoint)
        self.assertIn('live_orders_enabled": False',endpoint)
    def test_bad_ingest_does_not_erase_last_valid_snapshot(self):
        ingest=SOURCE.split('        async def ingest_quotes():',1)[1].split('        ingest_task =',1)[0]
        self.assertIn('snapshot_cache["error"] = "ingest_unavailable"',ingest)
        self.assertNotIn('snapshot_cache.clear()',ingest)
    def test_batch_rejects_empty_and_invalid_prices_before_cache(self):
        batch=SOURCE.split('    @app.post("/dhan/ltp-batch")',1)[1].split('    # Historical candles',1)[0]
        self.assertIn('if not quotes:',batch)
        self.assertLess(batch.index('if not quotes:'),batch.index('snapshot_cache.update('))
if __name__=="__main__":
    unittest.main()
