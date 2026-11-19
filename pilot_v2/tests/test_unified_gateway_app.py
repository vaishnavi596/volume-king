"""One app entry, one gateway, one read pipeline; offline auth-isolation tests."""
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from pilot_v2.atomic_verified_login import AtomicVerifiedLogin
from pilot_v2.device_verifier import P256ChallengeVerifier, encode_b64
from pilot_v2.durable_challenges import DurableP256ChallengeVerifier
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.internal_dhan_read_port import DhanReadBatch, InternalDhanReadPort
from pilot_v2.unified_data_pipeline import V2UnifiedReadPipeline
from pilot_v2.unified_gateway_app import create_v2_unified_app
from pilot_v2.private_backup_vault import ServerBackupVault, seal_local_preferences
import json

NOW = 1800000000
IST = ZoneInfo("Asia/Kolkata")


class UnifiedGatewayAcceptance(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / "auth.db"
        self.device = "master-v2-unified-0001"
        self.private = ec.generate_private_key(ec.SECP256R1())
        pub = self.private.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        sessions = DurableDeviceSessions(db)
        sessions.bootstrap(self.device, authorize_bootstrap=lambda _: True)
        verifier = DurableP256ChallengeVerifier(db, {self.device: pub})
        login = AtomicVerifiedLogin(verifier, sessions)
        self.login = login
        self.sessions = sessions
        self.vault_path = Path(tmp.name) / "backup.db"
        self.calls = []

        def transport(feed, symbols):
            self.calls.append((feed, symbols))
            return DhanReadBatch(
                "dhan", symbols,
                {s: {"price": 101, "observed_at": NOW} for s in symbols},
                len(self.calls), NOW)

        port = InternalDhanReadPort(
            transport=transport, selected_equities=("RELIANCE",),
            clock=lambda: NOW)
        self.pipeline = V2UnifiedReadPipeline(
            read_port=port,
            clock=lambda: datetime(2026, 11, 19, 11, 0, tzinfo=IST),
            monotonic=lambda: 10)
        self.client = TestClient(create_v2_unified_app(
            verified_login=login, data_pipeline=self.pipeline))

    def signed_bearer(self):
        r = self.client.post("/v2-pilot/auth/challenge",
                             json={"device_id": self.device})
        self.assertEqual(r.status_code, 200)
        nonce = r.json()["challenge"]
        signature = self.private.sign(
            P256ChallengeVerifier.signed_message(self.device, nonce),
            ec.ECDSA(hashes.SHA256()))
        r = self.client.post("/v2-pilot/auth/login",
                             json={"device_id": self.device, "challenge": nonce,
                                   "signature": encode_b64(signature)})
        self.assertEqual(r.status_code, 200)
        return r.json()["device_bearer"]

    def test_provider_never_called_before_signed_login(self):
        self.assertEqual(self.client.get("/v2-pilot/quotes").status_code, 401)
        self.assertEqual(self.client.get("/v2-pilot/indices",
                                        headers={"Authorization": "Bearer " + "x" * 48}
                                        ).status_code, 403)
        self.assertEqual(self.calls, [])

    def test_verified_login_serves_both_feeds_one_app(self):
        bearer = self.signed_bearer()
        headers = {"Authorization": "Bearer " + bearer}
        q = self.client.get("/v2-pilot/quotes", headers=headers)
        i = self.client.get("/v2-pilot/indices", headers=headers)
        self.assertEqual(q.status_code, 200)
        self.assertEqual(i.status_code, 200)
        self.assertEqual(set(i.json()["quotes"]), {"NIFTY", "BANKNIFTY", "SENSEX"})
        self.assertEqual(set(q.json()["quotes"]), {"RELIANCE"})
        self.assertEqual(len(self.calls), 2)
        self.assertFalse(q.json()["quotes"]["RELIANCE"]["live_verified"])

    def test_missing_transport_denied_as_503(self):
        bearer = self.signed_bearer()
        self.pipeline._port._transport = lambda *_: (_ for _ in ()).throw(OSError())
        r = self.client.get("/v2-pilot/quotes",
                            headers={"Authorization": "Bearer " + bearer})
        self.assertEqual(r.status_code, 503)
        self.assertEqual(self.calls, [])

    def test_opt_in_backup_mount_requires_exact_login_session_store(self):
        # Ordinary gateway never mounts private storage.
        self.assertEqual(self.client.get("/v2-pilot/private-backup").status_code, 404)
        vault = ServerBackupVault.from_durable_sessions(
            self.vault_path, self.sessions)
        wrong = DurableDeviceSessions(Path(self.vault_path.parent) / "wrong.db")
        mismatched = ServerBackupVault.from_durable_sessions(
            Path(self.vault_path.parent) / "wrong-vault.db", wrong)
        with self.assertRaises(ValueError):
            create_v2_unified_app(
                verified_login=self.login, data_pipeline=self.pipeline,
                private_backup_vault=mismatched)
        client = TestClient(create_v2_unified_app(
            verified_login=self.login, data_pipeline=self.pipeline,
            private_backup_vault=vault), base_url="https://testserver")
        self.assertEqual(client.get("/v2-pilot/private-backup").status_code, 401)
        bearer = self.signed_bearer()
        headers = {"Authorization": "Bearer " + bearer}
        raw = json.dumps({"kind": "botking-v2-local-preferences",
            "schema_version": 1, "watchlists": {}, "scanner": {},
            "smart_data": {}, "analysis_slots": {}})
        encrypted = seal_local_preferences(raw, "long private backup password")
        result = client.post("/v2-pilot/private-backup", headers=headers,
            json={"expected_revision": 0, "encrypted_envelope": encrypted})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(client.get("/v2-pilot/private-backup", headers=headers)
                         .json()["encrypted_envelope"], encrypted)
        self.assertEqual(self.calls, [])  # No Dhan traffic for backups.
        self.sessions.logout(bearer)
        self.assertEqual(client.get("/v2-pilot/private-backup",
                                    headers=headers).status_code, 403)

    def test_production_health_never_claims_market_live(self):
        result = self.client.get("/v2-pilot/health")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers.get("cache-control"), "no-store")
        self.assertFalse(result.json()["live_data_verified"])
        self.assertFalse(result.json()["live_orders_enabled"])
        self.assertEqual(self.calls, [])

    def test_signed_manual_read_uses_same_trusted_pipeline(self):
        self.assertEqual(self.client.post("/v2-pilot/manual/indices").status_code, 401)
        self.assertEqual(self.calls, [])
        bearer = self.signed_bearer()
        headers = {"Authorization": "Bearer " + bearer}
        self.assertEqual(self.client.get("/v2-pilot/quotes", headers=headers).status_code, 200)
        self.assertEqual(self.client.post("/v2-pilot/manual/quotes", headers=headers).status_code, 200)
        self.assertEqual(self.calls, [("quotes", ("RELIANCE",)), ("quotes", ("RELIANCE",))])
        self.assertEqual(self.client.post("/v2-pilot/manual/orders", headers=headers).status_code, 404)

    def test_server_logout_revokes_bearer_without_provider_read(self):
        bearer = self.signed_bearer()
        headers = {"Authorization": "Bearer " + bearer}
        self.assertEqual(self.client.post("/v2-pilot/auth/logout", headers=headers).status_code, 200)
        self.assertEqual(self.client.get("/v2-pilot/quotes", headers=headers).status_code, 403)
        self.assertEqual(self.calls, [])

    def test_master_only_roster_updates_selected_quotes_atomically(self):
        from pilot_v2.unified_gateway_app import create_v2_unified_app
        def update(symbols):
            changed = self.pipeline.replace_selected_equities(symbols)
            return len(symbols)
        client = TestClient(create_v2_unified_app(
            verified_login=self.login, data_pipeline=self.pipeline,
            master_roster_updater=update))
        self.assertEqual(client.post("/v2-pilot/master/roster",
                         json={"symbols": ["TCS"]}).status_code, 401)
        self.assertEqual(client.post("/v2-pilot/master/roster",
                         json={"symbols": ["TCS"]},
                         headers={"Authorization": "Bearer " + "a" * 48}).status_code, 403)
        bearer = self.signed_bearer()
        headers = {"Authorization": "Bearer " + bearer}
        self.assertEqual(client.post("/v2-pilot/master/roster",
                         json={"symbols": ["TCS", "INFY"]},
                         headers=headers).json()["selected_equities"], 2)
        result = client.get("/v2-pilot/quotes", headers=headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(set(result.json()["quotes"]), {"TCS", "INFY"})
        self.assertEqual(client.post("/v2-pilot/master/roster",
                         json={"symbols": ["TCS", "TCS"]},
                         headers=headers).status_code, 422)
        self.assertEqual(set(client.get("/v2-pilot/quotes",
                         headers=headers).json()["quotes"]), {"TCS", "INFY"})

    def test_roster_update_unavailable_when_no_private_persistor(self):
        bearer = self.signed_bearer()
        self.assertEqual(self.client.post("/v2-pilot/master/roster",
                          json={"symbols": ["TCS"]},
                          headers={"Authorization": "Bearer " + bearer}).status_code, 503)

    def test_factory_fail_closed(self):
        with self.assertRaises(ValueError):
            create_v2_unified_app(verified_login=None, data_pipeline=self.pipeline)
        with self.assertRaises(ValueError):
            create_v2_unified_app(verified_login=None, data_pipeline=None)


if __name__ == "__main__":
    unittest.main()
