"""Offline regression checks using real Flet controls; no broker or network access."""
import ast
import asyncio
import copy
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

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

def start(prefs=None,cache_path=None):
    source=(ROOT/'src/main.py').read_text()
    tree=ast.parse(source)
    assert isinstance(tree.body[-1],ast.Expr)
    tree.body.pop()  # Do not start the Flet client during the offline audit.
    env={'__name__':'audit_main','__file__':str(ROOT/'src/main.py')}
    exec(compile(tree,'audit_main.py','exec'),env)
    # Test preferences use a private file, never another test's persisted state.
    import tempfile
    cache_temp=tempfile.TemporaryDirectory() if cache_path is None else None
    if cache_temp:
        import atexit
        atexit.register(cache_temp.cleanup)
    env['CACHE_FILE']=Path(cache_temp.name)/'cache.json' if cache_temp else Path(cache_path)
    settings_temp=tempfile.TemporaryDirectory()
    import atexit
    atexit.register(settings_temp.cleanup)
    env["STATE"]=Path(settings_temp.name)/"settings.json"
    page=Page(dict({"manual_contract_confirmed":True,"bot_lot_size":1},**(prefs or {})));page.settings_temp=settings_temp;page.cache_temp=cache_temp;local={};previous=sys.getprofile()
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
        page,v=start({'scanner_live':False,'source':'Yahoo Finance'})
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

    def test_added_filters_visible_toggle_restore_and_individual_remove(self):
        page,v=start({'scanner_live':False})
        v['scan_busy'][0]=True
        names=['OI Support','OI Resistance','OI Profile','Max Pain','Volume']
        for name in names:
            v['filter_choice'].value=name;v['filter_edit'](True)
        self.assertEqual(v['added_filters'],names)
        self.assertEqual(len(v['added_filter_list'].controls),5)
        for row in v['added_filter_list'].controls:
            self.assertEqual(row.content.controls[2].text,'Remove ×')
        checkbox=v['added_filter_list'].controls[0].content.controls[0]
        if isinstance(checkbox,ft.Column):checkbox=checkbox.controls[0].controls[0]
        checkbox.value=False;checkbox.on_change(event(checkbox))
        self.assertIn(names[0],v['added_filters']);self.assertNotIn(names[0],v['filter_selected'])
        _,restored=start(page.client_storage.get('bot_king_preferences'))
        self.assertEqual(restored['added_filters'],names)
        self.assertNotIn(names[0],restored['filter_selected'])
        restored['scan_busy'][0]=True
        for name in names:restored['remove_added_filter'](name)
        self.assertEqual(restored['added_filters'],[])
        self.assertFalse(any(n in restored['filter_selected'] for n in names))

    def test_complete_scanner_flow_for_every_timeframe(self):
        import time
        def texts(controls):
            out=[]
            def walk(c):
                if isinstance(c,ft.Text):out.append(str(c.value))
                for child in c._get_children():walk(child)
            for c in controls:walk(c)
            return ' | '.join(out)
        for tf in ['1m','3m','5m','15m','30m','1h','1d']:
            with self.subTest(timeframe=tf):
                page,v=start({'scanner_live':False,'scanner_timeframe':tf,'scanner_budget':'Any'})
                async def run():
                    original=asyncio.to_thread
                    async def history(fn,*args,**kwargs):
                        now=int(time.time());step=v['timeframe_spec'](tf)['seconds']
                        return {'bars':[(now-(99-i)*step,24000+i*5,24006+i*5,23999+i*5,24005+i*5,1000) for i in range(100)]}
                    asyncio.to_thread=history
                    try:await v['scan_market']()
                    finally:asyncio.to_thread=original
                asyncio.run(run())
                self.assertNotIn('Refresh failed',v['scan_status'].value)
                rendered=texts(v['scan_result'].controls)
                self.assertIn('TOP SETUP • SIMULATION ONLY',rendered)
                self.assertIn('Scenario horizon: '+v['timeframe_spec'](tf)['horizon'],rendered)
                self.assertFalse(v['diagnostics'])

    def test_stale_wait_reason_is_not_sideways(self):
        import time
        page,v=start({'scanner_live':False,'scanner_timeframe':'3m','scanner_budget':'Any'})
        async def run():
            original=asyncio.to_thread
            async def history(*args,**kwargs):
                now=int(time.time())-6*3600
                return {'bars':[(now-(99-i)*180,24000+i*5,24006+i*5,23999+i*5,24005+i*5,1000) for i in range(100)]}
            asyncio.to_thread=history
            try:await v['scan_market']()
            finally:asyncio.to_thread=original
        asyncio.run(run())
        values=[]
        def walk(c):
            if isinstance(c,ft.Text):values.append(str(c.value))
            for child in c._get_children():walk(child)
        for c in v['scan_result'].controls:walk(c)
        text=' | '.join(values)
        self.assertIn('Last candle is too old',text)
        self.assertNotIn('Market is sideways',text)

    def test_expiry_preview_uses_same_calendar_and_skips_closed_today(self):
        _,v=start()
        for symbol in ['NIFTY','BANKNIFTY','SENSEX','HDFCBANK']:
            self.assertEqual(v['preview_expiries'](symbol),[d.isoformat() for d in v['option_dates'](symbol)])
        tz=timezone(timedelta(hours=5,minutes=30))
        before=v['option_dates']('NIFTY',datetime(2026,11,3,10,0,tzinfo=tz))
        after=v['option_dates']('NIFTY',datetime(2026,11,3,21,0,tzinfo=tz))
        self.assertEqual(before[0].isoformat(),'2026-11-03')
        self.assertEqual(after[0].isoformat(),'2026-11-10')

    def test_paused_refresh_has_no_countdown_and_scanner_fields_not_in_rows(self):
        _,v=start({'scanner_live':True})
        class ClosedClock(datetime):
            @classmethod
            def now(cls,tz=None):return datetime(2026,11,7,21,0,tzinfo=tz)
        v['refresh_scan_age'].__globals__['datetime']=ClosedClock
        v['scan_last_success'][0]=ClosedClock.now().timestamp()-15
        v['scan_next_refresh'][0]=ClosedClock.now().timestamp()+60
        v['refresh_scan_age']()
        self.assertIsNone(v['scan_next_refresh'][0])
        self.assertIn('PAUSED',v['scan_age_display'].value)
        self.assertIn('15 sec ago',v['scan_age_display'].value)
        top=v['scanner']()[2].content.controls
        self.assertIn(v['scan_tf'],top);self.assertIn(v['scan_period'],top);self.assertIn(v['scan_refresh'],top)
        self.assertFalse(any(isinstance(c,ft.Row) and v['scan_tf'] in c.controls for c in top))

    def test_filter_routing_and_capability_limits(self):
        import time
        _,v=start({'scanner_live':False})
        v['filter_modes']['EMA 9/21']='Chart'
        now=int(time.time());bars=[(now-(39-i)*300,100+i,103+i,99+i,102+i,100) for i in range(40)]
        result=v['analyze_current'](bars,['EMA 9/21'],'5m')
        self.assertFalse(result['votes']);self.assertTrue(v['ema_on_chart']())
        v['filter_modes']['EMA 9/21']='Analysis'
        self.assertFalse(v['ema_on_chart']())
        self.assertEqual(v['analyze_current'](bars,['EMA 9/21'],'5m')['votes'][0]['name'],'EMA 9/21')
        self.assertEqual([x.key for x in v['filter_mode_control']('RSI 14').options],['Analysis'])
        self.assertEqual([x.key for x in v['filter_mode_control']('EMA 9/21').options],['Analysis','Chart','Both'])

    def test_news_rss_freshness_dedup_and_unsafe_xml(self):
        from email.utils import format_datetime
        import time
        _,v=start()
        date=format_datetime(datetime.now(timezone.utc))
        xml=('<rss><channel><item><title>HDFC Bank profit rises</title><link>https://example.com/a</link><pubDate>'+date+'</pubDate><source>Example</source></item>'
             '<item><title>HDFC Bank profit rises</title><link>https://example.com/a</link><pubDate>'+date+'</pubDate></item>'
             '<item><title>Old</title><link>https://example.com/old</link><pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate></item></channel></rss>').encode()
        items=v['parse_news_rss'](xml,'Test source')
        self.assertEqual(len(items),1);self.assertEqual(items[0]['source'],'Example')
        with self.assertRaises(ValueError):v['parse_news_rss'](b'<!DOCTYPE rss><rss/>','Test')
        self.assertEqual(v['headline_signal']([{'title':'HDFC Bank denies fraud rumour'}])['bias'],'UNCLASSIFIED')
        self.assertEqual(v['headline_signal']([{'title':'HDFC Bank profit rises'},{'title':'HDFC Bank raises guidance'}])['bias'],'POSITIVE')

    def test_combined_missing_options_is_not_neutral_or_confirmed(self):
        import time
        _,v=start();now=time.time()
        candle={'bias':'BULLISH','timestamp':now,'reason':'test'}
        items=[{'title':'HDFC Bank profit rises','published':now,'source':'A','url':'https://example.com/a'}, {'title':'HDFC Bank raises guidance','published':now,'source':'B','url':'https://example.com/b'}]
        local={'items':items,'status':'Available'};world={'items':[],'status':'Unavailable'}
        result=v['combine_analysis']('HDFCBANK','5m',candle,local,world)
        self.assertEqual(result['overall'],'WAIT');self.assertEqual(result['coverage'],2)
        self.assertEqual(result['options']['bias'],'UNAVAILABLE')
        self.assertEqual(result['news']['bias'],'POSITIVE')

    def test_options_volume_alone_has_no_direction(self):
        import time
        _,v=start();now=time.time()
        v['option_snapshots']['HDFCBANK']={'symbol':'HDFCBANK','timeframe':'5m','timestamp':now,'verified':True,'call_volume':10000,'put_volume':1,'direction':'BULLISH'}
        self.assertEqual(v['option_component']('HDFCBANK','5m')['bias'],'UNCONFIRMED')
        snap=v['option_snapshots']['HDFCBANK'];snap['direction_basis']='validated_trade_flow'
        self.assertEqual(v['option_component']('HDFCBANK','5m')['bias'],'BULLISH')
        snap['timestamp']=now-86400
        self.assertFalse(v['option_component']('HDFCBANK','5m')['available'])

    def test_combined_agreement_conflict_and_entity_relevance(self):
        import time
        _,v=start();now=time.time()
        candle={'bias':'BULLISH','timestamp':now,'reason':'test'}
        local={'items':[{'title':'HDFC Bank profit rises','published':now},{'title':'HDFC Bank raises guidance','published':now}],'status':'Available'}
        v['option_snapshots']['HDFCBANK']={'symbol':'HDFCBANK','timeframe':'5m','timestamp':now,'verified':True,'direction':'BULLISH','direction_basis':'validated_trade_flow'}
        self.assertEqual(v['combine_analysis']('HDFCBANK','5m',candle,local,{'items':[]})['overall'],'BULLISH')
        v['option_snapshots']['HDFCBANK']['direction']='BEARISH'
        self.assertEqual(v['combine_analysis']('HDFCBANK','5m',candle,local,{'items':[]})['overall'],'WAIT')
        # Another company's headlines cannot supply the news vote for this symbol.
        self.assertEqual(v['combine_analysis']('SBIN','5m',candle,local,{'items':[]})['news']['bias'],'UNCLASSIFIED')

    def test_news_fetch_failure_does_not_invent_headlines(self):
        _,v=start()
        with patch('urllib.request.urlopen',side_effect=OSError('test failure')):
            result=v['fetch_news']('HDFCBANK')
        self.assertEqual(result['items'],[]);self.assertIn('Unavailable',result['status'])

    def test_scroll_layout_page_saves_and_no_tools(self):
        _,v=start({'scanner_live':False})
        def texts(controls):
            out=[]
            def walk(c):
                if isinstance(c,ft.Text):out.append(str(c.value))
                for child in c._get_children():walk(child)
            for c in controls:walk(c)
            return out
        options=' | '.join(texts(v['options']()))
        for name in ['Option Chain','OI Analysis','Put Call Ratio','Premium Money Flow','Strategy Selector']:self.assertIn(name,options)
        home=texts(v['dashboard']());self.assertNotIn('Tools',home)
        self.assertIn("TODAY'S PAPER RISK",home)
        self.assertEqual(v['body'].horizontal_alignment,ft.CrossAxisAlignment.STRETCH)
        v['sl'].value='invalid';v['save_page'](1)
        self.assertEqual(v['page_save_status'][1].value,'Saved on this device')
        v['save_page'](2);self.assertIn('stop_loss',v['page_save_status'][2].value)

    def test_backup_restore_excludes_secrets_and_never_arms_automation(self):
        import json
        page,v=start({'scanner_live':False})
        v['prefs'].update(api_key='SECRET',api_url='https://secret.example/token',access_token='TOKEN',bot_custom='HDFCBANK')
        payload=v['backup_payload']();self.assertNotIn('api_key',payload['data']);self.assertNotIn('api_url',payload['data']);self.assertNotIn('access_token',payload['data'])
        payload['data'].update(protection_enabled=True,scanner_live=True,mode='Auto',bot_custom='SBIN')
        v['backup_text'].value=json.dumps(payload);v['restore_confirm'].value=True;v['import_backup']()
        self.assertEqual(v['bot_custom'].value,'SBIN');self.assertEqual(v['mode'].value,'Paper')
        self.assertFalse(v['scan_live'].value);self.assertFalse(v['protection_enabled'].value)
        self.assertEqual(v['prefs']['api_key'],'SECRET')
        previous=v['bot_custom'].value
        payload['data']['bot_custom']='BAD';payload['data']['paper_journal']=[{'event':'EXIT'}]
        v['backup_text'].value=json.dumps(payload);v['restore_confirm'].value=True;v['import_backup']()
        self.assertEqual(v['bot_custom'].value,previous)
        self.assertIn('blocked',v['backup_status'].value)

    def test_setting_history_undo(self):
        page,v=start({'scanner_live':False})
        old=v['bot_custom'].value
        v['bot_custom'].value='SBIN';v['bot_custom'].on_change(event(v['bot_custom']))
        self.assertEqual(v['prefs']['setting_changes'][-1]['key'],'bot_custom')
        v['undo_setting']();self.assertEqual(v['bot_custom'].value,old)

    def test_paper_protection_manual_assisted_and_auto(self):
        for mode in ['Manual','Assisted','Auto (Paper)']:
            with self.subTest(mode=mode):
                page,v=start({'scanner_live':False,'bot_expiry_mode':'Manual','bot_expiry':'2099-12-01','bot_premium':100,'protection_enabled':True,'protection_profit':10,'protection_mode':mode})
                v['bot_paper_action']('BUY');v['paper_mark'].value='120';v['check_paper_protection']()
                if mode=='Auto (Paper)':
                    self.assertIsNone(v['bot_position']['side']);self.assertEqual(v['prefs']['paper_journal'][-1]['paper_pnl'],20)
                else:self.assertEqual(v['bot_position']['side'],'BUY')
                if mode=='Assisted':self.assertTrue(v['protection_pending']);self.assertFalse(v['protection_no_reply'].value)

    def test_stale_manual_mark_blocks_timeout_exit(self):
        import time
        page,v=start({'scanner_live':False,'bot_expiry_mode':'Manual','bot_expiry':'2099-12-01','bot_premium':100,'protection_enabled':True,'protection_profit':10,'protection_mode':'Assisted','protection_no_reply':True})
        v['bot_paper_action']('BUY');v['paper_mark'].value='120';v['check_paper_protection']()
        v['protection_pending']['deadline']=time.time()-1;v['protection_sample']['time']=time.time()-120
        async def run():
            original=asyncio.sleep;calls=0
            class StopLoop(Exception):pass
            async def tick(*args):
                nonlocal calls
                calls+=1
                if calls>1:raise StopLoop()
            asyncio.sleep=tick
            try:
                with self.assertRaises(StopLoop):await v['protection_clock']()
            finally:asyncio.sleep=original
        asyncio.run(run());self.assertEqual(v['bot_position']['side'],'BUY')
        self.assertIn('stale',v['protection_status'].value)

    def test_android_inactive_does_not_pause_scanner(self):
        page,v=start({'scanner_live':False,'source':'Dhan'})
        active=v['app_active']
        active[0]=True
        before=len(page.tasks)
        event=type('Lifecycle',(),{'state':'inactive'})()
        v['lifecycle_changed'](event)
        self.assertTrue(active[0])
        self.assertEqual(len(page.tasks),before)
        self.assertNotIn('backgrounded',v['runtime_status'].value.lower())

    def test_android_paused_and_resumed_schedule_refresh(self):
        page,v=start({'scanner_live':False,'source':'Dhan'})
        v['app_active'][0]=True
        v['lifecycle_changed'](type('Lifecycle',(),{'state':'paused'})())
        self.assertFalse(v['app_active'][0])
        self.assertIn('backgrounded',v['runtime_status'].value.lower())
        before=len(page.tasks)
        v['lifecycle_changed'](type('Lifecycle',(),{'state':'resumed'})())
        self.assertTrue(v['app_active'][0])
        self.assertGreater(len(page.tasks),before)
        self.assertEqual(page.tasks[-1][0].__name__,'refresh_after_resume')

    def test_closed_session_dhan_retry_has_cooldown_and_generation_guard(self):
        # Inspect the actual coroutine AST without starting network requests.
        source=(ROOT/'src/main.py').read_text()
        tree=ast.parse(source)
        funcs=[node for node in ast.walk(tree)
               if isinstance(node,ast.AsyncFunctionDef) and node.name=='refresh_market']
        self.assertEqual(len(funcs),1)
        body=funcs[0]
        names={node.id for node in ast.walk(body) if isinstance(node,ast.Name)}
        self.assertTrue({'closed_session_retry_generation','last_scanned_generation',
                         'provider_generation','successes'}.issubset(names))
        waits=[node for node in ast.walk(body)
               if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
               and node.func.attr=='sleep' and node.args]
        self.assertTrue(any(isinstance(node.args[0],ast.Constant)
                            and node.args[0].value==5 for node in waits))
        self.assertTrue(any(isinstance(node,ast.Constant) and node.value==180
                            for node in ast.walk(body)))
        retry_conditions=[node for node in ast.walk(body)
                          if isinstance(node,ast.If)
                          and 'closed_session_retry_generation' in ast.unparse(node.test)
                          and 'successes == 0' in ast.unparse(node.test)]
        self.assertEqual(len(retry_conditions),1)
        retry_source=ast.unparse(retry_conditions[0])
        self.assertIn('provider_generation[0] != generation',retry_source)
        self.assertIn('not dhan_feed.connected',retry_source)

    def test_historical_health_records_success_without_claiming_live(self):
        from feed_health import FeedHealth
        health=FeedHealth(clock=lambda:12345)
        request=health.begin('Dhan:HDFCBANK:5m')
        self.assertTrue(health.finish('Dhan:HDFCBANK:5m',request,'HISTORICAL',
                                      source='Dhan',data_time=12000,
                                      error='Market closed; historical only'))
        row=health.get('Dhan:HDFCBANK:5m')
        self.assertEqual(row['state'],'HISTORICAL')
        self.assertEqual(row['last_success'],12345)
        self.assertEqual(row['data_time'],12000)
        self.assertNotEqual(row['state'],'AVAILABLE')

    def test_stale_combined_fusion_card_suppresses_direction(self):
        page,v=start({'scanner_live':False})
        symbol='NIFTY'
        v['fusion_cache'][symbol+':5m']={
            'overall':'BULLISH','coverage':3,'timestamp':1,
            'candle':{'bias':'BULLISH','timestamp':1},
            'options':{'bias':'BULLISH','available':False},
            'news':{'bias':'POSITIVE'},'reason':'Old agreement',
        }
        card=v['fusion_card'](symbol,'5m',compact=True)
        rendered=[]
        def walk(control):
            value=getattr(control,'value',None)
            if isinstance(value,str):rendered.append(value)
            for child in control._get_children():walk(child)
        walk(card)
        self.assertTrue(any('WAIT' in value for value in rendered))
        self.assertTrue(any('HISTORICAL' in value for value in rendered))
        self.assertFalse(any(value.startswith('BULLISH • 3/3') for value in rendered))

    def test_options_underlying_provider_is_dhan_not_yahoo(self):
        _,v=start({'scanner_live':False,'source':'Dhan'})
        values=[]
        def walk(node):
            value=getattr(node,'value',None)
            if isinstance(value,str):values.append(value)
            for child in node._get_children():walk(child)
        walk(v['option_chain_preview']())
        self.assertTrue(any('Underlying provider: Dhan' in x for x in values))
        self.assertTrue(any('CE/PE quotes require' in x for x in values))
        self.assertFalse(any('Underlying quotes may come from Yahoo Finance' in x for x in values))
        self.assertTrue(any('Option chain not connected' in x for x in values))

    def test_dhan_batch_errors_are_specific_and_do_not_echo_secrets(self):
        from feed_health import safe_error
        from market_feed import FeedError
        cases=[
            ("Dhan upstream unavailable or token expired (HTTP 503)",
             "Dhan upstream temporarily unavailable; retry later"),
            ("Dhan HTTPS connection or response failed",
             "Dhan HTTPS connection failed or timed out; retry"),
            ("Invalid Dhan batch response",
             "Dhan batch response missing or invalid"),
            ("Empty Dhan batch response",
             "Dhan batch response missing or invalid"),
            ("Dhan server key rejected (HTTP 403); reconnect",
             "Dhan server access rejected (HTTP 403); reconnect"),
        ]
        for raw,expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(safe_error(FeedError(raw)),expected)
        secret="token=never-display-this"
        self.assertNotIn(secret,safe_error(FeedError("Unknown error "+secret)))

    def test_dhan_adapter_rejects_empty_and_accepts_partial_batch(self):
        from server_feed import ServerDhanReadOnly
        from market_feed import FeedError
        feed=ServerDhanReadOnly()
        with patch.object(feed,'_call',return_value={
                'source':'dhan','quotes':{},'live_orders_enabled':False}):
            with self.assertRaisesRegex(FeedError,'Empty Dhan batch response'):
                feed.batch_quotes()
        with patch.object(feed,'_call',return_value={
                'source':'dhan','quotes':{'RELIANCE':1234.5},
                'live_orders_enabled':False}):
            result=feed.batch_quotes()
        self.assertEqual(list(result),['RELIANCE'])
        self.assertIsNone(result['RELIANCE']['quote_timestamp'])
        self.assertEqual(result['RELIANCE']['freshness'],'unverified')

    def test_empty_dhan_batch_does_not_clear_active_failure(self):
        _,v=start({'scanner_live':False,'source':'Dhan'})
        feed=v['dhan_feed']
        feed._origin='https://example.invalid'
        feed._pairing_key='test-only'
        with patch.object(feed,'batch_quotes',return_value={}):
            asyncio.run(v['refresh_watch_batch']())
        self.assertEqual(v['dhan_batch_issue'][0],
                         'Dhan batch response missing or invalid')
        self.assertIn('batch failed',v['watch_batch_status'][0])
        self.assertNotIn('LTP loaded',v['watch_batch_status'][0])

    def test_successful_dhan_watchlist_retry_clears_settings_error(self):
        _,v=start({'scanner_live':False,'source':'Dhan'})
        feed=v['dhan_feed']
        feed._origin='https://example.invalid'
        feed._pairing_key='test-only'
        v['dhan_batch_issue'][0]='Data request failed (FeedError)'
        v['connection_status'].value='Dhan connected; watchlist batch failed'
        complete={symbol:{'source':'Dhan','price':1234.5,'symbol':symbol}
                  for symbol in v['all_watch_symbols']()}
        with patch.object(feed,'batch_quotes',return_value=complete):
            asyncio.run(v['refresh_watch_batch']())
        self.assertEqual(len(complete),51)
        self.assertIsNone(v['dhan_batch_issue'][0])
        self.assertIn('Dhan connected • 51/51',v['connection_status'].value)
        self.assertIn('equity LTP quotes returned',v['connection_status'].value)
        self.assertNotIn('batch failed',v['connection_status'].value)

    def test_partial_dhan_batch_is_not_reported_as_complete(self):
        _,v=start({'scanner_live':False,'source':'Dhan'})
        feed=v['dhan_feed']
        feed._origin='https://example.invalid'
        feed._pairing_key='test-only'
        with patch.object(feed,'batch_quotes',return_value={
                'RELIANCE':{'source':'Dhan','price':1234.5,'symbol':'RELIANCE'}}):
            asyncio.run(v['refresh_watch_batch']())
        self.assertIn('Partial Dhan batch: 1/',v['dhan_batch_issue'][0])
        self.assertIn('Dhan LTP partial: 1/',v['watch_batch_status'][0])
        self.assertNotIn('LTP loaded:',v['watch_batch_status'][0])

    def test_nifty_retry_failure_surfaces_despite_complete_equity_scan(self):
        _,v=start({'scanner_live':False,'source':'Dhan'})
        v['dhan_feed']._origin='https://example.invalid'
        v['dhan_feed']._pairing_key='test-only'
        v['scan_progress'].update(total=51,valid=51,checked=51,failed=0,state='Complete')
        v['failed_symbols']['NIFTY']='Dhan upstream temporarily unavailable; retry later'
        def text_values(control):
            values=[]
            def walk(node):
                value=getattr(node,'value',None)
                if isinstance(value,str):values.append(value)
                for child in node._get_children():walk(child)
            walk(control)
            return values
        shown=text_values(v['data_overview']())
        self.assertTrue(any('Market data NIFTY:' in x for x in shown))
        self.assertFalse(any('No active errors reported' in x for x in shown))
        v['failed_symbols'].pop('NIFTY')
        recovered=text_values(v['data_overview']())
        self.assertFalse(any('Market data NIFTY:' in x for x in recovered))

    def test_dhan_batch_failure_stays_visible_until_recovery(self):
        _,v=start({'scanner_live':False,'source':'Dhan'})
        def texts(control):
            found=[]
            def walk(node):
                value=getattr(node,'value',None)
                if isinstance(value,str):found.append(value)
                for child in node._get_children():walk(child)
            walk(control)
            return found
        v['dhan_batch_issue'][0]='Data request failed (FeedError)'
        shown=texts(v['data_overview']())
        self.assertTrue(any('Dhan watchlist batch:' in value and 'FeedError' in value
                            for value in shown))
        self.assertFalse(any('No active errors reported' in value for value in shown))
        v['dhan_batch_issue'][0]=None
        recovered=texts(v['data_overview']())
        self.assertFalse(any('Dhan watchlist batch:' in value for value in recovered))

    def test_historical_strength_widget_mutes_bars_and_labels(self):
        _,v=start({'scanner_live':False,'source':'Yahoo Finance'})
        row={'source':'Yahoo Finance','timestamp':1,'historical':True,
             'votes':[{'vote':1},{'vote':-1}]}
        widget=v['strength_widget'](row,'NIFTY')
        values=[]
        colors=[]
        def walk(control):
            value=getattr(control,'value',None)
            if isinstance(value,str):values.append(value)
            color=getattr(control,'bgcolor',None)
            if color is not None:colors.append(color)
            for child in control._get_children():walk(child)
        walk(widget)
        self.assertTrue(any('Historical votes' in value for value in values))
        palette=v['strength_widget'].__globals__
        self.assertIn(palette['MUTED'],colors)
        self.assertIn(palette['BORDER'],colors)
        self.assertNotIn(palette['GREEN'],colors)
        self.assertNotIn(palette['RED'],colors)

    def test_palette_contrast(self):
        _,v=start()
        colors=v['txt'].__globals__
        def lum(h):
            values=[int(h[i:i+2],16)/255 for i in (1,3,5)]
            values=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in values]
            return sum(x*y for x,y in zip(values,[.2126,.7152,.0722]))
        def ratio(a,b):
            lo,hi=sorted((lum(a),lum(b)));return (hi+.05)/(lo+.05)
        for fg,bg in [('WHITE','PANEL'),('MUTED','PANEL2'),('RED','PANEL2'),('BG','RED'),('BG','GREEN'),('BG','GOLD')]:self.assertGreaterEqual(ratio(colors[fg],colors[bg]),4.5)
        self.assertGreaterEqual(ratio(colors['BORDER'],colors['PANEL2']),3)

if __name__=='__main__':unittest.main()



