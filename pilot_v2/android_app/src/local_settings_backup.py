"""V2 user-owned local preference backup; no server or broker settings.

Only explicitly whitelisted Watchlist, Scanner, Smart Data, and Dashboard
analysis-slot choices are accepted. Parse ALL fields before mutating app state.
"""
import json
from app_state import LocalWatchlists
from scanner_state import ScannerSelection
from smart_data import SmartDataSettings
from local_analysis_slots import LocalAnalysisSlots
from chart_style import chart_style_choice
from chart_window import choose_chart_window
from chart_visibility import validated_chart_visible

BACKUP_KIND = "botking-v2-local-preferences"
MAX_BACKUP_CHARS = 16384
FIELDS = {"kind", "schema_version", "watchlists", "scanner",
          "smart_data", "analysis_slots"}
FIELDS_V2 = FIELDS | {"chart_style"}
FIELDS_V3 = FIELDS_V2 | {"chart_window"}
FIELDS_V4 = FIELDS_V3 | {"chart_visible"}


class LocalBackupError(ValueError):
    pass


def export_local_backup(watchlists, scanner, smart, analysis_slots, *,
                        chart_style=None, chart_window=None, chart_visible=None):
    data = {
        "kind": BACKUP_KIND,
        "schema_version": 1,
        "watchlists": watchlists.saved_state(),
        "scanner": scanner.saved_state(),
        "smart_data": smart.saved_state(),
        "analysis_slots": analysis_slots.saved_state(),
    }
    if chart_style is not None:
        data["schema_version"] = 2
        data["chart_style"] = chart_style_choice(chart_style)
    if chart_window is not None:
        if chart_style is None:
            raise LocalBackupError("Chart history window requires the chart style preference")
        data["schema_version"] = 3
        data["chart_window"] = choose_chart_window(chart_window)
    if chart_visible is not None:
        if chart_style is None or chart_window is None:
            raise LocalBackupError("Chart visibility requires existing chart preferences")
        data["schema_version"] = 4
        data["chart_visible"] = validated_chart_visible(chart_visible)
    return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def parse_local_backup(text):
    if type(text) is not str or len(text) > MAX_BACKUP_CHARS or not text:
        raise LocalBackupError("Invalid local backup length")
    try:
        doc = json.loads(text)
        if (type(doc) is not dict or doc.get("kind") != BACKUP_KIND
                or type(doc.get("schema_version")) is not int
                or doc["schema_version"] not in (1, 2, 3, 4)
                or set(doc) != {1: FIELDS, 2: FIELDS_V2,
                                   3: FIELDS_V3, 4: FIELDS_V4}[doc["schema_version"]]):
            raise LocalBackupError("Only V2 local preference backups are accepted")
        watchlists = LocalWatchlists.from_saved(doc["watchlists"])
        scanner = ScannerSelection.from_saved(doc["scanner"], watchlists)
        smart = SmartDataSettings.from_saved(doc["smart_data"])
        slots = LocalAnalysisSlots.from_saved(doc["analysis_slots"], watchlists)
        style = (chart_style_choice(doc["chart_style"])
                 if doc["schema_version"] >= 2 else None)
        window = (choose_chart_window(doc["chart_window"])
                  if doc["schema_version"] >= 3 else None)
        visible = (validated_chart_visible(doc["chart_visible"])
                   if doc["schema_version"] == 4 else None)
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError) as exc:
        raise LocalBackupError("Invalid or unsupported local preferences backup") from exc
    if doc["schema_version"] == 4:
        return watchlists, scanner, smart, slots, style, window, visible
    if doc["schema_version"] == 3:
        return watchlists, scanner, smart, slots, style, window
    if doc["schema_version"] == 2:
        return watchlists, scanner, smart, slots, style
    return watchlists, scanner, smart, slots
