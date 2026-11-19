"""V2 device-only manual PAPER simulation ledger; never sends orders.

A confirmed simulated position requires a previously validated saved local
risk plan. Exit prices are entered manually; P&L is hypothetical, not sourced
from Dhan/Oracle. Entries remain session-only and carry no broker credentials.
"""
from math import isfinite
from local_paper_slots import SLOTS, _validate_preview

class PaperLedgerError(ValueError):
    pass

class ManualPaperLedger:
    def __init__(self):
        self._open = {}
        self._closed = []

    def open_simulation(self, slot, preview, *, confirmed=False):
        if slot not in SLOTS or type(slot) is not str or confirmed is not True:
            raise PaperLedgerError("Explicit PAPER-only confirmation required")
        if slot in self._open:
            raise PaperLedgerError("Close existing simulated position first")
        if preview is None:
            raise PaperLedgerError("Save a validated PAPER risk plan first")
        try:
            plan = _validate_preview(preview)
        except (ValueError, TypeError, KeyError) as exc:
            raise PaperLedgerError("Invalid saved PAPER risk plan") from None
        self._open[slot] = plan
        return True

    def close_simulation(self, slot, manual_exit, *, confirmed=False):
        if slot not in SLOTS or type(slot) is not str or confirmed is not True:
            raise PaperLedgerError("Explicit PAPER-only confirmation required")
        if slot not in self._open:
            raise PaperLedgerError("No simulated position in this slot")
        try:
            exit_price = float(manual_exit)
        except (TypeError, ValueError, OverflowError):
            raise PaperLedgerError("Valid manually entered exit required") from None
        if not isfinite(exit_price) or exit_price <= 0:
            raise PaperLedgerError("Positive finite exit required")
        plan = self._open.pop(slot)
        direction = 1 if plan["side"] == "BUY" else -1
        pnl = (exit_price - plan["entry"]) * plan["quantity"] * direction
        record = {"slot": slot, "side": plan["side"],
                  "entry": plan["entry"], "exit": exit_price,
                  "quantity": plan["quantity"], "paper_pnl": round(pnl, 2),
                  "source": "manual_simulation", "orders_enabled": False,
                  "verified_live": False}
        self._closed.append(record)
        self._closed = self._closed[-50:]
        return dict(record)

    def open_rows(self):
        return tuple((slot, dict(self._open[slot]) if slot in self._open else None)
                     for slot in SLOTS)

    def closed_rows(self):
        return tuple(dict(row) for row in self._closed)

    def clear_closed(self):
        self._closed.clear()
