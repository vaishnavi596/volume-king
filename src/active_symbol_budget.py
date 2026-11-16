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


def plan_due_history_symbols(active, *, now, last_attempts=None, cooldown_until=0,
                             minimum_spacing=180, max_batch=3, mapped_symbols=None,
                             last_global_attempt=None, global_spacing=1.5):
    """Pure bounded 1m history worklist; this function NEVER calls Dhan.

    Caller must serialize actual requests and persist last_attempts in its
    existing coordinator. All timestamps use the same monotonic clock.
    On 429 cooldown, return no work. This is not an upstream quota guarantee.
    """
    from math import isfinite
    if not isinstance(active, ActiveSymbolBudget):
        raise ValueError("active must be a validated ActiveSymbolBudget")
    numeric = (now, cooldown_until, minimum_spacing, global_spacing)
    if last_global_attempt is not None:
        numeric += (last_global_attempt,)
    if any(type(v) not in (int, float) or not isfinite(v) for v in numeric):
        raise ValueError("non-finite history scheduling time")
    if now < 0 or cooldown_until < 0 or minimum_spacing < 30 or global_spacing < 1:
        raise ValueError("invalid history scheduling window")
    if last_global_attempt is not None and last_global_attempt > now:
        raise ValueError("last_global_attempt is in the future")
    if type(max_batch) is not int or not 1 <= max_batch <= 3:
        raise ValueError("max_batch must be from 1 through 3")
    if last_attempts is None:
        last_attempts = {}
    if not isinstance(last_attempts, dict):
        raise ValueError("last_attempts must be a mapping")
    # Optional broker entitlement/security-ID whitelist: unmapped saved
    # equities must not consume attempts or pretend to have live candles.
    if mapped_symbols is not None:
        if not isinstance(mapped_symbols, (list, tuple, set, frozenset)):
            raise ValueError("mapped_symbols must be a sequence")
        if any(not _valid_symbol(sym) for sym in mapped_symbols):
            raise ValueError("invalid mapped symbol")
        mapped_symbols = frozenset(mapped_symbols)
    if now < cooldown_until:
        return ()
    # Batch cardinality alone does not constrain repeated scheduling ticks.
    # Consumers must record every *actual* provider attempt on a shared
    # monotonic clock and pass that timestamp here to prevent quick fanout.
    if (last_global_attempt is not None
            and now - last_global_attempt < global_spacing):
        return ()
    due = []
    for sym in active.indices + active.equities:
        if mapped_symbols is not None and sym not in mapped_symbols:
            continue
        previous = last_attempts.get(sym)
        if previous is not None:
            if type(previous) not in (int, float) or not isfinite(previous) or previous < 0:
                raise ValueError("invalid last attempt timestamp")
            if now - previous < minimum_spacing:
                continue
        due.append(sym)
    # Oldest attempt first; deterministic tie-break prevents per-cycle
    # oscillation and keeps a fixed upper bound on request bursts.
    return tuple(sorted(due, key=lambda sym: (
        last_attempts.get(sym, -1), sym))[:max_batch])
