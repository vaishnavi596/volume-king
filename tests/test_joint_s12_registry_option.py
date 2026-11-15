"""Joint S12 staged registry and equity option gateway guards."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.dhan_registry import load_dynamic_instruments
from backend.server import create_app, DHAN_VERIFIED_INSTRUMENTS


class DynamicRegistryTests(unittest.TestCase):
    def fixture(self):
        data = {"schema_version": 1, "source": "dhan_instrument_master",
                "mode": "staging_only", "equity_count": 300,
                "equities": {f"TEST{i}": {"segment": "NSE_EQ",
                             "security_id": 200000+i, "instrument": "EQUITY"}
                             for i in range(300)}}
        # Keep the verified RELIANCE mapping consistent.
        data["equities"]["RELIANCE"] = data["equities"].pop("TEST0")
        data["equities"]["RELIANCE"]["security_id"] = 2885
        return data

    def test_valid_staged_registry_extends_lookup_without_orders(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"equities.json"
            p.write_text(json.dumps(self.fixture()))
            mapping = load_dynamic_instruments(DHAN_VERIFIED_INSTRUMENTS, p)
        self.assertEqual(mapping["TEST1"], ("NSE_EQ", 200001, "EQUITY"))
        self.assertEqual(mapping["RELIANCE"], DHAN_VERIFIED_INSTRUMENTS["RELIANCE"])
        self.assertEqual(mapping["NIFTY"], DHAN_VERIFIED_INSTRUMENTS["NIFTY"])

    def test_bad_registry_fails_closed_without_partial_additions(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"equities.json"
            for mutation in ("count", "collision", "id", "json"):
                data=self.fixture()
                if mutation=="count": data["equity_count"] = 299
                if mutation=="collision": data["equities"]["RELIANCE"]["security_id"] = 99
                if mutation=="id": data["equities"]["TEST1"]["security_id"] = -1
                p.write_text("{" if mutation=="json" else json.dumps(data))
                with self.subTest(mutation=mutation):
                    self.assertEqual(load_dynamic_instruments(DHAN_VERIFIED_INSTRUMENTS,p),
                                     DHAN_VERIFIED_INSTRUMENTS)

    def test_search_is_authenticated_and_does_not_fetch_dhan_data(self):
        client = TestClient(create_app(pairing_key="k"*40))
        self.assertEqual(client.get("/v2/instruments/search").status_code,403)
        with patch("backend.server.DhanFeed._post",side_effect=AssertionError("broker called")):
            response=client.get("/v2/instruments/search?q=RELIANCE",
                        headers={"X-BotKing-Key": "k"*40})
        self.assertEqual(response.status_code,200)
        self.assertIn("RELIANCE",response.json()["symbols"])
        self.assertFalse(response.json()["live_orders_enabled"])

    def test_equity_option_expiry_preserves_broker_mapping_and_safety(self):
        client=TestClient(create_app(pairing_key="k"*40))
        with patch.dict("os.environ", {"DHAN_CLIENT_ID": "test-client"}):
            with patch("pathlib.Path.read_text",return_value="test-token"):
                with patch("backend.server.DhanFeed.option_expiries",
                           return_value=["2099-12-31"]) as feed:
                    response=client.post("/dhan/option-expiries",
                         json={"symbol": "RELIANCE"},
                         headers={"X-BotKing-Key":"k"*40})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()["expiries"],["2099-12-31"])
        self.assertFalse(response.json()["live_orders_enabled"])
        feed.assert_called_once_with("NSE_EQ",2885)


if __name__=="__main__":
    unittest.main()
