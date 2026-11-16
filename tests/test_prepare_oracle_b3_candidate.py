"""Offline safety checks for the Oracle B3 candidate generator; never deploys."""
import hashlib
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


if __name__ == "__main__":
    unittest.main()
