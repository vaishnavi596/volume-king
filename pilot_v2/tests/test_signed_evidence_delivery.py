"""Signed evidence client contract: no live source or external HTTPS in tests."""
import ast
import json
import sys
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from app_signed_evidence_delivery import read_signed_evidence_batch
from secure_https_reader import V2ReadonlyHTTPSReader, FeedError
from evidence_inbox import DeviceEvidenceInbox

ORIGIN = "https://approved-v2.example.test"
TOKEN = "synthetic_only_bearer_token_12345678"


class Response:
    status = 200
    def __init__(self, url, body, *, on_read=None, content_type="application/json"):
        self.url = url
        self.body = body
        self.on_read = on_read
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self.headers["Cache-Control"] = "no-store"

    def geturl(self):
        return self.url

    def read(self, maximum):
        if self.on_read:
            self.on_read()
        return self.body[:maximum]

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeOpener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.response


class SignedEvidenceDeliveryTests(unittest.TestCase):
    def reader(self, opener):
        return V2ReadonlyHTTPSReader(ORIGIN, TOKEN, opener=opener)

    def test_authenticated_200_exact_envelope_only_then_atomic_staging(self):
        url = ORIGIN + "/v2-pilot/evidence"
        opener = FakeOpener(Response(
            url, json.dumps({"events": [{"kind": "expiries", "symbol": "NIFTY",
                                         "revision": 1, "available": []}]}).encode()))
        reader = self.reader(opener)
        inbox = DeviceEvidenceInbox()
        with patch("app_signed_evidence_delivery.apply_staged_evidence_batch",
                   return_value={"events": 1, "updated": 1}) as stage:
            self.assertEqual(read_signed_evidence_batch(
                reader, inbox, selected_equities=("TCS",)), {"events": 1, "updated": 1})
            stage.assert_called_once()
            self.assertTrue(stage.call_args.kwargs["trusted_transport"])
        self.assertEqual(len(opener.requests), 1)
        self.assertEqual(opener.requests[0].get_method(), "GET")
        self.assertTrue(opener.requests[0].get_full_url().startswith("https://"))
        self.assertEqual(opener.requests[0].get_header("Authorization"), "Bearer " + TOKEN)

    def test_401_invalidates_and_no_staging(self):
        url = ORIGIN + "/v2-pilot/evidence"
        opener = FakeOpener(error=HTTPError(url, 401, "unauthorized", {}, None))
        reader = self.reader(opener)
        with patch("app_signed_evidence_delivery.apply_staged_evidence_batch") as stage:
            with self.assertRaises(FeedError):
                read_signed_evidence_batch(reader, DeviceEvidenceInbox(),
                                           selected_equities=())
            stage.assert_not_called()
        self.assertFalse(reader.session_active)

    def test_invalid_payload_redirect_and_logout_race_preserve_cache(self):
        url = ORIGIN + "/v2-pilot/evidence"
        inbox = DeviceEvidenceInbox()
        for response in (
                Response(url, b'{"events":[]}'),
                Response(url, b'{"not_events":[]}'),
                Response(url, b'{"events":[{}]}'),
                Response(url + "/redirect", b'{"events":[]}'),
                Response(url, b'{"events":[]}', content_type="text/html")):
            reader = self.reader(FakeOpener(response))
            with self.subTest(body=response.body, url=response.url):
                with self.assertRaises(FeedError):
                    read_signed_evidence_batch(reader, inbox, selected_equities=())
        reader = self.reader(FakeOpener())
        reader._opener.response = Response(
            url, b'{"events":[{}]}', on_read=reader.invalidate)
        with patch("app_signed_evidence_delivery.apply_staged_evidence_batch") as stage:
            with self.assertRaises(FeedError):
                read_signed_evidence_batch(reader, inbox, selected_equities=())
            stage.assert_not_called()

    def test_scanner_ce_pe_strikes_refresh_without_navigation_or_synthesis(self):
        source = (SRC / "main.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("option_strike_hosts = {}", source)
        self.assertIn("tracked_option_strikes(scanner[0].symbol)", source)
        self.assertIn("control.controls = option_strike_rows(symbol)", source)
        self.assertIn('if snapshot["status"] != "HIST":', source)
        self.assertIn("CE/PE strikes WAIT · no trusted selected expiry", source)
        self.assertIn("option_strike_hosts.clear()", source)
        begin = source.index("def manual_verified_evidence_refresh(")
        end = source.index("def clear_local_device_session(", begin)
        self.assertIn("refresh_visible_option_labels(symbol)", source[begin:end])
        self.assertNotIn("render()", source[begin:end])

    def test_scanner_option_and_expiry_controls_refresh_without_page_render(self):
        source = (SRC / "main.py").read_text(encoding="utf-8")
        ast.parse(source)
        # The same verified event batch updates existing mounted UI refs,
        # preserving the user's Scanner selection and scroll position.
        self.assertIn("option_summary_labels = {}", source)
        self.assertIn("expiry_dropdowns = {}", source)
        self.assertIn("tracked_expiry_dropdown(scanner[0].symbol, ft.Dropdown(", source)
        self.assertIn("tracked_option_summary(scanner[0].symbol, option_evidence.summary(", source)
        self.assertIn("refresh_visible_option_labels(symbol)", source)
        start = source.index("def manual_verified_evidence_refresh(")
        end = source.index("def clear_local_device_session(", start)
        callback = source[start:end]
        self.assertIn("refresh_visible_option_labels(symbol)", callback)
        self.assertNotIn("render()", callback)
        self.assertIn("control.options = new_options", source)
        self.assertIn("control.disabled = not bool(available)", source)

    def test_only_real_signed_reader_and_explicit_flet_action(self):
        with self.assertRaises(FeedError):
            read_signed_evidence_batch(object(), DeviceEvidenceInbox(),
                                       selected_equities=())
        with self.assertRaises(FeedError):
            read_signed_evidence_batch(self.reader(FakeOpener()), DeviceEvidenceInbox(),
                                       selected_equities=("NIFTY",))
        source = (SRC / "main.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("on_click=manual_verified_evidence_refresh", source)
        self.assertIn("read_signed_evidence_batch(", source)
        self.assertIn("refresh_visible_filter_labels(symbol, timeframe)", source)
        self.assertNotIn("trusted_transport=True)  # UI", source)


if __name__ == "__main__":
    unittest.main()
