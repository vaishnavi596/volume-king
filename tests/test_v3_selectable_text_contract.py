import re
import unittest
from pathlib import Path


class SelectableTextContract(unittest.TestCase):
    def test_app_shell_is_wrapped_in_selection_area(self):
        source = Path(__file__).resolve().parents[1].joinpath("src", "main.py").read_text(encoding="utf-8")
        self.assertRegex(source, re.escape(
            "page.add(ft.SafeArea(content=ft.SelectionArea(content=app_shell),expand=True))"))


if __name__ == "__main__":
    unittest.main()
