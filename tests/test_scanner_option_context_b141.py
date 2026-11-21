"""Source-scope regression: per-underlying cached option context is display-only.

No broker call or fabricated directional filter votes in Scanner.
"""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.py"


class ScannerOptionContextRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        ast.parse(cls.source, filename=str(SOURCE))

    def block(self, left, right):
        return self.source.split(left, 1)[1].split(right, 1)[0]

    def test_cache_is_exact_provider_generation_symbol_and_listed_expiry(self):
        helper = self.block("    def matching_option_context_for_symbol(sym):",
                            "    def enrich_context_filter_rows(sym,rows):")
        for clause in ('gen==generation', 'underlying==sym', 'data.get("symbol")==sym',
                       'data.get("expiry")==listed', 'data.get("source")=="dhan"',
                       'data.get("signal_eligible") is False'):
            self.assertIn(clause, helper)
        self.assertNotIn('option_chain_metrics(', helper)
        self.assertNotIn('asyncio.to_thread(', helper)

    def test_option_filters_remain_informational_and_never_vote(self):
        block = self.block("    def enrich_context_filter_rows(sym,rows):",
                           "    def shared_filter_report(sym,tf,result):")
        self.assertIn("data=matching_option_context_for_symbol(sym)", block)
        self.assertIn('row["vote"]=None', block)
        self.assertIn("if name==\"Max Pain\"", block)
        self.assertIn('row["detail"]="No matching Dhan expiry snapshot for "+sym+" • WAIT"', block)
        self.assertNotIn('row["vote"]=1', block)
        self.assertNotIn('row["vote"]=-1', block)

    def test_scanner_context_does_not_borrow_current_options_symbol(self):
        block = self.block("    def scanner_option_context():", "    def scanner():")
        self.assertIn("data=matching_option_context_for_symbol(symbol)", block)
        self.assertIn('str(data.get("expiry"))', block)
        self.assertNotIn('data.get("expiry")!=expiry.value', block)
        self.assertIn("no OI/PCR/Max Pain scanner vote", block)


if __name__ == "__main__":
    unittest.main()
