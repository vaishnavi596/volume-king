"""Offline safety checks for the Oracle B3 candidate generator; never deploys."""
import hashlib
import concurrent.futures
import hmac
import threading
import time
from typing import Optional
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "prepare_oracle_b3_candidate", ROOT / "scripts" / "prepare_oracle_b3_candidate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SOURCE = b'''import threading
from typing import Optional
def create_app():
    pairing_key = "test"
    # Historical candles are cached only after provider validation succeeds.
    candle_cache = {}
    @app.post("/dhan/intraday")
    def dhan_intraday(body: DhanIntradayRequest, x_botking_key: Optional[str] = Header(default=None)):
        if not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403)
        with candle_lock:
            cached = candle_cache.get((body.symbol, str(body.interval)))
        if body.interval in (3, 30):
            return dhan_intraday(body, x_botking_key=x_botking_key)
        return DhanFeed().intraday({})
'''


class OracleB3CandidateTests(unittest.TestCase):
    def test_reject_wrong_production_hash(self):
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            module.prepare(SOURCE)

    def test_inserts_only_lock_block_and_decorator(self):
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(SOURCE).hexdigest()):
            output = module.prepare(SOURCE).decode()
        self.assertIn("tuple(threading.RLock() for _ in range(32))", output)
        self.assertIn('@app.post("/dhan/intraday")\n    @history_singleflight', output)
        self.assertIn("return dhan_intraday(body, x_botking_key=x_botking_key)", output)
        self.assertIn("return DhanFeed().intraday({})", output)
        self.assertEqual(output.count("def history_singleflight("), 1)

    def test_refuses_existing_singleflight(self):
        source = SOURCE.replace(b"candle_cache = {}", b"history_singleflight = None\n    candle_cache = {}")
        with patch.object(module, "EXPECTED_SHA", hashlib.sha256(source).hexdigest()):
            with self.assertRaisesRegex(ValueError, "already present"):
                module.prepare(source)


    def test_exact_oracle_lock_block_cold_miss_one_mock_provider_call(self):
        """Execute the exact inserted lock wrapper with mocked cache/provider."""
        class Header:
            def __init__(self, default=None):
                self.default = default

        class HTTPException(Exception):
            def __init__(self, status, detail):
                self.status_code = status

        class DhanIntradayRequest:
            symbol = "RELIANCE"
            interval = 5

        namespace = {"threading": threading, "hmac": hmac, "Optional": Optional,
                     "Header": Header, "HTTPException": HTTPException,
                     "DhanIntradayRequest": DhanIntradayRequest}
        code = ('def build_guard(handler):\n'
                '    pairing_key = "K" * 40\n'
                + module.LOCK_BLOCK
                + '    return history_singleflight(handler)\n')
        exec(compile(code, "<oracle-b3-lock-runtime>", "exec"), namespace)
        cache = {}
        calls = []
        entered = threading.Event()
        release = threading.Event()

        def mock_handler(body, x_botking_key=None):
            if (body.symbol, body.interval) in cache:
                return cache[(body.symbol, body.interval)]
            calls.append(1)
            entered.set()
            if not release.wait(timeout=3):
                raise AssertionError("mock provider timed out")
            cache[(body.symbol, body.interval)] = [71]
            return [71]

        guarded = namespace["build_guard"](mock_handler)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(guarded, DhanIntradayRequest(),
                                x_botking_key="K" * 40)
            self.assertTrue(entered.wait(timeout=2))
            second = pool.submit(guarded, DhanIntradayRequest(),
                                 x_botking_key="K" * 40)
            time.sleep(0.05)
            try:
                self.assertEqual(len(calls), 1)
            finally:
                release.set()
            self.assertEqual(first.result(timeout=3), [71])
            self.assertEqual(second.result(timeout=3), [71])
        self.assertEqual(len(calls), 1)

        with self.assertRaises(HTTPException) as error:
            guarded(DhanIntradayRequest(), x_botking_key="wrong")
        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(len(calls), 1)

if __name__ == "__main__":
    unittest.main()
