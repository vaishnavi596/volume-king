"""Offline PCR index/equity contract audit; never hits Oracle or Dhan."""
import sys
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
from server_feed import ServerDhanReadOnly

EXPIRY = "2026-11-26"


class DhanEquityPcrContractAudit(TestCase):
    def setUp(self):
        self.feed = ServerDhanReadOnly()
        self.feed._origin = "https://example.org"
        self.feed._pairing_key = "test-only-not-secret"

    def test_expiry_request_does_not_restrict_equities_to_indexes(self):
        for symbol in ("NIFTY", "BANKNIFTY", "SENSEX", "RELIANCE", "HDFCBANK"):
            with self.subTest(symbol=symbol):
                with patch.object(self.feed, "_call", return_value={
                    "source": "dhan", "symbol": symbol,
                    "expiries": [EXPIRY], "live_orders_enabled": False,
                }) as call:
                    self.assertEqual(self.feed.option_expiries(symbol), [EXPIRY])
                    call.assert_called_once_with("/dhan/option-expiries", {"symbol": symbol})

    def test_equity_pcr_is_unverified_information_not_live_signal(self):
        for symbol in ("RELIANCE", "HDFCBANK"):
            with self.subTest(symbol=symbol):
                data = {
                    "source": "dhan", "symbol": symbol, "expiry": EXPIRY,
                    "pcr": 0.8, "max_pain": 1500,
                    "freshness": "unverified", "signal_eligible": False,
                    "live_orders_enabled": False,
                }
                with patch.object(self.feed, "_call", return_value=data) as call:
                    result = self.feed.option_chain_metrics(symbol, EXPIRY)
                    self.assertEqual(result["pcr"], 0.8)
                    self.assertIs(result["signal_eligible"], False)
                    call.assert_called_once_with("/dhan/option-chain", {
                        "symbol": symbol, "expiry": EXPIRY})

    def test_option_ui_requests_only_selected_underlying_not_all_51(self):
        app = (SRC / "main.py").read_text(encoding="utf-8")
        block = app[app.index("    async def refresh_selected_options():"):
                    app.index("    def option_metrics(kind):")]
        self.assertIn("sym=chain_symbol.value", block)
        self.assertIn("dhan_feed.option_expiries,sym", block)
        self.assertIn("dhan_feed.option_chain_metrics,sym,chosen", block)
        self.assertIn("dhan_option_context_cache[(generation,sym,chosen)]", block)
        self.assertIn("if sym not in DHAN_VERIFIED_SYMBOLS:", block)
        self.assertIn("option_retry_until", block)

    def test_backend_requires_mapped_equity_and_listed_expiry(self):
        server = (SRC.parent / "backend" / "server.py").read_text(encoding="utf-8")
        self.assertIn('DYNAMIC_INSTRUMENTS.get(body.symbol)', server)
        self.assertIn('instrument[0] not in ("IDX_I", "BSE_I", "NSE_EQ")', server)
        self.assertIn("No Dhan listed option expiries for this underlying", server)
        self.assertIn("Dhan option chain incomplete or unverified", server)
        self.assertIn("Dhan option chain rate limited; retry later", server)


if __name__ == "__main__":
    main()
