"""FT2 exact-timeframe Doctor source contract regression.

The 5m ranking snapshot must never be treated as independent 1m/3m
LIVE engine evidence. This tests current source wiring without Dhan I/O.
"""
from pathlib import Path
import unittest


class FiveEngineDoctorFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).resolve().parents[1] /
                      "src" / "main.py").read_text(encoding="utf-8")

    def test_selected_filter_doctor_reads_exact_frame(self):
        self.assertIn('snap=(read_five_engine_context(symbol,tf)', self.source)
        self.assertNotIn('snap=(read_five_engine_context(symbol,"5m")\n'
                         '                      if tf=="5m"', self.source)

    def test_master_doctor_never_calls_5m_for_other_frame(self):
        self.assertIn('snap=(read_five_engine_context(scanner_sym,scanner_tf)',
                      self.source)
        self.assertIn('if scanner_tf=="5m" and scanner_engine_frame_eligible else None)',
                      self.source)
        self.assertNotIn('scanner_engine_5m_eligible', self.source)

    def test_historical_engine_publishers_preserve_exact_timeframe(self):
        self.assertIn('symbol=sym,timeframe=timeframe,generation=provider_generation[0]',
                      self.source)
        self.assertIn('snapshot=scanner_snapshot(historical_only)', self.source)
        self.assertIn('live_verified=False,freshness="historical_unverified"', self.source)


if __name__ == "__main__":
    unittest.main()
