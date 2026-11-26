import pathlib, unittest
SRC = (pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()

class CompactUiContract(unittest.TestCase):
    def test_compact_mode_default_on_and_saved(self):
        self.assertIn('prefs.get("compact_ui",True)', SRC)
        self.assertIn('"bot_position","compact_ui"}', SRC)

    def test_text_has_readable_floor_and_switch_exists(self):
        self.assertIn("max(12,round(size*0.88))", SRC)
        self.assertIn("Compact view (smaller text, tighter spacing)", SRC)
