"""B240: remembered SSK is opt-in, stored only in its own client-storage key."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class SskRememberTests(unittest.TestCase):
    def setUp(self):
        self.src=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
    def test_saved_only_when_remember_on(self):
        self.assertIn('await ssk_store_write_async(access_key if (ssk_remember.value and access_key) else "")',self.src)
    def test_never_in_preferences(self):
        for bad in ('prefs["server_access"]',"prefs['server_access']",'prefs["ssk"]'):
            self.assertNotIn(bad,self.src)
        self.assertIn('SSK_STORE_KEY="bot_king_ssk_v1"',self.src)
    def test_disconnect_and_rejection_forget_key(self):
        self.assertIn('page.run_task(ssk_store_write_async,"");ssk_remember.value=False  # explicit Disconnect',self.src)
        self.assertIn('"key rejected","http 401","http 403","session rejected"',self.src)
    def test_single_auto_login_attempt_at_start(self):
        self.assertIn("page.run_task(ssk_auto_login)",self.src)
        self.assertIn("ssk_auto_login_done[0]=True",self.src)
    def test_storage_only_async_never_sync(self):
        self.assertIn("get_async(SSK_STORE_KEY)",self.src)
        self.assertIn("set_async(SSK_STORE_KEY",self.src)
        self.assertNotIn("page.client_storage.get(SSK_STORE_KEY)",self.src)
        self.assertNotIn("page.client_storage.set(SSK_STORE_KEY",self.src)
    def test_offline_price_falls_back_to_last_known_then_hist(self):
        self.assertIn("def hist_close_for_display(sym):",self.src)
        self.assertIn("B242: feed off",self.src)
        self.assertIn('for frame in ("1m","3m","5m"):',self.src)
    def test_hindi_labels_present(self):
        i18n=(ROOT/"src"/"i18n.py").read_text(encoding="utf-8")
        self.assertIn("Server access key (saved only if Remember is ON)",i18n)
        self.assertIn("इस फ़ोन पर SSK याद रखें",i18n)
if __name__=="__main__":unittest.main()
