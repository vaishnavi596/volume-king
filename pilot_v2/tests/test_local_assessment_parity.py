"""V1 four-factor assessment → V2 local WAIT/HIST without invented signals."""
import sys
import unittest
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from local_assessment_evidence import (
    LocalAssessmentEvidence, AssessmentEvidenceError, FACTORS)

def evidence(direction="bullish", observed=100):
    return {"direction": direction, "source": "dhan",
            "eligible": True, "observed_at": observed}

class AssessmentParityTests(unittest.TestCase):
    def setUp(self):
        self.assessment = LocalAssessmentEvidence()

    def test_four_factors_all_wait_without_external_producer(self):
        self.assertEqual(FACTORS, ("news", "futures", "options", "candle"))
        rows = self.assessment.rows("TCS", selected_equities=("TCS",))
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(value == "WAIT" for _, value in rows))
        self.assertIn("0/4", self.assessment.label(
            "TCS", selected_equities=("TCS",)))

    def test_partial_independent_factor_revisions_and_selected_roster(self):
        self.assertTrue(self.assessment.accept(
            "TCS", 2, {"options": evidence()}, selected_equities=("TCS",),
            trusted_transport=True))
        self.assertFalse(self.assessment.accept(
            "TCS", 1, {"options": evidence("bearish")},
            selected_equities=("TCS",), trusted_transport=True))
        self.assertTrue(self.assessment.accept(
            "TCS", 1, {"news": evidence("neutral")},
            selected_equities=("TCS",), trusted_transport=True))
        rows = dict(self.assessment.rows("TCS", selected_equities=("TCS",)))
        self.assertEqual(rows["Options"], "BULLISH HIST")
        self.assertEqual(rows["News"], "NEUTRAL HIST")
        self.assertEqual(rows["Candle"], "WAIT")
        self.assertEqual(self.assessment.rows("TCS")[0][1], "WAIT")
        self.assessment.forget_removed(())
        self.assertTrue(all(value == "WAIT" for _, value in self.assessment.rows(
            "TCS", selected_equities=("TCS",))))

    def test_trust_schema_and_source_fail_closed(self):
        for changed, trust in (
            ({"news": evidence()}, False),
            ({"news": dict(evidence(), source="yahoo")}, True),
            ({"news": dict(evidence(), eligible=False)}, True),
            ({"news": dict(evidence(), observed_at=0)}, True),
            ({"news": dict(evidence(), direction="green")}, True),
            ({"news": dict(evidence(), confidence=99)}, True),
        ):
            with self.subTest(data=changed):
                with self.assertRaises(AssessmentEvidenceError):
                    self.assessment.accept(
                        "TCS", 1, changed, selected_equities=("TCS",),
                        trusted_transport=trust)
        self.assertEqual(
            dict(self.assessment.rows("TCS", selected_equities=("TCS",)))["News"],
            "WAIT")

    def test_scanner_ui_uses_four_independent_wait_gated_factors(self):
        src = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertIn("from local_assessment_evidence import", src)
        self.assertIn("assessment = LocalAssessmentEvidence()", src)
        self.assertIn("for factor, value in assessment.rows(", src)
        self.assertIn("scanner[0].symbol, selected_equities=state.selected", src)
        self.assertIn("assessment.forget_removed(state.selected)", src)
        self.assertNotIn("ServerAngelFeed", src)

if __name__ == "__main__":
    unittest.main()
