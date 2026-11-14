"""Fail-closed Dhan CE/PE open-interest metrics; never infer missing data."""
import math


class OptionMetricsUnavailable(ValueError):
    pass


def _oi(leg):
    if not isinstance(leg, dict):
        raise OptionMetricsUnavailable("Missing option leg")
    value = leg.get("oi")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise OptionMetricsUnavailable("Invalid option open interest")
    return float(value)


def calculate_option_metrics(response):
    """Require a complete strike-by-strike Dhan chain before computing metrics.

    A Dhan success envelope is not evidence of a complete or fresh option chain.
    Return calculations only; caller must separately verify expiry, underlying,
    timestamps, entitlement, and market-session freshness.
    """
    if not isinstance(response, dict) or response.get("status") != "success":
        raise OptionMetricsUnavailable("Dhan option chain not successful")
    data = response.get("data")
    chain = data.get("oc") if isinstance(data, dict) else None
    if not isinstance(chain, dict) or not 2 <= len(chain) <= 2000:
        raise OptionMetricsUnavailable("Incomplete or oversized Dhan option chain")
    strikes = []
    for raw_strike, legs in chain.items():
        try:
            strike = float(raw_strike)
        except (TypeError, ValueError):
            raise OptionMetricsUnavailable("Invalid strike") from None
        if not math.isfinite(strike) or strike <= 0 or not isinstance(legs, dict):
            raise OptionMetricsUnavailable("Invalid strike row")
        ce = _oi(legs.get("ce"))
        pe = _oi(legs.get("pe"))
        strikes.append((strike, ce, pe))
    strikes.sort()
    if any(strikes[i][0] == strikes[i - 1][0] for i in range(1, len(strikes))):
        raise OptionMetricsUnavailable("Duplicate strikes")
    total_ce = sum(ce for _, ce, _ in strikes)
    total_pe = sum(pe for _, _, pe in strikes)
    if not all(math.isfinite(v) for v in (total_ce, total_pe)) or total_ce <= 0 or total_pe <= 0:
        raise OptionMetricsUnavailable("Insufficient call open interest")
    # At candidate settlement strike S, CE intrinsic payout is max(0,S-K),
    # and PE intrinsic payout is max(0,K-S), weighted by open interest.
    payouts = [(sum(ce * max(0.0, settlement - strike) + pe * max(0.0, strike - settlement)
                    for strike, ce, pe in strikes), settlement) for settlement, _, _ in strikes]
    if not all(math.isfinite(payout) for payout, _ in payouts):
        raise OptionMetricsUnavailable("Invalid option payout")
    return {"ce_oi": total_ce, "pe_oi": total_pe, "pcr": total_pe / total_ce,
            "max_pain": min(payouts)[1], "strike_count": len(strikes),
            "freshness": "unverified", "signal_eligible": False}


def listed_atm_window(response, *, spot, wings=3):
    """Return seven listed strikes around spot, or fail closed.

    This is a read-only display extractor. Broker freshness and expiry are not
    established by a successful response; no row is a directional vote.
    """
    if type(spot) not in (int, float) or not math.isfinite(spot) or spot <= 0:
        raise OptionMetricsUnavailable("Invalid spot price")
    if type(wings) is not int or wings != 3:
        raise OptionMetricsUnavailable("Only ATM plus three listed strikes each side supported")
    if not isinstance(response, dict) or response.get("status") != "success":
        raise OptionMetricsUnavailable("Unverified option chain response")
    data = response.get("data")
    chain = data.get("oc") if isinstance(data, dict) else None
    if not isinstance(chain, dict) or not 7 <= len(chain) <= 2000:
        raise OptionMetricsUnavailable("Insufficient listed strikes")
    indexed = []
    for key, legs in chain.items():
        try:
            strike = float(key)
        except (TypeError, ValueError):
            raise OptionMetricsUnavailable("Invalid listed strike") from None
        if not math.isfinite(strike) or strike <= 0 or not isinstance(legs, dict):
            raise OptionMetricsUnavailable("Invalid listed strike row")
        indexed.append((strike, legs))
    indexed.sort(key=lambda row: row[0])
    if any(indexed[i][0] == indexed[i-1][0] for i in range(1, len(indexed))):
        raise OptionMetricsUnavailable("Duplicate listed strike")
    atm = min(range(len(indexed)), key=lambda i: (abs(indexed[i][0]-spot), indexed[i][0]))
    if atm < 3 or atm + 3 >= len(indexed):
        raise OptionMetricsUnavailable("ATM lacks three listed strikes on both sides")
    result = []
    for strike, legs in indexed[atm-3:atm+4]:
        row = {"strike": strike}
        for side in ("ce", "pe"):
            leg = legs.get(side)
            if not isinstance(leg, dict):
                raise OptionMetricsUnavailable("Missing CE/PE leg")
            oi = _oi(leg)
            row[side] = {"oi": oi}
            for field in ("volume", "last_price", "previous_oi"):
                value = leg.get(field)
                if value is None:
                    continue
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    raise OptionMetricsUnavailable("Invalid optional option leg field")
                row[side][field] = float(value)
        result.append(row)
    return {"atm": indexed[atm][0], "rows": tuple(result),
            "freshness": "unverified", "signal_eligible": False, "source": "dhan"}
