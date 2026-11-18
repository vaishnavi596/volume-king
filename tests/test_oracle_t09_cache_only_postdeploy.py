"""Offline T09 no-provider cache-only HTTP gate; no remote calls in tests."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_oracle_t09_cached_candle_readback_20261118.py"
spec = importlib.util.spec_from_file_location("t09_cache_only", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

class T09CacheOnlyGateTests(unittest.TestCase):
    def test_source_pins_match_deployed_reader_and_protect_other_modules(self):
        self.assertEqual(
            probe.SOURCE_SHA["assessment_api.py"],
            "33caaba5f8c20d366685cf4a72f5d64dfc38adf87f06671b87ce6152863b00bc")
        self.assertEqual(
            probe.SOURCE_SHA["server.py"],
            "9327e33a204e06affad383bd8af80ae0ed5f90bc79ee2b1410cadcb7fc5e12b5")
        self.assertEqual(
            probe.SOURCE_SHA["assessment_state.py"],
            "ea2db1787be5cddc1ff2235db6592c7858519fc97b18d8c65c011ef9c7a3e3d2")

    def test_allowlist_never_contains_provider_path(self):
        self.assertEqual(probe.ALLOWED_PATHS, {
            "/health", "/v2/candles/NIFTY/5", "/v2/assessment/NIFTY?timeframe=5m"})
        with self.assertRaisesRegex(RuntimeError, "NON_ALLOWLISTED"):
            probe.get("/dhan/intraday", "test-key")

    def test_cache_and_readback_never_claim_causality_or_live_signal(self):
        bars = [[1,100,102,99,101,1000],[301,101,103,100,102,1500]]
        result = probe.evaluate(
            (200, {"status":"ok"}),
            (200, {"source":"dhan","bars":bars,"freshness":"historical_unverified"}),
            (200, {"timeframe":"5m","signal_eligible":False,
                   "factors":{"candle":{"status":"unavailable"}}}))
        self.assertEqual(result["status"],
                         "CACHE_AND_ASSESSMENT_HTTP_PASS_PUBLISH_CAUSALITY_UNPROVEN")
        self.assertFalse(result["actual_intraday_post_proven"])
        self.assertFalse(result["dhan_routes_called"])
        self.assertEqual(result["candle_factor_status"],"unavailable")

    def test_empty_cache_stays_uncorroborated_no_provider_call(self):
        result = probe.evaluate(
            (200, {}),(200, {"source":"dhan","bars":[],"freshness":"stale_or_missing"}),
            (200, {"timeframe":"5m","signal_eligible":False}))
        self.assertEqual(result["status"],"NO_CACHED_HISTORY_NO_DHAN_REQUEST")
        self.assertEqual(result["cached_bar_count"],0)

    def test_false_live_eligibility_fails_closed(self):
        result = probe.evaluate(
            (200, {}),(200, {"source":"dhan","bars":[[1],[2]],"freshness":"historical_unverified"}),
            (200, {"timeframe":"5m","signal_eligible":True}))
        self.assertEqual(result["status"],"HOLD_HTTP_OR_SAFETY")

    def test_main_uses_only_three_allowed_gets_and_has_no_mutations(self):
        calls=[]
        def fake(path,key):
            calls.append(path)
            if path=="/health":return 200,{}
            if path=="/v2/candles/NIFTY/5":return 200,{"source":"dhan","bars":[]}
            return 200,{"timeframe":"5m","signal_eligible":False}
        with patch.object(probe,"sha_preflight"), patch.object(probe,"resolve_key",return_value="secret"), patch.object(probe,"get",side_effect=fake):
            self.assertEqual(probe.main(),0)
        self.assertEqual(calls,["/health","/v2/candles/NIFTY/5",
                                "/v2/assessment/NIFTY?timeframe=5m"])

if __name__=="__main__":
    unittest.main()
