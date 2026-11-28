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
        raw=self.source.split('raw_snapshot=(contextual_five_engine.peek(',1)[1].split('sections={',1)[0]
        self.assertIn('symbol=scanner_sym,timeframe=scanner_tf,generation=generation)',raw)
        self.assertIn('if scanner_engine_frame_eligible else None)',raw)
        self.assertNotIn('five_engine_snapshots.get(scanner_sym)',raw)
        self.assertNotIn('scanner_engine_5m_eligible', self.source)

    def test_display_chips_and_summary_read_exact_requested_frame(self):
        chips=self.source.split("    def five_engine_chips(",1)[1].split("    def super_five_card(",1)[0]
        summary=self.source.split("    def five_engine_summary(",1)[1].split("    def ensure_cached_historical_engine_publish(",1)[0]
        self.assertIn('exact_frame=display_timeframe or "5m"',chips)
        self.assertIn('read_five_engine_context(sym,exact_frame)',chips)
        self.assertIn('read_five_engine_context(symbol,exact_frame)',summary)
        self.assertIn('not any(e.eligible and e.source=="Dhan"',summary)
        self.assertNotIn('read_five_engine_context(sym,"5m")',chips)
        self.assertNotIn('read_five_engine_context(symbol,"5m")',summary)
        self.assertIn('five_engine_chips(index_name,display_timeframe="1m")',self.source)
        self.assertIn('five_engine_chips(sym,display_timeframe="1m")',self.source)
        self.assertIn('five_engine_chips(row["symbol"],display_timeframe="1m")',self.source)

    def test_historical_engine_publishers_preserve_exact_timeframe(self):
        self.assertIn('symbol=sym,timeframe=timeframe,generation=provider_generation[0]',
                      self.source)
        self.assertIn('snapshot=scanner_snapshot(historical_only)', self.source)
        self.assertIn('live_verified=False,freshness="historical_unverified"', self.source)


if __name__ == "__main__":
    unittest.main()
