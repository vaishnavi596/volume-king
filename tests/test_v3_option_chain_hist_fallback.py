import re
import unittest
from pathlib import Path

SRC = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")


class OptionChainHistFallbackContract(unittest.TestCase):
    def setUp(self):
        i = SRC.index("def option_chain_preview")
        self.body = SRC[i:i + 6000]

    def test_uses_exact_symbol_expiry_last_good(self):
        self.assertIn('market_store.get("option_context_last_good","Dhan",chain_symbol.value,expiry.value)', self.body)

    def test_hist_label_is_not_live_and_signals_wait(self):
        self.assertIn("HIST • last saved Dhan chain", self.body)
        self.assertIn("NOT LIVE • signals WAIT", self.body)

    def test_saved_chain_must_match_symbol_expiry_and_be_available(self):
        self.assertIn('saved.get("symbol") == chain_symbol.value', self.body)
        self.assertIn('saved.get("expiry") == expiry.value', self.body)
        self.assertIn('saved_context.get("available")', self.body)

    def test_live_path_still_requires_connection(self):
        self.assertIn("dhan_feed.connected", self.body)


if __name__ == "__main__":
    unittest.main()


class ClosedMarketMessageContract(unittest.TestCase):
    def test_closed_market_refresh_message_is_not_a_login_error(self):
        self.assertIn("REFRESH BLOCKED • market closed: HIST cache only", SRC)
        self.assertIn("current Dhan login required.", SRC)  # open-market wording kept

    def test_quote_check_button_is_labelled_test_only(self):
        self.assertIn("Check Clone B3 Dhan Quotes (test only)", SRC)
        self.assertIn("does not switch the app to LIVE", SRC)
