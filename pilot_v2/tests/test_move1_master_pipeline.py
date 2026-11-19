"""Move-1 master pipeline offline contract tests; no Oracle or network activity."""
import importlib.util
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("v2_move1_master", TOOLS / "move1_master_pipeline.py")
master = importlib.util.module_from_spec(spec)
spec.loader.exec_module(master)


class MasterPipelineContractTests(unittest.TestCase):
    def test_five_routes_found_with_exact_methods(self):
        source = '''
def create_app():
    @app.get("/v2-pilot/health")
    def health(): pass
    @app.post("/v2-pilot/auth/challenge")
    def challenge(): pass
    @app.post("/v2-pilot/auth/login")
    def login(): pass
    @app.get("/v2-pilot/indices")
    def indices(): pass
    @app.get("/v2-pilot/quotes")
    def quotes(): pass
'''
        self.assertEqual(master.route_decorators(source), master.REQUIRED_ROUTES)

    def test_wrong_method_does_not_count(self):
        self.assertNotIn(("POST", "/v2-pilot/auth/login"),
                         master.route_decorators(
                             '@app.get("/v2-pilot/auth/login")\ndef login(): pass'))

    def test_no_v1_or_order_route_required(self):
        self.assertFalse(any("/orders" in path or path == "/health"
                             for _, path in master.REQUIRED_ROUTES))

    def test_pinned_commit_mandatory(self):
        with self.assertRaises(ValueError):
            master.validate_commit("main")
        self.assertEqual(master.validate_commit("f" * 40), "f" * 40)


if __name__ == "__main__":
    unittest.main()
