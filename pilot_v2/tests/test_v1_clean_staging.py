"""V2-only staged legacy engine integrity and provider quarantine checks."""
import ast
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "v1_clean_staging"
BASE = ROOT.parent / "src"
MODULES = ("analysis_quality", "candle_retention", "chart_indicators",
           "dhan_three_minute", "five_engine", "scanner_engine")
BANNED = {"market_feed", "server_feed", "oracle_226_client", "urllib", "requests",
          "httpx", "socket", "websocket", "secure_credentials"}
class CleanMigrationTest(unittest.TestCase):
    def test_pure_module_blob_parity_and_compile(self):
        for n in MODULES:
            with self.subTest(n=n):
                original = (BASE/(n+".py")).read_bytes()
                staged = (STAGE/(n+".py")).read_bytes()
                self.assertEqual(staged, original)
                compile(staged, str(STAGE/(n+".py")), "exec")
    def test_no_legacy_provider_or_network_import(self):
        for n in MODULES:
            with self.subTest(n=n):
                s=(STAGE/(n+".py")).read_text()
                for word in ("yahoo", "angel one", "angelfeed", "angelbroking"):
                    self.assertNotIn(word, s.lower())
                for item in ast.walk(ast.parse(s)):
                    if isinstance(item, ast.Import):
                        names=[x.name for x in item.names]
                    elif isinstance(item, ast.ImportFrom):
                        names=[item.module or ""]
                    else:
                        continue
                    for module in names:
                        self.assertNotIn(module.split(".")[0], BANNED)
    def test_staging_not_executable_ui_or_provider(self):
        main=(ROOT/"android_app"/"src"/"main.py").read_text()
        self.assertNotIn("v1_clean_staging",main)
        self.assertNotIn("from market_feed import",main)
        self.assertNotIn("from server_feed import",main)
    def test_all_six_real_engine_functions_exist(self):
        funcs=("quality_check","retain_candle_history","chart_indicators",
               "completed_three_minute_bars","combine_evidence","analyze")
        for n,fn in zip(MODULES,funcs):
            with self.subTest(n=n):
                tree=ast.parse((STAGE/(n+".py")).read_text())
                self.assertIn(fn,[node.name for node in tree.body
                                  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))])
if __name__=="__main__": unittest.main()
