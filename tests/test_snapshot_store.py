import asyncio
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from test_audit import start
from snapshot_store import SnapshotStore,age_label

class SnapshotTests(unittest.TestCase):
    def market(self,stamp=1700000000):
        return {"price":100,"bars":[[stamp,99,101,98,100,10]],"source":"Yahoo Finance","quote_timestamp":stamp}
    def test_restart_restores_quotes_and_never_secrets(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cache.json';store=SnapshotStore(path)
            data=dict(self.market(),api_key='SECRET',nested={'jwtToken':'SECRET','public':'yes'})
            self.assertTrue(store.put('market',('Auto','NIFTY','5m','7d'),data))
            self.assertNotIn('SECRET',path.read_text())
            restored=SnapshotStore(path)
            self.assertEqual(restored.latest_markets()['NIFTY']['price'],100)
            self.assertTrue(restored.latest_markets()['NIFTY']['cached'])
            self.assertIsNone(restored.get('market','Auto','NIFTY','1m','7d'))
    def test_bad_or_older_data_does_not_replace_good_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            store=SnapshotStore(Path(d)/'cache.json')
            parts=('Auto','NIFTY','5m','7d')
            self.assertTrue(store.put('market',parts,self.market(200)))
            self.assertFalse(store.put('market',parts,self.market(100)))
            self.assertFalse(store.put('market',parts,{'price':None,'bars':[]}))
            self.assertEqual(store.get('market',*parts)['quote_timestamp'],200)
    def test_option_contract_expiry_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            store=SnapshotStore(Path(d)/'cache.json')
            data={'rows':[{'side':'CE','strike':24000,'premium':100,'timestamp':1}],'complete':True}
            self.assertTrue(store.put('options',('NIFTY','2099-01-01'),data))
            self.assertIsNone(store.get('options','BANKNIFTY','2099-01-01'))
            self.assertIsNone(store.get('options','NIFTY','2099-01-02'))
    def test_cache_io_failure_and_corruption_are_nonfatal(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cache.json';path.write_text('{broken')
            store=SnapshotStore(path);self.assertFalse(store.records)
            with patch('os.replace',side_effect=OSError('full')):
                self.assertFalse(store.put('market',('Auto','NIFTY','5m','7d'),self.market()))
            self.assertFalse(store.records)
    def test_age_labels_do_not_become_live_on_load(self):
        self.assertIn('10 days',age_label(1000,now=1000+864000))
        self.assertEqual(age_label(None),'Time unavailable')
        self.assertEqual(age_label(1001,now=1000),'Invalid future time')
    def test_super_five_requires_dhan_connection_before_first_fetch(self):
        _,v=start({'scanner_live':False,'source':'Yahoo Finance'})
        self.assertEqual(v['prefs']['source'],'Dhan')
        card=v['super_five_card']()
        self.assertFalse(v['top5_candidates'])
        import flet as ft
        texts=[]
        def walk(c):
            if isinstance(c,ft.Text):texts.append(str(c.value))
            for child in c._get_children():walk(child)
        walk(card)
        self.assertTrue(any('Dhan disconnected' in text for text in texts))
        self.assertTrue(any('no live signal' in text for text in texts))
    def test_restart_keeps_historical_snapshot_but_broker_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cache.json'
            _,v=start({'scanner_live':False,'source':'Broker API'},cache_path=path)
            historical=dict(self.market(),source='Angel One')
            v['market_store'].put('market',('Broker API','NIFTY','5m','7d'),historical)
            _,restored=start({'scanner_live':False,'source':'Broker API'},cache_path=path)
            self.assertEqual(restored['prefs']['source'],'Dhan')
            # The legacy Angel snapshot stays on disk, but must not leak into
            # the active Dhan-only quote cache or appear as a verified quote.
            self.assertIsNotNone(restored['market_store'].get('market','Broker API','NIFTY','5m','7d'))
            self.assertNotIn('NIFTY',restored['quotes'])
            with patch('urllib.request.urlopen',side_effect=AssertionError('Legacy provider must not run')):
                with self.assertRaisesRegex(Exception,'Dhan disconnected'):
                    restored['get_market_data']('NIFTY','5m','7d')
            self.assertIn('SSK/Oracle not connected',restored['quote_caption']('NIFTY'))

    def test_ranked_directions_survive_restart_as_historical(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cache.json'
            rows=[{'symbol':s,'bias':'BULLISH','timestamp':1000,'score':80,'reason':'old trend','source':'Yahoo Finance'} for s in ['A','B','C','D','E']]
            SnapshotStore(path).put('ranking',('configured50',),{'rows':rows,'checked_at':'old'})
            _,v=start({'scanner_live':False,'source':'Yahoo Finance'},cache_path=path)
            self.assertEqual(v['prefs']['source'],'Dhan')
            self.assertFalse(v['top5_candidates'])
            # Saved Yahoo rankings must not be promoted as Dhan signals.
            self.assertIsNotNone(v['market_store'].get('ranking','configured50'))
    def test_cached_recent_candles_do_not_publish_new_live_signal(self):
        _,v=start({'scanner_live':False,'scanner_timeframe':'5m','scanner_period':'7d'})
        end=int(time.time()//300)*300-300
        bars=[[end-(39-i)*300,100+i,103+i,99+i,102+i,100] for i in range(40)]
        async def respond(fn,*args,**kwargs):
            if fn.__name__=='get_market_data':
                return {'bars':bars,'price':bars[-1][4],'cached':True,'source':'Yahoo Finance'}
            return {'items':[],'status':'Unavailable'}
        with patch('asyncio.to_thread',side_effect=respond):
            asyncio.run(v['scan_market']())
        self.assertEqual(v['scan_shared']['direction'],'WAIT')
        self.assertIsNone(v['market_store'].get('analysis','NIFTY','5m'))

    def test_analysis_and_fusion_cache_exact_symbol_frame_identity(self):
        for incremental in (False,True):
            with self.subTest(incremental=incremental), tempfile.TemporaryDirectory() as d:
                path=Path(d)/"cache.json"
                store=SnapshotStore(path,incremental=incremental)
                analysis={"symbol":"TCS","tf":"3m","direction":"WAIT","basis":"historical"}
                fusion={"symbol":"TCS","timeframe":"3m","candle":{},"options":{},"news":{},
                        "overall":"WAIT","coverage":0,"reason":"historical","headlines":[],
                        "global_headlines":[],"news_status":"Unavailable","global_status":"Unavailable"}
                for kind,payload in (("analysis",analysis),("fusion",fusion)):
                    self.assertTrue(store.put(kind,("TCS","3m"),payload))
                    self.assertFalse(store.put(kind,("INFY","3m"),payload))
                    self.assertFalse(store.put(kind,("TCS","5m"),payload))
                    self.assertFalse(store.put(kind,("TCS",),payload))
                    self.assertIsNone(store.get(kind,"INFY","3m"))
                    self.assertEqual(store.get(kind,"TCS","3m"),payload)
                self.assertEqual(store.diagnostics()["rejected_since_start"],6)
                restored=SnapshotStore(path,incremental=incremental)
                self.assertEqual(restored.get("analysis","TCS","3m"),analysis)
                self.assertEqual(restored.get("fusion","TCS","3m"),fusion)
                self.assertIsNone(restored.get("fusion","TCS","5m"))
