"""Read-only benchmark of actual already cached BOT KING data on the phone.

NO synthetic fixtures; no broker calls, no credential access. Missing data is typed ERROR (analysis stays ineligible).
The benchmark reports Python elapsed times, never claims Flutter raster timing.
"""
from __future__ import annotations
import math
import time
from chart_indicators import chart_indicators
from scanner_engine import analyze, DEFAULT_FILTERS
from v3_stock_diagnostics import classify_stock
from dhan_three_minute import completed_three_minute_bars

INDEXES=("NIFTY","BANKNIFTY","SENSEX")

def benchmark_cached_capacity(equities, quotes, histories, generation, requested_equities):
    if requested_equities not in (51,70):
        raise ValueError("Only 51 and 70 equity tests are supported")
    start=time.perf_counter()
    dedup=list(dict.fromkeys(s for s in equities if isinstance(s,str) and s and s not in INDEXES))
    selected=dedup[:requested_equities]
    names=list(INDEXES)+selected
    expected=requested_equities+3
    missing_equity_count=max(0,requested_equities-len(selected))
    after_inventory=time.perf_counter()
    # V3 derives completed 3m Watchlist bars from Dhan 1m, rather than
    # necessarily storing a separate chart_snapshots[(sym,"3m",gen)] record.
    # Reproduce the same exact session-aligned 3m derivation locally; do not
    # mislabel a missing stored 3m slot as missing actual 3m evidence.
    histories=dict(histories)
    derived_3m=0
    for sym in names:
        target=(sym,"3m",generation)
        if target in histories and (histories[target] or {}).get("bars"):
            continue
        source=histories.get((sym,"1m",generation)) or {}
        if source.get("source")!="Dhan" or source.get("_scanner_timeframe")!="1m":
            continue
        bars=completed_three_minute_bars(source.get("bars"),now_epoch=time.time())
        if len(bars)>=2:
            histories[target]=dict(source,bars=[list(row) for row in bars],
                                   _scanner_timeframe="3m",historical=True,
                                   live_verified=False,freshness="historical_unverified")
            derived_3m+=1
    after_derive=time.perf_counter()
    quote_present=0
    quote_missing=[]
    coverage={"1m":0,"3m":0,"5m":0}
    missing_by_frame={"1m":[],"3m":[],"5m":[]}
    for symbol in names:
        q=quotes.get(symbol) or {}
        p=q.get("price") if isinstance(q,dict) else None
        if isinstance(q,dict) and q.get("source")=="Dhan" and type(p) in (float,int) and math.isfinite(p) and p>0:
            quote_present+=1
        else:
            quote_missing.append(symbol)
        for frame in coverage:
            h=histories.get((symbol,frame,generation)) or {}
            bars=h.get("bars") if isinstance(h,dict) else None
            if (isinstance(h,dict) and h.get("source")=="Dhan"
                    and h.get("_scanner_timeframe",frame)==frame
                    and isinstance(bars,(list,tuple)) and len(bars)>=2):
                coverage[frame]+=1
            else:
                missing_by_frame[frame].append(symbol)
    after_coverage=time.perf_counter()
    chart_available=0
    scanner_technical_available=0
    technical_wait=0
    errors=[]
    for symbol in names:
        frame="1m" if symbol in INDEXES else "3m"
        row=histories.get((symbol,frame,generation)) or {}
        bars=row.get("bars") if isinstance(row,dict) else None
        if not bars or row.get("source")!="Dhan" or row.get("_scanner_timeframe",frame)!=frame:
            technical_wait+=1
            continue
        try:
            chart=chart_indicators(bars)
            scan=analyze(bars,selected=DEFAULT_FILTERS,timeframe=frame)
            if chart.get("status")=="AVAILABLE":chart_available+=1
            if scan.get("reason") not in ("Need 30 valid candles","Invalid or future candle in series","Candles out of order or duplicated","Irregular candle spacing within trading session"):
                if scan.get("count",0)>=30:scanner_technical_available+=1
                else:technical_wait+=1
            else:technical_wait+=1
        except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError) as exc:
            errors.append({"symbol":symbol,"stage":"TECHNICAL","type":type(exc).__name__})
            technical_wait+=1
    after_technical=time.perf_counter()
    # Audit each independent stock without blocking peers. Errors identify the
    # missing/bad cache stage; they do not assert broker transport failure.
    stock_diagnostics=[classify_stock(sym,quotes.get(sym),histories,generation)
                       for sym in names]
    incomplete_count=sum(row["state"]=="ERROR" for row in stock_diagnostics)
    after_diagnostics=time.perf_counter()
    def ms(t1,t2):return round((t2-t1)*1000,3)
    return {
        "requested_equities":requested_equities,
        "requested_instruments":expected,
        "selected_equities":len(selected),
        "unselected_equity_slots":missing_equity_count,
        "observed_instruments":len(names),
        "dhan_quote_present":quote_present,
        "quote_missing_count":len(quote_missing)+missing_equity_count,
        "quote_missing_sample":quote_missing[:12],
        "history_presence":coverage,
        "derived_3m_from_valid_1m":derived_3m,
        "history_missing_sample":{tf:missing_by_frame[tf][:6] for tf in coverage},
        "technical_chart_available":chart_available,
        "technical_scanner_analyzed":scanner_technical_available,
        "technical_wait":technical_wait+missing_equity_count,
        "five_live_options_filters":"NOT MEASURED — requires verified live option evidence",
        "ui_raster_ms":"UNMEASURED — Python timers cannot see Flutter frame completion",
        "errors":errors[:12],
        "stock_error_count":incomplete_count+missing_equity_count,
        "stock_errors":[{"symbol":row["symbol"],"codes":row["error_codes"]}
                        for row in stock_diagnostics if row["state"]=="ERROR"][:73],
        "stock_states":stock_diagnostics,
        "recovery_hint":"On matching data arrival rerun local test; other symbols continue. Doctor compares active errors to resolved.",

        "elapsed_ms":{
            "inventory":ms(start,after_inventory),
            "completed_3m_derivation":ms(after_inventory,after_derive),
            "cache_presence":ms(after_derive,after_coverage),
            "real_cached_technical_compute":ms(after_coverage,after_technical),
            "stock_error_classification":ms(after_technical,after_diagnostics),
            "total_python":ms(start,after_diagnostics)},
        "source":"existing Dhan cache only, no fake data, no network calls",
        "note":"Partial cache does not imply app failure; market may be closed or bars absent."
    }
