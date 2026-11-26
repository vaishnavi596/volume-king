import unittest
from five_engine import EngineEvidence, compose_snapshot
from v3_verified_alerts import VerifiedAlertGate

class VerifiedAlertsTests(unittest.TestCase):
    def test_quorum_freshness_and_foreground(self):
        g=VerifiedAlertGate()
        snapshot=compose_snapshot(**{n:EngineEvidence(n,80,20,verified=True,timestamp=1000,source="Dhan") for n in ("technical","candle","options")})
        args=dict(symbol="NIFTY",timeframe="3m",generation=1,now=1010,foreground=True,connected=True,historical_mode=False)
        key=g.candidate(snapshot,**args)
        self.assertEqual(key,("NIFTY","3m","BULLISH"))
        g.acknowledge(key,delivered=False)
        self.assertEqual(g.candidate(snapshot,**args),key)
        g.acknowledge(key,delivered=True)
        self.assertIsNone(g.candidate(snapshot,**args))
        for changes in (dict(now=1400),dict(foreground=False),dict(connected=False),dict(historical_mode=True)):
            self.assertIsNone(g.candidate(snapshot,**dict(args,generation=2,**changes)))
        self.assertIsNone(g.candidate(compose_snapshot(),**args))
        self.assertEqual(g.report()["orders_sent"],0)
        self.assertEqual(g.report()["native_background"],"NOT_WIRED")


    def test_old_generation_cannot_clear_alert_deduplication(self):
        g=VerifiedAlertGate()
        snapshot=compose_snapshot(**{n:EngineEvidence(n,80,20,verified=True,timestamp=1000,source="Dhan") for n in ("technical","candle","options")})
        args=dict(symbol="NIFTY",timeframe="3m",generation=2,now=1010,foreground=True,connected=True,historical_mode=False)
        key=g.candidate(snapshot,**args)
        g.acknowledge(key,delivered=True)
        self.assertIsNone(g.candidate(snapshot,**dict(args,generation=1)))
        self.assertIsNone(g.candidate(snapshot,**args))
        with self.assertRaises(ValueError):VerifiedAlertGate(0)
