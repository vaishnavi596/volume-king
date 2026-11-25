import unittest
from v3_platinum_registry import FEATURES, CHECKPOINTS, registry_report

class PlatinumRegistryTests(unittest.TestCase):
    def test_fixed_scope_and_no_false_closure(self):
        r=registry_report()
        self.assertEqual(len(set(key for key,name in FEATURES)),32)
        self.assertEqual(len(CHECKPOINTS),4)
        self.assertEqual(r["checkpoints"],128)
        self.assertEqual([b["features"] for b in r["batches"]],[5,7,5,5,5,5])
        self.assertEqual(r["verified"]+r["unreconciled"],128)
        self.assertTrue(all(row["state"]=="OPEN" for row in r["rows"]))
        self.assertEqual(r["provider_requests"],0)
        self.assertTrue(any(row["verified_subitem"] for row in r["rows"]))
    def test_resource_subitems_do_not_award_checkpoint_credit(self):
        rows={row["id"]:row for row in registry_report()["rows"]}
        for key,run in (("B2.03",45655842571),("B2.07",45657927264)):
            self.assertEqual(rows[key]["verified_subitem"]["ci_run"],run)
            self.assertEqual(rows[key]["state"],"OPEN")
            self.assertTrue(all(v["state"]=="UNRECONCILED" for v in rows[key]["checkpoints"].values()))

    def test_both_doctors_wired(self):
        from pathlib import Path
        s=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
        self.assertIn('"platinum_feature_registry":__import__("v3_platinum_registry").registry_report()',s)
        self.assertIn('data["platinum_feature_registry"]=',s)
