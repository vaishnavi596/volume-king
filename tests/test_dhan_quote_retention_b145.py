"""B145 Dhan LTP retention during candle scanner refresh (source contract)."""
import ast
from pathlib import Path
import unittest

SRC=Path(__file__).resolve().parents[1]/"src"/"main.py"

class QuoteRetentionB145(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=SRC.read_text(encoding="utf-8")
        ast.parse(cls.source,filename=str(SRC))

    def test_candle_fetched_at_cannot_supersede_existing_quote(self):
        block=self.source.split('                            incoming_price=data.get("price")',1)[1].split(
            '                            # Shared local analysis publishes immediately',1)[0]
        for needle in ('incoming_has_quote=', 'saved_has_quote=',
                       'not incoming_has_quote','saved_price',
                       'quotes[sym]=dict(data,price=saved_price',
                       'freshness="unverified"', 'live_verified=False'):
            self.assertIn(needle,block)
        self.assertIn('previous_stamp>data_stamp',block)
        self.assertNotIn('price=bars[-1]',block)

    def test_index_ltp_independent_from_history(self):
        block=self.source.split('    async def refresh_dhan_index_quotes(force=False):',1)[1].split(
            '    manual_quote_last_attempt=',1)[0]
        self.assertIn('dhan_feed.index_batch_quotes',block)
        self.assertIn('dhan_feed.quote,missing_symbol',block)
        self.assertIn('await asyncio.sleep(1.1)',block)
        self.assertIn('provider_data_unavailable',block)

    def test_sensex_mapping_and_diagnostic_kept(self):
        self.assertIn('def sensex_full_diagnostic_panel():',self.source)
        self.assertIn('"segment":"BSE_I","security_id":51',self.source)
        self.assertIn('source_verified_live',self.source)

if __name__=="__main__":
    unittest.main()
