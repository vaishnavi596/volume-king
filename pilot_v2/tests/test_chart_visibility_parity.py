"""Native V1 chart toggle -> V2 persisted/backup safe parity."""
import json
import sys
import unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/"android_app"/"src"
sys.path.insert(0,str(SRC))
from chart_visibility import validated_chart_visible
from app_state import LocalWatchlists
from scanner_state import ScannerSelection
from smart_data import SmartDataSettings
from local_analysis_slots import LocalAnalysisSlots
from local_settings_backup import export_local_backup,parse_local_backup,LocalBackupError
class ChartToggleParity(unittest.TestCase):
    def setUp(self):
        self.w=LocalWatchlists()
        self.w.add(0,"TCS")
        self.sc=ScannerSelection("TCS","3m")
        self.smart=SmartDataSettings()
        self.slots=LocalAnalysisSlots(["NIFTY","TCS","NIFTY"])
    def test_all_show_hide_options_roundtrip(self):
        for visible in (True,False):
            self.assertIs(validated_chart_visible(visible),visible)
            data=export_local_backup(self.w,self.sc,self.smart,self.slots,
                chart_style="Candles",chart_window=35,chart_visible=visible)
            self.assertEqual(json.loads(data)["schema_version"],4)
            self.assertEqual(parse_local_backup(data)[4:],("Candles",35,visible))
        for bad in (None,1,0,"false",[]):
            with self.assertRaises(ValueError):
                validated_chart_visible(bad)
    def test_old_backup_versions_unchanged(self):
        for style,window,length in ((None,None,4),("Line",None,5),("Candles",70,6)):
            doc=export_local_backup(self.w,self.sc,self.smart,self.slots,
                                    chart_style=style,chart_window=window)
            self.assertEqual(len(parse_local_backup(doc)),length)
    def test_missing_or_extra_fields_fail_closed(self):
        doc=json.loads(export_local_backup(self.w,self.sc,self.smart,self.slots,
                            chart_style="Line",chart_window=15,chart_visible=True))
        for key,value in (("chart_visible",1),("chart_visible","false"),
                          ("schema_version",5),("api_key","secret")):
            with self.subTest(key=key),self.assertRaises(LocalBackupError):
                parse_local_backup(json.dumps(dict(doc,**{key:value})))
    def test_app_controls_are_local_only(self):
        s=(SRC/"main.py").read_text(encoding="utf-8")
        for token in ('label="Show Scanner chart"',"on_change=toggle_scanner_chart",
                      "chart_visible_key =", "chart_visible=chart_visible[0]",
                      "new_chart_visible = restored[6] if len(restored) == 7 else None"):
            self.assertIn(token,s)
        self.assertNotIn("ServerAngelFeed(",s)
