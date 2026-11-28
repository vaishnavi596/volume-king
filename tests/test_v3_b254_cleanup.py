import unittest

SRC = open("src/main.py", encoding="utf-8").read()


class Cleanup(unittest.TestCase):
    def test_bell_is_a_real_button_with_event_list(self):
        self.assertIn("def show_signal_bell():", SRC)
        self.assertIn('ft.IconButton(icon=ft.Icons.NOTIFICATIONS_NONE', SRC)
        self.assertNotIn("ft.Icon(ft.Icons.NOTIFICATIONS_NONE", SRC)

    def test_dead_indicator_switches_are_not_rendered_and_dummy_sections_gone(self):
        self.assertIn("indicator_rows=[ema,rsi,atr,", SRC)
        self.assertNotIn("indicator_rows=[ema,ema200,sma50", SRC)
        self.assertNotIn("07  ALERTS • NOT CONNECTED", SRC)
        self.assertNotIn("08  BACKTEST • NOT CONNECTED", SRC)
        self.assertNotIn("are in Options → Trading Center", SRC)

    def test_doctor_claims_match_reality_and_report_box_reasons(self):
        self.assertNotIn("STATUS_NOTE_ONLY_NO_OVERLAY", SRC)
        self.assertIn('"Supertrend":"PLOTTED_ON_NATIVE_CHART"', SRC)
        self.assertIn('data["box_coverage"]', SRC)
        self.assertIn("BK-DOC-BOXCOV-001", SRC)

    def test_empty_boxes_keep_wait_prefix_and_say_why(self):
        self.assertIn('label="O WAIT • चेन नहीं मिली (शायद F&O नहीं)"', SRC)
        self.assertIn('label="F WAIT • अभी सिर्फ़ इंडेक्स पर"', SRC)


if __name__ == "__main__":
    unittest.main()
