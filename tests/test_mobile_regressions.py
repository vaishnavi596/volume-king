"""Phone failures reproduced from the November 4 audit; no real orders/network."""
import asyncio
import json
import os
from pathlib import Path
import tempfile
import time
from datetime import datetime, timezone
import unittest
from unittest.mock import patch
import flet as ft
from test_audit import start, event, Page
from storage_paths import storage_paths
from preference_store import PreferenceWriter, load_preferences
from snapshot_store import SnapshotStore


def walk(control):
    yield control
    for child in control._get_children():
        yield from walk(child)


class MobileRegressionTests(unittest.TestCase):
    def test_historical_candle_time_is_visible_without_spoofing_quote_freshness(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn('historical_time=float(result["bars"][-1][0])', source)
        self.assertIn('data_time=quote_time if isinstance(quote_time,(int,float)) else historical_time', source)
        self.assertIn('"quote_timestamp":None', source)
        self.assertIn('state="HISTORICAL"', source)
        self.assertNotIn('quote_timestamp=historical_time', source)


    def test_background_dhan_history_requests_are_bounded_and_progress_visible(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn('asyncio.wait_for(asyncio.to_thread(get_market_data,sym,"5m","5d"),timeout=25)', source)
        self.assertIn('scan_progress["state"]="Loading histories: "', source)
        self.assertIn('market_completed[0]+=1', source)
        self.assertIn('history_failed=[0]', source)
        self.assertIn('history_failed[0]+=1', source)
        self.assertIn('Ranking completed candles: 0 / ', source)
        self.assertIn('Loading candle histories: 0 / ', source)

    def test_android_enum_lifecycle_resumed_does_not_pause_scanner(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn('state.endswith(".resumed")', source)
        self.assertIn('app_active[0]=True', source)
        self.assertIn('if raw is None:raw=getattr(e,"data",None)', source)
        self.assertNotIn('log_error("lifecycle_unknown"', source)

    def test_disconnected_dhan_hides_saved_quote_prices(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn('def dhan_offline():', source)
        self.assertIn('q=None if dhan_offline() else quotes.get(sym)', source)
        self.assertIn('CONNECT DHAN', source)
        self.assertIn('Dhan disconnected • saved prices hidden', source)

    def test_first_dhan_scan_not_blocked_by_stale_lifecycle(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn('pending_dhan_scan=(prefs.get("source")=="Dhan" and dhan_feed.connected', source)
        self.assertIn('if not app_active[0] and not pending_dhan_scan:', source)

    def test_dhan_scanner_requires_connection_and_defaults_to_30_seconds(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn('value=str(prefs.get("scanner_refresh","30"))', source)
        self.assertIn('if prefs.get("source")=="Dhan" and not dhan_feed.connected:', source)
        self.assertIn('scan_status.value="Dhan login required • automatic scan paused"', source)
        self.assertIn('scan_status.value="Dhan login required • scan paused"', source)
        self.assertIn('scan_busy[0]=False\n            return', source)

    def test_chart_compare_renders_both_provider_trends(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn("tiny_chart(symbol.value)", source)
        self.assertIn("tiny_chart(peer)", source)
        self.assertIn("Separate price trends", source)
        self.assertIn("Comparison unavailable • both symbols require verified provider candle history", source)
        self.assertIn("log_error(\"chart_comparison\",exc)", source)

    def test_chart_auto_loads_on_open_and_selection_change(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn("def chart_selection_changed(e):", source)
        self.assertIn("symbol.on_change=chart_selection_changed", source)
        self.assertIn("timeframe.on_change=chart_selection_changed", source)
        self.assertIn("if changed and i==5 and not chart_load_busy[0]:", source)
        self.assertIn("page.run_task(load_chart)", source)
        self.assertIn("log_error(\"load_chart\",exc)", source)
        self.assertIn("chart_load_pending=[False]", source)
        self.assertIn("chart_load_pending[0]=True", source)
        self.assertIn("if chart_load_pending[0]:", source)

    def test_dashboard_has_three_independent_index_analysis_panels(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn("def dashboard_index_analysis():", source)
        self.assertIn("dashboard_index_analysis(),", source)
        self.assertIn('("NIFTY","BANKNIFTY","SENSEX")', source)
        self.assertIn("Previous candle direction is not a current signal", source)
        self.assertIn("no verified 5m candle series", source)

    def test_dashboard_indexes_auto_fetch_with_bounded_retry(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn("async def dashboard_index_quote_poll():", source)
        self.assertIn("page.run_task(dashboard_index_quote_poll)", source)
        self.assertIn('("NIFTY","BANKNIFTY","SENSEX")', source)
        self.assertIn("delay=min(60,15*2**min(failures[sym]-1,2))", source)
        self.assertIn("exchange timestamp unverified", source)
        self.assertIn("if sym not in DHAN_VERIFIED_SYMBOLS:", source)
        self.assertIn("Dhan instrument mapping not verified", source)

    def test_super_five_uses_independent_minute_cached_refresh(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn("async def super_five_minute_refresh():", source)
        self.assertIn("page.run_task(super_five_minute_refresh)", source)
        self.assertIn("await asyncio.sleep(60)", source)
        self.assertIn("snapshot.get(\"bars\")", source)
        self.assertIn("API STATUS & ERROR MONITOR", source)

    def test_closed_market_dhan_retry_uses_three_minute_cooldown(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn('one automatic retry in 3 minutes', source)
        self.assertIn('for _ in range(36):', source)
        self.assertIn('await asyncio.sleep(5)', source)
        self.assertNotIn('one automatic retry in 15 minutes', source)

    def test_fresh_install_defaults_to_dhan(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn('"confidence":75,"source":"Dhan","api_url"', source)
        self.assertIn('prefs["source"]="Dhan"', source)

    def test_dhan_history_startup_has_bounded_batch_wait(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn('Checking Dhan batch before historical scan', source)
        self.assertIn('asyncio.wait_for(asyncio.to_thread(dhan_feed.batch_quotes),timeout=20)', source)

    def test_dhan_connect_queues_new_history_generation(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn('state="Dhan historical scan queued; LTP independently checked"', source)
        self.assertIn('provider_generation[0]+=1', source)

    def test_background_market_task_recovers_from_unhandled_errors(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn('async def supervised_market_refresh():', source)
        self.assertIn('log_error("market_loop_crash",exc)', source)
        self.assertIn('page.run_task(supervised_market_refresh)', source)
        self.assertNotIn('page.run_task(refresh_market)', source)


    def test_android_app_private_storage_survives_restart_with_native_bridge_down(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"FLET_APP_STORAGE_DATA": directory}), patch("pathlib.Path.home", side_effect=PermissionError()):
                settings, cache = storage_paths()
            class UnavailableStorage:
                def set(self, *args):raise OSError("native bridge unavailable")
                def get(self, *args):raise OSError("native bridge unavailable")
            page=Page({});page.client_storage=UnavailableStorage()
            writer=PreferenceWriter(page,settings)
            self.assertTrue(writer.save({"language":"हिंदी","scanner_symbol":"TCS"}))
            self.assertEqual(load_preferences(settings,page.client_storage)["scanner_symbol"],"TCS")
            data={"price":100,"bars":[[100,99,101,98,100,10]],"source":"Yahoo Finance","quote_timestamp":100}
            self.assertTrue(SnapshotStore(cache).put("market",("Auto","TCS","5m","7d"),data))
            self.assertEqual(SnapshotStore(cache).latest_markets()["TCS"]["price"],100)

    def test_full_company_list_available_in_every_picker_and_searchable(self):
        _,v=start({"scanner_live":False})
        self.assertEqual(len(v["watch_symbols"]),51)
        for key in ("chain_symbol","scan_symbol","bot_symbol"):
            picker=v[key]
            self.assertTrue(set(v["watch_symbols"]).issubset({o.key for o in picker.options}))
            search=v["symbol_search"](picker);search.value="TCS";search.on_change(event(search))
            self.assertIn("TCS",{o.key for o in picker.options})
            search.value="";search.on_change(event(search))
            self.assertTrue(set(v["watch_symbols"]).issubset({o.key for o in picker.options}))

    def test_custom_symbol_restarts_in_all_selectors(self):
        page,v=start({"scanner_live":False})
        v["option_add_symbol"].value="TESTCO";v["add_option_symbol"](None)
        _,restored=start(page.client_storage.get("bot_king_preferences"))
        for key in ("chain_symbol","scan_symbol","bot_symbol"):
            self.assertIn("TESTCO",{o.key for o in restored[key].options})

    def test_changing_instrument_cannot_keep_previous_option_contract(self):
        _,v=start({"scanner_live":False,"bot_symbol":"NIFTY","bot_strike":23400,"bot_premium":80,"bot_lot_size":25})
        v["bot_symbol"].value="TCS";v["bot_symbol"].on_change(event(v["bot_symbol"]))
        for key in ("bot_strike","bot_premium","bot_lot_size"):
            self.assertEqual(v[key].value,"")
        self.assertFalse(v["manual_contract_confirmed"].value)
        with self.assertRaises(ValueError):v["bot_values"]()

    def test_calculator_marks_unverified_contract_and_quantity_explicitly(self):
        _,v=start({"scanner_live":False,"bot_lots":2,"bot_lot_size":25,"max_total_lots":4})
        v["calculate_bot"]()
        self.assertIn("MANUAL EXAMPLE",v["bot_preview"].value)
        self.assertIn("2 lots × 25 units = 50",v["bot_preview"].value)

    def test_long_switch_label_wraps_once_in_both_languages(self):
        _,v=start({"scanner_live":False})
        control=ft.Switch(label="Enable paper protection demonstration")
        wrapper=v["decorate_help"](control)
        for language in ("English","हिंदी","English"):
            from i18n import localize_tree
            localize_tree(wrapper,language)
            self.assertEqual(control.label,"")
            texts=[c for c in walk(wrapper) if isinstance(c,ft.Text)]
            self.assertEqual(len(texts),1)
            self.assertTrue(wrapper.controls[0].controls[1].expand)

    def test_slider_displays_actual_percentage_and_scroll_does_not_write_disk(self):
        page,v=start({"scanner_live":False})
        v["select"](2)
        texts=[c.value for root in v["body"].controls for c in walk(root) if isinstance(c,ft.Text)]
        self.assertFalse(any("{value}" in text for text in texts))
        v["conf"].value=80;v["conf"].on_change(event(v["conf"]))
        self.assertIn("80%",v["conf"]._bk_help_label.value)
        before=v["preference_writer"].revision
        for i in range(20):v["remember_scroll"](type("Scroll",(),{"pixels":i*10})())
        self.assertEqual(v["preference_writer"].revision,before)

    def test_candle_analysis_survives_news_failure(self):
        _,v=start({"scanner_live":False,"source":"Yahoo Finance"})
        end=int(time.time()//300)*300-300
        bars=[[end-(39-i)*300,100+i,103+i,99+i,102+i,100] for i in range(40)]
        async def respond(fn,*args,**kwargs):
            if fn.__name__=="get_market_data":return {"bars":bars,"price":bars[-1][4],"cached":False,"source":"Yahoo Finance","quote_timestamp":end}
            raise TimeoutError()
        with patch("asyncio.to_thread",side_effect=respond):asyncio.run(v["scan_market"]())
        self.assertEqual(v["scan_shared"]["timestamp"],end)
        self.assertEqual(v["quotes"]["NIFTY"]["price"],bars[-1][4])
        card=v["fusion_card"]("NIFTY","5m")
        text=" ".join(c.value for c in walk(card) if isinstance(c,ft.Text))
        self.assertIn("Candles:",text)
        self.assertNotIn("Waiting for candles",text)
        self.assertFalse(v["scan_busy"][0])

    def test_setting_time_is_converted_to_ist(self):
        _,v=start({"scanner_live":False})
        self.assertIn("13:05:40 IST",v["display_setting_time"]("2026-11-04T07:35:40+00:00"))

    def test_auto_scan_schedules_short_ticks_and_sets_next_due_time(self):
        _,v=start({"scanner_live":True,"scanner_refresh":"60","source":"Yahoo Finance"})
        class Clock(datetime):
            @classmethod
            def now(cls,tz=None):
                base=datetime(2026,11,4,7,30,tzinfo=timezone.utc)
                return base.astimezone(tz) if tz else base.replace(tzinfo=None)
        v["auto_scan_loop"].__globals__["datetime"]=Clock
        end=int(Clock.now(timezone.utc).timestamp())-300
        bars=[[end-(39-i)*300,100+i,103+i,99+i,102+i,100] for i in range(40)]
        async def respond(fn,*args,**kwargs):
            if fn.__name__=="get_market_data":return {"bars":bars,"price":bars[-1][4],"source":"Yahoo Finance","quote_timestamp":end}
            return {"items":[],"status":"No headlines"}
        ticks=[]
        async def tick(delay):
            ticks.append(delay);v["scan_live"].value=False
        with patch("asyncio.to_thread",side_effect=respond),patch("asyncio.sleep",side_effect=tick):
            asyncio.run(v["auto_scan_loop"](v["scan_auto_generation"][0]))
        self.assertEqual(ticks,[1])
        self.assertIsNotNone(v["scan_last_success"][0])
        self.assertGreater(v["scan_next_refresh"][0],Clock.now().timestamp())

