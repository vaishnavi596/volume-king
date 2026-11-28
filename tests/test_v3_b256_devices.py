import os, sys, tempfile, unittest
sys.path[:0] = ["src", "backend"]
try:
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover
    TestClient = None
from device_registry import DeviceRegistry, DeviceDisabled, RedeemLocked

MASTER = "M" * 40


class Registry(unittest.TestCase):
    def setUp(self):
        self.t = [1000.0]
        self.r = DeviceRegistry(os.path.join(tempfile.mkdtemp(), "d.json"), clock=lambda: self.t[0])

    def test_code_is_single_use_and_expires(self):
        c = self.r.create_code("Bhai")["code"]
        out = self.r.redeem(c)
        self.assertTrue(out["device_key"].startswith("bkd_"))
        self.assertIsNone(self.r.redeem(c))                       # single use
        c2 = self.r.create_code("X")["code"]
        self.t[0] += 601
        self.assertIsNone(self.r.redeem(c2))                       # expired

    def test_disable_enable_delete_and_persist(self):
        out = self.r.redeem(self.r.create_code("A")["code"])
        self.assertEqual(self.r.check(out["device_key"])["name"], "A")
        self.r.set_enabled(out["device_id"], False)
        with self.assertRaises(DeviceDisabled): self.r.check(out["device_key"])
        self.r.set_enabled(out["device_id"], True)
        r2 = DeviceRegistry(self.r.path, clock=lambda: self.t[0])    # survives restart; stores hashes only
        self.assertIsNotNone(r2.check(out["device_key"]))
        self.assertNotIn(out["device_key"], open(self.r.path).read())
        self.r.delete(out["device_id"])
        self.assertIsNone(self.r.check(out["device_key"]))

    def test_wrong_codes_lock_redeem(self):
        for _ in range(10): self.r.redeem("WRONGCODE")
        with self.assertRaises(RedeemLocked): self.r.redeem("WRONGCODE")
        self.t[0] += 601
        self.assertIsNone(self.r.redeem("WRONGCODE"))


@unittest.skipIf(TestClient is None, "fastapi not installed")
class Routes(unittest.TestCase):
    def test_flow(self):
        os.environ["BOTKING_CLONE_DEVICES_FILE"] = os.path.join(tempfile.mkdtemp(), "d.json")
        import clone_v2_gateway as g
        app = g.create_app(key_bytes=MASTER.encode())
        c = TestClient(app)
        H = {"X-BotKing-Key": MASTER}
        self.assertEqual(c.get("/clone-v2/whoami", headers=H).json()["role"], "master")
        code = c.post("/clone-v2/devices/code", json={"name": "Bhai"}, headers=H).json()["code"]
        dev = c.post("/clone-v2/devices/redeem", json={"code": code}).json()
        D = {"X-BotKing-Key": dev["device_key"]}
        self.assertEqual(c.get("/clone-v2/whoami", headers=D).json()["role"], "device")
        self.assertEqual(c.get("/clone-v2/devices", headers=D).status_code, 403)       # clone cannot manage devices
        self.assertEqual(c.post("/clone-v2/devices/code", json={}, headers=D).status_code, 403)
        c.post("/clone-v2/devices/set", json={"id": dev["device_id"], "enabled": False}, headers=H)
        r = c.get("/clone-v2/whoami", headers=D)
        self.assertEqual((r.status_code, r.json()["detail"]), (403, "DEVICE_DISABLED"))
        c.post("/clone-v2/devices/set", json={"id": dev["device_id"], "enabled": True}, headers=H)
        self.assertEqual(c.get("/clone-v2/whoami", headers=D).status_code, 200)
        self.assertEqual(c.get("/clone-v2/whoami", headers={"X-BotKing-Key": "nope"}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
