"""B248: pure maths for the friendly option order ticket (no I/O, no orders).

BUY: stop below entry, target above. SELL: mirrored. Money is premium x units.
"""
import math

def _num(x):
    try:
        v = float(str(x).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None

def price_from_pct(entry, pct, side, kind):
    """kind 'sl' or 'tg'. Returns price or None."""
    e, p = _num(entry), _num(pct)
    if e is None or p is None or e <= 0 or p <= 0:
        return None
    sign = 1 if side == "BUY" else -1
    move = -sign if kind == "sl" else sign
    price = e * (1 + move * p / 100.0)
    return round(price, 2) if price > 0 else None

def pct_from_price(entry, price, side, kind):
    """Percent distance in the correct direction; None if price is on the wrong side."""
    e, q = _num(entry), _num(price)
    if e is None or q is None or e <= 0 or q <= 0:
        return None
    sign = 1 if side == "BUY" else -1
    move = -sign if kind == "sl" else sign
    pct = (q - e) / e * 100.0 * move
    return round(pct, 2) if pct > 0 else None

def ticket_summary(entry, side, lots, unit, sl_price, tg_price):
    """Rupee view. Every field None when inputs are invalid."""
    e, q, u = _num(entry), None, None
    try:
        q = int(lots); u = int(unit)
    except (TypeError, ValueError):
        return {"valid": False, "reason": "lots/unit"}
    if e is None or e <= 0 or q <= 0 or u <= 0:
        return {"valid": False, "reason": "entry/lots/unit"}
    qty = q * u
    sl, tg = _num(sl_price), _num(tg_price)
    sign = 1 if side == "BUY" else -1
    out = {"valid": True, "qty": qty, "invested": round(e * qty, 2),
           "max_loss": round(e * qty, 2) if side == "BUY" else None,
           "loss": None, "profit": None, "rr": None, "sl_ok": False, "tg_ok": False}
    if sl is not None and sl > 0 and (sl - e) * sign < 0:
        out["sl_ok"] = True
        out["loss"] = round(abs(e - sl) * qty, 2)
    if tg is not None and tg > 0 and (tg - e) * sign > 0:
        out["tg_ok"] = True
        out["profit"] = round(abs(tg - e) * qty, 2)
    if out["loss"] and out["profit"]:
        out["rr"] = round(out["profit"] / out["loss"], 1)
    return out
