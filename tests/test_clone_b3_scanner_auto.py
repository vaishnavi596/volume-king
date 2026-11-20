"""Source-level regression guard for Clone B3 scanner Auto Scan OFF.

This checks the actual Dhan-mode loop predicate without importing Flet or
issuing network requests. It does not replace an Android runtime test.
"""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.py"


class ScannerAutoToggleGuard(unittest.TestCase):
    def test_auto_loop_honors_off_even_with_dhan_selected(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        loops = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "auto_scan_loop"
        ]
        self.assertEqual(len(loops), 1)
        loop = next(node for node in loops[0].body if isinstance(node, ast.While))
        condition = ast.unparse(loop.test)
        self.assertIn("scan_live.value", condition)
        self.assertIn("scan_auto_generation[0]", condition)
        self.assertNotIn("prefs.get('source') == 'Dhan'", condition)
        self.assertNotIn(' or ', condition)

    def test_auto_off_generation_cancels_previous_loop(self):
        text = SOURCE.read_text(encoding="utf-8")
        handler = text.split("    def auto_scan_changed(e):", 1)[1].split(
            "    # Fast local signal pass:", 1
        )[0]
        self.assertIn("scan_auto_generation[0]+=1", handler)
        self.assertIn("if scan_live.value:", handler)
        self.assertIn("page.run_task(auto_scan_loop,scan_auto_generation[0])", handler)


if __name__ == "__main__":
    unittest.main()
