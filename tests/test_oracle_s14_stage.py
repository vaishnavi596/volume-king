"""Offline S14 Oracle-specific staging guards; nothing touches production."""
import unittest
from scripts.oracle_s14_patch import make_stage, OLD_OPTION

def oracle_fixture():
    return '''import math
import os
import re
from fastapi import HTTPException
from pydantic import BaseModel
DHAN_VERIFIED_INSTRUMENTS = {}
DYNAMIC_INSTRUMENTS = load_dynamic_instruments()
class DhanIntradayRequest(BaseModel):
    symbol: str
def load_dynamic_instruments(): pass
def create_app():
    option_expiry_cache = {}
    calculate_oi_levels = 1
    build_assessment_snapshot = 1
    current_scope = 1
    live_orders_enabled = False
    def dhan_index_ltp_batch(): pass
    def dhan_option_expiries():
        '''+OLD_OPTION+'''
        return instrument
    def dhan_option_chain():
        '''+OLD_OPTION+'''
        return instrument
    @app.post("/dhan/ltp-batch")
    def dhan_ltp_batch(): pass
'''

class OracleS14StageTests(unittest.TestCase):
    def test_narrow_patches_preserve_assessment_logic(self):
        src=oracle_fixture()
        result=make_stage(src)
        self.assertEqual(result.count('instrument = DYNAMIC_INSTRUMENTS.get(body.symbol)'),2)
        self.assertIn('build_assessment_snapshot',result)
        self.assertIn('calculate_oi_levels',result)
        self.assertIn('option_expiry_cache',result)
        self.assertIn('dhan_selected_ltp_batch',result)
        self.assertNotIn('"/v2/instruments/search"',result)

    def test_refuses_existing_route_and_drift(self):
        s=oracle_fixture()
        with self.assertRaisesRegex(ValueError, "duplicate route"):
            make_stage(s+'\n# /dhan/selected-ltp-batch')
        with self.assertRaisesRegex(ValueError, "drifted"):
            make_stage(s.replace('IDX_I','UNKNOWN',1))

if __name__=="__main__":
    unittest.main()
