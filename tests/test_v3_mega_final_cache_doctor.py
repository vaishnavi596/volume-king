import unittest
import tempfile
from pathlib import Path
from snapshot_store import SnapshotStore, public_copy, age_label
from feed_health import FeedHealth
from refresh_policy import completed_bar_revision
from watchlist_policy import normalize_watchlists
from v3_compact_doctor import compact_doctor

class MegaFinalTests(unittest.TestCase):
    def test_snapshot_rejects_invalid_capacity_and_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"cache.json"
            with self.assertRaises(ValueError):SnapshotStore(p,0)
            store=SnapshotStore(p)
            self.assertFalse(store.put("market",("Dhan","NIFTY","3m","5d"),{"price":float("nan")}))
            self.assertEqual(store.diagnostics()["rejected_since_start"],1)
            self.assertEqual(public_copy({"nested":{"access-key":"secret","token":"secret","price":1}}),{"nested":{"price":1}})
            self.assertFalse(store.valid("market",{"price":100,"bars":[[1,True,102,99,101,10]]}))
            self.assertEqual(age_label(1,now=float("nan")),"Time unavailable")
            self.assertEqual(age_label(True,now=10),"Time unavailable")

    def test_duplicate_health_completion_is_not_success(self):
        clock=[100]
        h=FeedHealth(clock=lambda:clock[0])
        req=h.begin("NIFTY")
        self.assertTrue(h.finish("NIFTY",req,"AVAILABLE"))
        clock[0]=200
        self.assertFalse(h.finish("NIFTY",req,"AVAILABLE"))
        self.assertEqual(h.get("NIFTY")["last_success"],100)

    def test_invalid_bar_does_not_trigger_revision(self):
        self.assertEqual(completed_bar_revision([[1,100,102,99,101,10]]),(1,100,102,99,101,10))
        for row in ([1,True,102,99,101,10],[1,100,98,99,101,10],[1,100,102,99,101,-1],[float("nan"),100,102,99,101,10]):
            self.assertIsNone(completed_bar_revision([row]))

    def test_roster_cannot_override_provider_capacity(self):
        with self.assertRaises(ValueError):normalize_watchlists([[],[],[],[],[]],maximum=71)

    def test_compact_doctor_keeps_unverified_and_contradictory_filter_visible(self):
        out=compact_doctor([{"symbol":"NIFTY","state":"UNVERIFIED"}],["EMA 9/21"],[{"name":"EMA 9/21","vote":1,"status":"ERROR"}],scanner_symbol="NIFTY",scanner_timeframe="3m",provider_connected=True)
        self.assertEqual(out["healthy_stock_count_hidden"],0)
        self.assertEqual(out["healthy_filter_count_hidden"],0)
        self.assertEqual(out["issue_count"],2)
