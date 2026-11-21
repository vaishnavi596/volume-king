"""SENSEX B143 explicitly opt-in read-only diagnostic source guards."""
import ast
from pathlib import Path
import unittest

MAIN=Path(__file__).resolve().parents[1]/"src"/"main.py"
GATEWAY=Path(__file__).resolve().parents[1]/"backend"/"clone_v2_gateway.py"

class SensexFullDiagnosticB143(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=MAIN.read_text()
        cls.server=GATEWAY.read_text()
        ast.parse(cls.app,filename=str(MAIN))

    def panel(self):
        return self.app.split("    def sensex_full_diagnostic_panel():",1)[1].split(
            "    def v3_live_building_panel():",1)[0]

    def test_exact_index_mapping_preserved(self):
        self.assertIn('"SENSEX": ("BSE_I", 51)',self.server)
        self.assertIn('"segment":"BSE_I","security_id":51',self.panel())

    def test_explicit_opt_in_not_autopolled(self):
        p=self.panel()
        self.assertIn('on_click=lambda e:page.run_task(run_sensex_probe,e)',p)
        self.assertEqual(p.count('dhan_feed.quote,"SENSEX"'),1)
        self.assertEqual(p.count('dhan_feed.intraday,"SENSEX",1,start,end'),1)
        self.assertIn('clone_v2_gateway.connected',p)
        self.assertIn('dhan_feed.connected',p)
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/index-ltp-batch")',p)
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/intraday")',p)
        self.assertIn('SKIPPED_ACTIVE_HISTORY_WORKER',p)
        self.assertIn('provider_generation[0]',p)

    def test_fails_closed_and_reports_stage_not_fake_ltp(self):
        p=self.panel()
        for token in ('VALID_DHAN_QUOTE_UNVERIFIED_TIME','EMPTY_BROKER_HISTORY',
                      'AUTH_OR_PERMISSION','INVALID_CANDLE_SHAPE','LOGIN_CHANGED',
                      'PROVIDER_OR_GATEWAY_EVIDENCE_INCOMPLETE',
                      '"source_verified_live":False','"orders_sent":0'):
            self.assertIn(token,p)
        self.assertNotIn('quotes["SENSEX"]=',p)
        self.assertNotIn('live_verified=True',p)
        self.assertNotIn('order_place(',p)
        self.assertIn('content.append(sensex_full_diagnostic_panel())',self.app)

if __name__=="__main__":
    unittest.main()
