"""Clone B3 Scanner-to-Options explicit matching context regression.

No network requests are made by these source checks.
"""
import ast
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")


class ScannerMatchingOptionsTests(unittest.TestCase):
    def test_explicit_only_and_scoped(self):
        tree = ast.parse(SOURCE)
        methods = [node for node in ast.walk(tree)
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        action = next(node for node in methods if node.name == "open_matching_scanner_options")
        body = ast.get_source_segment(SOURCE, action) or ""
        self.assertIn("symbol not in DHAN_VERIFIED_OPTION_SYMBOLS", body)
        self.assertIn("chain_symbol.value=symbol", body)
        self.assertIn('option_expiry_choice.value="Nearest"', body)
        self.assertIn("refresh_option_expiry(", body)
        scanner = next(node for node in methods if node.name == "scanner_option_context")
        view = ast.get_source_segment(SOURCE, scanner) or ""
        self.assertIn("symbol!=chain_symbol.value", view)
        self.assertIn('"Open Options for "+symbol', view)
        self.assertIn("on_click=open_matching_scanner_options", view)

    def test_option_votes_remain_disabled(self):
        scanner = SOURCE.split("    def scanner_option_context():", 1)[1].split(
            "    def scanner():", 1)[0]
        self.assertIn("no OI/PCR/Dhan Max Pain scanner vote or live trade signal", scanner)
        enrichment = SOURCE.split("    def enrich_context_filter_rows(", 1)[1].split(
            "    def shared_filter_report(", 1)[0]
        self.assertIn('row["vote"]=None', enrichment)


if __name__ == "__main__":
    unittest.main()
