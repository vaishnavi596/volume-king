"""S18-B offline regression: 70 total and one owner; no real files."""
import unittest
from scripts.oracle_s18_watchlist_patch import make_stage

FIXTURE = """class WatchlistError(Exception):
    pass

class WatchlistStore:
    def __init__(self):
        self.data = {str(i): [] for i in range(1, 6)}
        self.saved = 0
    def check_id(self, list_id):
        return str(list_id)
    def validate(self, symbols):
        if len(symbols) > 70 or len(set(symbols)) != len(symbols):
            raise WatchlistError("Invalid watchlist")
        return symbols
    def save(self):
        self.saved += 1
    def replace(self, list_id, symbols):
        list_id = self.check_id(list_id)
        validated = self.validate(symbols)
        previous = self.data[list_id]
        self.data[list_id] = validated
        try:
            self.save()
        except Exception:
            self.data[list_id] = previous
            raise
        return list(self.data[list_id])
"""

class S18WatchlistTests(unittest.TestCase):
    def create(self):
        namespace={}
        exec(compile(make_stage(FIXTURE),"<staged-watchlist>","exec"),namespace)
        return namespace["WatchlistStore"](),namespace["WatchlistError"]

    def test_global_70_and_no_second_owner(self):
        store, error=self.create()
        store.replace(1,["T"+str(i) for i in range(40)])
        store.replace(2,["T"+str(i) for i in range(40,70)])
        self.assertEqual(sum(map(len,store.data.values())),70)
        before={k:list(v) for k,v in store.data.items()}
        saves=store.saved
        for group, symbols in [(3,["T1"]),(3,["T70"]),(2,["T40","T1"])]:
            with self.subTest(group=group),self.assertRaises(error):
                store.replace(group,symbols)
            self.assertEqual(store.data,before)
            self.assertEqual(store.saved,saves)
        store.replace(1,["T"+str(i) for i in range(39)])
        store.replace(3,["T70"])
        self.assertEqual(sum(map(len,store.data.values())),70)

    def test_legacy_over_limit_is_preserved_until_user_reduces_it(self):
        store,error=self.create()
        store.data["1"]=["T"+str(i) for i in range(70)]
        store.data["2"]=["T70"]
        with self.assertRaises(error):
            store.replace(2,["T71"])
        self.assertEqual(len(store.data["1"]),70)
        self.assertEqual(store.data["2"],["T70"])
        store.replace(2,[])
        self.assertEqual(len(store.data["1"]),70)

    def test_existing_cross_list_duplicate_cannot_be_added_again(self):
        store,error=self.create()
        store.data["1"]=["T1"]
        store.data["2"]=["T1"]
        with self.assertRaises(error):
            store.replace(3,["T1"])
        self.assertEqual(store.data["1"],["T1"])
        self.assertEqual(store.data["2"],["T1"])

    def test_stage_is_idempotent_fail_closed(self):
        changed=make_stage(FIXTURE)
        with self.assertRaisesRegex(ValueError,"already installed"):
            make_stage(changed)

if __name__=="__main__":
    unittest.main()
