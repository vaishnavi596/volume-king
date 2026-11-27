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


def averaging_scenarios(entry, lots, unit, levels, stop, target, target_avg):
    """Rupee view for 'no averaging' and after each owner-typed level (BUY only, same contract).

    levels: [(price, lots), ...] any order. Returns [] on invalid input. Each row:
    label, lots, qty, avg, invested, loss_at_stop, profit_at_target, target.
    """
    e, s, t = _num(entry), _num(stop), _num(target)
    try:
        q0, u = int(lots), int(unit)
    except (TypeError, ValueError):
        return []
    if None in (e, s, t) or e <= 0 or q0 <= 0 or u <= 0 or not (s < e < t):
        return []
    lv = []
    for price, n in levels or []:
        p, k = _num(price), None
        try:
            k = int(n)
        except (TypeError, ValueError):
            pass
        if p is not None and k and k > 0 and s < p < e:
            lv.append((p, k))
    lv.sort(key=lambda x: -x[0])
    ta = _num(target_avg)
    rows = []
    qty, cost = q0 * u, e * q0 * u
    def row(label, n_lots, q, c, tgt):
        avg = c / q
        return {"label": label, "lots": n_lots, "qty": q, "avg": round(avg, 2), "invested": round(c, 2),
                "loss_at_stop": round((avg - s) * q, 2),
                "target": tgt, "profit_at_target": (round((tgt - avg) * q, 2) if tgt and tgt > avg else None)}
    rows.append(row("औसत नहीं", q0, qty, cost, t))
    n_lots = q0
    for i, (p, k) in enumerate(lv, 1):
        n_lots += k
        qty += k * u
        cost += p * k * u
        rows.append(row("स्तर %d के बाद (₹%g)" % (i, p), n_lots, qty, cost, ta if ta else t))
    return rows
