"""V2 manual PAPER risk preview using the unmodified V1 pure paper engine.

No broker API, orders, automated execution, or market-price reads.
"""
from paper_engine import finite, levels, risk_check


def preview_manual_paper_risk(side, entry, quantity, stop_pct, target_pct,
                              capital, max_risk, risk_pct):
    if type(side) is not str or side not in ("BUY", "SELL"):
        raise ValueError("Invalid paper direction")
    if isinstance(quantity, bool):
        raise ValueError("Paper quantity must be a whole number")
    quantity = int(quantity)
    if not 1 <= quantity <= 100000:
        raise ValueError("Invalid paper quantity")
    entry = finite(entry, "Manual paper entry", .000001)
    capital = finite(capital, "Paper capital", .000001)
    max_risk = finite(max_risk, "Paper risk limit", .000001)
    risk_pct = finite(risk_pct, "Paper risk percent", .000001)
    stop, target = levels(side, entry, stop_pct, target_pct)
    planned = risk_check(entry, quantity, stop, capital, capital,
                         max_risk, risk_pct)
    return {
        "status": "PAPER PREVIEW ONLY",
        "side": side,
        "entry": entry,
        "quantity": quantity,
        "stop": stop,
        "target": target,
        "planned_risk": planned,
        "target_gross_gain": abs(target - entry)*quantity,
        "orders_enabled": False,
        "live_verified": False,
    }
