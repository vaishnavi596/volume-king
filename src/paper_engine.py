"""Deterministic manual-mark PAPER execution only. No network/order API."""
import math
from datetime import date,datetime

def finite(value,label="value",minimum=0):
    n=float(value)
    if not math.isfinite(n) or n<minimum:raise ValueError(label+" must be finite and at least "+str(minimum))
    return n
def levels(side,entry,stop_pct,target_pct):
    entry=finite(entry,"Entry",.000001);stop_pct=finite(stop_pct,"Stop",.000001);target_pct=finite(target_pct,"Target",.000001)
    if side not in ("BUY","SELL") or stop_pct>=100 or (side=="SELL" and target_pct>=100):raise ValueError("Invalid side or stop")
    sign=1 if side=="BUY" else -1
    return entry*(1-sign*stop_pct/100),entry*(1+sign*target_pct/100)
def pnl(side,entry,exit_price,quantity,fees=0):
    if side not in ("BUY","SELL"):raise ValueError("Invalid side")
    quantity=finite(quantity,"Quantity",1);entry=finite(entry,"Entry",.000001)
    mark=finite(exit_price,"Exit");fees=finite(fees,"Charges")
    gross=(mark-entry)*quantity*(1 if side=="BUY" else -1)
    return gross,gross-fees
def validate_expiry(value,today=None):
    d=datetime.strptime(value.strip(),"%Y-%m-%d").date()
    if d<(today or date.today()):raise ValueError("Expired contract cannot be entered")
    return d
def risk_check(entry,quantity,stop_price,capital,max_notional,max_risk,risk_pct):
    entry=finite(entry,"Entry",.000001);quantity=finite(quantity,"Quantity",1)
    capital=finite(capital,"Paper capital",.000001)
    max_notional=finite(max_notional,"Notional limit",.000001)
    max_risk=finite(max_risk,"Risk limit",.000001);risk_pct=finite(risk_pct,"Risk percent",.000001)
    if risk_pct>100:raise ValueError("Risk percent must not exceed 100")
    planned=abs(entry-finite(stop_price,"Stop"))*quantity
    if entry*quantity>min(capital,max_notional)+1e-8:raise ValueError("Paper notional/capital limit exceeded; this is not broker margin")
    if planned>min(max_risk,capital*risk_pct/100)+1e-8:raise ValueError("Per-trade planned-risk limit exceeded")
    return planned
def evaluate_mark(position,mark,settings):
    if not position.get("side"):return {"action":"HOLD","position":dict(position)}
    mark=finite(mark,"Manual mark",.000001);p=dict(position)
    side=p["side"];entry=finite(p["entry"],"Entry",.000001)
    stop,target=levels(side,entry,p.get("stop_loss_pct",2),p.get("target_pct",4))
    stop=p.get("stop_price",stop);target=p.get("target_price",target)
    best=max(float(p.get("best_mark",entry)),mark) if side=="BUY" else min(float(p.get("best_mark",entry)),mark)
    p["best_mark"]=best
    if settings.get("trailing"):
        step=finite(settings.get("trail_pct",2),"Trail",.000001)
        if step>=100:raise ValueError("Trail must be below 100%")
        stop=max(stop,best*(1-step/100)) if side=="BUY" else min(stop,best*(1+step/100))
    p["stop_price"]=stop;p["target_price"]=target
    stopped=mark<=stop if side=="BUY" else mark>=stop
    reached=mark>=target if side=="BUY" else mark<=target
    if stopped:return {"action":"EXIT","reason":"Paper stop/trailing stop","position":p}
    if reached:return {"action":"EXIT","reason":"Paper target","position":p}
    gain=(mark/entry-1)*(1 if side=="BUY" else -1)*100
    unit=int(p.get("unit_size",1));qty=int(p["quantity"])
    if unit<1 or qty<1 or qty%unit:raise ValueError("Invalid whole-unit paper quantity")
    if settings.get("partial") and not p.get("partial_done") and gain>=finite(settings.get("partial_trigger",2),"Partial trigger",.000001):
        fraction=finite(settings.get("partial_pct",50),"Partial fraction",.000001)
        if fraction>=100:raise ValueError("Partial fraction must be below 100")
        close_qty=int(qty*fraction/100)//unit*unit
        if 0<close_qty<qty:return {"action":"PARTIAL","quantity":close_qty,"position":p,"reason":"Paper partial profit"}
    if (side=="BUY" and settings.get("average") and int(p.get("additions",0))<int(settings.get("max_additions",1))
            and mark<=float(p.get("last_add_price",entry))*(1-finite(settings.get("dip_pct",5),"Dip",.000001)/100)):
        add_qty=int(settings.get("add_units",1))*unit
        if add_qty<=0 or qty+add_qty>int(settings.get("max_units",2))*unit:raise ValueError("Maximum total quantity exceeded")
        avg=(entry*qty+mark*add_qty)/(qty+add_qty)
        # Averaging must never widen the original stop.
        new_stop=max(stop,levels(side,avg,p.get("stop_loss_pct",2),p.get("target_pct",4))[0])
        p.update(entry=avg,quantity=qty+add_qty,additions=int(p.get("additions",0))+1,last_add_price=mark,stop_price=new_stop,
                 target_price=levels(side,avg,p.get("stop_loss_pct",2),p.get("target_pct",4))[1])
        return {"action":"ADD","position":p,"quantity":add_qty,"reason":"Paper averaging; stop not widened"}
    return {"action":"HOLD","position":p,"reason":"Within paper limits"}
