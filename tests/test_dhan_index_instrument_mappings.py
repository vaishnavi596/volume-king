"""Guard instrument-master-verified Dhan index mappings without broker requests."""
import ast
import unittest
from pathlib import Path


class DhanIndexInstrumentMappings(unittest.TestCase):
    def test_dhan_index_instrument_master_mappings(self):
        source = (Path(__file__).resolve().parents[1] / "backend" / "server.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        assignments = [node for node in tree.body if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == "DHAN_VERIFIED_INSTRUMENTS"
                               for target in node.targets)]
        self.assertEqual(len(assignments), 1)
        mappings = ast.literal_eval(assignments[0].value)
        self.assertEqual(mappings["NIFTY"], ("IDX_I", 13, "INDEX"))
        self.assertEqual(mappings["BANKNIFTY"], ("IDX_I", 25, "INDEX"))
        self.assertEqual(mappings["SENSEX"], ("BSE_I", 51, "INDEX"))
        self.assertEqual(len({(mappings[s][0], mappings[s][1])
                              for s in ("NIFTY", "BANKNIFTY", "SENSEX")}), 3)


if __name__ == "__main__":
    unittest.main()
