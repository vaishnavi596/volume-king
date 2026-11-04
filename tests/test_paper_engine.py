"""Price/quantity risk and manual paper execution regression tests."""
import unittest
from datetime import date
from paper_engine import levels,pnl,risk_check,validate_expiry,evaluate_mark
from test_audit import start,event

class EngineTests(unittest.TestCase):
    def position(self,side='BUY',quantity=4):
        stop,target=levels(side,100,10,20)
        return dict(side=side,entry=100,quantity=quantity,unit_size=1,stop_loss_pct=10,target_pct=20,stop_price=stop,target_price=target)
    def test_side_levels_and_net_pnl(self):
        self.assertEqual(levels('BUY',100,2,4),(98,104))
        self.assertEqual(levels('SELL',100,2,4),(102,96))
        self.assertEqual(pnl('SELL',100,90,10,5),(100,95))
        self.assertEqual(pnl('BUY',100,90,10,5),(-100,-105))
        with self.assertRaises(ValueError):levels('SELL',100,2,100)
    def test_validation_and_caps(self):
        with self.assertRaises(ValueError):validate_expiry('2020-01-01',date(2026,11,4))
        self.assertEqual(risk_check(100,10,98,10000,2000,100,1),20)
        for args in [(100,10,98,10000,500,100,1),(100,10,98,10000,2000,10,1),(float('nan'),1,98,1000,1000,100,1)]:
            with self.assertRaises(ValueError):risk_check(*args)
    def test_stop_has_priority_over_averaging(self):
        self.assertEqual(evaluate_mark(self.position(),89,dict(average=True,dip_pct=5))['action'],'EXIT')
    def test_average_bounded_and_stop_never_widens(self):
        p=self.position();d=evaluate_mark(p,95,dict(average=True,dip_pct=5,max_additions=1,add_units=1,max_units=5))
        self.assertEqual(d['action'],'ADD');self.assertEqual(d['position']['quantity'],5)
        self.assertEqual(d['position']['entry'],99);self.assertGreaterEqual(d['position']['stop_price'],p['stop_price'])
        self.assertEqual(evaluate_mark(d['position'],94,dict(average=True,dip_pct=1,max_additions=1))['action'],'HOLD')
        with self.assertRaises(ValueError):evaluate_mark(p,95,dict(average=True,dip_pct=5,max_units=4))
    def test_partial_rounds_to_whole_lots_and_only_once(self):
        p=self.position(quantity=12);p['unit_size']=3
        d=evaluate_mark(p,103,dict(partial=True,partial_trigger=2,partial_pct=50))
        self.assertEqual(d['action'],'PARTIAL');self.assertEqual(d['quantity'],6)
        p['partial_done']=True
        self.assertEqual(evaluate_mark(p,103,dict(partial=True))['action'],'HOLD')
    def test_trailing_stop_only_tightens_both_sides(self):
        for side,first,second in [('BUY',108,107),('SELL',92,93)]:
            p=evaluate_mark(self.position(side),first,dict(trailing=True,trail_pct=2))['position']
            q=evaluate_mark(p,second,dict(trailing=True,trail_pct=2))['position']
            self.assertEqual(p['stop_price'],q['stop_price'])

class UiPaperTests(unittest.TestCase):
    def test_cash_quantity_and_side_exit_charges(self):
        _,v=start(dict(bot_segment='Cash',bot_symbol='SBIN',cash_quantity=10,bot_premium=100,scanner_live=False))
        self.assertEqual(v['bot_values']()[3:],(10,'SBIN CASH'))
        v['bot_paper_action']('SELL');self.assertEqual(v['bot_position']['stop_price'],102)
        v['paper_exit_price'].value='90';v['paper_exit_fees'].value='5';v['bot_paper_action']('EXIT')
        self.assertEqual(v['prefs']['paper_journal'][-1]['paper_pnl'],95)
    def test_index_cash_and_unconfirmed_entry_block(self):
        _,v=start(dict(bot_segment='Cash',bot_symbol='NIFTY',scanner_live=False))
        with self.assertRaises(ValueError):v['bot_values']()
        _,v=start(dict(manual_contract_confirmed=False,scanner_live=False))
        v['bot_paper_action']('BUY');self.assertIsNone(v['bot_position']['side'])
    def test_invalid_exit_does_not_clear_position_and_unknown_has_no_price(self):
        _,v=start(dict(scanner_live=False));v['bot_paper_action']('BUY')
        v['paper_exit_price'].value='nan';v['bot_paper_action']('EXIT');self.assertEqual(v['bot_position']['side'],'BUY')
        v['paper_exit_price'].value='';v['protection_sample'].update(mark=123,time=0,position_id='old')
        v['bot_paper_action']('EXIT');row=v['prefs']['paper_journal'][-1]
        self.assertIsNone(row['paper_pnl']);self.assertIsNone(row['exit_price'])
        self.assertEqual(v['paper_risk_ledger']()['unknown_exits'],1)
    def test_start_pause_stop_and_restore_stopped(self):
        page,v=start(dict(scanner_live=False));v['bot_paper_action']('BUY');v['paper_run']('Start')
        self.assertEqual(v['paper_bot_state'],['Running']);v['paper_run']('Pause')
        v['paper_mark'].value='1';v['paper_tick']();self.assertEqual(v['bot_position']['side'],'BUY')
        v['paper_run']('Stop');self.assertEqual(v['paper_bot_state'],['Stopped'])
        _,r=start(page.client_storage.get('bot_king_preferences'));self.assertEqual(r['paper_bot_state'],['Stopped'])
    def test_selector_location_and_no_master_save(self):
        _,v=start(dict(scanner_live=False))
        def controls(root):
            yield root
            for child in root._get_children():yield from controls(child)
        for i in range(4):
            v['select'](i);items=[x for root in v['body'].controls for x in controls(root)]
            self.assertEqual(any(x is v['source'] for x in items),i==2)
            self.assertFalse(any(getattr(x,'text',None)=='Save changes' for x in items))
    def test_autosave_retains_previous_valid_risk(self):
        page,v=start(dict(scanner_live=False));field=v['paper_risk_pct']
        field.value='2';field.on_change(event(field));field.value='nan';field.on_change(event(field))
        self.assertEqual(page.client_storage.get('bot_king_preferences')['paper_risk_pct'],2)
        self.assertTrue(field.error_text)

    def test_chart_reuses_view_until_context_changes(self):
        _,v=start(dict(scanner_live=False,chart_provider='TradingView Lightweight'))
        v['scanner_compact_chart']();first=v['tv_view'][0]
        v['scanner_compact_chart']();self.assertIs(v['tv_view'][0],first)
        v['scan_tf'].value='15m';v['scanner_compact_chart']();self.assertIsNot(v['tv_view'][0],first)
        view=v['tv_view'][0]
        e=type('Event',(),dict(control=view,message='BOT KING Lightweight Charts ready'))()
        v['chart_console'](e);self.assertTrue(v['tv_ready'][0])
        self.assertIn('Chart ready',v['tradingview_status'].value)
    def test_manual_tick_target_exit_and_reentry_cooldown(self):
        _,v=start(dict(scanner_live=False,auto_reentry=True))
        v['bot_paper_action']('BUY');v['paper_run']('Start');v['paper_mark'].value='84';v['paper_tick']()
        self.assertIsNone(v['bot_position']['side']);self.assertEqual(v['prefs']['paper_journal'][-1]['paper_pnl'],4)
        v['paper_tick']();self.assertIsNone(v['bot_position']['side']);self.assertIn('cooldown',v['paper_state_status'].value)
    def test_addition_emergency_blocks_but_stop_exit_remains_available(self):
        _,v=start(dict(scanner_live=False,bot_premium=100,stop_loss=10,dip_step=5,buy_dip=True,max_trades=5,max_total_lots=2))
        v['bot_paper_action']('BUY');v['paper_run']('Start');v['emergency_stop'].value=True
        v['paper_mark'].value='95';v['paper_tick']();self.assertEqual(v['bot_position']['quantity'],1)
        v['paper_mark'].value='89';v['paper_tick']();self.assertIsNone(v['bot_position']['side'])
        self.assertEqual(v['prefs']['paper_journal'][-1]['paper_pnl'],-11)
    def test_manual_tick_averaging_and_partial_are_recorded(self):
        _,v=start(dict(scanner_live=False,bot_premium=100,stop_loss=10,target=20,dip_step=5,buy_dip=True,max_trades=5,max_total_lots=2))
        v['bot_paper_action']('BUY');v['paper_run']('Start');v['paper_mark'].value='95';v['paper_tick']()
        self.assertEqual(v['bot_position']['quantity'],2);self.assertEqual(v['bot_position']['entry'],97.5)
        self.assertEqual(v['prefs']['paper_journal'][-1]['event'],'ADD')
        v['partial_profit'].value=True;v['paper_mark'].value='101';v['paper_tick']()
        self.assertEqual(v['bot_position']['quantity'],1);self.assertEqual(v['prefs']['paper_journal'][-1]['event'],'PARTIAL')
