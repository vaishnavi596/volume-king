"""Offline regression checks using real Flet controls; no broker or network access."""
import ast
import asyncio
import copy
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import flet as ft

class Storage:
    def __init__(self,prefs): self.data={'bot_king_preferences':copy.deepcopy(prefs)}
    def get(self,key): return copy.deepcopy(self.data.get(key))
    def set(self,key,value): self.data[key]=copy.deepcopy(value)

class Page:
    def __init__(self,prefs):
        self.client_storage=Storage(prefs);self.controls=[];self.tasks=[];self.platform=ft.PagePlatform.ANDROID
    def add(self,*controls): self.controls.extend(controls)
    def update(self): pass
    def run_task(self,fn,*args): self.tasks.append((fn,args))
    def launch_url(self,url): pass

def start(prefs=None):
    source=(ROOT/'src/main.py').read_text()
    tree=ast.parse(source)
    assert isinstance(tree.body[-1],ast.Expr)
    tree.body.pop()  # Do not start the Flet client during the offline audit.
    env={'__name__':'audit_main','__file__':str(ROOT/'src/main.py')}
    exec(compile(tree,'audit_main.py','exec'),env)
    env['STATE']=ROOT/'tests'/'nonexistent_settings_for_test.json'
    page=Page(prefs or {});local={};previous=sys.getprofile()
    def trace(frame,event,arg):
        if event=='return' and frame.f_code.co_name=='app_main':local.update(frame.f_locals)
    sys.setprofile(trace)
    try:env['app_main'](page)
    finally:sys.setprofile(previous)
    return page,local

def event(control):return type('Event',(),{'control':control})()

class AuditTests(unittest.TestCase):
    def test_all_pages_have_unique_controls_and_restore_page(self):
        page,v=start({'last_page':2,'scanner_live':False})
        self.assertEqual(v['current'],[2])
        for i in range(4):
            v['select'](i);seen=set()
            def walk(c):
                self.assertNotIn(id(c),seen);seen.add(id(c))
                for child in c._get_children():walk(child)
            for c in v['body'].controls:walk(c)
        self.assertEqual(page.client_storage.get('bot_king_preferences')['last_page'],3)

    def test_autosave_is_independent_and_restores_dropdown_types(self):
        page,v=start({'scanner_symbol':'BANKNIFTY','scanner_timeframe':'3m','scanner_budget':'Custom','scanner_min':70,'scanner_max':140,'scanner_live':False,'bot_lots':2,'max_total_lots':4,'option_qty':3})
        self.assertEqual(v['bot_lots'].value,'2')
        self.assertEqual(v['option_qty'].value,'3')
        v['sl'].value='bad';v['sl'].on_change(event(v['sl']));self.assertTrue(v['sl'].error_text)
        v['bot_custom'].value='HDFCBANK';v['bot_custom'].on_change(event(v['bot_custom']))
        v['save_settings'](None)
        self.assertEqual(page.client_storage.get('bot_king_preferences')['bot_custom'],'HDFCBANK')
        v['scan_budget'].value='Any';v['scan_budget'].on_change(event(v['scan_budget']));self.assertFalse(v['scan_min'].visible)
        v['scan_budget'].value='Custom';v['scan_budget'].on_change(event(v['scan_budget']));self.assertTrue(v['scan_min'].visible)
        _,restored=start(page.client_storage.get('bot_king_preferences'))
        self.assertEqual(restored['scan_symbol'].value,'BANKNIFTY')
        self.assertEqual(restored['scan_tf'].value,'3m')
        self.assertFalse(restored['scan_live'].value)

    def test_paper_position_restarts_and_rejects_duplicate_entry(self):
        page,v=start({'bot_expiry_mode':'Manual','bot_expiry':'2026-12-01','bot_lots':2,'bot_lot_size':25,'max_total_lots':4})
        v['bot_paper_action']('BUY');v['bot_paper_action']('SELL')
        self.assertEqual(v['bot_position']['side'],'BUY')
        self.assertEqual(v['bot_position']['quantity'],50)
        _,restored=start(page.client_storage.get('bot_king_preferences'))
        self.assertEqual(restored['bot_position']['side'],'BUY')
        v['bot_paper_action']('EXIT');self.assertIsNone(v['bot_position']['side'])
        v['bot_premium'].value='inf'
        with self.assertRaises(ValueError):v['bot_values']()

    def test_ohlc_aggregation_provider_boundary_and_hours(self):
        _,v=start()
        t=int(datetime(2026,11,3,9,15,tzinfo=timezone(timedelta(hours=5,minutes=30))).timestamp())
        bars=[(t+i*60,100+i,103+i,99+i,102+i,10) for i in range(6)]
        self.assertEqual(v['aggregate_3m'](bars),[[t,100.,105.,99.,104.,30.],[t+180,103.,108.,102.,107.,30.]])
        self.assertFalse(v['regular_hours'](datetime(2026,11,7,10,0)))
        self.assertTrue(v['regular_hours'](datetime(2026,11,3,10,0)))
        v['prefs']['source']='Broker API'
        with self.assertRaises(RuntimeError):v['get_market_data']('NIFTY')
        result=v['analyze_current'](bars*6,None,'1m')
        self.assertEqual(result['bias'],'WAIT')

    def test_superseded_scan_cannot_publish(self):
        page,v=start({'scanner_live':False})
        before=list(v['scan_result'].controls)
        async def run():
            original=asyncio.to_thread
            async def delayed(fn,*args,**kwargs):
                v['scan_generation'][0]+=1
                return {'bars':[(1700000000+i*300,100,101,99,100,100) for i in range(40)]}
            asyncio.to_thread=delayed
            try:await v['scan_market']()
            finally:asyncio.to_thread=original
        asyncio.run(run())
        self.assertEqual(v['scan_result'].controls,before)
        self.assertTrue(any(fn.__name__=='restart_latest_scan' for fn,args in page.tasks))

    def test_derived_expiry_persists_after_mode_change(self):
        page,v=start({'bot_expiry_mode':'Manual','bot_expiry':'2099-12-01'})
        v['bot_expiry_mode'].value='Nearest (preview)'
        v['bot_expiry_mode'].on_change(event(v['bot_expiry_mode']))
        expected=v['bot_expiry'].value
        self.assertNotEqual(expected,'2099-12-01')
        prefs=page.client_storage.get('bot_king_preferences')
        self.assertEqual(prefs['bot_expiry'],expected)
        _,restored=start(prefs)
        self.assertEqual(restored['bot_expiry'].value,expected)
        v['option_expiry_choice'].value='Next'
        v['option_expiry_choice'].on_change(event(v['option_expiry_choice']))
        self.assertEqual(page.client_storage.get('bot_king_preferences')['option_expiry'],v['expiry'].value)

    def test_inflight_dashboard_response_rejected_after_source_change(self):
        page,v=start({'scanner_live':False})
        async def run():
            original_thread=asyncio.to_thread;original_sleep=asyncio.sleep;switched=False
            async def delayed(fn,*args,**kwargs):
                nonlocal switched
                if not switched:
                    switched=True
                    v['source'].value='Broker API';v['source'].on_change(event(v['source']))
                return {'price':100,'change':0,'bars':[]}
            class StopLoop(Exception):pass
            async def stop(*args,**kwargs):raise StopLoop()
            asyncio.to_thread=delayed;asyncio.sleep=stop
            try:
                with self.assertRaises(StopLoop):await v['refresh_market']()
            finally:asyncio.to_thread=original_thread;asyncio.sleep=original_sleep
        asyncio.run(run())
        self.assertEqual(v['prefs']['source'],'Broker API')
        self.assertEqual(v['quotes'],{})
        self.assertEqual(v['top5_candidates'],[])

    def test_daily_entry_limit_persists_and_exit_stays_available(self):
        page,v=start({'bot_expiry_mode':'Manual','bot_expiry':'2099-12-01','max_trades':1})
        v['bot_paper_action']('BUY');v['bot_paper_action']('EXIT');v['bot_paper_action']('SELL')
        self.assertIsNone(v['bot_position']['side'])
        self.assertIn('Daily paper entry limit',v['bot_trade_status'].value)
        _,restored=start(page.client_storage.get('bot_king_preferences'))
        restored['bot_paper_action']('BUY')
        self.assertIsNone(restored['bot_position']['side'])
        self.assertEqual(restored['paper_risk_ledger']()['entries'],1)

    def test_daily_planned_risk_and_concurrent_entries(self):
        page,v=start({'bot_expiry_mode':'Manual','bot_expiry':'2099-12-01','max_trades':10,'bot_premium':100,'bot_lots':2,'bot_lot_size':25,'max_total_lots':4,'max_daily_loss':100})
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(v['bot_paper_action'],['BUY']*8))
        self.assertEqual(v['paper_risk_ledger']()['entries'],1)
        v['bot_paper_action']('EXIT');v['bot_paper_action']('BUY')
        self.assertIsNone(v['bot_position']['side'])
        self.assertIn('planned-risk budget',v['bot_trade_status'].value)
        self.assertEqual(v['paper_risk_ledger']()['planned_risk_used'],100)
        v['max_daily_loss'].value='nan';v['bot_paper_action']('BUY')
        self.assertIsNone(v['bot_position']['side'])

if __name__=='__main__':unittest.main()
