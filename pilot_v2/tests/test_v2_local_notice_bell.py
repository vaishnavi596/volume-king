"""V2 header bell opens already-existing Settings local notices, no market feed."""
import ast
import sys
import unittest
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from local_notices import LocalNoticeCenter
from v1_visual_style import v1_header

class DummyIcons:
    EMOJI_EVENTS = "trophy"
    NOTIFICATIONS_NONE = "bell"

class FakeFT:
    Icons = DummyIcons
    FontWeight = type("Weight", (), {"BOLD": "bold", "NORMAL": "normal"})
    CrossAxisAlignment = type("Alignment", (), {"CENTER": "center"})
    Colors = type("Colors", (), {})
    padding = type("Padding", (), {"only": staticmethod(lambda **kw: kw)})
    @staticmethod
    def Text(value, **kwargs):
        return ("text", value, kwargs)
    @staticmethod
    def Icon(name, **kwargs):
        return ("icon", name, kwargs)
    @staticmethod
    def IconButton(**kwargs):
        return ("button", kwargs)
    @staticmethod
    def Row(controls, **kwargs):
        return ("row", controls, kwargs)
    @staticmethod
    def Container(**kwargs):
        return ("container", kwargs)

class LocalBellParity(unittest.TestCase):
    def test_v1_header_bell_is_actual_clickable_local_button(self):
        called = []
        header = v1_header(FakeFT, "2", on_notices_click=lambda e: called.append(1))
        row = header[1]["content"]
        bell = row[1][-1]
        self.assertEqual(bell[0], "button")
        self.assertIn("not market alerts", bell[1]["tooltip"])
        bell[1]["on_click"](None)
        self.assertEqual(called, [1])

    def test_real_flet_callback_opens_settings_not_a_network_endpoint(self):
        main = (SRC / "main.py").read_text(encoding="utf-8")
        ast.parse(main)
        self.assertIn("def open_local_notices(e):", main)
        self.assertIn("page.navigation_bar.selected_index = 2", main)
        self.assertIn("on_notices_click=open_local_notices", main)
        self.assertIn("notices.unread", main)
        self.assertIn("Price alerts and push notifications not connected", main)
        self.assertEqual(main.count("ft.NavigationDestination("), 3)
        self.assertNotIn("submit_order(", main)

if __name__ == "__main__":
    unittest.main()
