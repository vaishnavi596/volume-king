"""Mobile screenshot regressions: real controls and offline chart deliveries."""
import asyncio
import unittest
from unittest.mock import patch
import flet as ft
from test_audit import start


def texts(control):
    out=[]
    def walk(node):
        if isinstance(node,ft.Text):out.append(node.value)
        for child in node._get_children():walk(child)
    walk(control)
    return out


class JointLayoutRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page,cls.v=start({'source':'Dhan','scanner_live':False,'last_page':2})

    def test_navigation_labels_do_not_wrap_or_inherit_body_font(self):
        for _,label in self.v['nav_items']:
            self.assertTrue(label._get_attr("noWrap"))  # Flet 0.25 getter reads the wrong attribute.
            self.assertEqual(label.max_lines,1)
            self.assertEqual(label.size,12)

    def test_shared_vote_component_preserves_exact_zero_and_historical_status(self):
        widget=self.v['vote_display']((100,0,8))
        self.assertIn('Bullish 100%',texts(widget))
        self.assertIn('Bearish 0%',texts(widget))
        self.assertTrue(any('HIST • NOT live' in value for value in texts(widget)))
        bar=widget.controls[1]
        self.assertEqual(bar.height,4)
        self.assertEqual(bar.controls[0].expand,100)
        self.assertEqual(bar.controls[1].width,0)
        self.assertIsNone(bar.controls[1].expand)

    def test_three_surfaces_use_identical_vote_layout(self):
        row={'source':'Dhan','historical':True,'timestamp':1,'votes':[{'name':'Supertrend','vote':1},{'name':'MACD','vote':-1}]}
        expected=texts(self.v['vote_display']((50,50,2)))
        self.assertEqual(texts(self.v['strength_widget'](row,'RELIANCE')),expected)
        self.assertIn("1m • WAIT", texts(self.v['compact_watch_signal'](row,True,False))[0])
        row["timeframe"]="1m"
        watch=texts(self.v['compact_watch_signal'](row,True,False))
        self.assertIn("Bullish 50%",watch)
        self.assertIn("Bearish 50%",watch)
        self.assertIn("1m • 2 directional votes • NOT live",watch)
        self.assertEqual(texts(self.v['historical_vote_bar']((50,50,2))),expected)

    def test_watchlist_details_collapsed_and_redundant_caption_removed(self):
        controls=self.v['watchlist']()
        all_text=[value for c in controls for value in texts(c)]
        self.assertFalse(any('are on Dashboard' in value for value in all_text))
        detail=[c for c in controls if isinstance(c,ft.ExpansionTile)]
        self.assertEqual(len(detail),1)
        self.assertFalse(bool(detail[0].initially_expanded))
        self.assertIs(controls[-1],self.v['watch_list'])

    def test_paper_actions_not_exposed_on_chart_or_settings(self):
        for builder in ('charts','settings'):
            if builder not in self.v:continue
            values=[value for c in self.v[builder]() for value in texts(c)]
            self.assertFalse(any('BUY • Paper' in value or 'Paper trading: ENABLED' in value or 'PAPER BOT' in value for value in values))

    def test_ready_visible_chart_receives_corrected_candles_without_http_or_navigation(self):
        v=self.v
        class View:
            page=object()
            def __init__(self):self.sent=[]
            def run_javascript(self,code):self.sent.append(code)
        view=View();sym=v['scan_symbol'].value;tf=v['scan_tf'].value
        context=(sym,tf,v['scan_period'].value,'Dhan','Candlestick',True,v['provider_generation'][0])
        previous=(v['current'][0],v['tv_view'][0],v['tv_context'][0],v['chart_provider'][0])
        key='scanner_chart_'+sym
        saved=v['candles'].get(key)
        try:
            v['current'][0]=3;v['chart_provider'][0]='TradingView Lightweight'
            v['tv_view'][0]=view;v['tv_context'][0]=context;v['tv_booted'][0]=True;v['tv_ready'][0]=True
            v['candles'][key]={'source':'Dhan','_scanner_timeframe':tf,'_scanner_generation':v['scan_generation'][0],
                               'bars':[[1700000000,100,102,99,101,1000],[1700000300,101,103,100,102,1000]]}
            with patch('asyncio.to_thread',side_effect=AssertionError('local delivery must not fetch')):
                asyncio.run(v['sync_visible_chart']())
                asyncio.run(v['sync_visible_chart']())
                self.assertEqual(len(view.sent),1)
                v['candles'][key]['bars'][-1][4]=101.5
                asyncio.run(v['sync_visible_chart']())
                self.assertEqual(len(view.sent),2)
                self.assertIn('101.5',view.sent[-1])
                v['current'][0]=2
                asyncio.run(v['sync_visible_chart']())
                self.assertEqual(len(view.sent),2)
        finally:
            v['current'][0],v['tv_view'][0],v['tv_context'][0],v['chart_provider'][0]=previous
            if saved is None:v['candles'].pop(key,None)
            else:v['candles'][key]=saved

    def test_unmounted_webview_does_not_invoke_native_methods(self):
        v=self.v
        class View:
            page=None
            def invoke_method(self,*a,**k):raise AssertionError('detached view')
        old_view,old_context=v['tv_view'][0],v['tv_context'][0]
        try:
            v['tv_view'][0]=View()
            v['tv_context'][0]=(v['scan_symbol'].value,v['scan_tf'].value,v['scan_period'].value,'Dhan','Candlestick',True,v['provider_generation'][0])
            asyncio.run(v['tv_load_widget']())
        finally:v['tv_view'][0]=old_view;v['tv_context'][0]=old_context

    def test_active_chart_error_is_reported_until_success(self):
        v=self.v
        v['log_error']('chart',AssertionError('never include arbitrary exception contents'))
        try:
            values=texts(v['data_overview']())
            self.assertTrue(any('chart: AssertionError' in value for value in values))
            self.assertFalse(any('never include' in value for value in values))
            self.assertFalse(any(value=='No active errors reported' for value in values))
        finally:v['display_failures'].pop('chart',None)
