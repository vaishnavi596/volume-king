import unittest
import flet as ft
from test_audit import start
from analysis_quality import quality_check
from help_content import describe

class HelpQualityTests(unittest.TestCase):
    def bars(self):
        return [[100000+i*300,100,102,99,101,10] for i in range(40)]
    def test_completed_candles_only(self):
        bars=self.bars();now=bars[-1][0]+150
        q=quality_check(bars,300,now)
        self.assertTrue(q['usable']);self.assertEqual(q['completed_count'],39)
        self.assertEqual(q['excluded_count'],1)
    def test_invalid_future_stale_and_unordered_block_signal(self):
        bars=self.bars();now=bars[-1][0]+300
        for changed in (bars+[[now+100,100,102,99,101,10]],bars+[bars[-1]],bars+[[now-1,100,90,110,101,10]]):
            self.assertFalse(quality_check(changed,300,now)['usable'])
        self.assertFalse(quality_check(bars,300,now+10000)['usable'])
    def test_help_popup_reports_validation_and_closes(self):
        page,v=start({'scanner_live':False})
        v['sl'].error_text='Enter a positive number'
        dialog=v['show_help']('Stop loss',v['sl'])
        self.assertTrue(dialog.open)
        self.assertIn('validation error',dialog.content.controls[2].value)
        v['close_help'](dialog);self.assertFalse(dialog.open)
    def test_help_does_not_reveal_credentials(self):
        _,v=start({'scanner_live':False,'broker':'Angel One'})
        field=next(iter(v['credential_inputs'].values()));field.value='PRIVATE_SECRET'
        dialog=v['show_help']('API Key',field)
        self.assertNotIn('PRIVATE_SECRET',str([c.value for c in dialog.content.controls]))
    def test_missing_and_stale_options_help_is_dynamic(self):
        _,v=start({'source':'Broker API','scanner_live':False})
        v['angel_feed'].key='test';v['angel_feed'].token='test'
        self.assertIn('उपलब्ध नहीं',v['help_status']('OI Analysis'))
        v['option_feed'].update(symbol=v['chain_symbol'].value,expiry=v['expiry'].value,rows=[{'timestamp':1}])
        self.assertIn('पुराने',v['help_status']('OI Analysis'))
        self.assertIn('9',describe('PCR'))
    def test_wrap_fields_have_bounded_help_wrappers(self):
        _,v=start({'scanner_live':False})
        field=ft.TextField(label='Custom')
        row=v['decorate_help'](ft.Row([field],wrap=True))
        wrapper=row.controls[0]
        self.assertEqual(wrapper.width,300);self.assertFalse(wrapper.expand)
        self.assertIs(wrapper.controls[0].controls[0].content,field)
    def test_ai_quality_is_attached_and_bad_input_blocks(self):
        _,v=start({'scanner_live':False})
        bars=self.bars()+[[1,100,90,110,101,10]]
        result=v['analyze_current'](bars,None,'5m')
        self.assertEqual(result['bias'],'WAIT')
        self.assertFalse(result['quality']['usable'])
        self.assertIn('not a win probability',result['agreement_detail']['limitation'])
