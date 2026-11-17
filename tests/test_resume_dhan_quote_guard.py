"""Resume history must preserve prior Dhan price, candle identity and chart.

Source-specific invariants and a real retention-helper replay; no network.
"""
import sys
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from candle_retention import retain_candle_history,valid_candle_history

SOURCE=(ROOT/"src"/"main.py").read_text(encoding="utf-8")

class ResumeDhanQuoteGuardTests(unittest.TestCase):
    def setUp(self):
        self.body=SOURCE.split('    async def refresh_after_resume():',1)[1].split('    def lifecycle_changed(e):',1)[0]

    def test_last_valid_dhan_price_is_preserved(self):
        self.assertIn('previous.get("source")=="Dhan"',self.body)
        self.assertIn('math.isfinite(previous["price"])',self.body)
        self.assertIn('quotes[sym]=dict(previous,bars=verified_bars',self.body)
        self.assertIn('valid_candle_history(history.get("bars"))',self.body)

    def test_resume_downgrades_freshness(self):
        self.assertIn('freshness="unverified"',self.body)
        self.assertIn('freshness="historical_unverified"',self.body)
        self.assertIn('live_verified=False',self.body)

    def test_missing_previous_quote_is_never_verified_live_from_history(self):
        self.assertIn('quotes[sym]=dict(data,historical=True,live_verified=False,',self.body)
        self.assertIn('freshness="historical_unverified"',self.body)

    def test_1m_or_3m_resume_never_overwrites_legacy_5m_quote_history(self):
        self.assertIn('selected_tf=scan_tf.value or "1m"',self.body)
        self.assertIn('get_market_data,sym,selected_tf',self.body)
        self.assertIn('if selected_tf=="5m":',self.body)
        self.assertIn('chart_snapshots[(sym,selected_tf,generation)]=dict(',self.body)
        self.assertIn('_scanner_timeframe=selected_tf',self.body)
        self.assertLess(self.body.index('if selected_tf=="5m":'),
                        self.body.index('quotes[sym]=dict(previous,bars=verified_bars'))

    def test_resume_chart_snapshot_retains_good_history_before_publish(self):
        self.assertIn('prior_chart=chart_snapshots.get((chart_sym,chart_tf,generation)) or {}',self.body)
        self.assertIn('chart_data=retain_candle_history(chart_data,prior_chart,provider="Dhan")',self.body)
        self.assertIn('if valid_candle_history(chart_data.get("bars")):',self.body)
        self.assertLess(self.body.index('chart_data=retain_candle_history(chart_data,prior_chart,provider="Dhan")'),
                        self.body.index('chart_snapshots[(chart_sym,chart_tf,generation)]=chart_data'))

    def test_short_response_real_retention_helper_does_not_erase_previous_history(self):
        old=[[10000+i*60,100,101,99,100.5,100] for i in range(35)]
        previous={"source":"Dhan","bars":old,"candle_fetched_at":10020,
                  "historical":True,"live_verified":False}
        received={"source":"Dhan","bars":old[-2:],"live_verified":True}
        retained=retain_candle_history(received,previous,provider="Dhan")
        self.assertTrue(valid_candle_history(retained.get("bars")))
        self.assertEqual(retained["bars"],old)
        self.assertEqual(retained["candle_fetched_at"],10020)
        self.assertTrue(retained["historical"])
        self.assertFalse(retained["live_verified"])
        self.assertEqual(retained["freshness"],"historical_unverified")

if __name__=="__main__":
    unittest.main()
