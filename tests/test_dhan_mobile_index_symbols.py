"""Read-only mobile gateway must permit three verified indexes without polluting equity snapshot."""
import ast
import unittest
from pathlib import Path


class DhanMobileIndexSymbols(unittest.TestCase):
    def test_three_index_symbols_allowed(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "server_feed.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        declarations = {target.id: node.value for node in tree.body if isinstance(node, ast.Assign)
                        for target in node.targets if isinstance(target, ast.Name)}
        symbols = ast.literal_eval(declarations["DHAN_VERIFIED_INDEX_SYMBOLS"].args[0])
        self.assertEqual(set(symbols), {"NIFTY", "BANKNIFTY", "SENSEX"})
        allowed = ast.literal_eval(declarations["DHAN_VERIFIED_SYMBOLS"].args[0])
        self.assertTrue(set(symbols).issubset(allowed))
        # The equity snapshot parser explicitly rejects NIFTY and index symbols
        # because indexes must come from their separate mapped Dhan LTP path.
        self.assertIn('or symbol == "NIFTY" for symbol in unavailable', source)
        self.assertIn('or symbol == "NIFTY"', source)


if __name__ == "__main__":
    unittest.main()
