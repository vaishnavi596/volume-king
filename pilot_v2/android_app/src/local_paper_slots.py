"""V2 safe five-slot PAPER planning records; no simulated fills or orders.

Only manual risk *previews* can be retained. No broker credentials, market
quotes, trade actions, journal fills or legacy V1 prefs are imported.
"""
import math

SLOTS = ("Bot 1", "Bot 2", "Bot 3", "Bot 4", "Bot 5")
PREVIEW_FIELDS = {"side", "entry", "quantity", "stop", "target",
                  "planned_risk", "target_gross_gain"}
ENVELOPE_FIELDS = {"schema_version", "selected_slot", "previews"}


class PaperSlotError(ValueError):
    pass


def _validate_preview(preview):
    if type(preview) is not dict or set(preview) != PREVIEW_FIELDS:
        raise PaperSlotError("Only manual PAPER risk previews may be saved")
    if preview["side"] not in ("BUY", "SELL") or type(preview["side"]) is not str:
        raise PaperSlotError("Unsupported manual paper side")
    if type(preview["quantity"]) is not int or not 1 <= preview["quantity"] <= 100000:
        raise PaperSlotError("Invalid paper quantity")
    for key in PREVIEW_FIELDS - {"side", "quantity"}:
        value = preview[key]
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise PaperSlotError("Invalid paper risk preview value")
    if preview["entry"] <= 0 or preview["stop"] <= 0 or preview["target"] <= 0:
        raise PaperSlotError("Manual paper prices must be positive")
    if preview["side"] == "BUY" and not (preview["stop"] < preview["entry"] < preview["target"]):
        raise PaperSlotError("Invalid BUY paper preview levels")
    if preview["side"] == "SELL" and not (preview["target"] < preview["entry"] < preview["stop"]):
        raise PaperSlotError("Invalid SELL paper preview levels")
    return dict(preview)


class LocalPaperPlanSlots:
    def __init__(self):
        self.selected_slot = SLOTS[0]
        self.previews = {slot: None for slot in SLOTS}

    def choose(self, slot):
        if type(slot) is not str or slot not in SLOTS:
            raise PaperSlotError("Unknown local paper plan slot")
        self.selected_slot = slot

    def save_preview(self, result):
        if type(result) is not dict or result.get("status") != "PAPER PREVIEW ONLY" or result.get("orders_enabled") is not False or result.get("live_verified") is not False:
            raise PaperSlotError("Only disabled-order paper previews can be saved")
        candidate = _validate_preview({key: result[key] for key in PREVIEW_FIELDS})
        self.previews[self.selected_slot] = candidate

    def clear(self):
        self.previews[self.selected_slot] = None

    def rows(self):
        return tuple((slot, self.previews[slot]) for slot in SLOTS)

    def saved_state(self):
        return {"schema_version": 1, "selected_slot": self.selected_slot,
                "previews": {slot: (dict(value) if value else None)
                             for slot, value in self.rows()}}

    @classmethod
    def from_saved(cls, raw):
        if type(raw) is not dict or set(raw) != ENVELOPE_FIELDS or type(raw["schema_version"]) is not int or raw["schema_version"] != 1 or raw["selected_slot"] not in SLOTS:
            raise PaperSlotError("Invalid V2 paper plan storage")
        saved = raw["previews"]
        if type(saved) is not dict or set(saved) != set(SLOTS):
            raise PaperSlotError("Invalid five paper plan slots")
        obj = cls()
        obj.selected_slot = raw["selected_slot"]
        obj.previews = {slot: _validate_preview(value) if value is not None else None
                        for slot, value in saved.items()}
        return obj
