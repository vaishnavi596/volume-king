"""Official compact Dhan Futures mapping is unverified until separately audited."""
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"backend"))
from dhan_futures_master import futures_candidates_from_dhan_compact,futures_master_readiness
from futures_context import select_verified_future
from datetime import date

HEADER="EXCH_ID,SEGMENT,INSTRUMENT,UNDERLYING_SYMBOL,SECURITY_ID,SM_EXPIRY_DATE,DISPLAY_NAME\n"
GOOD="NSE,D,FUTIDX,NIFTY,12345,2026-12-31,NIFTY DEC FUT\n"

class FuturesMasterTests(unittest.TestCase):
    def test_valid_compact_candidate_is_not_authenticated(self):
        rows=futures_candidates_from_dhan_compact(HEADER+GOOD+
            "NSE,E,EQUITY,RELIANCE,2885,,RELIANCE\n")
        self.assertEqual(len(rows),1)
        row=rows[0]
        self.assertEqual(row["underlying"],"NIFTY")
        self.assertEqual(row["expiry"],"2026-12-31")
        self.assertEqual(row["security_id"],"12345")
        self.assertFalse(row["master_verified"])
        self.assertIsNone(select_verified_future(rows,"NIFTY",date(2026,12,31)))
        self.assertFalse(futures_master_readiness(rows)["mapping_eligible"])

    def test_fails_closed_on_missing_underlying_schema_or_conflicts(self):
        for raw in (HEADER.replace("UNDERLYING_SYMBOL,","")+GOOD,
                    HEADER+GOOD+GOOD,
                    HEADER+GOOD.replace("NIFTY,12345","NIFTY,1.5"),
                    HEADER+GOOD.replace("NIFTY,12345","NIFTY,-3"),
                    HEADER+GOOD.replace("2026-12-31","2026-02-30"),
                    HEADER+GOOD.replace("NIFTY,12345","NIFTY:BAD,12345"),
                    HEADER+GOOD.replace("NIFTY DEC FUT",""),
                    "not a csv"):
            with self.subTest(text=raw[:60]):
                with self.assertRaises(ValueError):
                    futures_candidates_from_dhan_compact(raw)

    def test_no_future_contract_guessed_from_equities(self):
        self.assertEqual(futures_candidates_from_dhan_compact(
            HEADER+"NSE,E,EQUITY,RELIANCE,2885,2026-12-31,RELIANCE\n"),[])

if __name__=="__main__":unittest.main()
