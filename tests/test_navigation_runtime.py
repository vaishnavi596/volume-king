import asyncio
import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
import flet as ft
from flet.core.client_storage import ClientStorage
from preference_store import PreferenceWriter,load_preferences
from test_audit import start,event

class LoopBridge:
    """Native result callbacks arrive on the same event loop as UI tasks."""
    def __init__(self):self.async_calls=0;self.sync_calls=0
    def _convert_attr_json(self,value):return json.dumps(value)
    def _invoke_method(self,*args,**kwargs):
        self.sync_calls+=1
        received=threading.Event()
        asyncio.get_running_loop().call_later(.005,received.set)
        if not received.wait(.03):raise TimeoutError("UI loop blocked waiting for native callback")
        return "true"
    async def _invoke_method_async(self,*args,**kwargs):
        self.async_calls+=1
        received=asyncio.Event()
        asyncio.get_running_loop().call_later(.005,received.set)
        await asyncio.wait_for(received.wait(),.5)
        return "true"

class NavigationRuntimeTests(unittest.TestCase):
    def test_real_flet_sync_storage_reproduces_loop_starvation(self):
        async def run():
            bridge=LoopBridge();storage=ClientStorage(bridge)
            with self.assertRaises(TimeoutError):storage.set('key',{'value':1})
            self.assertTrue(await storage.set_async('key',{'value':2}))
            self.assertEqual(bridge.sync_calls,1);self.assertEqual(bridge.async_calls,1)
        asyncio.run(run())
    def test_writer_uses_real_flet_async_storage_without_blocking(self):
        async def run(path):
            bridge=LoopBridge()
            class Page:
                client_storage=ClientStorage(bridge)
                def run_task(self,fn,*args):return asyncio.create_task(fn(*args))
            page=Page();writer=PreferenceWriter(page,path)
            self.assertTrue(writer.save({'value':1}))
            await asyncio.sleep(.02)
            self.assertEqual(bridge.sync_calls,0);self.assertEqual(bridge.async_calls,1)
            self.assertEqual(writer.status,'Preferences saved')
        with tempfile.TemporaryDirectory() as d:asyncio.run(run(Path(d)/'prefs.json'))
    def test_coalescing_keeps_newest_preference_snapshot(self):
        async def run(path):
            written=[]
            class Storage:
                async def set_async(self,key,value):
                    await asyncio.sleep(.01);written.append(copy.deepcopy(value));return True
            class Page:
                client_storage=Storage()
                def run_task(self,fn,*args):return asyncio.create_task(fn(*args))
            writer=PreferenceWriter(Page(),path)
            writer.save({'value':1});await asyncio.sleep(0)
            writer.save({'value':2});writer.save({'value':3})
            await asyncio.sleep(.05)
            self.assertEqual([v['value'] for v in written],[1,3])
            self.assertEqual(json.loads(path.read_text())['value'],3)
        with tempfile.TemporaryDirectory() as d:asyncio.run(run(Path(d)/'prefs.json'))
    def test_newer_disk_preferences_survive_native_write_failure(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'prefs.json'
            path.write_text(json.dumps({'value':'new','_prefs_revision':3}))
            class Storage:
                def get(self,key):return {'value':'old','_prefs_revision':2}
            self.assertEqual(load_preferences(path,Storage())['value'],'new')
    def test_navigation_buttons_remain_stable_and_open_each_page(self):
        _,v=start({'scanner_live':False})
        buttons=[c.content for c in v['navbar'].controls]
        expected=['MARKET & DATA STATUS','Options • One scroll page','Settings & Trading Bot','RULE-BASED SCANNER • Chart & Analysis','Watchlist • 5 Lists','Charts • Technical Analysis']
        for i,button in enumerate(buttons):
            button.on_click(event(button))
            self.assertEqual(v['current'][0],i)
            self.assertEqual([id(c.content) for c in v['navbar'].controls],[id(c) for c in buttons])
            texts=[]
            def walk(c):
                if isinstance(c,ft.Text):texts.append(c.value)
                for child in c._get_children():walk(child)
            for root in v['body'].controls:walk(root)
            self.assertIn(expected[i],texts)
    def test_background_render_does_not_save_preferences_or_reset_scroll(self):
        page,v=start({'scanner_live':False})
        before=v['preference_writer'].revision;tasks=len(page.tasks)
        for _ in range(10):v['select'](0)
        self.assertEqual(v['preference_writer'].revision,before)
        self.assertEqual(len(page.tasks),tasks)
    def test_progress_refresh_is_coalesced_and_cannot_reopen_old_page(self):
        page,v=start({'scanner_live':False})
        before=len(page.tasks)
        for _ in range(50):v['request_view_refresh'](0)
        self.assertEqual(len(page.tasks),before+1)
        v['select'](1)
        asyncio.run(v['flush_view_refresh']())
        self.assertEqual(v['current'][0],1)
    def test_page_builder_error_keeps_existing_page_and_navigation(self):
        _,v=start({'scanner_live':False})
        previous=list(v['body'].controls)
        def broken():raise RuntimeError('render failed')
        v['pages'][1]=broken
        v['select'](1)
        self.assertEqual(v['current'][0],0)
        self.assertEqual(v['body'].controls,previous)
        self.assertIn('navigation:',v['diagnostics'][-1])
