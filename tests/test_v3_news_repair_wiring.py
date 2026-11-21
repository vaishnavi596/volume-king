"""News/Event real cached RSS wiring and five-signal fail-closed contracts."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
AST=ast.parse(SRC)
FNS={x.name:ast.get_source_segment(SRC,x) or "" for x in ast.walk(AST)
     if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
class TestNewsRepair(unittest.TestCase):
    def test_news_rss_keeps_https_url_through_dedupe(self):
        body=FNS["combine_analysis"]
        self.assertIn("matching_urls",body)
        self.assertIn('"url":matching_urls.get(',body)
        self.assertIn('.startswith("https://")',body)
        self.assertIn('deduplicate_news_context(tagged',body)
    def test_news_card_does_not_require_scanner_fusion(self):
        body=FNS["news_event_overview"]
        self.assertIn('news_cache.get(key)',body)
        self.assertIn('page.launch_url(article)',body)
        self.assertIn('url.startswith("https://")',body)
        self.assertIn('len(seen)>=3',body)
    def test_pcr_maxpain_render_independently_and_oi_not_faked(self):
        body=FNS["option_metrics"]
        self.assertIn('if kind=="PCR":',body)
        self.assertIn('if kind=="OI":',body)
        self.assertIn('math.isfinite(value)',body)
        self.assertIn('OI Support / Resistance: verified directional evidence not connected',body)
        self.assertIn('PCR ERROR',body)
        self.assertIn('Max Pain ERROR',body)

    def test_news_context_never_counts_as_trading_vote(self):
        body=FNS["combine_analysis"]
        self.assertIn("news_bias=None",body)
        self.assertIn('overall="WAIT"',body) if 'overall="WAIT"' in body else self.assertIn('else "WAIT"',body)
    def test_70_probe_is_real_stock_only(self):
        from v3_live_capacity_probe import benchmark_cached_capacity
        test=benchmark_cached_capacity(["RELIANCE"],{}, {},1,70)
        self.assertEqual(test["unconfigured_equity_slots"] if "unconfigured_equity_slots" in test
                         else test["unconfigured_symbols_are_not_provider_errors"],69)
        self.assertEqual(test["quote_missing_count"],4)
        self.assertEqual(test["stock_error_count"],4)
        self.assertEqual(test["technical_wait"],4)
if __name__=="__main__":unittest.main()
