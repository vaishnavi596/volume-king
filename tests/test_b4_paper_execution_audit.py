"""Paper-only engine audit: deterministic calculations, not broker latency."""
import statistics
import time
import unittest
from pathlib import Path

from paper_engine import evaluate_mark, levels, pnl, risk_check

ROOT = Path(__file__).resolve().parents[1]


class PaperExecutionAuditTests(unittest.TestCase):
    def position(self, side="BUY"):
        stop, target = levels(side, 100, 2, 4)
        return {"side": side, "entry": 100., "quantity": 10,
                "unit_size": 1, "stop_loss_pct": 2, "target_pct": 4,
                "stop_price": stop, "target_price": target}

    def test_buy_sell_target_stop_and_net_charges(self):
        for side, target, stop in (("BUY", 104, 98), ("SELL", 96, 102)):
            with self.subTest(side=side):
                p = self.position(side)
                self.assertEqual(evaluate_mark(p, target, {})["action"], "EXIT")
                self.assertEqual(evaluate_mark(p, stop, {})["action"], "EXIT")
                gross, net = pnl(side, 100, target, 10, 3)
                self.assertEqual(gross, 40)
                self.assertEqual(net, 37)

    def test_target_precedes_partial_profit_and_average(self):
        p = self.position("BUY")
        x = evaluate_mark(p, 104, {"partial": True, "partial_trigger": 1,
                                   "average": True, "dip_pct": 1})
        self.assertEqual(x["action"], "EXIT")
        x = evaluate_mark(p, 103, {"partial": True, "partial_trigger": 2,
                                   "partial_pct": 50})
        self.assertEqual(x["action"], "PARTIAL")
        self.assertEqual(x["quantity"], 5)

    def test_notional_risk_limit_rejects_oversize(self):
        self.assertEqual(risk_check(100, 10, 98, 10000, 5000, 100, 1), 20)
        with self.assertRaises(ValueError):
            risk_check(100, 1000, 98, 10000, 5000, 100, 1)

    def test_paper_ui_has_no_broker_submission(self):
        text = (ROOT / "src" / "paper_engine.py").read_text()
        self.assertNotIn("urllib", text)
        self.assertNotIn("requests.", text)
        main = (ROOT / "src" / "main.py").read_text()
        self.assertIn('note("Start never enables real orders.', main)
        self.assertIn('mark=finite(paper_mark.value,"Manual mark"', main)
        self.assertIn('bot_paper_action("EXIT")', main)

    def test_pure_engine_benchmark_not_network_or_ui_latency(self):
        p = self.position()
        durations = []
        for i in range(500):
            mark = 100.01 if i % 2 else 99.99
            started = time.perf_counter_ns()
            result = evaluate_mark(p, mark, {})
            durations.append((time.perf_counter_ns() - started) / 1e6)
            self.assertEqual(result["action"], "HOLD")
        durations.sort()
        p50 = durations[len(durations) // 2]
        p95 = durations[int(len(durations) * .95)]
        print("PAPER_ENGINE_LOCAL_ONLY_MS P50=%.4f P95=%.4f N=%d" %
              (p50, p95, len(durations)))
        # Broad CPU-hang guard only; not a guarantee of subsecond trading.
        self.assertLess(p95, 1000)


if __name__ == "__main__":
    unittest.main()
