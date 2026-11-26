import unittest
from five_engine import ContextualFiveEngineCache, compose_snapshot, EngineEvidence

class DirectionalComponentJoinTests(unittest.TestCase):
    def test_validated_option_can_complete_quorum_context_cannot(self):
        now=1795662000
        cache=ContextualFiveEngineCache()
        key=dict(symbol="NIFTY",timeframe="5m",generation=1)
        cache.publish(**key,snapshot=compose_snapshot(
            technical=EngineEvidence("technical",80,20,verified=True,timestamp=now-30,source="Dhan"),
            candle=EngineEvidence("candle",70,30,verified=True,timestamp=now-10,source="Dhan")))
        option=dict(symbol="NIFTY",underlying="NIFTY",timeframe="5m",generation=1,
            expiry="2026-12-31",source="Dhan",contract="NIFTY fixture",
            timestamp=now-2,mapping_verified=True,verified=True,available=True,
            live_verified=True,historical=False,direction_basis="validated_trade_flow",
            bias="BULLISH",bullish=80,bearish=20)
        original=cache.peek(**key)
        for bad in (dict(option,generation=0),dict(option,symbol="SENSEX"),
                    dict(option,direction_basis="pcr"),dict(option,timestamp=now-100),
                    dict(option,expiry="2020-01-01")):
            self.assertFalse(cache.publish_directional_components(**key,now=now,options=bad))
            self.assertIs(cache.peek(**key),original)
        self.assertTrue(cache.publish_directional_components(**key,now=now,options=option))
        self.assertEqual(cache.peek(**key)["combined"]["state"],"BULLISH")
        self.assertEqual(cache.peek(**key)["combined"]["coverage"],3)
