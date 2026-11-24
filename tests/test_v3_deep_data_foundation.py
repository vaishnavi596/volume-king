"""Deep Batch 1: cache capacity and safe Clone HTTP reporting."""
import tempfile
from pathlib import Path
import unittest
from test_audit import start
from snapshot_store import SnapshotStore
from feed_health import safe_error
from server_feed import FeedError

class DeepDataFoundationTests(unittest.TestCase):
    def test_73_instruments_three_frames_survive_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"cache.json"
            store=SnapshotStore(path)
            for sym in range(73):
                for tf,step in (("1m",60),("3m",180),("5m",300)):
                    rows=[[1700000000+i*step,100,102,99,101,10] for i in range(30)]
                    payload=dict(price=None,bars=rows,source="Dhan",live_verified=False,
                                 freshness="historical_unverified",_scanner_timeframe=tf)
                    self.assertTrue(store.put("market",("Dhan",str(sym),tf,"2d"),payload))
            restored=SnapshotStore(path)
            for sym in range(73):
                for tf in ("1m","3m","5m"):
                    self.assertIsNotNone(restored.get("market","Dhan",str(sym),tf,"2d"))
    def test_clone_statuses_survive_sanitization(self):
        for status,message in (
            (401,"Clone SSK authorization expired (HTTP 401)"),
            (403,"Clone SSK authorization expired (HTTP 403)"),
            (424,"Clone Dhan authorization required (HTTP 424)"),
            (429,"Clone Dhan rate limit; retry later (HTTP 429)"),
            *((n,f"Clone Dhan upstream or gateway unavailable (HTTP {n})") for n in (502,503,504)),
        ):
            self.assertIn(f"HTTP {status}",safe_error(FeedError(message)))
        self.assertNotIn("SECRET",safe_error(FeedError("untrusted SECRET response")))
