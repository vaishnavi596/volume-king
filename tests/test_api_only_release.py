import asyncio
import time
import unittest
from unittest.mock import patch

import flet as ft
from test_audit import start
from market_feed import FeedError

def strings(control):
    result=[str(control.value)] if isinstance(control,ft.Text) else []
    for child in control._get_children():result.extend(strings(child))
    return result

class ApiOnlyReleaseTests(unittest.TestCase):
    def test_all_legacy_provider_settings_migrate_to_broker_only(self):
        for source in ('Auto','Yahoo Finance','Broker API'):
            _,v=start({'source':source,'scanner_live':False})
            self.assertEqual(v['source'].value,'Broker API')
            self.assertEqual([o.key for o in v['source'].options],['Broker API'])
            self.assertTrue(v['source'].disabled)

    def test_old_nonbroker_cache_cannot_substitute_for_broker_failure(self):
        _,v=start({'scanner_live':False})
        v['market_store'].put('market',('Broker API','NIFTY','5m','7d'),
            dict(price=100,bars=[[1,100,101,99,100,1]],source='Yahoo Finance',quote_timestamp=1))
        with patch('urllib.request.urlopen') as request:
            with self.assertRaises(FeedError):v['get_market_data']('NIFTY','5m','7d')
            request.assert_not_called()

    def test_no_visible_page_offers_yahoo_or_modeled_trade_scenarios(self):
        _,v=start({'scanner_live':False})
        for i in range(5):
            v['select'](i)
            text=' '.join(t for root in v['body'].controls for t in strings(root))
            self.assertNotIn('Yahoo',text)
            self.assertNotIn('TOP SETUP • SIMULATION ONLY',text)

    def test_home_unknown_account_is_not_reported_as_zero_or_flat(self):
        _,v=start({'scanner_live':False})
        text=' '.join(strings(v['broker_positions_card']()))
        self.assertIn('positions unavailable',text)
        self.assertNotIn('no positions at',text)
        self.assertNotIn('P&L 0',text)

    def test_home_uses_verified_broker_snapshot_and_account_epoch(self):
        _,v=start({'scanner_live':False});ui=v['live_controls']
        ui.positions_snapshot={'epoch':v['angel_feed'].epoch,'time':time.time(),
            'rows':[dict(tradingsymbol='TEST-EQ',producttype='INTRADAY',netqty='2',pnl='12.50')]}
        text=' '.join(strings(v['broker_positions_card']()))
        self.assertIn('TEST-EQ',text);self.assertIn('Qty 2',text);self.assertIn('P&L 12.50',text)
        v['angel_feed'].disconnect()
        self.assertNotIn('TEST-EQ',' '.join(strings(v['broker_positions_card']())))

    def test_failed_account_refresh_invalidates_position_snapshot(self):
        _,v=start({'scanner_live':False});ui=v['live_controls']
        ui.positions_snapshot={'epoch':v['angel_feed'].epoch,'time':time.time(),'rows':[]}
        with patch.object(v['angel_feed'],'live',side_effect=FeedError('unavailable')):
            asyncio.run(ui.refresh())
        self.assertIsNone(ui.positions_snapshot)

    def test_native_api_chart_choice_survives_restart(self):
        _,v=start({'scanner_live':False,'chart_provider':'BOT KING / API'})
        self.assertEqual(v['chart_provider'][0],'BOT KING / API')

    def test_budget_quote_list_uses_actual_premium_and_verified_lot_cost(self):
        _,v=start({'scanner_live':False})
        v['option_feed'].update(symbol=v['chain_symbol'].value,expiry=v['expiry'].value,
            rows=[dict(strike=24000,side='CE',premium=150,lot_size=25,timestamp=time.time())])
        card=v['scanner_premium_quotes']('NIFTY',100,200)
        buttons=[c for c in card.content.controls[1].controls if isinstance(c,ft.OutlinedButton)]
        self.assertIn('₹150.00',buttons[0].text)
        self.assertIn('₹3,750.00',buttons[0].text)
        with patch.object(v['angel_feed'],'live') as submit:
            buttons[0].on_click(None);submit.assert_not_called()
        self.assertEqual(v['live_controls'].price.value,'150')
        self.assertEqual(v['current'][0],1)

    def test_stale_or_other_symbol_quotes_do_not_enter_budget_results(self):
        _,v=start({'scanner_live':False})
        v['option_feed'].update(symbol=v['chain_symbol'].value,expiry=v['expiry'].value,
            rows=[dict(strike=24000,side='CE',premium=150,lot_size=25,timestamp=time.time()-100)])
        for sym in ('NIFTY','TCS'):
            text=' '.join(strings(v['scanner_premium_quotes'](sym,100,200)))
            self.assertIn('No fresh budget-matching',text)

    def test_nonmatching_budget_does_not_generate_theoretical_alternative(self):
        _,v=start({'scanner_live':False})
        v['option_feed'].update(symbol=v['chain_symbol'].value,expiry=v['expiry'].value,
            rows=[dict(strike=24000,side='CE',premium=250,lot_size=25,timestamp=time.time())])
        text=' '.join(strings(v['scanner_premium_quotes']('NIFTY',100,200)))
        self.assertIn('No fresh budget-matching',text)
        self.assertNotIn('modeled',text)
