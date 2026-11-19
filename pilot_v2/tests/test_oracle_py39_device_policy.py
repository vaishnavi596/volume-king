"""Regression for Oracle Python 3.9-compatible device policy annotations."""
import ast
from pathlib import Path
import unittest


class OraclePy39PolicyTests(unittest.TestCase):
    def test_policy_postpones_runtime_union_annotation(self):
        path = Path(__file__).resolve().parents[1] / "device_policy.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertTrue(any(
            isinstance(n, ast.ImportFrom)
            and n.module == "__future__"
            and any(a.name == "annotations" for a in n.names)
            for n in tree.body
        ))
        from pilot_v2.device_policy import DeviceRegistry
        self.assertIsNone(DeviceRegistry().master_id)


if __name__ == "__main__":
    unittest.main()
