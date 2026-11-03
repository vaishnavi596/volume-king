import flet as ft
import json
import traceback
import asyncio
import urllib.request
import urllib.parse
from scanner_engine import DEFAULT_FILTERS, ALL_FILTERS, analyze, rank_candidates
from datetime import datetime, date, timedelta
from pathlib import Path

BG="#080F18"; PANEL="#102735"; PANEL2="#12313E"; GOLD="#E9B949"; GREEN="#16C784"; RED="#F05270"; WHITE="#EAF1F6"; MUTED="#A9BBC5"
STATE=Path.home()/".bot_king_settings.json"

def app_main(page:ft.Page):
    page.title="BOT KING"; page.theme_mode=ft.ThemeMode.DARK; page.bgcolor=BG; page.padding=0; page.spacing=0
    page.window_width=420; page.window_height=850
    prefs={"mode":"Paper","stop_loss":2.0,"target":4.0,"max_trades":2,"confidence":75,"source":"Yahoo Finance","api_url":"","api_key":""}
    try:
        if STATE.exists(): prefs.update(json.loads(STATE.read_text()))
    except Exception: pass
    try:
        stored=page.client_storage.get("bot_king_preferences")
        if isinstance(stored,dict):prefs.update(stored)
    except Exception:pass
    quotes={}
    candles={}
    market_status="Connecting Yahoo Finance…"
    symbols_yahoo={"NIFTY":"^NSEI","NIFTY 50":"^NSEI","BANKNIFTY":"^NSEBANK","BANK NIFTY":"^NSEBANK","SENSEX":"^BSESN","RELIANCE":"RELIANCE.NS","HDFCBANK":"HDFCBANK.NS","ICICIBANK":"ICICIBANK.NS","TCS":"TCS.NS","INFY":"INFY.NS","BHARTIARTL":"BHARTIARTL.NS","SBIN":"SBIN.NS","ITC":"ITC.NS"}
    def get_yahoo(ticker,interval="5m",range_="1d"):
        code=symbols_yahoo.get(ticker,ticker+".NS")
        url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(code,safe="")+"?interval="+interval+"&range="+range_
        request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (BOT KING Market Preview)","Accept":"application/json"})
        with urllib.request.urlopen(request,timeout=9) as response:
            data=json.load(response)["chart"]["result"][0]
        meta=data["meta"]
        vals=data["indicators"]["quote"][0]
        timestamps=data.get("timestamp",[])
        bars=[(t,o,h,l,cl,v) for t,o,h,l,cl,v in zip(timestamps,vals["open"],vals["high"],vals["low"],vals["close"],vals["volume"]) if None not in (o,h,l,cl)]
        price=meta.get("regularMarketPrice")
        previous=meta.get("chartPreviousClose") or meta.get("previousClose")
        change=((price/previous-1)*100) if price is not None and previous else None
        return {"price":price,"change":change,"high":meta.get("regularMarketDayHigh"),"low":meta.get("regularMarketDayLow"),"bars":bars,"time":datetime.now().strftime("%H:%M")}
    def save():
        # Android-friendly persistent preferences; never persist broker secrets.
        safe={k:v for k,v in prefs.items() if k not in ("api_key","api_secret","access_token","password","totp")}
        errors=[]
        try:
            page.client_storage.set("bot_king_preferences",safe)
            return True
        except Exception as exc:errors.append(str(exc))
        try:
            STATE.write_text(json.dumps(safe))
            return True
        except Exception as exc:errors.append(str(exc))
        return False
    def txt(s,size=14,color=WHITE,bold=False):
        return ft.Text(str(s),size=size,color=color,weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL)
    def card(*children):
        return ft.Container(content=ft.Column(list(children),spacing=6),bgcolor=PANEL,border_radius=12,padding=10,border=ft.border.all(1,"#79652F"))
    def heading(s):return txt(s,19,WHITE,True)
    def pill(s,selected=False):
        return ft.Container(content=txt(s,12,BG if selected else MUTED,selected),bgcolor=GOLD if selected else PANEL2,padding=ft.padding.symmetric(12,8),border_radius=20)
    def note(s):return txt(s,12,MUTED)
    def unavailable(s):return txt("DATA UNAVAILABLE — "+s,13,RED)
    def quote_price(sym):
        q=quotes.get(sym)
        return f'{q["price"]:,.2f}' if q and q.get("price") is not None else "—"
    def quote_change(sym):
        q=quotes.get(sym)
        v=q.get("change") if q else None
        return f'{v:+.2f}%' if v is not None else "—"
    def price_color(sym):
        q=quotes.get(sym)
        v=q.get("change") if q else None
        return GREEN if v is not None and v>=0 else RED if v is not None else MUTED
    def tiny_chart(sym):
        q=quotes.get(sym) or {}
        bars=q.get("bars") or []
        values=[b[4] for b in bars[-30:]]
        if len(values)<2:return note("Chart unavailable")
        lo,hi=min(values),max(values)
        spread=max(hi-lo,.001)
        points=[ft.LineChartDataPoint(i,(v-lo)/spread*100) for i,v in enumerate(values)]
        return ft.LineChart(data_series=[ft.LineChartData(data_points=points,stroke_width=2,color=price_color(sym),curved=False)],min_x=0,max_x=len(points)-1,min_y=-5,max_y=105,left_axis=ft.ChartAxis(labels_size=0),bottom_axis=ft.ChartAxis(labels_size=0),right_axis=ft.ChartAxis(labels_size=0),top_axis=ft.ChartAxis(labels_size=0),border=ft.border.all(0,"#000000"),expand=True)

    def section(title,child):return card(txt(title,15,GOLD,True),child)
    scan_shared={"direction":"WAIT","basis":"Awaiting automatic scan","tf":"—","symbol":"NIFTY"}
    top5_candidates=[]
    top5_last_update=["—"]
    dashboard_index=["NIFTY"]
    dashboard_tool=[""]
    def dashboard_index_set(name):
        dashboard_index[0]=name
        select(0)
    def dashboard_tool_open(name):
        dashboard_tool[0]=name
        if name=="Scanner":select(3)
        elif name=="Paper Trade":select(2)
        elif name=="OI Data":select(1)
        else:select(0)
    def open_candidate_chart(symbol):
        scan_symbol.value=symbol
        select(3)
        trigger_scan()
    def dashboard():
        def index(name):
            return ft.Container(content=ft.Column([txt(name,13,MUTED,True),txt(quote_price(name),16,GOLD,True),txt(quote_change(name),11,price_color(name),True)]),bgcolor=PANEL2,border_radius=12,padding=9,expand=True)
        return [section("AI AUTO SCANNER • "+scan_shared["direction"],ft.Column([note(scan_shared["symbol"]+" • "+scan_shared["tf"]+" candles"),note(scan_shared["basis"]),note("5m signal is not confirmed by 15m/1h; OI/PCR/News unavailable")],spacing=4)),dashboard_positions(),section("AI BEST SETUP",note("WAIT • Live option premium, liquidity and expiry not verified")),section("TOP 5 • MULTI-FILTER WATCH",ft.Column(
                [note("Updated "+top5_last_update[0]+" • 5m candle ranking using active scanner filters; NOT a win probability")]
                + ([ft.Container(content=ft.Column([txt(x["symbol"]+" • "+x["bias"]+" • "+str(x["score"])+"% votes",12,GREEN if x["bias"]=="BULLISH" else RED,True),note("5m • "+str(x["age"])+"s old • "+x["reason"]),note("Tap to open chart")],spacing=2),on_click=lambda e,s=x["symbol"]:open_candidate_chart(s),bgcolor=PANEL2,padding=9,border_radius=8) for x in top5_candidates]
                   if top5_candidates else [note("WAIT • no fresh qualified candidates; not a trade guarantee")])
            ,spacing=6)),section("MARKET OVERVIEW",ft.Column([ft.Row([ft.Container(content=txt(x,11,MUTED,True),width=100),ft.Container(content=txt(quote_price(x),13,GOLD,True),expand=True),txt(quote_change(x),11,price_color(x),True)]) for x in ["NIFTY","BANKNIFTY","SENSEX"]])),section("API STATUS",note(market_status+" • Broker/Option Chain/News disconnected")),section("Tools",ft.Row([ft.ElevatedButton(x,on_click=lambda e,v=x:dashboard_tool_open(v)) for x in ["OI Data","Scanner","Paper Trade"]],wrap=True))]

    search=ft.TextField(label="Search in selected list",hint_text="e.g. RELIANCE",expand=True,border_color="#294158",color=WHITE,bgcolor=PANEL2)
    watch_symbols=["RELIANCE","HDFCBANK","ICICIBANK","TCS","INFY","BHARTIARTL","SBIN","ITC","LT","AXISBANK","KOTAKBANK","HINDUNILVR","BAJFINANCE","BAJAJFINSV","MARUTI","M&M","TITAN","SUNPHARMA","ULTRACEMCO","ASIANPAINT","NTPC","POWERGRID","TATAMOTORS","TATASTEEL","JSWSTEEL","HCLTECH","WIPRO","TECHM","NESTLEIND","HINDALCO","ONGC","COALINDIA","ADANIENT","ADANIPORTS","BEL","TRENT","EICHERMOT","GRASIM","CIPLA","DRREDDY","APOLLOHOSP","DIVISLAB","SBILIFE","HDFCLIFE","BAJAJ-AUTO","HEROMOTOCO","BRITANNIA","INDUSINDBK","SHRIRAMFIN","BPCL"]
    watch_groups=[list(prefs.get("watchlist_"+str(i),watch_symbols if i==1 else [])) for i in range(1,6)]
    active_watch=[0]
    watch_list=ft.Column(spacing=8)
    selected_watch=[""]
    watch_filter=["All"]
    add_symbol=ft.TextField(label="Add NSE symbol",hint_text="e.g. HDFCBANK",expand=True)
    feedback=txt("",12,MUTED)
    def store_watch():
        for i,group in enumerate(watch_groups,1):prefs["watchlist_"+str(i)]=list(group)
        return save()
    def all_watch_symbols():
        return list(dict.fromkeys(sym for group in watch_groups for sym in group))
    def change_watch(i):
        active_watch[0]=i
        watch_filter[0]="All"
        search.value=""
        feedback.value=""
        select(1)
    async def validate_and_add(sym):
        try:
            q=await asyncio.to_thread(get_yahoo,sym)
            if q.get("price") is None:raise ValueError("No market price")
            quotes[sym]=q
        except Exception:
            feedback.value="Quote not verified. Check symbol, internet or provider limits; not added."
            page.update()
            return
        if sym not in watch_groups[active_watch[0]]:
            watch_groups[active_watch[0]].append(sym)
            store_watch()
        if sym not in [o.key for o in chain_symbol.options]:
            chain_symbol.options.append(ft.dropdown.Option(sym))
        feedback.value=sym+" added and saved to List "+str(active_watch[0]+1)
        add_symbol.value=""
        select(1)
    def add_watch(e):
        sym=(add_symbol.value or "").strip().upper().removesuffix(".NS")
        if not sym or len(sym)>25 or not all(c.isalnum() or c in "-&." for c in sym):
            feedback.value="Enter a valid NSE ticker (letters, numbers, -, &, .)."
        elif sym in watch_groups[active_watch[0]]:
            feedback.value="Already in this list."
        else:
            feedback.value="Checking market symbol..."
            page.run_task(validate_and_add,sym)
        page.update()
    def set_filter(v):
        watch_filter[0]=v
        select(1)
    def open_stock(sym):
        selected_watch[0]=sym
        if sym not in [o.key for o in symbol.options]:
            symbol.options.append(ft.dropdown.Option(sym))
        symbol.value=sym
        chart_tab[0]="Chart"
        select(2)
        page.run_task(load_chart)
    def remove_stock(sym):
        group=watch_groups[active_watch[0]]
        if sym in group:
            group.remove(sym)
            store_watch()
            feedback.value=sym+" removed from List "+str(active_watch[0]+1)
        select(1)
    def fill_watch(_=None):
        watch_list.controls.clear()
        visible_count=0
        for sym in watch_groups[active_watch[0]]:
            if search.value and search.value.upper() not in sym:continue
            change=(quotes.get(sym) or {}).get("change")
            direction="Bullish" if change is not None and change>0 else "Bearish" if change is not None and change<0 else "Neutral"
            if watch_filter[0]!="All" and watch_filter[0]!=direction:continue
            visible_count+=1
            watch_list.controls.append(ft.Row([
                ft.Container(content=ft.Row([ft.Icon(ft.Icons.CANDLESTICK_CHART,color=GOLD,size=20),ft.Column([txt(sym,12,WHITE,True),note(direction)],expand=True,spacing=0),ft.Column([txt(quote_price(sym),13,price_color(sym),True),txt(quote_change(sym),10,price_color(sym))],horizontal_alignment=ft.CrossAxisAlignment.END)],spacing=8),bgcolor=PANEL,border_radius=9,padding=9,expand=True,on_click=lambda e,v=sym:open_stock(v)),
                ft.IconButton(icon=ft.Icons.CLOSE,icon_color=RED,tooltip="Remove from this list",on_click=lambda e,v=sym:remove_stock(v))
            ],spacing=2))
        if visible_count==0:
            message="No matching stocks found. Clear search to show this list." if search.value or watch_filter[0]!="All" else "This watchlist is empty. Add a stock below."
            watch_list.controls.append(note(message))
        page.update()
    search.on_change=fill_watch
    def clear_watch_search(e):
        search.value=""
        fill_watch()
    def watchlist():
        fill_watch()
        return [heading("Watchlist • 5 Lists"),
            ft.Row([ft.Container(content=ft.TextButton("List "+str(i+1),on_click=lambda e,k=i:change_watch(k),style=ft.ButtonStyle(color=GOLD if active_watch[0]==i else MUTED,padding=2)),expand=True) for i in range(5)],spacing=0),
            note("List "+str(active_watch[0]+1)+" • "+str(len(watch_groups[active_watch[0]]))+" symbols • tap a row for details"),
            ft.Row([search,ft.IconButton(icon=ft.Icons.CLOSE,tooltip="Clear search",on_click=clear_watch_search)],spacing=2),ft.Row([ft.TextButton(text=n,on_click=lambda e,v=n:set_filter(v),style=ft.ButtonStyle(color=GOLD if watch_filter[0]==n else MUTED)) for n in ["All","Bullish","Bearish","Neutral"]],scroll=ft.ScrollMode.AUTO),
            ft.Row([add_symbol,ft.ElevatedButton("Add",on_click=add_watch,bgcolor=GOLD,color=BG)]),feedback,
            note(market_status+" • Quotes may be delayed"),watch_list]
    symbol=ft.Dropdown(label="Symbol",value=prefs.get("chart_symbol","NIFTY"),options=[ft.dropdown.Option(x) for x in ["NIFTY","BANKNIFTY","SENSEX"]],expand=True)
    timeframe=ft.Dropdown(label="Timeframe",value=prefs.get("chart_timeframe","5m"),options=[ft.dropdown.Option(x) for x in ["1m","5m","15m","1h","1D"]],width=120)
    ema=ft.Switch(label="EMA 20 / 50",value=bool(prefs.get("chart_ema",True)),active_color=GREEN)
    vwap=ft.Switch(label="VWAP",value=bool(prefs.get("chart_vwap",True)),active_color=GREEN)
    rsi=ft.Switch(label="RSI",value=bool(prefs.get("chart_rsi",False)),active_color=GREEN)
    chart_tab=["Chart"]
    drawing_mode=["None"]
    compare_symbol=ft.Dropdown(label="Compare",value="BANKNIFTY",options=[ft.dropdown.Option(x) for x in ["NIFTY","BANKNIFTY","SENSEX","RELIANCE","HDFCBANK"]])
    macd=ft.Switch(label="MACD (12,26,9)",value=bool(prefs.get("chart_macd",False)),active_color=GREEN)
    volume=ft.Switch(label="Volume",value=bool(prefs.get("chart_volume",True)),active_color=GREEN)
    ema200=ft.Switch(label="EMA 200",value=bool(prefs.get("chart_ema200",False)),active_color=GREEN)
    sma50=ft.Switch(label="SMA 50",value=bool(prefs.get("chart_sma50",False)),active_color=GREEN)
    bollinger=ft.Switch(label="Bollinger Bands",value=bool(prefs.get("chart_bollinger",False)),active_color=GREEN)
    atr=ft.Switch(label="ATR 14",value=bool(prefs.get("chart_atr",False)),active_color=GREEN)
    supertrend=ft.Switch(label="Supertrend",value=bool(prefs.get("chart_supertrend",False)),active_color=GREEN)
    def persist_chart_settings(e=None):
        prefs.update({"chart_ema":ema.value,"chart_vwap":vwap.value,"chart_rsi":rsi.value,"chart_macd":macd.value,"chart_volume":volume.value,"chart_ema200":ema200.value,"chart_sma50":sma50.value,"chart_bollinger":bollinger.value,"chart_atr":atr.value,"chart_supertrend":supertrend.value})
        prefs.update(chart_symbol=symbol.value,chart_timeframe=timeframe.value,chart_type=prefs.get("chart_type","Candlestick"))
        saved=save()
        if e is not None:
            chart_message.value="Chart preferences saved." if saved else "Could not save chart preferences."
            page.update()
    for control in [ema,vwap,rsi,macd,volume,ema200,sma50,bollinger,atr,supertrend]:
        control.on_change=persist_chart_settings
    chart_message=txt("",12,MUTED)
    def choose_chart_tab(v):
        chart_tab[0]=v
        select(2)
    chart_style=[prefs.get("chart_type","Candlestick")]
    chart_style_picker=ft.Dropdown(label="Chart type",value=prefs.get("chart_type","Candlestick"),options=[ft.dropdown.Option(x) for x in ["Candlestick","Line"]])
    symbol.on_change=persist_chart_settings
    timeframe.on_change=persist_chart_settings
    def chart_style_apply(e):
        chart_style[0]=chart_style_picker.value
        prefs["chart_type"]=chart_style_picker.value
        persist_chart_settings()
        select(2)
    def chart_candles():
        q=quotes.get(symbol.value) or {}
        bars=q.get("bars") or []
        if len(bars)<2:
            return ft.Container(content=ft.Column([ft.Icon(ft.Icons.CANDLESTICK_CHART,size=48,color=GOLD),txt("Candles loading / unavailable"),note("Yahoo Finance • internet connection required")],horizontal_alignment=ft.CrossAxisAlignment.CENTER),height=210,alignment=ft.alignment.center)
        bars=bars[-36:]
        if chart_style[0]=="Line":
            return ft.Container(content=tiny_chart(symbol.value),height=230)
        low=min(b[3] for b in bars);high=max(b[2] for b in bars)
        spread=max(high-low,.001)
        width=324; height=230
        controls=[]
        for i,(_,o,h,l,c,v) in enumerate(bars):
            x=i*width/len(bars)+2
            yhigh=10+(high-h)/spread*195
            ylow=10+(high-l)/spread*195
            yo=10+(high-o)/spread*195
            yc=10+(high-c)/spread*195
            color=GREEN if c>=o else RED
            controls.append(ft.Container(left=x+2,top=yhigh,width=2,height=max(1,ylow-yhigh),bgcolor=color))
            controls.append(ft.Container(left=x,top=min(yo,yc),width=max(3,width/len(bars)-2),height=max(2,abs(yc-yo)),bgcolor=color))
        return ft.Column([ft.Row([note(f"High {high:,.2f}"),note(f"Low {low:,.2f}")],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),ft.Container(content=ft.Stack(controls,width=width,height=height),height=height),note(f"Yahoo OHLC • {timeframe.value} • may be delayed")],spacing=3)
    def drawing_action(v):
        drawing_mode[0]=v
        chart_message.value=f"Drawing tool: {v}. Select another tool to change mode."
        page.update()
    chart_quantity=ft.TextField(label="Paper quantity",value="1",width=140,keyboard_type=ft.KeyboardType.NUMBER)
    chart_sl=ft.TextField(label="Stop loss % (paper)",value="2",width=150,keyboard_type=ft.KeyboardType.NUMBER)
    chart_target=ft.TextField(label="Target % (paper)",value="4",width=150,keyboard_type=ft.KeyboardType.NUMBER)
    chart_paper_status=txt("Paper trading • no real orders",12,MUTED)
    def open_positions():
        return prefs.setdefault("paper_positions",{})
    def trade_history():
        return prefs.setdefault("paper_history",[])
    def position_pnl(p):
        price=(quotes.get(p["symbol"]) or {}).get("price")
        if price is None:return None
        return (float(price)-float(p["entry"]))*int(p["qty"])*(1 if p["side"]=="BUY" else -1)
    def exit_paper(sym):
        p=open_positions().pop(sym,None)
        if p:
            pnl=position_pnl(p)
            trade_history().append({"event":"EXIT","symbol":sym,"side":p["side"],"qty":p["qty"],"price":(quotes.get(sym) or {}).get("price"),"pnl":pnl,"time":datetime.now().isoformat(timespec="seconds")})
            save()
        select(current[0])
    def chart_paper_trade(side):
        sym=symbol.value
        if side=="EXIT":
            if sym in open_positions():
                exit_paper(sym)
                chart_paper_status.value="Paper position closed."
            else:chart_paper_status.value="No open position for "+sym
        else:
            try:
                qty=int(chart_quantity.value)
                price=(quotes.get(sym) or {}).get("price")
                sl_pct=float(chart_sl.value);target_pct=float(chart_target.value)
                if qty<1 or qty>100000 or price is None or not (0<sl_pct<=100 and 0<target_pct<=100):raise ValueError()
                if sym in open_positions():
                    chart_paper_status.value="Position already open for "+sym+". Exit first."
                    select(2)
                    return
                price=float(price)
                sl_price=price*(1-sl_pct/100 if side=="BUY" else 1+sl_pct/100)
                target_price=price*(1+target_pct/100 if side=="BUY" else 1-target_pct/100)
                open_positions()[sym]={"symbol":sym,"side":side,"entry":price,"qty":qty,"sl":sl_price,"target":target_price,"time":datetime.now().isoformat(timespec="seconds")}
                trade_history().append({"event":side,"symbol":sym,"side":side,"qty":qty,"price":price,"time":datetime.now().isoformat(timespec="seconds")})
                saved=save()
                chart_paper_status.value="Paper "+side+" recorded"+(" and saved." if saved else " (storage unavailable).")
            except (ValueError,TypeError):
                chart_paper_status.value="Valid quantity, SL, target and available quote required."
        select(2)
    def chart_position_text():
        p=open_positions().get(symbol.value)
        if not p:return "Paper position: FLAT"
        pnl=position_pnl(p)
        return "Paper "+p["side"]+" "+p["symbol"]+" ×"+str(p["qty"])+" @ ₹"+format(p["entry"],",.2f")+" • "+("P&L unavailable" if pnl is None else "Unrealized P&L ₹"+format(pnl,",.2f"))
    def dashboard_positions():
        controls=[]
        total=0.0;missing=False
        for sym,p in open_positions().items():
            pnl=position_pnl(p)
            if pnl is None:missing=True
            else:total+=pnl
            controls.append(ft.Column([txt(sym+" • "+p["side"]+" ×"+str(p["qty"]),14,GOLD,True),note("Entry ₹"+format(p["entry"],",.2f")+" • SL ₹"+format(p["sl"],",.2f")+" • Target ₹"+format(p["target"],",.2f")),note("P&L unavailable" if pnl is None else "Unrealized P&L ₹"+format(pnl,",.2f")),ft.OutlinedButton("Exit "+sym,on_click=lambda e,v=sym:exit_paper(v))]))
        if not controls:controls.append(note("No open paper positions"))
        controls.append(txt("Total unrealized P&L "+("partially unavailable • " if missing else "")+"₹"+format(total,",.2f"),14,GOLD,True))
        history=trade_history()[-10:]
        controls.append(txt("Recent paper orders",15,GOLD,True))
        for h in reversed(history):
            controls.append(note(h.get("time","")+" • "+h.get("event","")+" "+h.get("symbol","")+" ×"+str(h.get("qty",""))))
        return section("My Positions • Paper Only",ft.Column(controls,spacing=9))
    def charts():
        content=[heading("Charts • Technical Analysis"),ft.Row([ft.TextButton(text=n,on_click=lambda e,v=n:choose_chart_tab(v),style=ft.ButtonStyle(color=GOLD if chart_tab[0]==n else MUTED)) for n in ["Chart","Indicators","Drawing","Compare","Levels","Signals"]],scroll=ft.ScrollMode.AUTO),ft.Row([symbol,timeframe]),ft.ElevatedButton("Apply / Refresh",on_click=lambda e:page.run_task(load_chart),bgcolor=GOLD,color=BG)]
        if chart_tab[0]=="Chart":
            content.append(section("Stock Details • "+symbol.value,ft.Column([
                txt("₹ "+quote_price(symbol.value),26,GOLD,True),
                txt("Change "+quote_change(symbol.value),14,price_color(symbol.value),True),
                note("Yahoo preview • delayed or unavailable"),
                ft.Row([chart_quantity,chart_sl,chart_target],wrap=True),
                ft.Row([ft.ElevatedButton("BUY • Paper",on_click=lambda e:chart_paper_trade("BUY"),bgcolor=GREEN,color=BG),ft.ElevatedButton("SELL • Paper",on_click=lambda e:chart_paper_trade("SELL"),bgcolor=RED,color=WHITE),ft.OutlinedButton("Exit",on_click=lambda e:chart_paper_trade("EXIT"))],wrap=True),
                txt(chart_position_text(),12,GOLD),chart_paper_status,
                note("Simulation only • no real orders")
            ])))
            content.extend([ft.Row([chart_style_picker,ft.ElevatedButton("Set chart type",on_click=chart_style_apply)]),section("Yahoo Candlestick Chart",chart_candles()),section("Price Trend",ft.Container(content=tiny_chart(symbol.value),height=120)),ft.Row([ft.TextButton("Indicators",on_click=lambda e:choose_chart_tab("Indicators")),ft.TextButton("Drawing",on_click=lambda e:choose_chart_tab("Drawing"))])])
        elif chart_tab[0]=="Indicators":
            content.append(section("Indicators • Toggle On / Off",ft.Column([ema,ema200,sma50,bollinger,vwap,rsi,macd,volume,atr,supertrend,ft.ElevatedButton("Save indicators",on_click=lambda e:persist_chart_settings(e)),note("Selected: "+", ".join(n for n,c in [("EMA20/50",ema),("EMA200",ema200),("VWAP",vwap),("RSI",rsi),("MACD",macd),("Volume",volume),("SMA50",sma50),("Bollinger",bollinger),("ATR14",atr),("Supertrend",supertrend)] if c.value)),note("Indicator calculations/overlays require separate implementation and validated candle history.")])))
        elif chart_tab[0]=="Drawing":
            content.append(section("Drawing Tools",ft.Column([ft.Row([ft.ElevatedButton(x,on_click=lambda e,v=x:drawing_action(v)) for x in ["Trendline","Horizontal","Vertical"]],wrap=True),ft.Row([ft.ElevatedButton(x,on_click=lambda e,v=x:drawing_action(v)) for x in ["Fibonacci","Clear"]],wrap=True),note("Drawing selection works; chart-touch drawing is not yet implemented."),chart_message])))
        elif chart_tab[0]=="Compare":
            content.append(section("Compare Symbols",ft.Column([compare_symbol,ft.ElevatedButton("Compare",on_click=lambda e:page.run_task(load_comparison)),note("Compare the selected symbol's Yahoo trend with the current chart.")])))
        elif chart_tab[0]=="Levels":
            content.append(section("Market Levels",note("Verified support and resistance calculations are not yet enabled.")))
        else:
            content.append(section("Signals",note("Trading signals remain disabled until tested and validated.")))
        return content
    async def load_chart():
        try:
            quotes[symbol.value]=await asyncio.to_thread(get_yahoo,symbol.value,timeframe.value,"5d" if timeframe.value in ["1m","5m","15m"] else "1mo")
            chart_message.value="Yahoo chart updated"
        except Exception as exc:
            chart_message.value="Yahoo candles unavailable; check connection or rate limits"
        select(2)
    async def load_comparison():
        try:
            quotes[compare_symbol.value]=await asyncio.to_thread(get_yahoo,compare_symbol.value)
            chart_message.value=f"{compare_symbol.value} loaded"
        except Exception:chart_message.value="Comparison data unavailable"
        select(2)
    chain_symbol=ft.Dropdown(label="Index / Stock",value="NIFTY",options=[ft.dropdown.Option(x) for x in ["NIFTY","BANKNIFTY","FINNIFTY","SENSEX"]+all_watch_symbols()],expand=True)
    option_add_symbol=ft.TextField(label="Add symbol",hint_text="e.g. HDFCBANK",expand=True)
    option_expiry_choice=ft.Dropdown(label="Expiry",value="Nearest",options=[ft.dropdown.Option(x) for x in ["Nearest","Next","Manual"]],expand=True)
    expiry=ft.TextField(label="Expiry date (calendar preview)",read_only=True,expand=True)
    option_expiry_note=txt("Calendar estimate only; holidays and listed contracts need broker/exchange verification.",11,GOLD)
    def monthly_expiry(year,month,weekday):
        import calendar
        last=calendar.monthrange(year,month)[1]
        d=date(year,month,last)
        return d-timedelta(days=(d.weekday()-weekday)%7)
    def option_dates(sym):
        today=date.today()
        weekly=sym in ("NIFTY","SENSEX")
        day=3 if sym=="SENSEX" else 1
        result=[]
        if weekly:
            for i in range(0,40):
                d=today+timedelta(days=i)
                if d.weekday()==day:result.append(d)
                if len(result)>=2:break
        else:
            for i in range(0,6):
                y=today.year+(today.month-1+i)//12
                m=(today.month-1+i)%12+1
                d=monthly_expiry(y,m,day)
                if d>=today:result.append(d)
                if len(result)>=2:break
        return result
    def refresh_option_expiry(e=None):
        if option_expiry_choice.value=="Manual":
            expiry.read_only=False
        else:
            expiry.read_only=True
            dates=option_dates(chain_symbol.value)
            idx=1 if option_expiry_choice.value=="Next" else 0
            expiry.value=dates[idx].isoformat() if len(dates)>idx else ""
        if e is not None:select(1)
    def add_option_symbol(e):
        sym=(option_add_symbol.value or "").strip().upper().replace(".NS","")
        if sym and sym.replace("-","").replace("&","").isalnum() and sym not in [o.key for o in chain_symbol.options]:
            chain_symbol.options.append(ft.dropdown.Option(sym))
        if sym and sym in [o.key for o in chain_symbol.options]:
            chain_symbol.value=sym
            option_add_symbol.value=""
            refresh_option_expiry()
        select(1)
    chain_symbol.on_change=refresh_option_expiry
    option_expiry_choice.on_change=refresh_option_expiry
    refresh_option_expiry()
    option_tab=["Option Chain"]
    strategy_choice=[""]
    option_notice=txt("",12,MUTED)
    def choose_option_tab(v):
        option_tab[0]=v
        select(1)
    def choose_strategy(v):
        strategy_choice[0]=v
        select(1)
    option_strike=ft.TextField(label="Strike price",hint_text="e.g. 25000",keyboard_type=ft.KeyboardType.NUMBER)
    option_side=ft.Dropdown(label="Contract",value="CE",options=[ft.dropdown.Option("CE"),ft.dropdown.Option("PE")],width=120)
    option_qty=ft.TextField(label="Lots (paper)",value="1",keyboard_type=ft.KeyboardType.NUMBER,width=120)
    option_paper_note=txt("Option paper entry requires verified premium and lot size.",12,MUTED)
    def option_paper_action(side):
        option_paper_note.value="Cannot "+side+": verified CE/PE premium, listed strike and lot size unavailable. No order placed."
        page.update()
    def options():
        content=[heading("Options Chain & Flow Analysis"),ft.Row([ft.TextButton(text=n,on_click=lambda e,v=n:choose_option_tab(v),style=ft.ButtonStyle(color=GOLD if option_tab[0]==n else MUTED)) for n in ["Option Chain","OI Analysis","PCR","Premium Flow","Strategy"]],scroll=ft.ScrollMode.AUTO),ft.Row([chain_symbol,option_expiry_choice]),ft.Row([expiry]),option_expiry_note,ft.Row([option_add_symbol,ft.ElevatedButton("Add",on_click=add_option_symbol)]),note("Stock options only where F&O contracts are listed; selection does not confirm availability."),ft.ElevatedButton("Apply selection",on_click=lambda e:select(1)),note("Selected: "+str(chain_symbol.value)+" • "+str(expiry.value or "expiry not set"))]
        if option_tab[0]=="Option Chain":
            content.extend([section("Option Chain",ft.Column([ft.Row([txt("CALL (CE)",14,GREEN,True),txt("STRIKE",14,GOLD,True),txt("PUT (PE)",14,RED,True)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),ft.Column([unavailable("Verified exchange option-chain feed not connected"),
                note("CE/PE premiums and listed strikes are not invented."),
                ft.Row([option_strike,option_side],wrap=True),
                option_qty,
                ft.Row([ft.ElevatedButton("BUY • Paper",on_click=lambda e:option_paper_action("BUY"),bgcolor=GREEN,color=BG),ft.ElevatedButton("SELL • Paper",on_click=lambda e:option_paper_action("SELL"),bgcolor=RED,color=WHITE)],wrap=True),
                option_paper_note,
                section("Option Chart",unavailable("Historical option premium data source required"))
            ])]))])
        elif option_tab[0]=="OI Analysis":content.append(section("OI Analysis",unavailable("Live CE/PE open interest API not connected")))
        elif option_tab[0]=="PCR":content.append(section("Put Call Ratio",unavailable("PCR requires validated option-chain data")))
        elif option_tab[0]=="Premium Flow":content.append(section("Premium Money Flow",unavailable("Premium-flow API not connected")))
        else:
            content.append(section("Strategy Selector",ft.Column([ft.Row([ft.ElevatedButton(n,on_click=lambda e,v=n:choose_strategy(v)) for n in ["Bull Call Spread","Bear Put Spread","Iron Condor"]],wrap=True),note("Selected strategy: "+(strategy_choice[0] or "None")),note("Educational preview only; no orders are placed")])))
        return content
    mode=ft.Dropdown(label="Trading mode",value=prefs["mode"],options=[ft.dropdown.Option(x) for x in ["Paper","Manual","Semi-Auto","Auto"]])
    source=ft.Dropdown(label="Data provider",value=prefs["source"],options=[ft.dropdown.Option(x) for x in ["Yahoo Finance","Broker API"]])
    broker_names=["Angel One","Dhan","Zerodha Kite","Upstox","FYERS","Alice Blue","5paisa","ICICI Direct","Kotak Neo","Motilal Oswal","Groww","Shoonya / Finvasia","Flattrade","SAMCO","IIFL Securities","Paytm Money","Pocketful","Nuvama","Tradejini","HDFC Securities","Sharekhan","Axis Direct","Zebu","Mastertrust","Choice Broking","Religare","Sahi","Custom API"]
    broker=ft.Dropdown(label="Select Indian API broker",value=prefs.get("broker","Angel One"),options=[ft.dropdown.Option(x) for x in broker_names])
    api_url=ft.TextField(label="Custom HTTPS API endpoint",value=prefs.get("api_url",""))
    broker_info=ft.Text("",size=13,color=MUTED)
    broker_fields={
        "Angel One":["API Key","Client Code","MPIN","TOTP (current 6-digit code)"],
        "Dhan":["Client ID","Access Token"],
        "Zerodha Kite":["API Key","API Secret","Request Token (after official login)"],
        "Upstox":["Client ID / API Key","Client Secret","Authorization Code"],
        "FYERS":["App ID","Secret Key","Authorization Code"],
        "ICICI Direct":["API Key","API Secret","Session Token"],
        "Kotak Neo":["Consumer Key","Client ID","MPIN","TOTP"],
        "Groww":["API Key","API Secret / Access Token"],
        "Shoonya / Finvasia":["User ID","Vendor Code","API Secret","TOTP"],
        "5paisa":["App Key","App Secret","Client Code","Session Token"],
        "Custom API":["API Key","API Secret","Access Token"]
    }
    default_fields=["API Key / App ID","API Secret (if required)","Client ID (if required)","Access Token / Authorization Code"]
    credential_inputs={}
    credential_column=ft.Column(spacing=10)
    connection_status=txt("Not connected. Live broker login is not enabled in this build.",12,MUTED)
    def update_broker_info(e=None):
        name=broker.value
        labels=broker_fields.get(name,default_fields)
        credential_inputs.clear()
        controls=[]
        for label in labels:
            secret=any(word in label.lower() for word in ["secret","mpin","totp","token","key","code"])
            field=ft.TextField(label=label,password=secret,can_reveal_password=secret)
            credential_inputs[label]=field
            controls.append(field)
        credential_column.controls=controls
        broker_info.value=name+" • Enter credentials on this device only. Nothing is saved or sent."
        connection_status.value="Not connected. Authentication adapter required for "+name+"."
        connection_status.color=MUTED
        if e is not None:page.update()
    broker.on_change=update_broker_info
    update_broker_info()
    def clear_broker_credentials(e):
        for field in credential_inputs.values():field.value=""
        connection_status.value="Credentials cleared from the form. No broker session was created."
        connection_status.color=GREEN
        page.update()
    def explain_broker_connection(e):
        connection_status.value="Not connected: secure broker authentication and callback service are not configured. No credentials transmitted."
        connection_status.color=RED
        page.update()

    # Trading Bot controls: offline calculation and paper-only order simulation.
    bot_symbol=ft.Dropdown(label="Instrument",value=prefs.get("bot_symbol","NIFTY"),options=[ft.dropdown.Option(x) for x in ["NIFTY","BANKNIFTY","FINNIFTY","HDFCBANK","ICICIBANK","RELIANCE","SBIN","Custom"]])
    bot_custom=ft.TextField(label="Custom symbol (optional)",value=prefs.get("bot_custom",""))
    bot_type=ft.Dropdown(label="Option type",value=prefs.get("bot_type","CE"),options=[ft.dropdown.Option(x) for x in ["CE","PE"]])
    bot_strike=ft.TextField(label="Strike price",value=str(prefs.get("bot_strike","23400")),keyboard_type=ft.KeyboardType.NUMBER)
    bot_expiry=ft.TextField(label="Expiry (YYYY-MM-DD)",value=prefs.get("bot_expiry",""),hint_text="Select contract expiry manually")
    bot_lots=ft.Dropdown(label="Number of lots",value=str(prefs.get("bot_lots",1)),options=[ft.dropdown.Option(str(i),f"{i} Lot"+("s" if i>1 else "")) for i in range(1,51)])
    # Calendar suggestions are only previews, not verified exchange contracts.
    def preview_expiries(instrument):
        today=date.today()
        # NIFTY weekly; other symbols monthly. Verify against exchange holiday calendar.
        dates=[]
        for offset in range(1,100):
            d=today+timedelta(days=offset)
            if d.weekday()!=1:continue
            if instrument=="NIFTY" or (d+timedelta(days=7)).month!=d.month:
                dates.append(d.isoformat())
            if len(dates)>=4:break
        return dates
    bot_expiry_mode=ft.Dropdown(label="Expiry selection",value="Nearest (preview)",options=[ft.dropdown.Option(x) for x in ["Nearest (preview)","Next (preview)","Manual"]])
    expiry_warning=ft.Text("Calendar estimate only. Holiday shifts and exchange-listed expiries are not verified; paper mode only.",size=12,color=GOLD)
    def update_expiry(e=None):
        choices=preview_expiries(bot_symbol.value)
        selected=choices[1] if bot_expiry_mode.value=="Next (preview)" and len(choices)>1 else (choices[0] if choices else "")
        if bot_expiry_mode.value!="Manual":
            bot_expiry.value=selected
            bot_expiry.read_only=True
        else:
            bot_expiry.read_only=False
        if e is not None:page.update()
    bot_expiry_mode.on_change=update_expiry
    bot_symbol.on_change=update_expiry
    bot_lot_size=ft.TextField(label="Units per lot (verify with exchange)",value=str(prefs.get("bot_lot_size",1)),keyboard_type=ft.KeyboardType.NUMBER)
    bot_premium=ft.TextField(label="Entry premium (INR)",value=str(prefs.get("bot_premium",80)),keyboard_type=ft.KeyboardType.NUMBER)
    bot_trailing=ft.Switch(label="Trailing stop (calculation only)",value=bool(prefs.get("bot_trailing",False)),active_color=GOLD)
    # Saved strategy preferences only: no unattended execution or live orders.
    auto_entry=ft.Switch(label="Auto entry (saved plan only)",value=bool(prefs.get("auto_entry",False)),active_color=GOLD)
    auto_reentry=ft.Switch(label="Re-entry after exit (saved plan)",value=bool(prefs.get("auto_reentry",False)),active_color=GOLD)
    buy_dip=ft.Switch(label="Buy on dip (saved plan only)",value=bool(prefs.get("buy_dip",False)),active_color=GOLD)
    partial_profit=ft.Switch(label="Partial profit booking (plan)",value=bool(prefs.get("partial_profit",False)),active_color=GOLD)
    max_total_lots=ft.Dropdown(label="Maximum total lots",value=str(prefs.get("max_total_lots",2)),options=[ft.dropdown.Option(str(i)) for i in range(1,51)])
    dip_step=ft.TextField(label="Minimum dip before adding (%)",value=str(prefs.get("dip_step",5)),keyboard_type=ft.KeyboardType.NUMBER)
    max_daily_loss=ft.TextField(label="Daily loss limit (INR)",value=str(prefs.get("max_daily_loss",1000)),keyboard_type=ft.KeyboardType.NUMBER)
    cooldown=ft.Dropdown(label="Re-entry cooldown (minutes)",value=str(prefs.get("cooldown",15)),options=[ft.dropdown.Option(str(i)) for i in [5,10,15,30,60]])
    squareoff=ft.Dropdown(label="Paper square-off time",value=str(prefs.get("squareoff","15:15")),options=[ft.dropdown.Option(x) for x in ["15:00","15:10","15:15","15:20","15:25"]])
    emergency_stop=ft.Switch(label="Emergency stop (paper)",value=bool(prefs.get("emergency_stop",False)),active_color=RED)
    bot_preview=txt("Enter contract and tap Calculate.",13,MUTED)
    bot_trade_status=txt("No paper option position open.",12,MUTED)
    bot_position={"side":None,"entry":None,"quantity":0,"contract":None}
    bot_expiry_mode.value=prefs.get("bot_expiry_mode","Nearest (preview)")
    update_expiry()
    def bot_values():
        p=float(bot_premium.value);st=float(sl.value);tg=float(target.value)
        lots=int(bot_lots.value);unit=int(bot_lot_size.value);strike=float(bot_strike.value)
        if not (p>0 and 0<st<100 and 0<tg<=1000 and 1<=lots<=50 and 1<=unit<=100000 and strike>0):
            raise ValueError("Check premium, strike, lots, lot size, stop loss and target.")
        if bot_expiry.value:
            datetime.strptime(bot_expiry.value.strip(),"%Y-%m-%d")
        sym=(bot_custom.value or "").strip().upper() if bot_symbol.value=="Custom" else bot_symbol.value
        if not sym:raise ValueError("Enter a custom symbol.")
        contract=f"{sym} {bot_strike.value} {bot_type.value} {bot_expiry.value or '(expiry not set)'}"
        return p,st,tg,lots*unit,contract
    def calculate_bot(e=None):
        try:
            p,st,tg,qty,contract=bot_values()
            bot_preview.value=(f"{contract} | Qty {qty} | Entry INR {p:.2f} | SL INR {p*(1-st/100):.2f} | Target INR {p*(1+tg/100):.2f} | "
                               f"Cost INR {p*qty:,.2f} | Max planned loss INR {p*qty*st/100:,.2f} | Planned profit INR {p*qty*tg/100:,.2f}. "
                               "Illustrative premium-based calculations; excludes charges, slippage and gaps. No live option quote.")
            bot_preview.color=GREEN
        except (ValueError,TypeError,OverflowError) as exc:
            bot_preview.value="Invalid input: "+str(exc)
            bot_preview.color=RED
        page.update()
    def bot_paper_action(side):
        if mode.value!="Paper":
            bot_trade_status.value="Live orders disabled. Select Paper mode for simulation."
            bot_trade_status.color=RED
        elif side=="EXIT":
            if bot_position["side"]:
                bot_trade_status.value="Paper option position closed at simulated entry premium (no live exit quote)."
                bot_position.update(side=None,entry=None,quantity=0,contract=None)
                bot_trade_status.color=GREEN
            else:
                bot_trade_status.value="No paper option position to exit."
                bot_trade_status.color=MUTED
        elif emergency_stop.value:
            bot_trade_status.value="Emergency stop active. New paper entries blocked."
            bot_trade_status.color=RED
        elif bot_position["side"]:
            bot_trade_status.value="Exit the existing paper position before another entry."
            bot_trade_status.color=RED
        else:
            try:
                p,st,tg,qty,contract=bot_values()
                if not bot_expiry.value:raise ValueError("Set contract expiry before paper entry.")
                bot_position.update(side=side,entry=p,quantity=qty,contract=contract)
                bot_trade_status.value=f"SIMULATED {side} {contract} | {qty} units @ INR {p:.2f} | SL INR {p*(1-st/100):.2f} | Target INR {p*(1+tg/100):.2f}. No real order."
                bot_trade_status.color=GREEN
            except (ValueError,TypeError,OverflowError) as exc:
                bot_trade_status.value="Paper entry blocked: "+str(exc)
                bot_trade_status.color=RED
        page.update()

    sl=ft.TextField(label="Stop loss %",value=str(prefs["stop_loss"]),keyboard_type=ft.KeyboardType.NUMBER)
    target=ft.TextField(label="Target %",value=str(prefs["target"]),keyboard_type=ft.KeyboardType.NUMBER)
    limit=ft.TextField(label="Max trades per day",value=str(prefs["max_trades"]),keyboard_type=ft.KeyboardType.NUMBER)
    conf=ft.Slider(min=70,max=85,divisions=15,value=prefs["confidence"],label="{value}%")
    status=txt("Broker orders disabled. Paper Buy/Sell is simulated.",12,RED)
    paper_position={"side":None,"entry":None,"symbol":None}
    paper_status=txt("Paper position: FLAT",12,MUTED)
    def paper_trade(side):
        if mode.value!="Paper":
            paper_status.value="Switch to Paper mode for simulated Buy / Sell."
            paper_status.color=RED
        elif side=="EXIT":
            if paper_position["side"]:
                paper_status.value="Paper position closed (simulation only)."
                paper_position.update(side=None,entry=None,symbol=None)
                paper_status.color=GREEN
            else:paper_status.value="No paper position to exit."
        else:
            sym=symbol.value
            q=quotes.get(sym)
            if not q or q.get("price") is None:
                paper_status.value="Cannot simulate entry: Yahoo quote unavailable."
                paper_status.color=RED
            else:
                paper_position.update(side=side,entry=q["price"],symbol=sym)
                paper_status.value=f"Paper {side} {sym} @ {q['price']:,.2f} • SL {sl.value}% • Target {target.value}% (not an actual order)"
                paper_status.color=GREEN
        page.update()

    def save_settings(_):
        try:
            stop=float(sl.value);take=float(target.value);count=int(limit.value)
            if not (0<stop<=100 and 0<take<=100 and 1<=count<=50):raise ValueError()
            bot_values()
            if not (1<=int(max_total_lots.value)<=50 and int(max_total_lots.value)>=int(bot_lots.value) and 0<float(dip_step.value)<=100 and float(max_daily_loss.value)>0):raise ValueError("Invalid strategy limits")
            prefs.update(mode=mode.value,source=source.value,broker=broker.value,api_url=api_url.value,stop_loss=stop,target=take,max_trades=count,confidence=int(conf.value),bot_symbol=bot_symbol.value,bot_custom=bot_custom.value,bot_type=bot_type.value,bot_strike=bot_strike.value,bot_expiry=bot_expiry.value,bot_lots=int(bot_lots.value),bot_lot_size=int(bot_lot_size.value),bot_premium=float(bot_premium.value),bot_trailing=bot_trailing.value,bot_expiry_mode=bot_expiry_mode.value,auto_entry=auto_entry.value,auto_reentry=auto_reentry.value,buy_dip=buy_dip.value,partial_profit=partial_profit.value,max_total_lots=int(max_total_lots.value),dip_step=float(dip_step.value),max_daily_loss=float(max_daily_loss.value),cooldown=int(cooldown.value),squareoff=squareoff.value,emergency_stop=emergency_stop.value)
            persisted=save();status.value=("Settings saved on device. Auto strategies are not running." if persisted else "Save failed: device storage unavailable. Settings will reset after restart.");status.color=GREEN if persisted else RED
        except Exception:
            status.value="Cannot save: check contract, lot limits, premium, SL, target and daily loss.";status.color=RED
        page.update()
    broker.value=prefs.get("broker","Angel One")
    settings_tab=["Trading Bot"]
    def choose_settings_tab(v):
        settings_tab[0]=v
        select(2)
    def settings():
        tabs=["Trading Bot","Broker & API","Risk & Money","Strategy","Alerts","Backtest"]
        content=[heading("Settings & Trading Bot"),ft.Row([ft.TextButton(text=n,on_click=lambda e,v=n:choose_settings_tab(v),style=ft.ButtonStyle(color=GOLD if settings_tab[0]==n else MUTED)) for n in tabs],scroll=ft.ScrollMode.AUTO)]
        if settings_tab[0]=="Trading Bot":
            content.extend([
                section("01  TRADING MODE",ft.Column([mode,note("Paper simulation only. Manual, Semi-Auto and Auto do not place real orders.")])),
                section("02  OPTION CONTRACT",ft.Column([
                    bot_symbol,bot_custom,ft.Row([bot_type,bot_strike],wrap=True),
                    bot_expiry_mode,bot_expiry,expiry_warning,ft.Row([bot_lots,bot_lot_size],wrap=True),
                    bot_premium,note("Enter the actual exchange lot size and premium manually. No option-chain feed is connected.")
                ],spacing=12)),
                section("03  RISK & TARGET",ft.Column([
                    ft.Row([sl,target],wrap=True),limit,
                    note("Trailing stop is a saved preference only. It does not automatically update or execute orders."),
                    ft.ElevatedButton("CALCULATE PLAN",on_click=calculate_bot,bgcolor=GOLD,color=BG),
                    bot_preview
                ],spacing=12)),
                section("04  AUTO STRATEGY (PREFERENCES ONLY)",ft.Column([
                    auto_entry,auto_reentry,buy_dip,partial_profit,bot_trailing,
                    max_total_lots,dip_step,cooldown,max_daily_loss,squareoff,emergency_stop,
                    note("Auto entry, re-entry, averaging, partial exits, trailing SL and square-off are NOT running. These switches save a plan only. Emergency stop immediately blocks new manual paper entries. No live orders.")
                ],spacing=12)),
                section("05  PAPER TRADE CONTROLS",ft.Column([
                    ft.Row([
                        ft.ElevatedButton("BUY (Paper)",on_click=lambda e:bot_paper_action("BUY"),bgcolor=GREEN,color=BG),
                        ft.ElevatedButton("SELL (Paper)",on_click=lambda e:bot_paper_action("SELL"),bgcolor=RED,color=WHITE),
                        ft.OutlinedButton("EXIT",on_click=lambda e:bot_paper_action("EXIT"))
                    ],wrap=True),bot_trade_status,
                    note("Paper orders use manually entered premium, not live market prices. SL/target are displayed, not executed.")
                ],spacing=12))
            ])
        elif settings_tab[0]=="Broker & API":
            content.append(section("Broker & Data Source",ft.Column([broker,broker_info,source,credential_column,api_url,ft.Row([ft.ElevatedButton("Connect / Check",on_click=explain_broker_connection,bgcolor=GOLD,color=BG),ft.OutlinedButton("Clear / Disconnect",on_click=clear_broker_credentials)],wrap=True),connection_status,note("Credentials are temporary and never saved. This is a setup form, not a live broker connection. For real login a secure broker-specific integration is required.") ])))
        elif settings_tab[0]=="Risk & Money":
            content.append(section("Risk Management",ft.Column([ft.Row([sl,target]),limit,note("Risk controls are stored but automatic SL/target execution is disabled.")])))
        elif settings_tab[0]=="Strategy":
            content.append(section("Strategy & Signal Filters",ft.Column([txt("Signal confidence filter (70–85%)",14),conf,note("Strategy engine is not connected; this is a saved preference only.")])))
        elif settings_tab[0]=="Alerts":
            content.append(section("Alerts",note("Alert delivery is not implemented. No active alerts.")))
        else:
            content.append(section("Backtest & Reports",note("Backtesting requires historical data and a validated strategy. No results are available.")))
        content.extend([ft.ElevatedButton("Save settings",on_click=save_settings,bgcolor=GOLD,color=BG),status,section("Safety",note("Broker orders, automatic trading and signals are disabled until secure integration and testing."))])
        return content


    # Scanner-only upgrade. Existing five page functions remain unchanged.
    scan_symbol=ft.Dropdown(label="Market / NSE stock",value="NIFTY",options=[ft.dropdown.Option(v) for v in list(dict.fromkeys(["NIFTY","BANKNIFTY","SENSEX"]+watch_symbols))])
    scan_budget=ft.Dropdown(label="Premium budget",value="80-120",options=[ft.dropdown.Option(v) for v in ["40-80","60-120","80-120","100-200","120-200","200-300","Custom","Any"]])
    scan_min=ft.TextField(label="Custom minimum (₹)",value="50",keyboard_type=ft.KeyboardType.NUMBER)
    scan_max=ft.TextField(label="Custom maximum (₹)",value="500",keyboard_type=ft.KeyboardType.NUMBER)
    scan_period=ft.Dropdown(label="Historical period",value="7d",options=[ft.dropdown.Option(v) for v in ["7d","1mo","3mo"]])
    scan_tf=ft.Dropdown(label="Candle timeframe",value="5m",options=[ft.dropdown.Option(v) for v in ["1m","5m","15m","1h","1d"]])
    scan_expiry=ft.Dropdown(label="Illustrative days to expiry (NOT actual NSE expiry)",value="14",options=[ft.dropdown.Option(v) for v in ["1","3","7","14","21","30"]])
    scan_auto=ft.Switch(label="Trend filter (simulation)",value=True,active_color=GREEN)
    scan_live=ft.Switch(label="Auto Scan (while app is open)",value=True,active_color=GREEN)
    scan_refresh=ft.Dropdown(label="Auto refresh interval",value="60",options=[ft.dropdown.Option(v) for v in ["30","60","120"]])
    scan_status=ft.Text("Auto Scan OFF • Yahoo underlying only; not a live option feed.",size=11,color=MUTED)
    scan_last_candle=[None]
    scan_last_success=[None]
    scan_next_refresh=[None]
    scan_age_display=ft.Text("Last successful scan: — | Candle age: — | Next refresh: —",size=11,color=MUTED)
    filter_names=ALL_FILTERS[:]
    # One-time migration restores the original ten defaults without overriding later user edits.
    if not prefs.get("default_ten_migrated"):
        prefs["scanner_filters"]=DEFAULT_FILTERS[:]
        prefs["default_ten_migrated"]=True
    filter_selected=[x for x in prefs.get("scanner_filters",DEFAULT_FILTERS) if x in filter_names]
    filter_query=ft.TextField(label="Find indicator",dense=True)
    filter_choice=ft.Dropdown(label="Select filter",options=[ft.dropdown.Option(x) for x in filter_names],dense=True)
    filter_feedback=note("Active: "+", ".join(filter_selected))
    chart_filter_names=["EMA 9/21","RSI 14","MACD","Supertrend"]
    chart_provider=["BOT KING / Yahoo"]
    # v1.2 Android runtime does not register the WebView control. Reset persisted invalid selection.
    prefs["chart_provider"]="BOT KING / Yahoo"
    def chart_provider_change(e):
        chart_provider[0]=e.control.value
        prefs["chart_provider"]=chart_provider[0]
        save()
        select(3)
    filter_checklist=ft.Column(spacing=0)
    def reset_default_filters(e):
        filter_selected[:]=DEFAULT_FILTERS[:]
        scanner_chart_indicators[:]=chart_filter_names[:]
        prefs["scanner_filters"]=filter_selected[:]
        prefs["scanner_chart_indicators"]=scanner_chart_indicators[:]
        save();select(3)
        if not scan_busy[0]:trigger_scan()
    def filter_checkbox_changed(e):
        name=e.control.data
        if e.control.value and name not in filter_selected:filter_selected.append(name)
        elif not e.control.value and name in filter_selected:filter_selected.remove(name)
        prefs["scanner_filters"]=filter_selected[:]
        save();select(3)
        if not scan_busy[0]:trigger_scan()
    def filter_edit(add):
        q=(filter_query.value.strip() if filter_query.value and filter_query.value.strip() else filter_choice.value or "").lower()
        hits=[x for x in filter_names if q and q in x.lower()]
        if len(hits)!=1:filter_feedback.value="Select one supported filter"
        elif add and hits[0] not in filter_selected:filter_selected.append(hits[0]);filter_feedback.value="Added "+hits[0]
        elif not add and hits[0] in filter_selected:filter_selected.remove(hits[0]);filter_feedback.value="Removed "+hits[0]
        else:filter_feedback.value="Already active or last filter"
        # Scanner votes and chart overlays share the same selected indicator state.
        prefs["scanner_filters"]=filter_selected[:];filter_query.value="";save();select(3)
        if not scan_busy[0]:trigger_scan()
    scan_auto_generation=[0]
    def auto_scan_changed(e):
        scan_auto_generation[0]+=1
        scan_status.value=("Auto Scan ON • checking for new Yahoo candles" if scan_live.value
                           else "Auto Scan OFF")
        page.update()
        if scan_live.value:
            page.run_task(auto_scan_loop,scan_auto_generation[0])
    async def auto_scan_loop(generation):
        # No background service: refresh runs only while this app/page is alive.
        while scan_live.value and generation==scan_auto_generation[0]:
            if not scan_busy[0]:
                scan_busy[0]=True
                await scan_market()
            try:
                delay=int(scan_refresh.value or "60")
            except (ValueError,TypeError):
                delay=60
            scan_next_refresh[0]=datetime.now().timestamp()+max(30,delay)
            await asyncio.sleep(max(30,delay))
    scan_live.on_change=auto_scan_changed
    def trigger_scan(e=None):
        if scan_tf.value=="1m":scan_period.value="7d"
        if not scan_busy[0]:
            scan_busy[0]=True
            page.run_task(scan_market)
    for c in [scan_symbol,scan_budget,scan_min,scan_max,scan_period,scan_tf,scan_expiry,scan_auto]:
        c.on_change=trigger_scan
    scan_result=ft.Column(spacing=12)
    scan_busy=[False]
    def scan_num(x):
        return f"{x:,.2f}" if isinstance(x,(float,int)) else "—"
    scanner_chart_visible=[True]
    scanner_chart_indicators=[x for x in prefs.get("scanner_chart_indicators",chart_filter_names) if x in chart_filter_names]
    scanner_chart_style=[prefs.get("scanner_chart_style","Candlestick")]
    def scanner_chart_toggle(e):
        scanner_chart_visible[0]=not scanner_chart_visible[0]
        select(3)
    def scanner_chart_filter(e):
        # Chart visibility is independent of the ten active background analysis filters.
        name=e.control.data
        if e.control.value and name not in scanner_chart_indicators:scanner_chart_indicators.append(name)
        if not e.control.value and name in scanner_chart_indicators:scanner_chart_indicators.remove(name)
        prefs["scanner_chart_indicators"]=scanner_chart_indicators[:]
        save();select(3)
    def scanner_chart_style_change(e):
        scanner_chart_style[0]=e.control.value
        prefs["scanner_chart_style"]=scanner_chart_style[0]
        save()
        select(3)
    def scanner_compact_chart():
        sym=scan_symbol.value or "NIFTY"
        hist=candles.get("scanner_chart_"+sym) or {}
        bars=(hist.get("bars") or [])[-35:]
        parts=[ft.Row([txt(sym+" • "+(scan_tf.value or "5m"),15,GOLD,True),ft.TextButton("Hide" if scanner_chart_visible[0] else "Show",on_click=scanner_chart_toggle)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN)]
        if scanner_chart_visible[0]:
            parts.append(ft.Dropdown(label="Chart display",value=scanner_chart_style[0],options=[ft.dropdown.Option("Candlestick"),ft.dropdown.Option("Line")],on_change=scanner_chart_style_change,dense=True))
            parts.append(note("BOT KING / Yahoo chart • TradingView embedded mode temporarily disabled: Android WebView extension is not installed."))
            parts.append(note("Underlying OHLC • delayed historical candles, NOT option premium"))
            if len(bars)>=2:
                closes=[float(b[4]) for b in bars]
                lows=[float(b[3]) for b in bars]
                highs=[float(b[2]) for b in bars]
                low=min(lows);high=max(highs);spread=max(high-low,.01)
                if scanner_chart_style[0]=="Line":
                    points=[ft.LineChartDataPoint(i,v) for i,v in enumerate(closes)]
                    series=[ft.LineChartData(data_points=points,stroke_width=2,color=GREEN,curved=False)]
                    if "EMA 9/21" in scanner_chart_indicators:
                        for length,color in [(9,GOLD),(21,"#72A7F2")]:
                            alpha=2/(length+1);z=closes[0];vals=[]
                            for i,v in enumerate(closes):
                                z=alpha*v+(1-alpha)*z
                                vals.append(ft.LineChartDataPoint(i,z))
                            series.append(ft.LineChartData(data_points=vals,stroke_width=1.5,color=color,curved=False))
                    visual=ft.LineChart(data_series=series,min_x=0,max_x=len(closes)-1,min_y=low-spread*.12,max_y=high+spread*.12,left_axis=ft.ChartAxis(labels_size=48),bottom_axis=ft.ChartAxis(labels_size=0),right_axis=ft.ChartAxis(labels_size=0),top_axis=ft.ChartAxis(labels_size=0),expand=True)
                else:
                    width=300;height=180;controls=[]
                    for i,(_,o,h,l,c,v) in enumerate(bars):
                        x=i*width/len(bars)+2
                        yy=lambda p:8+(high-float(p))/spread*(height-16)
                        color=GREEN if c>=o else RED
                        controls.append(ft.Container(left=x+2,top=yy(h),width=2,height=max(1,yy(l)-yy(h)),bgcolor=color))
                        controls.append(ft.Container(left=x,top=min(yy(o),yy(c)),width=max(3,width/len(bars)-2),height=max(2,abs(yy(c)-yy(o))),bgcolor=color))
                    if "EMA 9/21" in scanner_chart_indicators:
                        for length,color in [(9,GOLD),(21,"#72A7F2")]:
                            z=closes[0]
                            for i,v in enumerate(closes):
                                z+=2*(v-z)/(length+1)
                                controls.append(ft.Container(left=i*width/len(bars)+3,top=yy(z),width=3,height=3,bgcolor=color))
                    visual=ft.Stack(controls,width=width,height=height)
                parts.append(ft.Container(content=visual,height=190,alignment=ft.alignment.center))
                parts.append(note("Range ₹"+f"{low:,.2f}"+" – ₹"+f"{high:,.2f}"))
                if "RSI 14" in scanner_chart_indicators and len(closes)>=15:
                    dif=[closes[i]-closes[i-1] for i in range(-14,0)]
                    gain=sum(max(0,x) for x in dif);loss=sum(max(0,-x) for x in dif)
                    value=100 if loss==0 else 100-100/(1+gain/loss)
                    parts.append(note(f"RSI 14: {value:.1f}"))
                if "MACD" in scanner_chart_indicators:
                    def ema_series(n):
                        z=closes[0];out=[]
                        for v in closes:z+=2*(v-z)/(n+1);out.append(z)
                        return out
                    m=[x-y for x,y in zip(ema_series(12),ema_series(26))]
                    z=m[0]
                    for v in m:z+=2*(v-z)/10
                    parts.append(note(f"MACD: {m[-1]:.2f} • Signal: {z:.2f}"))
                if "Supertrend" in scanner_chart_indicators:
                    parts.append(note("Supertrend signal: see Analysis Basis; no fabricated overlay"))
            else:parts.append(note("Chart will appear after a successful scanner fetch."))
            parts.append(ft.Column([ft.Checkbox(label=x,value=x in scanner_chart_indicators,data=x,on_change=scanner_chart_filter) for x in chart_filter_names],spacing=0))
            parts.append(note("Chart switches affect display only. The 10 analysis filters below work independently. EMA is plotted; RSI/MACD show values; Supertrend shows analysis status."))
            parts.append(note("OI / PCR / Max Pain: unavailable until verified option-chain API is connected."))
        return section("COMPACT CHART • "+sym,ft.Column(parts,spacing=4))
    def scanner():
        filter_checklist.controls=[ft.Checkbox(label=x+(" • data unavailable" if x in ("OI Support","OI Resistance","OI Profile","Max Pain") else ""),value=x in filter_selected,data=x,on_change=filter_checkbox_changed) for x in DEFAULT_FILTERS]
        scan_min.visible=scan_budget.value=="Custom"
        scan_max.visible=scan_budget.value=="Custom"
        return [heading("AI SCANNER • Chart & Signals"),
            note("Yahoo underlying candles • simulated premiums, not live contracts"),
            card(ft.Row([scan_symbol,scan_tf],spacing=6),ft.Row([scan_budget,scan_period],spacing=6),ft.Row([scan_min,scan_max],spacing=6),ft.Row([scan_expiry,scan_refresh],spacing=6),
                 scan_live,scan_status,scan_age_display),
            scanner_compact_chart(),
            section("10 DEFAULT ANALYSIS FILTERS • ON/OFF",ft.Column([note("These control background scanner votes and Top 5 ranking, not chart visibility."),filter_checklist,ft.OutlinedButton("Restore default 10",on_click=reset_default_filters),note("Additional indicators: choose below; OI/PCR require verified exchange data.")],spacing=4)),section("ADD EXTRA FILTERS • Saved",ft.Column([filter_query,filter_choice,ft.Row([ft.ElevatedButton("Add",on_click=lambda e:filter_edit(True)),ft.OutlinedButton("Remove",on_click=lambda e:filter_edit(False))]),filter_feedback,note("Unavailable data cannot vote. Adding a filter does not imply a plotted overlay.")],spacing=5)),
            scan_result]
    def run_scan(e):
        if scan_busy[0]:return
        scan_busy[0]=True
        if not scan_live.value:
            scan_result.controls=[card(txt("Checking Yahoo market history…",16,GOLD,True))]
        page.update()
        page.run_task(scan_market)
    async def scan_market():
        import math
        from datetime import timezone
        try:
            sym=scan_symbol.value or "NIFTY"
            period=scan_period.value or "1mo"
            interval=scan_tf.value or "1d"
            # Yahoo supports limited intraday history; do not pretend 15m is daily.
            if interval=="1m" and period!="7d":
                raise ValueError("Yahoo 1m history is limited. Select 7d; only recent candles may be returned.")
            if interval=="5m" and period=="3mo":
                raise ValueError("Yahoo 5m candles cannot cover 3 months. Choose 7d or 1mo.")
            if interval in ("5m","15m") and period=="3mo":
                raise ValueError("Yahoo intraday history is limited. Choose 7d or 1mo.")
            hist=await asyncio.to_thread(get_yahoo,sym,interval,period)
            bars=hist.get("bars") or []
            candles["scanner_chart_"+sym]=hist
            closes=[float(b[4]) for b in bars if b[4] is not None and b[4]>0]
            if len(closes)<8:raise ValueError("Not enough valid Yahoo candles. Choose a longer period or daily timeframe.")
            latest_timestamp=bars[-1][0]
            scan_last_candle[0]=latest_timestamp
            updated=datetime.fromtimestamp(latest_timestamp,timezone.utc)
            age_hours=(datetime.now(timezone.utc)-updated).total_seconds()/3600
            price=closes[-1]
            first=closes[0]
            change=(price/first-1)*100
            # Estimate annual volatility using selected candle duration; for illustrative pricing only.
            annual_bars={"1m":375*252,"5m":75*252,"15m":25*252,"1h":7*252,"1d":252}[interval]
            returns=[math.log(closes[i]/closes[i-1]) for i in range(1,len(closes))]
            avg=sum(returns)/len(returns)
            variance=sum((v-avg)**2 for v in returns)/max(1,len(returns)-1)
            volatility=max(.08,min(1.5,math.sqrt(variance*annual_bars)))
            ma_fast=sum(closes[-min(5,len(closes)):])/min(5,len(closes))
            ma_slow=sum(closes[-min(20,len(closes)):])/min(20,len(closes))
            def ema(vals,n):
                z=vals[0];out=[z]
                for v in vals[1:]:z+=2*(v-z)/(n+1);out.append(z)
                return out
            votes=[]
            if "SMA 5/20" in filter_selected:votes.append(("SMA 5/20",1 if price>ma_fast>=ma_slow else -1 if price<ma_fast<=ma_slow else 0,"5="+scan_num(ma_fast)+" 20="+scan_num(ma_slow)))
            if "EMA 9/21" in filter_selected:
                x=ema(closes,9)[-1];y=ema(closes,21)[-1]
                votes.append(("EMA 9/21",1 if price>x>y else -1 if price<x<y else 0,"9="+scan_num(x)+" 21="+scan_num(y)))
            if "RSI 14" in filter_selected:
                dif=[closes[i]-closes[i-1] for i in range(1,len(closes))]
                g=sum(max(0,v) for v in dif[-14:]);l=sum(max(0,-v) for v in dif[-14:])
                val=100 if l==0 else 100-100/(1+g/l)
                votes.append(("RSI 14",1 if 52<=val<=70 else -1 if 30<=val<=48 else 0,f"RSI={val:.1f}"))
            if "MACD" in filter_selected:
                line=[x-y for x,y in zip(ema(closes,12),ema(closes,26))]
                sig=ema(line,9)[-1]
                votes.append(("MACD",1 if line[-1]>sig else -1 if line[-1]<sig else 0,"MACD="+scan_num(line[-1])+" signal="+scan_num(sig)))
            up=sum(v==1 for _,v,_ in votes);down=sum(v==-1 for _,v,_ in votes)
            direction="BULLISH" if up>=2 and up>=2*down else "BEARISH" if down>=2 and down>=2*up else "SIDEWAYS / WAIT"
            advanced=analyze(bars,filter_selected,interval)
            direction=advanced["bias"]
            basis=advanced["reason"]
            lines=[txt(v["name"]+" • "+("BULLISH" if v["vote"]==1 else "BEARISH" if v["vote"]==-1 else "NEUTRAL" if v["vote"]==0 else "UNAVAILABLE")+" • "+v["detail"],11,
                       GREEN if v["vote"]==1 else RED if v["vote"]==-1 else MUTED) for v in advanced["votes"]]
            lines=[txt(n+" • "+("BULLISH" if v==1 else "BEARISH" if v==-1 else "NEUTRAL")+" • "+d,11,GREEN if v==1 else RED if v==-1 else MUTED) for n,v,d in votes]
            support=min(closes[-min(20,len(closes)):])
            resistance=max(closes[-min(20,len(closes)):])
            budget=scan_budget.value or "80-120"
            if budget=="Custom":
                low=float(scan_min.value);high=float(scan_max.value)
            elif budget=="Any":low,high=0.,float("inf")
            else:low,high=map(float,budget.split("-"))
            if not (math.isfinite(low) and low>=0 and high>low):raise ValueError("Premium range must have a valid minimum and larger maximum.")
            days=int(scan_expiry.value or "14")
            def normal_cdf(x):return .5*(1+math.erf(x/math.sqrt(2)))
            def model(k,call,days_left):
                t=max(days_left,0.01)/365
                sig=volatility;r=.06
                d1=(math.log(price/k)+(r+.5*sig*sig)*t)/(sig*math.sqrt(t))
                d2=d1-sig*math.sqrt(t)
                if call:return max(0.,price*normal_cdf(d1)-k*math.exp(-r*t)*normal_cdf(d2))
                return max(0.,k*math.exp(-r*t)*normal_cdf(-d2)-price*normal_cdf(-d1))
            # Strike increments for stocks are not inferred from price: use illustrative grids.
            step=50 if sym=="NIFTY" else 100 if sym in ("BANKNIFTY","SENSEX") else max(1,round(price*.01))
            atm=round(price/step)*step
            pool=[]
            for i in range(-30,31):
                strike=atm+i*step
                if strike<=0:continue
                for call in (True,False):
                    premium=model(strike,call,days)
                    if premium<.05:continue
                    next_day=model(strike,call,max(1,days-1))
                    decay=max(0.,premium-next_day)
                    aligned=(direction=="BULLISH" and call) or (direction=="BEARISH" and not call)
                    # Penalize very far OTM and high daily time decay.
                    decay_pct=100*decay/max(premium,.01)
                    pool.append(dict(strike=strike,call=call,premium=premium,decay=decay,decay_pct=decay_pct,aligned=aligned,dist=abs(strike-price)/price))
            eligible=[v for v in pool if low<=v["premium"]<=high]
            if scan_auto.value and direction in ("BULLISH","BEARISH"):
                eligible.sort(key=lambda v:(not v["aligned"],v["dist"],v["decay_pct"]))
            else:eligible.sort(key=lambda v:(v["decay_pct"],v["dist"]))
            rows=[]
            for v in eligible[:3]:
                side="CE" if v["call"] else "PE"
                label="TREND-ALIGNED" if v["aligned"] else "COUNTER-TREND / CAUTION"
                rows.append(ft.Container(content=ft.Column([
                    txt(f'{sym} {v["strike"]:g} {side} • SIM ₹{v["premium"]:.2f}',14,GOLD,True),
                    txt(label,12,GREEN if v["aligned"] else MUTED,True),
                    note(f'Illustrative daily time decay ≈ ₹{v["decay"]:.2f} ({v["decay_pct"]:.1f}% of premium) if underlying/volatility stay constant.'),
                    note("Unverified strike/expiry • check broker.")
                ],spacing=6),bgcolor=PANEL2,padding=12,border_radius=10))
            age_warning=("STALE DATA — no trading decision from this quote." if age_hours>24 else "Data may be delayed; confirm with broker.")
            controls=[section("ANALYSIS BASIS • Candles & Filters",ft.Column([txt("Candle "+interval+" • Period "+period+" • "+str(len(bars))+" bars",12,GOLD,True),note("Latest UTC: "+updated.strftime("%d %b %Y %H:%M")),note(basis),*lines,note("OI/PCR/Max Pain not connected; unavailable filters never vote.")],spacing=5)),card(txt(sym+" • "+direction,19,GREEN if direction=="BULLISH" else RED if direction=="BEARISH" else GOLD,True),
                txt("Underlying historical close: ₹"+scan_num(price),15),
                txt("Yahoo candle (UTC): "+updated.strftime("%d %b %Y %H:%M"),12),
                txt("Data age: "+f"{max(0,age_hours):.1f}"+" hours • "+age_warning,12,RED if age_hours>24 else GOLD),
                txt("Selected timeframe: "+interval+" • Period: "+period+" • Move: "+f"{change:+.2f}%",12),
                txt("5-candle average: "+scan_num(ma_fast)+"  |  20-candle average: "+scan_num(ma_slow),12),
                txt("Support: "+scan_num(support)+"  |  Resistance: "+scan_num(resistance),12),
                txt("Indicative annualized volatility: "+f"{volatility*100:.1f}%",12),
                note("Rule-based scanner, not a trained AI model or calibrated probability."))]
            # Summary is a scenario calculator, never a live executable recommendation.
            fresh_limit={"1m":0.12,"5m":0.5,"15m":1.0,"1h":2.0,"1d":30.0}[interval]
            fresh=(0<=age_hours<=fresh_limit)
            aligned_choices=[v for v in eligible if v["aligned"] and v["dist"]<=0.04]
            selected=aligned_choices[0] if aligned_choices else None
            if direction not in ("BULLISH","BEARISH") or not fresh or selected is None:
                reason=("Market is sideways; wait for a clearer trend." if direction not in ("BULLISH","BEARISH")
                        else "Yahoo candle is too old for this selected timeframe." if not fresh
                        else "No suitable near-the-money, trend-aligned simulated premium matches this budget.")
                summary=section("TOP SETUP • WAIT / NO TRADE",ft.Column([
                    txt(reason,14,GOLD,True),
                    note("No entry, stop loss, target or holding-time recommendation is issued."),
                    note("Re-scan with fresh data; verify live option chain and contract with broker.")
                ],spacing=8))
            else:
                side="CE" if selected["call"] else "PE"
                entry=selected["premium"]
                # Explicitly illustrative percentage scenarios, NOT forecasted fills.
                stop=entry*0.80
                target1=entry*1.20
                target2=entry*1.35
                horizon={"1m":"3–10 minutes","5m":"10–30 minutes","15m":"30–60 minutes",
                         "1h":"1–3 hours","1d":"1 trading day"}[interval]
                intrinsic=max(0.0,price-selected["strike"]) if selected["call"] else max(0.0,selected["strike"]-price)
                time_value=max(0.0,entry-intrinsic)
                summary=section("TOP SETUP • SIMULATION ONLY",ft.Column([
                    txt(f'{sym} {selected["strike"]:g} {side} • modeled ₹{entry:.2f}',16,GOLD,True),
                    txt(f'Illustrative entry ₹{entry:.2f} | SL ₹{stop:.2f}',14),
                    txt(f'Illustrative targets ₹{target1:.2f} / ₹{target2:.2f}',14),
                    txt("Scenario horizon: "+horizon,13),
                    txt(f'Intrinsic ≈ ₹{intrinsic:.2f} | Time value ≈ ₹{time_value:.2f}',12),
                    note("20% stop and 20%/35% targets are fixed hypothetical scenarios, not market-derived predictions."),
                    note("Actual strike, expiry, premium, liquidity and order execution are UNVERIFIED. Do not trade from this simulation alone.")
                ],spacing=8))
            controls.insert(0,summary)
            if rows:
                controls.append(section("Premium candidates • SIMULATION ONLY",ft.Column(rows,spacing=8)))
            else:
                nearest=sorted(pool,key=lambda v:abs(v["premium"]-(low+high)/2) if math.isfinite(high) else v["dist"])[:3]
                lines=[note("No modeled contract matched this budget. Here are nearby theoretical prices; not real exchange quotes.")]
                for v in nearest:
                    lines.append(txt(f'{v["strike"]:g} {"CE" if v["call"] else "PE"} ≈ ₹{v["premium"]:.2f} (simulation)',12))
                controls.append(section("No budget match — alternatives",ft.Column(lines,spacing=7)))
            controls.append(section("Risk / validation",ft.Column([
                note("SIMULATION ONLY • Verify actual expiry, strikes, bid/ask, OI, lot size, IV and theta with a broker. Premium can decay rapidly; do not trade from modeled quotes."),
                ft.ElevatedButton("Dashboard",on_click=lambda e:select(0))
            ])))
            scan_shared.update(direction=direction,basis=basis,tf=interval,symbol=sym)
            scan_result.controls=controls
            scan_last_success[0]=datetime.now().timestamp()
            scan_next_refresh[0]=(scan_last_success[0]+int(scan_refresh.value or "60")) if scan_live.value else None
            scan_status.value="Last checked "+datetime.now().strftime("%H:%M:%S")+" • Yahoo candle "+updated.strftime("%H:%M UTC")+" • updates only when source changes"
            scan_age_display.value=(f"Last scan: 0 sec ago | Candle age: {max(0,int(age_hours*3600))} sec | Next auto refresh: "+(f"{int(scan_refresh.value or '60')} sec" if scan_live.value else "OFF"))
        except Exception as exc:
            scan_status.value="Refresh failed • last results may be stale"
            if not scan_live.value or not scan_result.controls:
                scan_result.controls=[card(unavailable("Scanner: "+str(exc)),note("No signal was generated. Check filters, internet and Yahoo availability."))]
        finally:
            scan_busy[0]=False
            if current[0] in (0,3):select(current[0])
    pages=[dashboard,options,settings,scanner]
    icons=[ft.Icons.DASHBOARD,ft.Icons.TABLE_CHART,ft.Icons.SETTINGS,ft.Icons.SEARCH]
    names=["Home","Options","Settings","Scanner"]
    body=ft.Column(expand=True,scroll=ft.ScrollMode.AUTO,spacing=12)
    navbar=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY,spacing=0,expand=True)
    current=[0]
    def select(i):
        current[0]=i
        body.controls.clear()
        body.controls.extend(pages[i]())
        navbar.controls.clear()
        for j in range(len(pages)):
            navbar.controls.append(ft.Container(content=ft.TextButton(content=ft.Column([ft.Icon(icons[j],color=GOLD if i==j else MUTED,size=19),txt(names[j],9,GOLD if i==j else MUTED)],horizontal_alignment=ft.CrossAxisAlignment.CENTER,spacing=2),on_click=lambda e,k=j:select(k),style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=0,vertical=6))),expand=1))
        page.update()
    page.add(ft.Container(content=ft.Row([ft.Icon(ft.Icons.EMOJI_EVENTS,color=GOLD,size=30),ft.Column([txt("BOT KING",19,GOLD,True),note("AI Trading Assistant • v1.2.0")],spacing=0),ft.Icon(ft.Icons.NOTIFICATIONS_NONE,color=GOLD)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),padding=ft.padding.only(left=14,right=14,top=32,bottom=7),bgcolor=BG),ft.Container(content=body,expand=True,padding=ft.padding.symmetric(horizontal=12,vertical=5)),ft.Container(content=navbar,bgcolor="#102330",padding=ft.padding.symmetric(vertical=5)))
    select(0)
    page.run_task(auto_scan_loop,scan_auto_generation[0])
    async def refresh_market():
        nonlocal market_status
        while True:
            if prefs.get("source")=="Yahoo Finance":
                successes=0
                symbols=list(dict.fromkeys(["NIFTY","BANKNIFTY","SENSEX"]+all_watch_symbols()))
                semaphore=asyncio.Semaphore(5)
                async def load_one(sym):
                    async with semaphore:
                        try:
                            quotes[sym]=await asyncio.to_thread(get_yahoo,sym)
                            return True
                        except Exception:
                            return False
                results=await asyncio.gather(*(load_one(sym) for sym in symbols))
                successes=sum(results)
                market_status=f"Yahoo Finance • {successes} instruments updated • "+datetime.now().strftime("%H:%M") if successes else "Yahoo Finance unavailable: check internet / rate limits"
                # Fresh candle-only Top 5; scan across the watchlist and include indexes.
                async def rank_one(sym):
                    async with semaphore:
                        try:
                            data=await asyncio.to_thread(get_yahoo,sym,"5m","5d")
                            return sym,analyze(data["bars"],filter_selected[:],"5m")
                        except Exception:return sym,None
                pairs=await asyncio.gather(*(rank_one(sym) for sym in list(dict.fromkeys(watch_symbols))))
                top5_candidates[:]=rank_candidates({sym:res for sym,res in pairs if res},max_age_seconds=1800)
                top5_last_update[0]=datetime.now().strftime("%d %b %H:%M")
                try:
                    if current[0]!=3:select(current[0])
                except Exception:pass
            await asyncio.sleep(120)
    page.run_task(refresh_market)

def main(page: ft.Page):
    try:
        app_main(page)
    except Exception:
        error=traceback.format_exc()
        print("BOT KING STARTUP ERROR:"+error,flush=True)
        page.controls.clear()
        page.bgcolor="#03080E"
        page.padding=16
        page.add(
            ft.Text("BOT KING — Startup Error",size=22,color="#FFCB12",weight=ft.FontWeight.BOLD),
            ft.Text("The app could not initialize. Please send a screenshot of this error.",color="#FFFFFF"),
            ft.Column([ft.Text(error,size=11,color="#FF8796",selectable=True)],scroll=ft.ScrollMode.AUTO,expand=True),
        )
        page.update()

ft.app(target=main)
