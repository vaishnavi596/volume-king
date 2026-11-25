import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from filter_wiring_audit import normalized_vote_trace_rows, doctor_filter_rows

class MasterTraceNormalizationTest(unittest.TestCase):
    def test_status_parity_and_no_context_vote(self):
        matrix=[{"name":"Supertrend","state":"CALCULATED","vote":1},
                {"name":"EMA 9/21","state":"CALCULATED","vote":0},
                {"name":"RSI","state":"CHART_ONLY","vote":1},
                {"name":"OI Support","state":"ADAPTER_NOT_DIRECTIONAL","vote":1},
                {"name":"MACD","state":"CANDLE_DATA_MISSING_OR_INVALID","vote":None}]
        scanner=doctor_filter_rows([{"filter":r["name"]} for r in matrix],matrix)
        master=normalized_vote_trace_rows(matrix)
        self.assertEqual([(r["status"],r["stage"]) for r in scanner],
                         [(r["status"],r["stage"]) for r in master])
        self.assertEqual([r["vote"] for r in master],[1,0,None,None,None])
