"""Preserve last valid Dhan candles across missing/partial historical refreshes.

Display-only history retention. Never invent exchange-live timestamps or a quote.
"""
from math import isfinite


def _valid_bars(rows, *, minimum=30):
    if not isinstance(rows,(list,tuple)) or len(rows)<minimum:
        return False
    previous=None
    for row in rows:
        if not isinstance(row,(list,tuple)) or len(row)<6:
            return False
        try:
            ts,op,hi,lo,cl,vol=row[:6]
            vals=(float(ts),float(op),float(hi),float(lo),float(cl),0.0 if vol is None else float(vol))
        except (TypeError,ValueError,OverflowError):
            return False
        if not all(isfinite(v) for v in vals):
            return False
        t,o,h,l,c,v=vals
        if min(t,o,h,l,c)<=0 or v<0 or l>min(o,c) or h<max(o,c) or previous is not None and t<=previous:
            return False
        previous=t
    return True


def valid_candle_history(rows):
    """Enough ordered OHLCV bars to support completed-candle filter analysis."""
    return _valid_bars(rows)


def retain_candle_history(incoming,previous,*,provider="Dhan"):
    """Keep a valid previous history if a same-provider new history is unusable.

    The return is always HISTORICAL / unverified if fallback is applied.
    No old data may be promoted as a fresh quote, and a cross-provider
    history must never be reused as the selected Dhan source.
    """
    new=incoming if isinstance(incoming,dict) else {}
    prior=previous if isinstance(previous,dict) else {}
    if new.get("source")!=provider or prior.get("source")!=provider:
        return dict(new)
    new_bars=new.get("bars")
    old_bars=prior.get("bars")
    if not _valid_bars(old_bars):
        return dict(new)
    # A recent Dhan refresh may contain just 2–4 completed candles. Revise
    # matching timestamps inside the last four retained bars without dropping
    # earlier valid history. Never accept isolated/gapped or cross-TF rows.
    if (isinstance(new_bars,(list,tuple)) and 2<=len(new_bars)<=4
            and _valid_bars(new_bars,minimum=2)
            and new.get("_scanner_timeframe")==prior.get("_scanner_timeframe")):
        old_index={row[0]:i for i,row in enumerate(old_bars)}
        recent={row[0] for row in old_bars[-4:]}
        incoming_ts={row[0] for row in new_bars}
        if (incoming_ts.issubset(recent) and len(incoming_ts)==len(new_bars)
                and [old_index[row[0]] for row in new_bars]
                ==list(range(old_index[new_bars[0][0]],old_index[new_bars[0][0]]+len(new_bars)))):
            merged=[list(row) for row in old_bars]
            for row in new_bars:
                merged[old_index[row[0]]]=list(row)
            revised=dict(new,bars=merged,historical=True,live_verified=False,
                         freshness="historical_unverified",
                         candle_fetched_at=new.get("candle_fetched_at",0),
                         _candle_partial_revised=True)
            return revised
    if _valid_bars(new_bars):
        if new_bars[-1][0]>=old_bars[-1][0]:
            return dict(new)
        # A provider's older historical window must not discard newer bars.
    # Preserve only the candle series; an independently verified quote LTP
    # and its source/freshness metadata are handled by the quote batch path.
    retained=dict(new,bars=list(old_bars),candle_fetched_at=prior.get("candle_fetched_at",0),
                  historical=True,cached=True,freshness="historical_unverified",
                  live_verified=False,_candle_retained=True)
    return retained

def retain_last_filter_votes(incoming,previous,*,selected_filters,provider="Dhan"):
    """Keep historical directional votes when a refresh has no usable analysis.

    Never reuse a different filter configuration, provider or a vote lacking
    the original candle timestamp. No live signal, score or trade eligibility.
    """
    new=dict(incoming) if isinstance(incoming,dict) else {}
    old=previous if isinstance(previous,dict) else {}
    if new.get("source")!=provider or old.get("source")!=provider:
        return new
    votes=new.get("votes") or ()
    if not isinstance(votes, (list, tuple)):
        votes = ()
    if any(isinstance(row,dict) and type(row.get("vote")) is int
           and row["vote"] in (-1,1) for row in votes):
        return new
    prior_votes=old.get("votes") or ()
    if not isinstance(prior_votes, (list, tuple)):
        return new
    selected=set(selected_filters)
    prior_names={v.get("name") for v in prior_votes if isinstance(v,dict)}
    if not selected or prior_names!=selected:
        return new
    if not any(isinstance(row,dict) and type(row.get("vote")) is int
               and row["vote"] in (-1,1) for row in prior_votes):
        return new
    timestamp=old.get("timestamp")
    if type(timestamp) not in (int,float) or not isfinite(timestamp) or timestamp<=0:
        return new
    new.update(votes=list(prior_votes),timestamp=timestamp,
               historical=True,live_verified=False,freshness="unverified",
               bias="WAIT",score=0,_last_votes_retained=True,
               reason="Last valid completed-candle filter votes retained as HIST; current analysis unavailable")
    return new
