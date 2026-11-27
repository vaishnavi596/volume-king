import contextlib
import io
import json
import os
import re
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "ops" / "botking-clone-web-renew.py"
IST = timezone(timedelta(hours=5, minutes=30))
OLD = "o" * 20 + "." + "l" * 10 + "." + "d" * 10
NEW = "n" * 20 + "." + "e" * 10 + "." + "w" * 10


class FakeResponse:
    status = 200

    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, n=-1):
        return self.body[:n] if n and n > 0 else self.body


class FakeOpener:
    def __init__(self, renew_body, validity):
        self.renew_body = renew_body
        self.validity = validity
        self.calls = []

    def open(self, req, timeout=20):
        path = req.full_url.split("/v2", 1)[1]
        token = req.get_header("Access-token")
        self.calls.append((path, token))
        if path == "/RenewToken":
            return FakeResponse(self.renew_body)
        body = {"dhanClientId": "1001", "dataPlan": "Active",
                "tokenValidity": self.validity.get(token, "01/01/2000 00:00")}
        return FakeResponse(json.dumps(body).encode())


def fmt(dt):
    return dt.strftime("%d/%m/%Y %H:%M")


def run_engine(root, fake, mode="--tick"):
    src = SRC.read_text()
    src = src.replace('Path("/home/opc/botking-clone-v2-private")', 'Path(' + repr(str(root)) + ')')
    src = re.sub(r"opener = urllib\.request\.build_opener\(.*?\n\)\n", "opener = FAKE\n", src, flags=re.S)
    os.environ["DHAN_CLIENT_ID"] = "1001"
    ns = {"FAKE": fake, "__name__": "engine"}
    import sys
    argv = sys.argv
    sys.argv = ["engine", mode]
    out = io.StringIO()
    code = None
    try:
        with contextlib.redirect_stdout(out):
            exec(compile(src, "engine", "exec"), ns)
    except SystemExit as e:
        code = e.code
    finally:
        sys.argv = argv
    lines = [json.loads(x) for x in out.getvalue().splitlines() if x.strip()]
    return code, lines


def setup(root, remaining_min=60):
    root = Path(root)
    os.chmod(root, 0o700)
    expiry = (datetime.now(IST) + timedelta(minutes=remaining_min)).replace(second=0, microsecond=0)
    (root / "dhan-token").write_text(OLD + "\n")
    os.chmod(root / "dhan-token", 0o600)
    import hashlib
    (root / "dhan-web-renewal-state.json").write_text(json.dumps({
        "source": "dhan_web", "fingerprint": hashlib.sha256(OLD.encode()).hexdigest(),
        "expires_at": expiry.isoformat()}) + "\n")
    os.chmod(root / "dhan-web-renewal-state.json", 0o600)
    return expiry


class RenewEngine(unittest.TestCase):
    def test_documented_response_renews(self):
        with tempfile.TemporaryDirectory() as d:
            exp = setup(d)
            new_exp = exp + timedelta(hours=24)
            fake = FakeOpener(json.dumps({"accessToken": NEW}).encode(),
                              {OLD: fmt(exp), NEW: fmt(new_exp)})
            code, lines = run_engine(d, fake)
            self.assertEqual(code, 0)
            self.assertEqual(lines[-1]["state"], "RENEWED")
            self.assertEqual((Path(d) / "dhan-token").read_text().strip(), NEW)
            self.assertFalse((Path(d) / "dhan-web-renewal-recovery").exists())
            self.assertFalse((Path(d) / "dhan-web-renewal-pending.json").exists())

    def test_unusual_key_still_renews(self):
        with tempfile.TemporaryDirectory() as d:
            exp = setup(d)
            new_exp = exp + timedelta(hours=24)
            fake = FakeOpener(json.dumps({"data": {"jwt": NEW}, "status": "ok"}).encode(),
                              {OLD: fmt(exp), NEW: fmt(new_exp)})
            code, lines = run_engine(d, fake)
            self.assertEqual(lines[-1]["state"], "RENEWED")
            self.assertEqual((Path(d) / "dhan-token").read_text().strip(), NEW)

    def test_unparseable_response_keeps_raw_and_reports_only_key_names(self):
        with tempfile.TemporaryDirectory() as d:
            exp = setup(d)
            body = json.dumps({"weird": NEW + "x y", "other": 1}).encode()
            fake = FakeOpener(body, {OLD: fmt(exp)})
            code, lines = run_engine(d, fake)
            self.assertEqual(code, 1)
            last = lines[-1]
            self.assertEqual(last["state"], "RENEWAL_BLOCKED_OR_FAILED")
            self.assertTrue(last["recovery_required"])
            self.assertEqual(last["response_keys"], ["other", "weird"])
            self.assertNotIn(NEW, json.dumps(last))
            raw = (Path(d) / "dhan-web-renewal-recovery").read_text()
            self.assertIn("weird", raw)
            self.assertEqual((Path(d) / "dhan-token").read_text().strip(), OLD)
            code2, lines2 = run_engine(d, fake)
            self.assertEqual(lines2[-1]["state"], "RECOVERY_REQUIRED")

    def test_not_due_never_calls_renew(self):
        with tempfile.TemporaryDirectory() as d:
            setup(d, remaining_min=300)
            fake = FakeOpener(b"{}", {})
            code, lines = run_engine(d, fake)
            self.assertEqual(lines[-1]["state"], "NOT_DUE")
            self.assertEqual(fake.calls, [])


if __name__ == "__main__":
    unittest.main()
