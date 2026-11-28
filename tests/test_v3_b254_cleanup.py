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


class Updater(unittest.TestCase):
    def test_updater_checks_often_but_applies_only_when_market_closed(self):
        u = open("ops/botking_autoupdate.sh", encoding="utf-8").read()
        self.assertIn('MARKET=1', u); self.assertIn('NEW_CODE_WAITING_FOR_MARKET_CLOSE', u)
        self.assertIn('"$HM" -ge 900', u); self.assertIn('"$HM" -lt 1545', u); self.assertIn('"$DOW" -le 5', u)
        self.assertIn("flock -n 9", u)
        self.assertIn("-mmin +1200", u)                                   # replay not re-run on every 30-min check
        self.assertIn("^LIVE_ORDERS_ENABLED = False", u)                   # guard kept
        self.assertNotIn("outside night window", u)

    def test_installer_moves_timer_to_every_30_minutes(self):
        i = open("ops/install_server_away_20261127.sh", encoding="utf-8").read()
        self.assertIn("OnCalendar=*:0/30", i)
        self.assertIn("systemctl restart botking-autoupdate.timer", i)

    def test_doctor_shows_when_code_was_applied(self):
        self.assertIn('"code_applied_at":_au.get("applied_at")', SRC)


class NewsWithoutLiveFeed(unittest.TestCase):
    def test_news_runs_when_market_closed_and_covers_indices(self):
        a = SRC.index("    async def refresh_superfive_news():")
        b = SRC.index("    async def super_five_minute_refresh():")
        seg = SRC[a:b]
        self.assertIn("reachable=dhan_feed.connected or clone_v2_gateway.connected", seg)
        self.assertIn('candidates=["NIFTY","BANKNIFTY","SENSEX"]', seg)
        self.assertIn("time.monotonic()-news_bootstrap_time[0]<1800", seg)     # repeats every 30 min
        self.assertNotIn("not dhan_feed.connected):\n            return", seg)
        self.assertIn("page.run_task(refresh_superfive_news)   # B254", SRC)
