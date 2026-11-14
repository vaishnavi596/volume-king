"""Batch 4 five-engine directional evidence must fail closed on missing inputs."""
import unittest
from five_engine import ENGINE_NAMES, EngineEvidence, combine_evidence


def evidence(name, bullish=None, verified=False):
    return EngineEvidence(name=name, bullish=bullish,
                          bearish=None if bullish is None else 100-bullish,
                          verified=verified, timestamp=1234567890 if verified else None,
                          source="dhan" if verified else "", reason="Test fixture")


class FiveEngineTests(unittest.TestCase):
    def test_missing_is_not_zero_or_bearish(self):
        missing=evidence("options")
        self.assertEqual(missing.display()["state"],"WAIT")
        self.assertIsNone(missing.display()["bullish"])
        self.assertFalse(missing.eligible)

    def test_unverified_percentage_cannot_vote(self):
        rows=[evidence(n,90,False) for n in ENGINE_NAMES]
        result=combine_evidence(rows)
        self.assertEqual(result["state"],"WAIT")
        self.assertEqual(result["coverage"],0)

    def test_three_independent_verified_engines_can_agree(self):
        rows=[evidence(n,80,True) if n in ENGINE_NAMES[:3] else evidence(n) for n in ENGINE_NAMES]
        result=combine_evidence(rows)
        self.assertEqual(result["state"],"BULLISH")
        self.assertEqual(result["coverage"],3)
        self.assertEqual(result["bullish"],80)

    def test_conflict_waits(self):
        rows=[evidence(n,v,True) for n,v in zip(ENGINE_NAMES,(80,20,80,20,50))]
        self.assertEqual(combine_evidence(rows)["state"],"WAIT")

    def test_two_verified_insufficient(self):
        rows=[evidence(n,80,True) if n in ENGINE_NAMES[:2] else evidence(n) for n in ENGINE_NAMES]
        self.assertEqual(combine_evidence(rows)["state"],"WAIT")

    def test_neutral_does_not_inflate_direction(self):
        rows=[evidence(n,v,True) for n,v in zip(ENGINE_NAMES,(50,50,80,80,50))]
        self.assertEqual(combine_evidence(rows)["state"],"WAIT")

    def test_invalid_inputs_rejected(self):
        for values in ((101,-1),(40,40),(True,False)):
            with self.subTest(values=values),self.assertRaises(ValueError):
                EngineEvidence("news",values[0],values[1],True,"",123,"dhan")
        with self.assertRaises(ValueError):
            combine_evidence([evidence("technical")]*5)

if __name__=="__main__":unittest.main()
