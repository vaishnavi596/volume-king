"""V2 user-owned local preference backup; no server or broker settings.

Only explicitly whitelisted Watchlist, Scanner, Smart Data, and Dashboard
analysis-slot choices are accepted. Parse ALL fields before mutating app state.
"""
import json
from app_state import LocalWatchlists
from scanner_state import ScannerSelection
from smart_data import SmartDataSettings
from local_analysis_slots import LocalAnalysisSlots

BACKUP_KIND = "botking-v2-local-preferences"
MAX_BACKUP_CHARS = 16384
FIELDS = {"kind", "schema_version", "watchlists", "scanner",
          "smart_data", "analysis_slots"}


class LocalBackupError(ValueError):
    pass


def export_local_backup(watchlists, scanner, smart, analysis_slots):
    data = {
        "kind": BACKUP_KIND,
        "schema_version": 1,
        "watchlists": watchlists.saved_state(),
        "scanner": scanner.saved_state(),
        "smart_data": smart.saved_state(),
        "analysis_slots": analysis_slots.saved_state(),
    }
    return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def parse_local_backup(text):
    if type(text) is not str or len(text) > MAX_BACKUP_CHARS or not text:
        raise LocalBackupError("Invalid local backup length")
    try:
        doc = json.loads(text)
        if (type(doc) is not dict or set(doc) != FIELDS
                or doc["kind"] != BACKUP_KIND
                or type(doc["schema_version"]) is not int
                or doc["schema_version"] != 1):
            raise LocalBackupError("Only V2 local preference backups are accepted")
        watchlists = LocalWatchlists.from_saved(doc["watchlists"])
        scanner = ScannerSelection.from_saved(doc["scanner"], watchlists)
        smart = SmartDataSettings.from_saved(doc["smart_data"])
        slots = LocalAnalysisSlots.from_saved(doc["analysis_slots"], watchlists)
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError) as exc:
        raise LocalBackupError("Invalid or unsupported local preferences backup") from exc
    return watchlists, scanner, smart, slots
