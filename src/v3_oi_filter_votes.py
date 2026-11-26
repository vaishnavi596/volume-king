"""Measured per-filter votes for the four OI filters (J4). No requests.

Each rule reads only the validated seven-strike Dhan window, the listed Max
Pain strike and the Dhan underlying price. The votes are positioning
heuristics shown on the filter rows; they are NOT part of the 13-filter T box,
and the O engine remains the only OI-based input to the five-engine quorum.

  OI Support    put wall (max PE OI): breached -> -1; held within 0.5% -> +1
  OI Resistance call wall (max CE OI): broken -> +1; capped within 0.5% -> -1
  OI Profile    window put/call OI ratio >1.2 -> +1, <0.8 -> -1
  Dhan Max Pain spot >0.2% under -> +1 (pull up), >0.2% over -> -1
"""
from math import isfinite

from five_engine import option_chain_display_context

NEAR = 0.005
PAIN_BAND = 0.002
PROFILE_BULL, PROFILE_BEAR = 1.2, 0.8


def _num(value):
    return type(value) in (int, float) and isfinite(value) and value > 0


def oi_filter_vote(name, metrics, spot):
    """Return ``(vote, detail)``; vote is -1, 0, 1 or None when not measurable."""
    if not _num(spot):
        return None, "WAIT: Dhan underlying price unavailable"
    context = option_chain_display_context(metrics)
    if not context.get("available"):
        return None, "WAIT: " + str(context.get("reason", "Dhan option window unavailable"))
    rows = context["rows"]
    if name == "OI Support":
        wall = max(rows, key=lambda r: r["pe"]["oi"])
        if wall["pe"]["oi"] <= 0:
            return None, "WAIT: no put OI in the listed window"
        strike = wall["strike"]
        if spot < strike:
            return -1, f"Put wall {strike:,.0f} breached by price"
        near = (spot - strike) / spot <= NEAR
        return (1 if near else 0), (f"Price holding above put wall {strike:,.0f}" if near
                                    else f"Put wall {strike:,.0f} below price, not tested")
    if name == "OI Resistance":
        wall = max(rows, key=lambda r: r["ce"]["oi"])
        if wall["ce"]["oi"] <= 0:
            return None, "WAIT: no call OI in the listed window"
        strike = wall["strike"]
        if spot > strike:
            return 1, f"Call wall {strike:,.0f} broken by price"
        near = (strike - spot) / spot <= NEAR
        return (-1 if near else 0), (f"Price capped under call wall {strike:,.0f}" if near
                                     else f"Call wall {strike:,.0f} above price, not tested")
    if name == "OI Profile":
        call = sum(r["ce"]["oi"] for r in rows)
        put = sum(r["pe"]["oi"] for r in rows)
        if call <= 0 or put < 0:
            return None, "WAIT: no usable call OI in the listed window"
        ratio = put / call
        vote = 1 if ratio > PROFILE_BULL else -1 if ratio < PROFILE_BEAR else 0
        return vote, f"Window put/call OI {ratio:.2f}"
    if name == "Dhan Max Pain":
        pain = metrics.get("max_pain") if isinstance(metrics, dict) else None
        if not _num(pain):
            return None, "WAIT: Max Pain strike unavailable"
        gap = (pain - spot) / spot
        vote = 1 if gap > PAIN_BAND else -1 if gap < -PAIN_BAND else 0
        return vote, f"Max Pain {pain:,.0f} vs price {spot:,.2f}"
    return None, "WAIT: not an OI filter"
