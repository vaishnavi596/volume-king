"""Selected symbol/timeframe, filter coverage and confirmation regressions."""
import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import flet as ft
from test_audit import start, event
from analysis_quality import agreement_detail
from scanner_engine import analyze, OPTION_FILTERS

IST=timezone(timedelta(hours=5,minutes=30))

class Clock(datetime):
    offset=0
    @classmethod
    def now(cls,tz=None):
        value=datetime(2026,11,5,10,0,tzinfo=IST)+timedelta(seconds=cls.offset)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)

def text_of(control):
    values=[]
    def walk(c):
        if isinstance(c,ft.Text):values.append(c.value)
        for child in c._get_children():walk(child)
    walk(control)
    return '\n'.join(values)

class SelectedSignalTests(unittest.TestCase):
    def setUp(self):
        Clock.offset=0
        self.page,self.v=start({'scanner_live':False,'scanner_symbol':'TCS','scanner_timeframe':'5m'})
        self.v['selected_analysis_card'].__globals__['datetime']=Clock
        self.now=Clock.now(timezone.utc).timestamp()

    def result(self,bias='BULLISH',stamp=None):
        votes=[dict(name=str(i),vote=1 if i<7 else -1) for i in range(10)]
        return dict(bias=bias,timestamp=self.now-300 if stamp is None else stamp,
                    requested_filters=10,votes=votes,reason='Test analysis')

    def state(self,**changes):
        v=self.v
        v['selected_analysis_state'].update(context=('TCS','5m',v['scan_generation'][0]),
            result=self.result(),source='Angel One',cached=False,**changes)

    def test_primary_card_names_exact_symbol_timeframe_and_separate_counts(self):
        self.state()
        text=text_of(self.v['selected_analysis_card']())
        for expected in ('TCS • 5m • BULLISH','Bullish: 7','Bearish: 3','Neutral: 0','Unavailable: 0','70.0%','Source: Angel One','not success probability'):
            self.assertIn(expected,text)

    def test_selection_change_cannot_relabel_previous_signal(self):
        self.state();self.v['scan_tf'].value='1m';self.v['scan_symbol'].value='NIFTY'
        text=text_of(self.v['selected_analysis_card']())
        self.assertIn('NIFTY • 1m • WAIT',text)
        self.assertNotIn('TCS •',text)
        self.assertNotIn('Bullish: 7',text)

    def test_changing_agreement_threshold_invalidates_previous_selected_signal(self):
        self.state();before=self.v['scan_generation'][0]
        self.v['conf'].value=85;self.v['conf'].on_change(event(self.v['conf']))
        self.assertGreater(self.v['scan_generation'][0],before)
        self.assertFalse(self.v['selected_analysis_state'])
        self.assertIn('TCS • 5m • WAIT',text_of(self.v['selected_analysis_card']()))

    def test_expiry_failure_cache_and_source_change_do_not_keep_current_direction(self):
        for condition in ('expired','failed','cached','provider'):
            with self.subTest(condition=condition):
                self.v['selected_analysis_state'].clear();Clock.offset=0;self.state()
                if condition=='expired':Clock.offset=700
                elif condition=='provider':self.v['scan_generation'][0]+=1
                else:self.v['selected_analysis_state'][condition]=True
                self.assertIn('TCS • 5m • WAIT',text_of(self.v['selected_analysis_card']()))

    def test_higher_timeframe_conflict_is_separate_from_primary_direction(self):
        self.state(higher=dict(result=self.result('BEARISH',self.now-900),source='Angel One',cached=False))
        text=text_of(self.v['selected_analysis_card']())
        self.assertIn('TCS • 5m • BULLISH',text)
        self.assertIn('15m: BEARISH • CONFLICT',text)

    def test_stale_higher_timeframe_does_not_claim_agreement(self):
        self.state(higher=dict(result=self.result('BULLISH',self.now-10000),source='Angel One',cached=False))
        self.assertIn('15m: WAIT • UNCONFIRMED',text_of(self.v['selected_analysis_card']()))

    def test_higher_fetch_uses_next_timeframe_and_rejects_obsolete_response(self):
        self.state()
        async def respond(fn,*args):
            self.assertEqual(args,('TCS','15m','7d'))
            self.v['scan_symbol'].value='NIFTY'
            return {'bars':[],'source':'Angel One'}
        with patch('asyncio.to_thread',side_effect=respond):
            asyncio.run(self.v['fetch_higher_confirmation']('TCS','5m',self.v['scan_generation'][0]))
        self.assertNotIn('higher',self.v['selected_analysis_state'])

    def test_higher_feed_failure_preserves_primary_without_claiming_confirmation(self):
        self.state()
        with patch('asyncio.to_thread',side_effect=TimeoutError()):
            asyncio.run(self.v['fetch_higher_confirmation']('TCS','5m',self.v['scan_generation'][0]))
        text=text_of(self.v['selected_analysis_card']())
        self.assertIn('TCS • 5m • BULLISH',text)
        self.assertIn('UNCONFIRMED',text)

    def test_sparse_available_filters_block_an_inflated_directional_score(self):
        bars=[[self.now-(40-i)*300,100+i,102+i,99+i,101+i,100] for i in range(40)]
        result=analyze(bars,['EMA 9/21','MACD','Supertrend']+OPTION_FILTERS,'5m')
        self.assertEqual(result['bias'],'WAIT')
        self.assertEqual(result['score'],0)
        self.assertFalse(result['coverage_ok'])
        self.assertIn('Insufficient filter coverage',result['reason'])
        self.assertEqual(agreement_detail(result)['unavailable_filters'],4)

    def test_not_enough_candles_marks_requested_filters_unavailable(self):
        detail=agreement_detail(analyze([]))
        self.assertEqual(detail['available_filters'],0)
        self.assertEqual(detail['unavailable_filters'],10)

    def test_daily_confirmation_does_not_invent_a_larger_timeframe(self):
        self.v['scan_tf'].value='1d'
        self.assertIn('not configured for daily',text_of(self.v['selected_analysis_card']()))

    def test_new_caption_does_not_share_controls_or_modify_super_five(self):
        v=self.v;before=list(v['top5_candidates'])
        for language in ('English','हिंदी'):
            v['prefs']['language']=language;v['select'](3);seen=set()
            def walk(c):
                self.assertNotIn(id(c),seen);seen.add(id(c))
                for child in c._get_children():walk(child)
            for control in v['body'].controls:walk(control)
        self.assertEqual(v['top5_candidates'],before)
