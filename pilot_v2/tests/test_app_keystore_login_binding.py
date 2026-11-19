"""Source-only Android Keystore public/sign callback boundary, no Android runtime."""
import ast
import hashlib
from threading import Event, Thread
import sys
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from app_keystore_login_binding import AndroidKeystoreLoginBinding
from app_device_reader_slot import DeviceReaderSlot
from app_p256_login import LOGIN_CONTEXT, V2P256LoginHTTPSClient
from secure_https_reader import FeedError, V2ReadonlyHTTPSReader

MASTER = "master_device_000001"
DELEGATE = "second_device_00001"


class KeystoreBindingTests(unittest.TestCase):
    def setUp(self):
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.public = self.key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        self.calls = []
        def signer(message):
            self.calls.append(message)
            return self.key.sign(message, ec.ECDSA(hashes.SHA256()))
        self.signer = signer

    def bind(self, device=MASTER, signer=None):
        return AndroidKeystoreLoginBinding(
            device, lambda: self.public, signer or self.signer)

    def test_public_only_enrollment_and_exact_login_context(self):
        binding = self.bind()
        self.assertEqual(binding.public_spki_for_owner_enrollment(), self.public)
        self.assertEqual(binding.public_key_fingerprint_sha256(),
                         hashlib.sha256(self.public).hexdigest())
        self.assertEqual(len(binding.public_key_fingerprint_sha256()), 64)
        signed = LOGIN_CONTEXT + MASTER.encode("ascii") + b"\x00" + bytes(range(32))
        sig = binding.sign_login_challenge(signed)
        self.key.public_key().verify(sig, signed, ec.ECDSA(hashes.SHA256()))
        self.assertEqual(self.calls, [signed])
        self.assertNotIn("private_key", repr(binding))
        client = binding.login_client("https://v2.example.test")
        self.assertIsInstance(client, V2P256LoginHTTPSClient)
        self.assertEqual(len(self.calls), 1)  # Constructor never signs or fetches.

    def test_cross_device_or_arbitrary_messages_never_reach_native_signer(self):
        binding = self.bind()
        prefix = LOGIN_CONTEXT + MASTER.encode("ascii") + b"\x00"
        samples = (b"", b"market-order", b"token", prefix,
                   prefix + bytes(31), prefix + bytes(33),
                   LOGIN_CONTEXT + DELEGATE.encode("ascii") + b"\x00" + bytes(32),
                   prefix + bytes(32) + b"trailing", "string", bytearray(prefix + bytes(32)))
        for value in samples:
            with self.subTest(value=repr(value)[:35]), self.assertRaises(FeedError):
                binding.sign_login_challenge(value)
        self.assertEqual(self.calls, [])

    def test_invalid_public_key_bad_signer_and_platform_exception_fail_closed(self):
        with self.assertRaises(FeedError):
            AndroidKeystoreLoginBinding(MASTER, lambda: b"private-key", self.signer)
        with self.assertRaises(FeedError):
            AndroidKeystoreLoginBinding(MASTER, lambda: self.public, None)
        with self.assertRaises(FeedError):
            AndroidKeystoreLoginBinding("bad id", lambda: self.public, self.signer)
        malformed = self.bind(signer=lambda message: b"sigbytes")
        with self.assertRaises(FeedError):
            malformed.sign_login_challenge(
                LOGIN_CONTEXT + MASTER.encode("ascii") + b"\x00" + bytes(32))
        def unavailable(message):
            raise RuntimeError("native-secret-alias")
        failed = self.bind(signer=unavailable)
        with self.assertRaises(FeedError) as error:
            failed.sign_login_challenge(
                LOGIN_CONTEXT + MASTER.encode("ascii") + b"\x00" + bytes(32))
        self.assertNotIn("native-secret-alias", str(error.exception))
        self.assertEqual(self.calls, [])

    def test_rotated_public_key_denied_before_old_signer_is_invoked(self):
        second_key = ec.generate_private_key(ec.SECP256R1())
        rotated_public = second_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        current = [self.public]
        binding = AndroidKeystoreLoginBinding(
            MASTER, lambda: current[0], self.signer)
        original_fingerprint = binding.public_key_fingerprint_sha256()
        current[0] = rotated_public
        message = LOGIN_CONTEXT + MASTER.encode("ascii") + b"\x00" + bytes(32)
        with self.assertRaises(FeedError) as error:
            binding.sign_login_challenge(message)
        self.assertNotIn("private", str(error.exception))
        self.assertEqual(self.calls, [])
        self.assertEqual(original_fingerprint, hashlib.sha256(self.public).hexdigest())
        with self.assertRaises(FeedError):
            binding.public_spki_for_owner_enrollment()
        with self.assertRaises(FeedError):
            binding.public_key_fingerprint_sha256()
        self.assertEqual(self.calls, [])

    def test_native_public_recheck_failure_denied_without_signing(self):
        calls = [0]
        def export():
            calls[0] += 1
            if calls[0] > 1:
                raise RuntimeError("sensitive platform key alias")
            return self.public
        binding = AndroidKeystoreLoginBinding(MASTER, export, self.signer)
        message = LOGIN_CONTEXT + MASTER.encode("ascii") + b"\x00" + bytes(32)
        with self.assertRaises(FeedError) as error:
            binding.sign_login_challenge(message)
        self.assertNotIn("sensitive", str(error.exception))
        self.assertEqual(self.calls, [])
        with self.assertRaises(FeedError):
            binding.public_spki_for_owner_enrollment()
        with self.assertRaises(FeedError):
            binding.public_key_fingerprint_sha256()

    def test_current_public_export_and_fingerprint_remain_consistent(self):
        calls = []
        def export():
            calls.append("public")
            return self.public
        binding = AndroidKeystoreLoginBinding(MASTER, export, self.signer)
        self.assertEqual(binding.public_spki_for_owner_enrollment(), self.public)
        self.assertEqual(binding.public_key_fingerprint_sha256(),
                         hashlib.sha256(self.public).hexdigest())
        message = LOGIN_CONTEXT + MASTER.encode("ascii") + b"\x00" + bytes(32)
        signature = binding.sign_login_challenge(message)
        self.key.public_key().verify(signature, message, ec.ECDSA(hashes.SHA256()))
        self.assertEqual(calls, ["public"] * 4)
        self.assertEqual(self.calls, [message])

    def test_strict_keystore_to_session_handoff_remains_dormant(self):
        slot = DeviceReaderSlot()
        binding = self.bind()
        with self.assertRaises(FeedError):
            slot.sign_in_with_keystore(object(), "https://v2.example.test")
        with self.assertRaises(FeedError):
            slot.sign_in_with_keystore(binding, "http://v2.example.test")
        self.assertEqual(self.calls, [])
        self.assertIsNone(slot.reader)
        with patch.object(slot, "_complete_sign_in", return_value=True) as approved_login:
            self.assertTrue(slot.sign_in_with_keystore(
                binding, "https://v2.example.test"))
            approved_login.assert_called_once()
            client, attempt = approved_login.call_args.args
            self.assertIsInstance(client, V2P256LoginHTTPSClient)
            self.assertIsInstance(attempt, int)
        # Constructing a client never invokes Keystore signing or network.
        self.assertEqual(self.calls, [])
        self.assertIsNone(slot.reader)

    def test_rotated_key_blocks_login_client_before_any_auth_request(self):
        later_key = ec.generate_private_key(ec.SECP256R1())
        latest_public = [self.public]
        binding = AndroidKeystoreLoginBinding(
            MASTER, lambda: latest_public[0], self.signer)
        latest_public[0] = later_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        slot = DeviceReaderSlot()
        with patch.object(slot, "_complete_sign_in") as login:
            with self.assertRaises(FeedError) as error:
                slot.sign_in_with_keystore(binding, "https://v2.example.test")
            login.assert_not_called()
        self.assertNotIn("private", str(error.exception))
        self.assertEqual(self.calls, [])
        self.assertIsNone(slot.reader)
        with self.assertRaises(FeedError):
            binding.login_client("https://v2.example.test")

    def test_platform_export_exception_blocks_login_client_without_secret_leak(self):
        exports = [0]
        def export():
            exports[0] += 1
            if exports[0] > 1:
                raise RuntimeError("secret native key alias")
            return self.public
        binding = AndroidKeystoreLoginBinding(MASTER, export, self.signer)
        with self.assertRaises(FeedError) as error:
            binding.login_client("https://v2.example.test")
        self.assertNotIn("secret native key alias", str(error.exception))
        self.assertEqual(self.calls, [])

    def test_invalid_login_input_keeps_last_local_reader_and_does_not_sign(self):
        slot = DeviceReaderSlot()
        current = V2ReadonlyHTTPSReader(
            "https://v2.example.test", "A" * 32, opener=Mock())
        slot._reader = current  # An actual in-memory read-only session.
        binding = self.bind()
        with self.assertRaises(FeedError):
            slot.sign_in_with_keystore(binding, "http://v2.example.test")
        with self.assertRaises(FeedError):
            slot.sign_in_with_keystore(binding, "https://v2.example.test", timeout=0)
        with self.assertRaises(FeedError):
            slot.sign_in_with_keystore(object(), "https://v2.example.test")
        with self.assertRaises(FeedError):
            slot.sign_in_with_keystore(
                binding, "https://v2.example.test", opener=object())
        # An opener property throwing platform-specific secrets must fail closed.
        class BrokenOpener:
            @property
            def open(self):
                raise RuntimeError("sensitive-native-handle")
        with self.assertRaises(FeedError) as error:
            slot.sign_in_with_keystore(
                binding, "https://v2.example.test", opener=BrokenOpener())
        self.assertNotIn("sensitive-native-handle", str(error.exception))
        self.assertIs(slot.reader, current)
        self.assertTrue(current.session_active)
        self.assertIs(slot.active_reader(), current)
        self.assertEqual(self.calls, [])

    def test_settings_clear_always_cancels_pending_login_even_without_reader(self):
        # Flet main isn't started in source-only CI; inspect the actual mounted
        # Settings callback so a future regression cannot gate cancellation
        # on 'reader is not None' before calling the slot's clear().
        tree = ast.parse((SRC / "main.py").read_text(encoding="utf-8"))
        handlers = [node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "clear_local_device_session"]
        self.assertEqual(len(handlers), 1)
        handler = handlers[0]
        unconditional_clear = [
            statement for statement in handler.body
            if isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Attribute)
            and statement.value.func.attr == "clear"
            and isinstance(statement.value.func.value, ast.Name)
            and statement.value.func.value.id == "device_session_slot"]
        self.assertEqual(len(unconditional_clear), 1)
        slot = DeviceReaderSlot()
        generation = slot._generation
        self.assertIsNone(slot.reader)
        slot.clear()  # Explicitly cancels attempts even with no reader.
        self.assertEqual(slot._generation, generation + 1)

    def test_manual_read_status_never_claims_complete_after_session_clear(self):
        source = (SRC / "main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        handlers = [node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "manual_verified_data_refresh"]
        self.assertEqual(len(handlers), 1)
        body = ast.get_source_segment(source, handlers[0])
        equities = body.index('equity_changed = (apply_data_only_quote_snapshot("quotes")')
        gate = body.index("if device_session_slot.reader is not reader or not reader.session_active:")
        completion = body.index("partial = index_changed is None or equity_changed is None")
        self.assertLess(equities, gate)
        self.assertLess(gate, completion)

    def test_failed_keystore_relogin_keeps_previous_verified_reader(self):
        binding = self.bind()
        slot = DeviceReaderSlot()
        previous = V2ReadonlyHTTPSReader(
            "https://v2.example.test", "A" * 32, opener=Mock())
        slot._reader = previous
        with patch.object(V2P256LoginHTTPSClient, "login",
                          side_effect=FeedError("V2 device login unavailable")):
            with self.assertRaises(FeedError):
                slot.sign_in_with_keystore(binding, "https://v2.example.test")
        self.assertIs(slot.reader, previous)
        self.assertTrue(previous.session_active)
        self.assertEqual(self.calls, [])

    def test_successful_keystore_relogin_replaces_and_scrubs_old_reader(self):
        binding = self.bind()
        slot = DeviceReaderSlot()
        previous = V2ReadonlyHTTPSReader(
            "https://v2.example.test", "A" * 32, opener=Mock())
        incoming = V2ReadonlyHTTPSReader(
            "https://v2.example.test", "B" * 32, opener=Mock())
        slot._reader = previous
        with patch.object(V2P256LoginHTTPSClient, "login", return_value=incoming):
            self.assertTrue(slot.sign_in_with_keystore(
                binding, "https://v2.example.test"))
        self.assertIs(slot.reader, incoming)
        self.assertFalse(previous.session_active)
        self.assertTrue(incoming.session_active)

    def test_inactive_new_signed_reader_cannot_replace_previous_session(self):
        binding = self.bind()
        slot = DeviceReaderSlot()
        previous = V2ReadonlyHTTPSReader(
            "https://v2.example.test", "A" * 32, opener=Mock())
        inactive = V2ReadonlyHTTPSReader(
            "https://v2.example.test", "B" * 32, opener=Mock())
        inactive.invalidate()
        slot._reader = previous
        with patch.object(V2P256LoginHTTPSClient, "login", return_value=inactive):
            with self.assertRaises(FeedError):
                slot.sign_in_with_keystore(binding, "https://v2.example.test")
        self.assertIs(slot.reader, previous)
        self.assertTrue(previous.session_active)
        self.assertFalse(inactive.session_active)

    def test_native_key_failure_during_relogin_preserves_prior_reader(self):
        slot = DeviceReaderSlot()
        previous = V2ReadonlyHTTPSReader(
            "https://v2.example.test", "A" * 32, opener=Mock())
        slot._reader = previous
        calls = [0]
        def public_key():
            calls[0] += 1
            if calls[0] > 1:
                raise RuntimeError("secret platform alias")
            return self.public
        binding = AndroidKeystoreLoginBinding(MASTER, public_key, self.signer)
        with self.assertRaises(FeedError) as error:
            slot.sign_in_with_keystore(binding, "https://v2.example.test")
        self.assertNotIn("secret platform alias", str(error.exception))
        self.assertIs(slot.reader, previous)
        self.assertTrue(previous.session_active)
        self.assertEqual(self.calls, [])

    def test_second_keystore_login_wins_over_older_inflight_login(self):
        binding = self.bind()
        slot = DeviceReaderSlot()
        previous = V2ReadonlyHTTPSReader(
            "https://v2.example.test", "A" * 32, opener=Mock())
        first = V2ReadonlyHTTPSReader(
            "https://v2.example.test", "B" * 32, opener=Mock())
        second = V2ReadonlyHTTPSReader(
            "https://v2.example.test", "C" * 32, opener=Mock())
        slot._reader = previous
        first_entered, release_first = Event(), Event()
        outcomes = []
        def login(self_client):
            if not first_entered.is_set():
                first_entered.set()
                if not release_first.wait(3):
                    raise FeedError("Timed-out synthetic first login")
                return first
            return second
        def first_worker():
            try:
                slot.sign_in_with_keystore(binding, "https://v2.example.test")
                outcomes.append("first accepted")
            except FeedError as error:
                outcomes.append(str(error))
        with patch.object(V2P256LoginHTTPSClient, "login", login):
            worker = Thread(target=first_worker, daemon=True)
            worker.start()
            try:
                self.assertTrue(first_entered.wait(3))
                self.assertIs(slot.reader, previous)
                self.assertTrue(slot.sign_in_with_keystore(
                    binding, "https://v2.example.test"))
            finally:
                release_first.set()
                worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(outcomes, ["Device sign-in was cancelled"])
        self.assertIs(slot.reader, second)
        self.assertTrue(second.session_active)
        self.assertFalse(previous.session_active)
        self.assertFalse(first.session_active)

    def test_clear_during_relogin_scrubs_previous_and_rejects_late_reader(self):
        binding = self.bind()
        slot = DeviceReaderSlot()
        previous = V2ReadonlyHTTPSReader(
            "https://v2.example.test", "A" * 32, opener=Mock())
        incoming = V2ReadonlyHTTPSReader(
            "https://v2.example.test", "B" * 32, opener=Mock())
        slot._reader = previous
        entered, release = Event(), Event()
        errors = []
        def delayed_login(self_client):
            entered.set()
            self.assertTrue(release.wait(3))
            return incoming
        def attempt():
            try:
                slot.sign_in_with_keystore(binding, "https://v2.example.test")
            except FeedError as error:
                errors.append(str(error))
        with patch.object(V2P256LoginHTTPSClient, "login", delayed_login):
            worker = Thread(target=attempt, daemon=True)
            worker.start()
            try:
                self.assertTrue(entered.wait(3))
                self.assertIs(slot.reader, previous)
                self.assertTrue(previous.session_active)
                slot.clear()
            finally:
                release.set()
                worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, ["Device sign-in was cancelled"])
        self.assertIsNone(slot.reader)
        self.assertFalse(previous.session_active)
        self.assertFalse(incoming.session_active)

    def test_logout_during_native_preflight_cancels_before_any_auth_io(self):
        entered = Event()
        release = Event()
        callbacks = [0]
        def delayed_public():
            callbacks[0] += 1
            if callbacks[0] > 1:
                entered.set()
                if not release.wait(3):
                    raise RuntimeError("test public export timed out")
            return self.public
        binding = AndroidKeystoreLoginBinding(MASTER, delayed_public, self.signer)
        slot = DeviceReaderSlot()
        errors = []
        def pending_login():
            try:
                slot.sign_in_with_keystore(binding, "https://v2.example.test")
            except FeedError as exc:
                errors.append(str(exc))
        worker = Thread(target=pending_login, daemon=True)
        with patch.object(slot, "_complete_sign_in", wraps=slot._complete_sign_in) as complete:
            worker.start()
            try:
                self.assertTrue(entered.wait(3), "native preflight did not start")
                slot.clear()  # Logout must supersede an in-progress key check.
            finally:
                release.set()
                worker.join(3)
            self.assertFalse(worker.is_alive())
            complete.assert_called_once()
        self.assertEqual(errors, ["Device sign-in was cancelled"])
        self.assertEqual(self.calls, [])
        self.assertIsNone(slot.reader)

    def test_login_client_enforces_approved_https_origin_before_network(self):
        binding = self.bind()
        with self.assertRaises(FeedError):
            binding.login_client("http://v2.example.test")
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
