import unittest
from pathlib import Path
from five_engine import compose_snapshot, live_gate_diagnostic, EngineEvidence
class LiveVotingGateTests(unittest.TestCase):
    def test_explicit_missing_quorum(self):
        snapshot=compose_snapshot(technical=EngineEvidence("technical",80,20,verified=True,timestamp=1795662000,source="Dhan"))
        row=live_gate_diagnostic(snapshot,symbol="NIFTY",timeframe="5m")
        self.assertEqual(row["coverage"],1)
        self.assertEqual(row["required"],3)
        self.assertEqual(row["state"],"WAIT")
        self.assertEqual(len(row["missing_engines"]),4)
        self.assertEqual(row["provider_requests"],0)
    def test_exchange_freshness_wiring(self):
        root=Path(__file__).resolve().parents[1]
        self.assertIn('("verified_live", "live_verified", "exchange_verified")',(root/"src/five_engine.py").read_text())
        self.assertIn('data["live_voting_gate"]=live_voting_gate_report',(root/"src/main.py").read_text())
