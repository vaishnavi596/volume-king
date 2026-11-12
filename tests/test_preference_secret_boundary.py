"""Regression: centralized secrets must not be persisted in Flet preferences."""
import unittest
from unittest.mock import patch
from src.preference_store import public_preferences, load_preferences, PreferenceWriter


class FakeStorage:
    def __init__(self, value):
        self.value=value
        self.written=None

    def get(self, key):
        return self.value

    def set(self, key, value):
        self.written=value
        return True


class FakePage:
    def __init__(self, storage):
        self.client_storage=storage


class PreferenceSecretBoundaryTests(unittest.TestCase):
    def test_sensitive_fields_removed_case_insensitively(self):
        values={"source":"Dhan","watchlist_1":["RELIANCE"],"api_key":"legacy",
                "PIN":"123456","pairing_key":"secret","dhan_token":"secret"}
        self.assertEqual(public_preferences(values),
                         {"source":"Dhan","watchlist_1":["RELIANCE"]})

    def test_nested_legacy_credentials_are_scrubbed(self):
        values={"source":"Dhan","providers":[{"name":"Dhan","access_token":"secret"}],
                "settings":{"PIN":"123456","watchlist":["NIFTY"]}}
        cleaned=public_preferences(values)
        self.assertEqual(cleaned["providers"],[{"name":"Dhan"}])
        self.assertEqual(cleaned["settings"],{"watchlist":["NIFTY"]})

    def test_legacy_native_secrets_removed_on_load(self):
        storage=FakeStorage({"_prefs_revision":2,"source":"Dhan","mpin":"secret"})
        with patch("src.preference_store.Path.read_text",return_value='{}'):
            loaded=load_preferences("/nonexistent",storage)
        self.assertEqual(loaded["source"],"Dhan")
        self.assertNotIn("mpin",loaded)

    def test_save_never_writes_secrets_to_disk_or_native(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as folder:
            storage=FakeStorage({})
            writer=PreferenceWriter(FakePage(storage),Path(folder)/"prefs.json")
            writer.save({"source":"Dhan","api_key":"secret","pin":"123456"})
            data=(Path(folder)/"prefs.json").read_text()
            self.assertNotIn("secret",data)
            self.assertNotIn("123456",data)
            self.assertEqual(storage.written["source"],"Dhan")
            self.assertNotIn("api_key",storage.written)
            self.assertNotIn("pin",storage.written)
