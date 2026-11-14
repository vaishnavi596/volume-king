"""Guard instrument-master-verified Dhan index mappings without broker requests."""
import ast
from pathlib import Path


def test_dhan_index_instrument_master_mappings():
    source = (Path(__file__).resolve().parents[1] / "backend" / "server.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignments = [node for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "DHAN_VERIFIED_INSTRUMENTS"
                           for target in node.targets)]
    assert len(assignments) == 1
    mappings = ast.literal_eval(assignments[0].value)
    assert mappings["NIFTY"] == ("IDX_I", 13, "INDEX")
    assert mappings["BANKNIFTY"] == ("IDX_I", 25, "INDEX")
    assert mappings["SENSEX"] == ("BSE_I", 51, "INDEX")
    assert len({(mappings[s][0], mappings[s][1]) for s in ("NIFTY", "BANKNIFTY", "SENSEX")}) == 3
