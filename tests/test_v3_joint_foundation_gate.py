"""Offline V3 joint source/upgrade gate; no broker/network or APK build."""
from pathlib import Path
import ast
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=(ROOT/".github/workflows/v1-pure-original-clone-apk.yml").read_text()
MAIN=(ROOT/"src/main.py").read_text()
CLIENT=(ROOT/"src/clone_v2_gateway.py").read_text()
SERVER=(ROOT/"backend/clone_v2_gateway.py").read_text()


class V3JointFoundationGate(unittest.TestCase):
    def test_source_compiles(self):
        for path in ("src/main.py","src/five_engine.py",
                     "src/clone_v2_gateway.py","backend/clone_v2_gateway.py"):
            with self.subTest(path=path):
                ast.parse((ROOT/path).read_text(),filename=path)

    def test_no_auto_or_ephemeral_same_package_apk(self):
        # Never produce a new independently signed APK for the same package.
        self.assertIn("workflow_dispatch:",WORKFLOW)
        self.assertNotIn("  push:",WORKFLOW.split("permissions:",1)[0])
        self.assertNotIn("keytool -genkeypair",WORKFLOW)
        for key in ("BOTKING_KEYSTORE_BASE64","BOTKING_KEYSTORE_PASSWORD",
                    "BOTKING_KEY_PASSWORD","BOTKING_KEY_ALIAS","BOTKING_SIGNING_SHA256"):
            self.assertIn("secrets."+key,WORKFLOW)
        self.assertIn("Permanent APK signer SHA-256 MATCH=PASS",WORKFLOW)
        self.assertIn("Output APK is not signed by the pinned keystore",WORKFLOW)
        self.assertLess(WORKFLOW.index("Require pinned permanent Android signing"),
                        WORKFLOW.index("flet build apk"))

    def test_429_stage_is_fixed_sanitized_enum(self):
        self.assertIn('"X-BotKing-429-Stage": "GATEWAY_PACING"',SERVER)
        self.assertIn('"X-BotKing-429-Stage": "PROVIDER_QUOTA"',SERVER)
        self.assertIn('"X-BotKing-429-Stage": "PROVIDER_COOLDOWN"',SERVER)
        self.assertIn('stage=="GATEWAY_PACING"',CLIENT)
        self.assertIn('stage in ("PROVIDER_QUOTA","PROVIDER_COOLDOWN")',CLIENT)
        self.assertIn('cooldown_seconds = 2 if "quote lane paced" in str(exc) else 30',CLIENT)

    def test_phone_doctors_explain_rate_limit_origin_not_just_http_429(self):
        self.assertIn('index_failure_429_stage=["NOT_APPLICABLE"]',MAIN)
        self.assertIn('"GATEWAY_PACING" if "quote lane paced" in diagnostic',MAIN)
        self.assertIn('"PROVIDER_QUOTA_OR_COOLDOWN" if "provider rate limit" in diagnostic',MAIN)
        self.assertIn('"rate_limit_origin":index_failure_429_stage[0]',MAIN)
        self.assertIn('"index_rate_limit_origin":index_failure_429_stage[0]',MAIN)

    def test_normalized_candle_parity_is_not_live_proof(self):
        self.assertIn('"normalized_bars_sha256": hashlib.sha256(',SERVER)
        self.assertIn('"normalized_transport_integrity"]="SHA256_MATCH"',CLIENT)
        self.assertIn("Clone candle normalized transport digest mismatch",CLIENT)
        self.assertIn('else:\n            response["normalized_transport_integrity"]="NOT_PROVIDED"',CLIENT)
        self.assertIn('"freshness": "historical_unverified" if bars',SERVER)

    def test_doctor_does_not_label_unverified_waits_as_errors(self):
        self.assertIn('errors=[row for row in filter_rows if row["status"]=="ERROR"]',MAIN)
        self.assertIn('"unavailable_evidence":unavailable_evidence',MAIN)
        self.assertIn('if row["status"]=="WAIT"',MAIN)

    def test_candle_integrity_survives_phone_to_doctor_with_derived_label(self):
        self.assertIn('candle_result.get("normalized_transport_integrity","NOT_PROVIDED")',MAIN)
        self.assertIn('"DERIVED_FROM_TRANSPORT_SHA256_MATCH"',MAIN)
        self.assertIn('"DERIVED_FROM_TRANSPORT_UNVERIFIED"',MAIN)
        self.assertIn('"candle_transport_integrity":str(history.get(',MAIN)
        retention=(ROOT/"src/candle_retention.py").read_text()
        self.assertIn('"MERGED_HISTORY_NOT_DIRECT_DIGEST"',retention)
        self.assertIn('"RETAINED_PRIOR_TRANSPORT_SHA256_MATCH"',retention)
        self.assertIn('"RETAINED_PRIOR_TRANSPORT_UNVERIFIED"',retention)

    def test_local_derived_watchlist_and_chart_do_not_inherit_raw_sha_match(self):
        # Three independent display paths: 1m→3m, retained 3m, 5m→10m/15m→30m.
        shared=MAIN.split('    def shared_history(sym,tf="5m"):',1)[1].split(
            '    watch_three_minute_cache={}',1)[0]
        self.assertIn('candle_transport_integrity=(',shared)
        self.assertIn('source_1m.get("candle_transport_integrity")',shared)
        self.assertIn('source.get("candle_transport_integrity")',shared)
        self.assertIn('"DERIVED_FROM_TRANSPORT_SHA256_MATCH"',shared)
        self.assertIn('"DERIVED_FROM_TRANSPORT_UNVERIFIED"',shared)
        self.assertIn('"RETAINED_DERIVED_HISTORY_UNVERIFIED"',shared)
        self.assertNotIn('live_verified=True',shared)

    def test_five_engine_missing_source_wiring_is_visible_not_fake_signal(self):
        from sys import path
        import sys
        sys.path.insert(0,str(ROOT/"src"))
        try:
            from five_engine import independent_engine_source_contract
            statuses=independent_engine_source_contract()
        finally:
            sys.path.pop(0)
        self.assertEqual(set(statuses),{"technical","candle","news","futures","options"})
        self.assertTrue(all("readiness" in v for v in statuses.values()))
        self.assertIn("source_wiring_contract",MAIN)
        self.assertIn("MEASURED_DIRECTIONAL_STRENGTH_NOT_WIRED",
                      statuses["options"]["readiness"])
        self.assertIn("MEASURED_DIRECTIONAL_STRENGTH_NOT_WIRED",
                      statuses["futures"]["readiness"])


if __name__=="__main__":
    unittest.main()
