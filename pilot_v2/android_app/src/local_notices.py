"""V2 in-app session notices: known local events only, no market alerts.

No push notifications, price thresholds, secret-bearing free text,
provider requests, user identifiers, or inference of live signals.
"""
EVENTS = {
    "WATCHLIST_ADDED": "Watchlist selection updated locally",
    "WATCHLIST_REMOVED": "Watchlist equity removed locally",
    "PAPER_PLAN_SAVED": "Manual PAPER risk preview saved locally",
    "PAPER_PLAN_CLEARED": "Manual PAPER preview cleared locally",
    "LOCAL_PREFS_RESTORED": "Local preferences restored for this session",
}
MAX_NOTICES = 20


class LocalNoticeError(ValueError):
    pass


class LocalNoticeCenter:
    def __init__(self):
        self._items = []
        self._next_id = 0

    def record(self, code):
        if type(code) is not str or code not in EVENTS:
            raise LocalNoticeError("Unrecognized local notice event")
        self._next_id += 1
        self._items.append({"id": self._next_id, "code": code, "read": False})
        self._items = self._items[-MAX_NOTICES:]

    @property
    def unread(self):
        return sum(not item["read"] for item in self._items)

    def visible(self):
        return tuple((EVENTS[item["code"]], not item["read"])
                     for item in reversed(self._items))

    def mark_read(self):
        for item in self._items:
            item["read"] = True

    def clear(self):
        self._items.clear()
