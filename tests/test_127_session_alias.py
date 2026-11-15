"""Gateway session expiry must revoke on either trusted packaging import path."""
import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.server import create_app

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from market_feed import SessionExpired as TopLevelSessionExpired
from src.market_feed import SessionExpired as PackageSessionExpired


class GatewayAliasExpiry127(unittest.TestCase):
    def test_both_trusted_session_expired_classes_revoke(self):
        class Feed:
            connected=False
            def __init__(self,exception):
                self.exception=exception
            def connect(self,*args):
                self.connected=True
            def disconnect(self):
                self.connected=False
            def expiries(self,symbol):
                raise self.exception("confidential provider response")
        for exception in (TopLevelSessionExpired,PackageSessionExpired):
            with self.subTest(module=exception.__module__):
                feed=Feed(exception)
                with TestClient(create_app("owner-access-key-"*3,feed,lambda:100.0)) as api:
                    res=api.post("/v1/login",
                        json={"api_key":"key","client_code":"code","pin":"pin",
                              "totp":"123456"},
                        headers={"X-BotKing-Key":"owner-access-key-"*3})
                    self.assertEqual(res.status_code,200,res.text)
                    headers={"Authorization":"Bearer "+res.json()["session"]}
                    result=api.post("/v1/expiries",json={"symbol":"NIFTY"},headers=headers)
                    self.assertEqual(result.status_code,401)
                    self.assertFalse(feed.connected)
                    self.assertNotIn("confidential provider response",result.text)

if __name__=="__main__":
    unittest.main()
