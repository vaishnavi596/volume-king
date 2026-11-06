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
        self.assertEqual(len(v["watch_symbols"]),50)
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
        _,v=start({"scanner_live":False})
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
        _,v=start({"scanner_live":True,"scanner_refresh":"60"})
        v["angel_feed"].key="test";v["angel_feed"].token="test"
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

