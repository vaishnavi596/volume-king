"""V2 Android startup must not require tzdata or system IANA timezone files."""
import subprocess
import sys
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "android_app" / "src"

class AndroidTimezoneBootTests(unittest.TestCase):
    def test_mobile_entrypoints_avoid_zoneinfo(self):
        for name in ("main.py", "smart_data.py"):
            source = (APP / name).read_text(encoding="utf-8")
            self.assertNotIn("ZoneInfo(", source)
            self.assertNotIn("from zoneinfo import", source)

    def test_market_gate_without_tzdata(self):
        script = "import builtins,sys\nold=builtins.__import__\ndef deny(name,*a,**kw):\n if name=='tzdata' or name.startswith('tzdata.') or name=='zoneinfo': raise ModuleNotFoundError('No module named tzdata')\n return old(name,*a,**kw)\nbuiltins.__import__=deny\nsys.path.insert(0,sys.argv[1])\nfrom smart_data import IST,SmartDataSettings,permitted_auto_refresh\nfrom datetime import datetime,timezone,timedelta\nassert IST.utcoffset(None)==timedelta(hours=5,minutes=30)\ns=SmartDataSettings()\na=datetime(2026,1,5,3,40,tzinfo=timezone.utc)\nassert permitted_auto_refresh(a,market_session_confirmed=True,settings=s)\nassert not permitted_auto_refresh(a,market_session_confirmed=False,settings=s)\nb=datetime(2026,1,5,10,15,tzinfo=timezone.utc)\nassert permitted_auto_refresh(b,market_session_confirmed=True,settings=s)\nassert not permitted_auto_refresh(b+timedelta(seconds=1),market_session_confirmed=True,settings=s)\nassert not permitted_auto_refresh(datetime(2026,1,4,5,tzinfo=timezone.utc),market_session_confirmed=True,settings=s)\n"
        result = subprocess.run(
            [sys.executable, "-S", "-c", script, str(APP)],
            capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == "__main__":
    unittest.main()
