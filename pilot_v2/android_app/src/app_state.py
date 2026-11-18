"""BOT KING V2 app-owned, offline watchlist selection; no server settings or I/O."""
from dataclasses import dataclass, field

INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")
MAX_EQUITIES = 70
WATCHLIST_COUNT = 5

class SelectionError(ValueError):
    pass

def valid_symbol(symbol):
    return (type(symbol) is str and 1 <= len(symbol) <= 32 and
            all(ch.isascii() and (ch.isupper() or ch.isdigit() or ch in "&-_")
                for ch in symbol) and symbol not in INDEXES)

@dataclass
class LocalWatchlists:
    """In-memory owner choices; persistence/sync comes in existing app batch."""
    groups: list = field(default_factory=lambda: [[] for _ in range(WATCHLIST_COUNT)])

    def __post_init__(self):
        if (type(self.groups) is not list or len(self.groups) != WATCHLIST_COUNT
                or any(type(g) is not list for g in self.groups)):
            raise SelectionError("Exactly five watchlists required")
        current = self.groups
        self.groups = [[] for _ in range(WATCHLIST_COUNT)]
        for index, group in enumerate(current):
            for symbol in group:
                self.add(index, symbol)

    @property
    def selected(self):
        return tuple(sorted(s for group in self.groups for s in group))

    def add(self, index, symbol):
        if type(index) is not int or index not in range(WATCHLIST_COUNT):
            raise SelectionError("Invalid watchlist")
        if not valid_symbol(symbol):
            raise SelectionError("Invalid NSE equity")
        if symbol in self.selected:
            raise SelectionError("Share already present in another watchlist")
        if len(self.selected) >= MAX_EQUITIES:
            raise SelectionError("Maximum 70 shares across all watchlists")
        self.groups[index].append(symbol)

    def remove(self, index, symbol):
        if type(index) is not int or index not in range(WATCHLIST_COUNT):
            raise SelectionError("Invalid watchlist")
        if symbol not in self.groups[index]:
            raise SelectionError("Share not in this watchlist")
        self.groups[index].remove(symbol)

    def selection_payload(self):
        return {"watchlists": [list(group) for group in self.groups]}
