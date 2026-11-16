"""Pure, read-only BOT KING active-symbol budget planning.

This module does not invoke Dhan, alter polling, or change Oracle production.
It separates saved watchlist equities from symbols needed by visible features.
"""
from dataclasses import dataclass

INDEX_SYMBOLS = frozenset(("NIFTY", "BANKNIFTY", "SENSEX"))
MAX_EQUITIES = 70


def _valid_symbol(value):
    if not isinstance(value, str) or not value or len(value) > 40:
        return False
    return all(c.isascii() and (c.isupper() or c.isdigit() or c in "-&") for c in value)


def _add(target, symbols):
    for symbol in symbols:
        if _valid_symbol(symbol):
            target.add(symbol)


@dataclass(frozen=True)
class ActiveSymbolBudget:
    equities: tuple
    indices: tuple
    watched_equities: int
    extra_equities: int
    total_instruments: int

    @property
    def unused_equity_slots(self):
        return max(0, MAX_EQUITIES - self.watched_equities)


def plan_active_symbols(
    watch_groups, *, dashboard=(), scanner=(), super_five=(), options=(),
    keep_indices=("NIFTY", "BANKNIFTY", "SENSEX"),
):
    """Plan data consumers, not Dhan API calls or exchange-data frequency.

    The 70-share capacity applies to saved equities; temporary consumers may
    require additional symbols, so never infer source-request savings from
    removed watchlist members alone. Invalid saved states fail closed.
    """
    if not isinstance(watch_groups, (list, tuple)) or len(watch_groups) != 5:
        raise ValueError("exactly five saved watchlists required")
    watched = set()
    for group in watch_groups:
        if not isinstance(group, (list, tuple)):
            raise ValueError("saved watchlist must be a sequence")
        for symbol in group:
            if not _valid_symbol(symbol) or symbol in INDEX_SYMBOLS:
                raise ValueError("invalid equity in saved watchlist")
            if symbol in watched:
                raise ValueError("duplicate saved equity across watchlists")
            watched.add(symbol)
    if len(watched) > MAX_EQUITIES:
        raise ValueError("saved equity capacity exceeded")
    active = set(watched)
    for feature in (dashboard, scanner, super_five, options):
        if not isinstance(feature, (list, tuple, set, frozenset)):
            raise ValueError("feature symbols must be a sequence")
        _add(active, feature)
    if not isinstance(keep_indices, (list, tuple, set, frozenset)):
        raise ValueError("indices must be a sequence")
    _add(active, keep_indices)
    indices = tuple(sorted(active & INDEX_SYMBOLS))
    equities = tuple(sorted(active - INDEX_SYMBOLS))
    return ActiveSymbolBudget(
        equities=equities, indices=indices,
        watched_equities=len(watched),
        extra_equities=len(set(equities) - watched),
        total_instruments=len(active),
    )
