"""PCR mapping audit is distinct from verified broker derivatives support."""
import sys
from pathlib import Path
from unittest import TestCase, main

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from option_underlying_status import option_underlying_status, summarize_underlyings


class OptionUnderlyingDiagnosticsTest(TestCase):
    INSTRUMENTS = {
        "NIFTY": ("IDX_I", 13, "INDEX"),
        "BANKNIFTY": ("IDX_I", 25, "INDEX"),
        "SENSEX": ("BSE_I", 51, "INDEX"),
        "RELIANCE": ("NSE_EQ", 2885, "EQUITY"),
        "HDFCBANK": ("NSE_EQ", 1333, "EQUITY"),
        "CASHONLY": ("NSE_EQ", 98765, "EQUITY"),
    }

    def test_cash_mapping_never_claims_pcr_availability(self):
        for sym in self.INSTRUMENTS:
            with self.subTest(sym=sym):
                row = option_underlying_status(sym, self.INSTRUMENTS)
                self.assertTrue(row["mapped"])
                self.assertEqual(row["status"], "mapping_only")
                self.assertFalse(row["expiry_verified"])
                self.assertFalse(row["chain_verified"])
                self.assertFalse(row["pcr_verified"])
                self.assertEqual(row["broker_requests"], 0)

    def test_unmapped_and_invalid_never_fabricated(self):
        self.assertEqual(option_underlying_status("UNMAPPED", self.INSTRUMENTS)["status"], "unmapped")
        for sym in ("", "bad symbol", "../orders", "X" * 40):
            self.assertEqual(option_underlying_status(sym, self.INSTRUMENTS)["status"], "invalid_symbol")
        self.assertFalse(option_underlying_status("X", {"X": ("NSE_EQ", True, "EQUITY")})["mapped"])
        self.assertFalse(option_underlying_status("X", {"X": ("OTHER", 1, "EQUITY")})["mapped"])

    def test_bounded_70_symbol_no_broker_scan(self):
        out = summarize_underlyings(["NIFTY", "RELIANCE", "CASHONLY", "UNMAPPED"],
                                    self.INSTRUMENTS)
        self.assertEqual(out["total"], 4)
        self.assertEqual(out["mapped_cash_or_index"], 3)
        self.assertEqual(out["broker_pcr_verified"], 0)
        self.assertEqual(out["network_requests"], 0)
        with self.assertRaises(ValueError):
            summarize_underlyings(["NIFTY"] * 2, self.INSTRUMENTS)
        with self.assertRaises(ValueError):
            summarize_underlyings([str(i) for i in range(71)], self.INSTRUMENTS)


if __name__ == "__main__":
    main()
