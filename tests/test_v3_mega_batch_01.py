import unittest
import tempfile
import os
from pathlib import Path
from clone_smart_refresh_priority import auto_equity_quote_due, safe_quote_batch_for_cache
from v3_vote_trace_doctor import audit_vote_trace
from five_engine import ENGINE_NAMES, EngineEvidence, compose_snapshot
from v3_verified_alerts import VerifiedAlertGate
from backend.dhan_expiry_store import load_expiry_metadata

class MegaBatch01Tests(unittest.TestCase):
    def test_refresh_nonfinite_inputs(self):
        self.assertTrue(auto_equity_quote_due(120,60))
        for bad in (float("nan"),float("inf"),-float("inf"),True):
            self.assertFalse(auto_equity_quote_due(bad,0))
            self.assertFalse(auto_equity_quote_due(120,bad))
            self.assertFalse(auto_equity_quote_due(120,0,floor_seconds=bad))

    def test_quote_batch_identity_and_cache(self):
        good={"source":"Dhan","price":100,"symbol":"A"}
        batch={"A":good,"B":dict(good,symbol="C"),"D":dict(good,symbol="D",cached=True)}
        self.assertEqual(safe_quote_batch_for_cache(batch,{},batch),{"A":good})

    def test_trace_null_combined_and_invalid_context(self):
        snap=compose_snapshot(**{n:EngineEvidence(n,80,20,verified=True,timestamp=1000,source="Dhan") for n in ENGINE_NAMES[:3]})
        rows=[{"engine":n,"status":"BULLISH","raw_verified":True,"raw_source":"Dhan","bullish_percent":80,"bearish_percent":20} for n in ENGINE_NAMES]
        args=dict(symbol="NIFTY",timeframe="3m",generation=1,market_open=True,filter_rows=[],box_rows=rows,snapshot=snap)
        self.assertEqual(audit_vote_trace(**args)["combined_vote"]["state"],"BULLISH")
        self.assertEqual(audit_vote_trace(**dict(args,snapshot=dict(snap,combined=None)))["combined_vote"]["state"],"WAIT")
        for changes in ({"generation":-1},{"market_open":"false"},{"symbol":" "}):
            with self.assertRaises(ValueError):audit_vote_trace(**dict(args,**changes))

    def test_alert_acknowledgement_generation_and_duplicate(self):
        gate=VerifiedAlertGate()
        snap=compose_snapshot(**{n:EngineEvidence(n,80,20,verified=True,timestamp=1000,source="Dhan") for n in ENGINE_NAMES[:3]})
        args=dict(symbol="NIFTY",timeframe="3m",generation=2,now=1010,foreground=True,connected=True,historical_mode=False)
        key=gate.candidate(snap,**args)
        self.assertIsNotNone(key)
        gate.acknowledge(key,delivered=True,generation=1)
        self.assertEqual(gate.report()["delivered"],0)
        gate.acknowledge(key,delivered=True,generation=2)
        gate.acknowledge(key,delivered=True,generation=2)
        self.assertEqual(gate.report()["delivered"],1)
        self.assertEqual(gate.report()["ignored_acknowledgements"],2)
        self.assertIsNone(gate.candidate(snap,**dict(args,generation=3,foreground="false")))

    def test_renewal_metadata_bounded_and_no_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"metadata.json"
            path.write_text('{"source":"dhan_web","expires_at":"2026-11-27T02:00:00+00:00"}')
            os.chmod(path,0o600)
            self.assertEqual(load_expiry_metadata(path)["source"],"dhan_web")
            link=Path(directory)/"link"
            link.symlink_to(path)
            with self.assertRaises(ValueError):load_expiry_metadata(link)
            path.write_text(" "*5000)
            with self.assertRaises(ValueError):load_expiry_metadata(path)
