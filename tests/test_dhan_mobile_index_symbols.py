"""Read-only mobile gateway must permit three verified indexes without polluting equity snapshot."""
import ast
import unittest
from pathlib import Path


class DhanMobileIndexSymbols(unittest.TestCase):
    def test_chart_uses_independent_ltp_for_all_three_indices(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        start = source.index("    def fetch_market_data_uncached(")
        end = source.index("    def ", start + 10)
        chart = source[start:end]
        self.assertIn('if ticker in ("NIFTY","BANKNIFTY","SENSEX"):', chart)
        self.assertIn("saved_index=quotes.get(ticker)", chart)
        self.assertIn('saved_index.get("source")=="Dhan"', chart)
        self.assertIn('math.isfinite(saved_index["price"]) and saved_index["price"]>0', chart)
        self.assertIn("else:\\n                    with dhan_batch_lock:".replace("\\n", "\n"), chart)
        self.assertNotIn('ticker=="NIFTY"', chart)
        self.assertNotIn('dhan_feed.quote(', chart)

    def test_three_index_symbols_allowed(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "server_feed.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        declarations = {target.id: node.value for node in tree.body if isinstance(node, ast.Assign)
                        for target in node.targets if isinstance(target, ast.Name)}
        symbols = ast.literal_eval(declarations["DHAN_VERIFIED_INDEX_SYMBOLS"].args[0])
        self.assertEqual(set(symbols), {"NIFTY", "BANKNIFTY", "SENSEX"})
        equities = ast.literal_eval(declarations["DHAN_VERIFIED_EQUITY_SYMBOLS"].args[0])
        allowed = set(equities) | set(symbols)
        self.assertIsInstance(declarations["DHAN_VERIFIED_SYMBOLS"], ast.BinOp)
        self.assertIsInstance(declarations["DHAN_VERIFIED_SYMBOLS"].op, ast.BitOr)
        self.assertTrue(set(symbols).issubset(allowed))
        # The equity snapshot parser explicitly rejects NIFTY and index symbols
        # because indexes must come from their separate mapped Dhan LTP path.
        self.assertIn("symbol not in DHAN_VERIFIED_EQUITY_SYMBOLS", source)
        self.assertIn("DHAN_VERIFIED_EQUITY_SYMBOLS", source)


if __name__ == "__main__":
    unittest.main()
