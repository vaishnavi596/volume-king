import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from v3_smart_active_doctor import active_report

class WatchlistGateSnapshotTest(unittest.TestCase):
    def test_selected_roster_and_unknown_transport(self):
        for n in (5,51,70):
            with self.subTest(n=n):
                syms=["S"+str(i) for i in range(n)]
                gates={"budget_full":True,"cooldown_seconds":0}
                report=active_report(generation=1,symbols=syms,quote_present=syms[:1],
                    index_present=[],connected={"Dhan":True},signal_present=[],
                    attempts={syms[0]:90},now_monotonic=100,market_open=True,
                    errors=[],progress={"watchlist_gate_snapshot":gates},
                    performance={},quote_attempt_age=None,candle_stamps={syms[0]:500},
                    now_epoch=1000)
                row=next(x for x in report["active"] if x["check"]=="WATCHLIST_FAIR_REFRESH")
                self.assertEqual(row["gate_snapshot"],gates)
                obs=row["symbol_observations"]
                self.assertEqual(len(obs),n)
                self.assertEqual(obs[0]["attempt_age_seconds"],10)
                self.assertEqual(obs[0]["cached_completed_3m_age_seconds"],500)
                self.assertTrue(obs[0]["quote_cached"])
                self.assertIsNone(obs[1]["attempt_age_seconds"])
                self.assertIsNone(obs[1]["cached_completed_3m_age_seconds"])
                self.assertFalse(obs[1]["quote_cached"])
                self.assertTrue(all(x["transport_success"]=="UNVERIFIED" for x in obs))
                self.assertEqual(report["provider_requests"],0)
                self.assertFalse(report["source_live_verified"])
