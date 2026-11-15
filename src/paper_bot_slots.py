"""Independent paper-bot slots and an offline-only portfolio ledger.

No broker orders, network calls or trade authorization. Everything here is a
simulation; the saved journal is a local accounting record, not a fill.
"""
import math

SLOTS = ("Bot 1", "Bot 2", "Bot 3", "Bot 4", "Bot 5")
EMPTY = {"side": None, "entry": None, "quantity": 0, "contract": None}
SLOT_FIELDS = ("bot_segment", "bot_symbol", "bot_custom", "bot_type", "bot_strike",
               "bot_expiry", "bot_expiry_mode", "bot_lots", "bot_lot_size",
               "bot_premium", "cash_quantity", "stop_loss", "target",
               "paper_trail_pct", "paper_partial_pct", "paper_partial_trigger",
               "paper_max_additions", "paper_add_units", "bot_trailing",
               "partial_profit", "buy_dip", "manual_contract_confirmed",
               "paper_break_even", "paper_break_even_trigger", "paper_break_even_fees")


def bootstrap(prefs):
    """Migrate a legacy single paper position once; never lose existing slots."""
    if not isinstance(prefs.get("paper_bot_positions"), dict):
        prefs["paper_bot_positions"] = {"Bot 1": dict(prefs.get("bot_position") or EMPTY)}
    positions = prefs["paper_bot_positions"]
    for key in list(positions):
        if key not in SLOTS or not isinstance(positions[key], dict):
            del positions[key]
    for key in SLOTS:
        positions.setdefault(key, dict(EMPTY))
    if not isinstance(prefs.get("paper_bot_configs"), dict):
        prefs["paper_bot_configs"] = {}
    return positions


def save_slot(prefs, slot, position, config):
    if slot not in SLOTS:
        raise ValueError("Unknown paper bot slot")
    if not isinstance(position, dict) or not isinstance(config, dict):
        raise ValueError("Invalid paper slot data")
    bootstrap(prefs)
    prefs["paper_bot_positions"][slot] = dict(position)
    prefs["paper_bot_configs"][slot] = {key: config[key] for key in SLOT_FIELDS if key in config}
    prefs["paper_bot_selected"] = slot


def load_slot(prefs, slot):
    if slot not in SLOTS:
        raise ValueError("Unknown paper bot slot")
    bootstrap(prefs)
    return dict(prefs["paper_bot_positions"][slot]), dict(prefs["paper_bot_configs"].get(slot) or {})


def record(prefs, slot, event, position, *, price=None, quantity=None, charges=0, pnl=None):
    """Append a bounded, tagged paper record. Never describe it as broker fill."""
    if slot not in SLOTS or event not in ("BUY", "SELL", "EXIT", "PARTIAL", "ADD"):
        raise ValueError("Invalid paper event")
    if not isinstance(position, dict):
        raise ValueError("Invalid paper position")
    if charges is None or isinstance(charges, bool):
        raise ValueError("Invalid charges")
    charges = float(charges)
    if not math.isfinite(charges) or charges < 0:
        raise ValueError("Invalid charges")
    events = prefs.setdefault("paper_portfolio_journal", [])
    if not isinstance(events, list):
        raise ValueError("Invalid paper journal")
    row = {"slot": slot, "event": event,
           "contract": position.get("contract"),
           "quantity": position.get("quantity") if quantity is None else quantity,
           "price": price, "charges": charges, "net_pnl": pnl,
           "kind": "paper_simulation"}
    events.append(row)
    del events[:-300]
    return row


def positions_summary(prefs):
    positions = bootstrap(prefs)
    summary = []
    for slot in SLOTS:
        p = positions[slot]
        summary.append({"slot": slot, "contract": p.get("contract") or "FLAT",
                        "side": p.get("side"),
                        "quantity": int(p.get("quantity") or 0)})
    return summary
