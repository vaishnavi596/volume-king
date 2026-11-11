"""Transparent, candle-only screening. No broker quotes or probability claims."""
from datetime import datetime, timezone, timedelta
import math

DEFAULT_FILTERS = ["Supertrend", "EMA 9/21", "RSI 14", "MACD", "VWAP",
                   "SMC Structure", "Order Block", "Pivot Points", "FVG", "Liquidity Sweep"]
OPTION_FILTERS = ["OI Support", "OI Resistance", "OI Profile", "Max Pain"]
ALL_FILTERS = DEFAULT_FILTERS + OPTION_FILTERS + ["SMA 5/20", "Volume", "ATR 14"]

def ema(values, period):
    out = []
    alpha = 2.0 / (period + 1)
    for value in values:
        out.append(value if not out else alpha * value + (1 - alpha) * out[-1])
    return out

def analyze(bars, selected=None, timeframe="5m"):
    selected = DEFAULT_FILTERS if selected is None else selected
    # Do not evaluate candles with timestamps in the future.
    now = datetime.now(timezone.utc).timestamp()
    clean = [b for b in bars if isinstance(b, (list, tuple)) and len(b) >= 6
             and all(isinstance(b[i], (int, float)) and math.isfinite(b[i]) and b[i] > 0 for i in (0,1,2,3,4))
             and b[0] <= now + 60
             and b[2] >= max(b[1], b[4]) and b[3] <= min(b[1], b[4]) and b[2] >= b[3]
             and isinstance(b[5], (int, float)) and math.isfinite(b[5]) and b[5] >= 0]
    # Out-of-order or duplicate bars can create false crossovers and invalid freshness.
    if any(clean[i][0] <= clean[i-1][0] for i in range(1, len(clean))):
        return {"bias":"WAIT","score":0,"votes":[],"reason":"Candles out of order or duplicated",
                "count":len(clean),"timeframe":timeframe,"timestamp":None}
    # Detect missing bars only inside the same NSE session; overnight gaps are normal.
    market_tz = timezone(timedelta(hours=5, minutes=30))
    interval_seconds = {"1m":60, "3m":180, "5m":300, "15m":900, "30m":1800, "1h":3600}.get(timeframe)
    if interval_seconds is not None:
        for previous, current in zip(clean, clean[1:]):
            same_session = (datetime.fromtimestamp(previous[0], market_tz).date() ==
                            datetime.fromtimestamp(current[0], market_tz).date())
            if same_session and current[0] - previous[0] > interval_seconds * 2:
                return {"bias":"WAIT","score":0,"votes":[],"reason":"Missing candles within trading session",
                        "count":len(clean),"timeframe":timeframe,"timestamp":None}
    if len(clean)<30:
        return {"bias":"WAIT","score":0,"votes":[],"reason":"Need 30 valid candles","count":len(clean),"timeframe":timeframe,"timestamp":None}
    close=[float(b[4]) for b in clean]
    high=[float(b[2]) for b in clean]
    low=[float(b[3]) for b in clean]
    vol=[float(b[5] or 0) for b in clean]
    votes=[]
    def add(name, side, detail):
        if name in selected:votes.append({"name":name,"vote":side,"detail":detail})
    p=close[-1]
    fast=sum(close[-5:])/5;slow=sum(close[-20:])/20
    add("SMA 5/20",1 if p>fast>slow else -1 if p<fast<slow else 0,f"MA5 {fast:.2f}, MA20 {slow:.2f}")
    e9=ema(close,9)[-1];e21=ema(close,21)[-1]
    add("EMA 9/21",1 if p>e9>e21 else -1 if p<e9<e21 else 0,f"EMA9 {e9:.2f}, EMA21 {e21:.2f}")
    dif=[close[i]-close[i-1] for i in range(1,len(close))]
    g=sum(max(v,0) for v in dif[-14:]);l=sum(max(-v,0) for v in dif[-14:])
    rsi=100 if l==0 else 100-100/(1+g/l)
    add("RSI 14",1 if 52<=rsi<=70 else -1 if 30<=rsi<=48 else 0,f"RSI {rsi:.1f}")
    macd=[a-b for a,b in zip(ema(close,12),ema(close,26))]
    sig=ema(macd,9)[-1]
    add("MACD",1 if macd[-1]>sig else -1 if macd[-1]<sig else 0,f"MACD {macd[-1]:.2f}, signal {sig:.2f}")
    # Session VWAP must not blend previous days.
    # NSE/BSE trading sessions follow Asia/Kolkata, not UTC calendar dates.
    market_tz=timezone(timedelta(hours=5,minutes=30))
    last_day=datetime.fromtimestamp(clean[-1][0],market_tz).date()
    session=[b for b in clean if datetime.fromtimestamp(b[0],market_tz).date()==last_day]
    vtotal=sum(float(b[5] or 0) for b in session)
    if vtotal:
        vwap=sum((b[2]+b[3]+b[4])/3*float(b[5] or 0) for b in session)/vtotal
        add("VWAP",1 if p>vwap else -1 if p<vwap else 0,f"Session VWAP {vwap:.2f}")
    else:add("VWAP",None,"Volume unavailable")
    tr=[high[0]-low[0]]+[max(high[i]-low[i],abs(high[i]-close[i-1]),abs(low[i]-close[i-1])) for i in range(1,len(close))]
    atr=tr[0];atr_values=[]
    for t in tr:atr=(atr*13+t)/14;atr_values.append(atr)
    add("ATR 14",0,f"ATR {atr_values[-1]:.2f}; volatility, not a direction")
    upper=lower=None;trend=1
    for i in range(len(close)):
        mid=(high[i]+low[i])/2
        ub=mid+3*atr_values[i];lb=mid-3*atr_values[i]
        if upper is not None:
            ub=min(ub,upper) if close[i-1]<=upper else ub
            lb=max(lb,lower) if close[i-1]>=lower else lb
            if trend==1 and close[i]<lower:trend=-1
            elif trend==-1 and close[i]>upper:trend=1
        upper,lower=ub,lb
    add("Supertrend",trend,"ATR(14) multiplier 3; "+("UP" if trend==1 else "DOWN"))
    # Confirmed swing structure uses prior completed bars, not current bar.
    prev_high=max(high[-21:-1]);prev_low=min(low[-21:-1])
    structure=1 if p>prev_high else -1 if p<prev_low else 0
    add("SMC Structure",structure,f"20-bar break: high {prev_high:.2f}, low {prev_low:.2f}")
    # Last opposite candle before an impulse is an approximation, not institutional order evidence.
    ob=0;ob_detail="No confirmed impulse / order block"
    for i in range(len(close)-2,max(1,len(close)-18),-1):
        body=close[i]-clean[i][1]
        if close[-1]>high[i] and body<0 and close[-1]-close[i]>atr_values[-1]:
            ob=1;ob_detail=f"Bullish candidate zone {low[i]:.2f}-{high[i]:.2f}";break
        if close[-1]<low[i] and body>0 and close[i]-close[-1]>atr_values[-1]:
            ob=-1;ob_detail=f"Bearish candidate zone {low[i]:.2f}-{high[i]:.2f}";break
    add("Order Block",ob,ob_detail)
    ph=(high[-2]+low[-2]+close[-2])/3
    add("Pivot Points",1 if p>ph else -1 if p<ph else 0,f"Previous-bar pivot {ph:.2f}")
    fvg=0;fvg_detail="No recent unfilled 3-candle gap"
    for i in range(len(close)-1,max(2,len(close)-12),-1):
        if low[i]>high[i-2] and p>=high[i-2]:fvg=1;fvg_detail=f"Bullish FVG {high[i-2]:.2f}-{low[i]:.2f}";break
        if high[i]<low[i-2] and p<=low[i-2]:fvg=-1;fvg_detail=f"Bearish FVG {high[i]:.2f}-{low[i-2]:.2f}";break
    add("FVG",fvg,fvg_detail)
    sweep=1 if low[-1]<min(low[-11:-1]) and p>min(low[-11:-1]) else -1 if high[-1]>max(high[-11:-1]) and p<max(high[-11:-1]) else 0
    add("Liquidity Sweep",sweep,"10-bar wick sweep with close back inside range" if sweep else "No confirmed sweep")
    avgvol=sum(vol[-21:-1])/20
    add("Volume",1 if avgvol>0 and vol[-1]>avgvol*1.2 and p>close[-2] else -1 if avgvol>0 and vol[-1]>avgvol*1.2 and p<close[-2] else 0,f"Volume {vol[-1]:.0f}, 20-bar avg {avgvol:.0f}")
    for name in OPTION_FILTERS:
        add(name,None,"UNAVAILABLE: verified live option chain not connected")
    directional=[v for v in votes if v["vote"] in (-1,1)]
    bulls=sum(v["vote"]==1 for v in directional)
    bears=sum(v["vote"]==-1 for v in directional)
    total=bulls+bears
    agreement=max(bulls,bears)/total if total else 0
    bias="BULLISH" if bulls>=3 and agreement>=.7 else "BEARISH" if bears>=3 and agreement>=.7 else "WAIT"
    # Require actual structure or trend confirmation to avoid indicator-count inflation.
    if bias!="WAIT" and not any(v["name"] in ("Supertrend","SMC Structure","EMA 9/21") and v["vote"]==(1 if bias=="BULLISH" else -1) for v in directional):bias="WAIT"
    return {"bias":bias,"score":round(agreement*100) if bias!="WAIT" else 0,
            "votes":votes,"reason":f"{bulls} bullish / {bears} bearish; {total} directional votes (NOT success probability)",
            "count":len(clean),"timeframe":timeframe,"timestamp":clean[-1][0],
            "atr":atr_values[-1],"price":p}

def rank_candidates(candidates, max_results=5, max_age_seconds=1800):
    now=datetime.now(timezone.utc).timestamp()
    if not isinstance(max_age_seconds, (int, float)) or not math.isfinite(max_age_seconds) or max_age_seconds <= 0:
        return []
    good=[]
    for symbol, result in candidates.items():
        if not isinstance(symbol, str) or not symbol.strip():continue
        if not isinstance(result, dict) or result.get("bias") not in ("BULLISH", "BEARISH"):continue
        timestamp=result.get("timestamp")
        score=result.get("score")
        votes=result.get("votes")
        if type(result.get("count")) is not int or result["count"] < 30:continue
        if not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp):continue
        if not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 100:continue
        if not isinstance(votes, list) or not votes:continue
        if any(not isinstance(v, dict) or v.get("vote") not in (-1, 0, 1, None) for v in votes):continue
        matching_votes=sum(v["vote"] == (1 if result["bias"] == "BULLISH" else -1) for v in votes)
        directional_votes=sum(v["vote"] in (-1, 1) for v in votes)
        if matching_votes < 3 or not directional_votes or matching_votes / directional_votes < .7:continue
        # A claimed strength score cannot exceed the actual directional agreement.
        if score > round(100 * matching_votes / directional_votes) + 1:continue
        if not any(v.get("name") in ("Supertrend", "SMC Structure", "EMA 9/21") and v["vote"] == (1 if result["bias"] == "BULLISH" else -1) for v in votes):continue
        age=now-timestamp
        if age<0 or age>max_age_seconds:continue
        good.append({"symbol":symbol,**result,"age":int(age)})
    good.sort(key=lambda x:(-x["score"], -len([v for v in x["votes"] if v["vote"] in (-1,1)]), x["symbol"]))
    return good[:max_results]
