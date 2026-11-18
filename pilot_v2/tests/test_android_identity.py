"""Validate V2 app metadata isolation, no APK build."""
import pathlib
import tomllib
import unittest

class PilotIdentityTests(unittest.TestCase):
    def test_independent_root(self):
        root=pathlib.Path(__file__).resolve().parents[2]
        v2=tomllib.loads((root/"pilot_v2/android_app/pyproject.toml").read_text())
        legacy=tomllib.loads((root/"pyproject.toml").read_text())
        self.assertEqual(v2["project"]["version"],"2.0.100")
        self.assertEqual(v2["tool"]["flet"]["product"],"BOT KING V2")
        self.assertNotEqual(v2["project"]["name"],legacy["project"]["name"])
        self.assertTrue((root/"pilot_v2/android_app/src/main.py").exists())

if __name__=="__main__":
    unittest.main()
