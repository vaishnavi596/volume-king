"""Three V1-style independent Dashboard analysis slots, app-owned V2 only.

No provider settings, network access, server preferences or live signals.
Each slot may select a Dashboard index or a currently selected equity.
"""
from app_state import INDEXES
from scanner_state import selectable_symbols

SLOT_DEFAULTS = INDEXES
SLOT_COUNT = 3


class AnalysisSlotError(ValueError):
    pass


class LocalAnalysisSlots:
    def __init__(self, slots=SLOT_DEFAULTS):
        if (type(slots) not in (tuple, list) or len(slots) != SLOT_COUNT
                or any(type(symbol) is not str or not symbol for symbol in slots)):
            raise AnalysisSlotError("Exactly three valid analysis slots required")
        self.slots = list(slots)

    def select(self, index, symbol, watchlists):
        if (type(index) is not int or index not in range(SLOT_COUNT)
                or type(symbol) is not str
                or symbol not in selectable_symbols(watchlists)):
            raise AnalysisSlotError("Analysis slot symbol must be currently selectable")
        changed = self.slots[index] != symbol
        self.slots[index] = symbol
        return changed

    def reconcile(self, watchlists):
        """Removed equity cannot remain a selectable Dashboard analysis source."""
        allowed = set(selectable_symbols(watchlists))
        changed = False
        for i, value in enumerate(self.slots):
            if value not in allowed:
                self.slots[i] = SLOT_DEFAULTS[i]
                changed = True
        return changed

    def saved_state(self):
        return {"schema_version": 1, "slots": list(self.slots)}

    @classmethod
    def from_saved(cls, raw, watchlists):
        if (type(raw) is not dict or set(raw) != {"schema_version", "slots"}
                or type(raw["schema_version"]) is not int
                or raw["schema_version"] != 1
                or type(raw["slots"]) is not list):
            raise AnalysisSlotError("Invalid local Dashboard analysis save")
        obj = cls(raw["slots"])
        if any(s not in selectable_symbols(watchlists) for s in obj.slots):
            raise AnalysisSlotError("Saved analysis contains removed or invalid symbol")
        return obj
