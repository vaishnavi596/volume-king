"""Synthetic no-network regressions for SHA-pinned Oracle T09 timeframe echo stage."""
import ast
import hashlib
import unittest
from unittest.mock import patch
from scripts import stage_oracle_t09_assessment_timeframe_echo_20261118 as stage

def fixture():
    # Ensure function starts at 26 and original return sits at 84.
    prefix = "\n"*25
    body = [
        "def assessment(symbol, timeframe=None, expiry=None, x_botking_key=None):",
        "    cached = read('acc', symbol, timeframe=timeframe, expiry=expiry)",
        "    data = {'symbol':symbol,'signal_eligible':False,'factors':{'candle':{'status':'unavailable'}},'assessment_filters':[]}",
    ]
    body += ["    pass"]* (84-26-3)
    body.append("    return data")
    return (prefix+"\n".join(body)+"\n").encode()

class T09AssessmentEchoStageTests(unittest.TestCase):
    def setUp(self):
        self.raw=fixture()
        self.p=patch.object(stage,"EXPECTED",hashlib.sha256(self.raw).hexdigest())
        self.p.start()
        self.addCleanup(self.p.stop)

    def test_only_added_field_and_original_signal_unchanged(self):
        patched=stage.stage_source(self.raw)
        self.assertNotEqual(self.raw,patched)
        env={"read":lambda *args,**kwargs:{}}
        exec(compile(patched,"<t09-test>","exec"),env)
        for tf in ("1m","3m","5m",None):
            with self.subTest(tf=tf):
                result=env["assessment"]("NIFTY",timeframe=tf)
                self.assertEqual(result["timeframe"],tf)
                self.assertIs(result["signal_eligible"],False)
                self.assertEqual(result["factors"]["candle"]["status"],"unavailable")

    def test_staging_preserves_other_definitions(self):
        raw=self.raw+b"\ndef extra_route():\n    return 'original'\n"
        with patch.object(stage,"EXPECTED",hashlib.sha256(raw).hexdigest()):
            patchdata=stage.stage_source(raw)
        self.assertIn(b"def extra_route():\n    return 'original'",patchdata)

    def test_sha_drift_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"SHA_DRIFT"):
            stage.stage_source(self.raw+b"# drift")

    def test_duplicated_assessment_function_rejected(self):
        raw=self.raw+b"\ndef assessment(x):\n    return {}\n"
        with patch.object(stage,"EXPECTED",hashlib.sha256(raw).hexdigest()):
            with self.assertRaisesRegex(ValueError,"FUNCTION_NOT_UNIQUE"):
                stage.stage_source(raw)

    def test_no_handler_lineage_change_allowed(self):
        raw=self.raw.replace(b"    return data",b"    return {}",1)
        with patch.object(stage,"EXPECTED",hashlib.sha256(raw).hexdigest()):
            with self.assertRaisesRegex(ValueError,"RETURN_DATA_ANCHOR_CHANGED"):
                stage.stage_source(raw)

if __name__=="__main__":
    unittest.main()
