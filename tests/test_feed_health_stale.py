"""Regression: stale feed responses must not masquerade as successful refreshes."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from feed_health import FeedHealth


class FeedHealthStaleTests(unittest.TestCase):
    def test_stale_does_not_advance_last_success(self):
        clock = [100.0]
        health = FeedHealth(clock=lambda: clock[0])
        request = health.begin('nifty')
        self.assertTrue(health.finish('nifty', request, 'AVAILABLE', source='Yahoo'))
        self.assertEqual(health.get('nifty')['last_success'], 100.0)
        clock[0] = 200.0
        request = health.begin('nifty')
        self.assertTrue(health.finish('nifty', request, 'STALE', source='Yahoo'))
        self.assertEqual(health.get('nifty')['last_success'], 100.0)
        self.assertEqual(health.get('nifty')['state'], 'STALE')

    def test_stale_without_prior_success_has_no_last_success(self):
        health = FeedHealth(clock=lambda: 200.0)
        request = health.begin('nifty')
        health.finish('nifty', request, 'STALE')
        self.assertNotIn('last_success', health.get('nifty'))


if __name__ == '__main__':
    unittest.main()
