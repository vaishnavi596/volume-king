"""Source-only backend/transport compatibility regression; no Dhan network."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class LiveBatchRouteContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = ast.parse((ROOT / "backend/server.py").read_text(encoding="utf-8"))

    def test_both_required_paired_batch_post_routes_exist(self):
        routes = set()
        for node in ast.walk(self.backend):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if (isinstance(decorator, ast.Call)
                        and isinstance(decorator.func, ast.Attribute)
                        and isinstance(decorator.func.value, ast.Name)
                        and decorator.func.value.id == "app"
                        and decorator.func.attr == "post"
                        and decorator.args
                        and isinstance(decorator.args[0], ast.Constant)):
                    routes.add(decorator.args[0].value)
        self.assertTrue({"/dhan/index-ltp-batch",
                         "/dhan/selected-ltp-batch"}.issubset(routes))

    def test_all_three_index_ids_use_dhan_documented_segment(self):
        mapping = None
        for node in self.backend.body:
            if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "DHAN_VERIFIED_INSTRUMENTS"
                    for t in node.targets):
                mapping = ast.literal_eval(node.value)
        self.assertIsNotNone(mapping)
        self.assertEqual(
            tuple(mapping[s] for s in ("NIFTY", "BANKNIFTY", "SENSEX")),
            (("IDX_I", 13, "INDEX"), ("IDX_I", 25, "INDEX"),
             ("IDX_I", 51, "INDEX")))
        self.assertNotIn("BSE_I", {mapping[s][0] for s in
                                   ("NIFTY", "BANKNIFTY", "SENSEX")})

    def test_v2_oracle_transport_path_matches_backend_route(self):
        src = (ROOT / "pilot_v2/oracle_dhan_read_transport.py").read_text(
            encoding="utf-8")
        mod = ast.parse(src)
        match = next(node for node in mod.body if isinstance(node, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "PATHS"
                             for t in node.targets))
        paths = ast.literal_eval(match.value)
        self.assertEqual(paths, {"indices": "/dhan/index-ltp-batch",
                                 "quotes": "/dhan/selected-ltp-batch"})


if __name__ == "__main__":
    unittest.main()
