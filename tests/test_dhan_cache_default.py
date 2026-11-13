"""Market cache provider identity must match the uncached Dhan default."""
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


class DhanCacheDefaultTests(unittest.TestCase):
    def test_market_cache_and_fetch_use_same_default(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("    def get_market_data(")
        end = source.index("    def fetch_market_data_uncached(", start)
        cache = source[start:end]
        self.assertIn('prefs.get("source","Dhan")', cache)
        self.assertNotIn('prefs.get("source","Auto")', cache)
        self.assertIn('ttl=90 if key[3]=="Dhan" else 10', cache)
        fetch = source[end:source.index("    def ", end + 5)]
        self.assertIn('selected=prefs.get("source","Dhan")', fetch)


if __name__ == "__main__":
    unittest.main()
