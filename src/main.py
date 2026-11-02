import flet as ft
import json
import asyncio
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

BG="#03080E"; PANEL="#071821"; PANEL2="#0B2630"; GOLD="#FFCB12"; GREEN="#00E778"; RED="#FF405D"; WHITE="#F1F5FA"; MUTED="#9DB2BD"
STATE=Path.home()/".bot_king_settings.json"

def main(page:ft.Page):
    page.title="BOT KING"; page.theme_mode=ft.ThemeMode.DARK; page.bgcolor=BG; page.padding=0; page.spacing=0
    page.window_width=420; page.window_height=850
    prefs={"mode":"Paper","stop_loss":2.0,"target":4.0,"max_trades":2,"confidence":75,"source":"Yahoo Finance","api_url":"","api_key":""}
    try:
        if STATE.exists(): prefs.update(json.loads(STATE.read_text()))
    except Exception: pass
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
        try: STATE.write_text(json.dumps(prefs))
        except Exception: pass
    def txt(s,size=14,color=WHITE,bold=False):
        return ft.Text(str(s),size=size,color=color,weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL)
    def card(*children):
        return ft.Container(content=ft.Column(list(children),spacing=12),bgcolor=PANEL,border_radius=18,padding=16,border=ft.border.all(1,"#A57D0C"))
    def heading(s):return txt(s,22,WHITE,True)
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

    def section(title,child):return card(txt(title,17,GOLD,True),child)
    dashboard_index=["NIFTY"]
    dashboard_tool=[""]
    def dashboard_index_set(name):
        dashboard_index[0]=name
        select(0)
    def dashboard_tool_open(name):
        dashboard_tool[0]=name
        if name=="Paper Trade":select(4)
        elif name=="OI Data":select(3)
        else:select(0)
    def dashboard():
        def index(name):
            return ft.Container(content=ft.Column([txt(name,13,MUTED,True),txt(quote_price(name),20,GOLD,True),txt(quote_change(name),11,price_color(name),True)]),bgcolor=PANEL2,border_radius=14,padding=12,expand=True)
        return [heading("Market Dashboard • YAHOO PREVIEW"),ft.Row([ft.TextButton(text=label,on_click=lambda e,v=val:dashboard_index_set(v),style=ft.ButtonStyle(color=GOLD if dashboard_index[0]==val else MUTED)) for label,val in [("NIFTY 50","NIFTY"),("BANK NIFTY","BANKNIFTY"),("SENSEX","SENSEX")]],scroll=ft.ScrollMode.AUTO),card(ft.Row([txt(dashboard_index[0],20,WHITE,True),pill("Yahoo preview" if dashboard_index[0] in quotes else "Offline")],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),txt(quote_price(dashboard_index[0]),36,GOLD,True),txt(quote_change(dashboard_index[0]),16,price_color(dashboard_index[0]),True),note(market_status),ft.Row([note("Source: Yahoo Finance"),note("Indicative / may be delayed")],alignment=ft.MainAxisAlignment.SPACE_BETWEEN)),ft.Row([index("NIFTY"),index("BANKNIFTY"),index("SENSEX")]),section("Market Sentiment",ft.Column([txt("Bullish —   /   Bearish —",17),unavailable("breadth and historical data required")])),section("Market Breadth",note("Advances —   Declines —   A/D ratio —")),section("Today's Setup",ft.Column([note("Bias: unavailable"),note("Support / Resistance: unavailable"),note("Signals are disabled until backtested")])),section("Trading Tools",ft.Column([ft.Row([ft.ElevatedButton(n,on_click=lambda e,v=n:dashboard_tool_open(v)) for n in ["OI Data","Scanner","Signals","Paper Trade"]],wrap=True),note("Scanner and Signals: live signal engine not yet connected" if dashboard_tool[0] in ("Scanner","Signals") else "Choose a tool above")])),section("Top Movers",unavailable("live NIFTY 50 constituent feed required"))]
    search=ft.TextField(hint_text="Search symbol (e.g. RELIANCE)",border_color="#294158",color=WHITE,bgcolor=PANEL2)
    watch_symbols=["RELIANCE","HDFCBANK","ICICIBANK","TCS","INFY","BHARTIARTL","SBIN","ITC","LT","AXISBANK","KOTAKBANK","HINDUNILVR","BAJFINANCE","BAJAJFINSV","MARUTI","M&M","TITAN","SUNPHARMA","ULTRACEMCO","ASIANPAINT","NTPC","POWERGRID","TATAMOTORS","TATASTEEL","JSWSTEEL","HCLTECH","WIPRO","TECHM","NESTLEIND","HINDALCO","ONGC","COALINDIA","ADANIENT","ADANIPORTS","BEL","TRENT","EICHERMOT","GRASIM","CIPLA","DRREDDY","APOLLOHOSP","DIVISLAB","SBILIFE","HDFCLIFE","BAJAJ-AUTO","HEROMOTOCO","BRITANNIA","INDUSINDBK","SHRIRAMFIN","BPCL"]
    watch_list=ft.Column(spacing=8)
    watch_page=[0]
    selected_watch=[""]
    page_size=12
    pager=ft.Row(alignment=ft.MainAxisAlignment.CENTER)
    watch_filter=["All"]
    add_symbol=ft.TextField(label="Add NSE symbol",hint_text="RELIANCE",expand=True)
    feedback=txt("",12,MUTED)
    def add_watch(e):
        sym=(add_symbol.value or "").strip().upper().replace(".NS","")
        if not sym or not sym.replace("-","").replace("&","").isalnum():
            feedback.value="Enter valid NSE symbol"
        elif sym in watch_symbols:
            feedback.value="Already in watchlist"
        else:
            watch_symbols.append(sym)
            add_symbol.value=""
            feedback.value=sym+" added; quote loads on next refresh"
        fill_watch()
    def set_filter(v):
        watch_filter[0]=v
        watch_page[0]=0
        fill_watch()

    def open_stock(sym):
        selected_watch[0]=sym
        if sym not in [o.key for o in symbol.options]:
            symbol.options.append(ft.dropdown.Option(sym))
        symbol.value=sym
        select(2)
    def remove_stock(sym):
        if sym in watch_symbols:watch_symbols.remove(sym)
        fill_watch()
    def fill_watch(_=None):
        watch_list.controls.clear()
        matching=[]
        for sym in watch_symbols:
            if search.value and search.value.upper() not in sym:continue
            change=(quotes.get(sym) or {}).get("change")
            direction="Bullish" if change is not None and change>0 else "Bearish" if change is not None and change<0 else "Neutral"
            if watch_filter[0]!="All" and watch_filter[0]!=direction:continue
            matching.append(sym)
        pages_count=max(1,(len(matching)+page_size-1)//page_size)
        watch_page[0]=min(watch_page[0],pages_count-1)
        for sym in matching[watch_page[0]*page_size:(watch_page[0]+1)*page_size]:
            watch_list.controls.append(ft.Container(content=ft.Row([ft.IconButton(icon=ft.Icons.CANDLESTICK_CHART,icon_color=GOLD,tooltip="Open chart",on_click=lambda e,v=sym:open_stock(v)),ft.Column([txt(sym,15,WHITE,True),note("Tap chart icon")],expand=True,spacing=1),ft.Column([txt(quote_price(sym),16,price_color(sym),True),txt(quote_change(sym),11,price_color(sym))],horizontal_alignment=ft.CrossAxisAlignment.END),ft.IconButton(icon=ft.Icons.CLOSE,icon_color=RED,tooltip="Remove stock",on_click=lambda e,v=sym:remove_stock(v))]),bgcolor=PANEL,border_radius=12,padding=8))
        pager.controls.clear()
        pager.controls.extend([ft.TextButton("‹",on_click=lambda e:move_watch(-1)),note(f"{watch_page[0]+1} / {pages_count}  •  {len(matching)} stocks"),ft.TextButton("›",on_click=lambda e:move_watch(1))])
        page.update()
    def move_watch(delta):
        watch_page[0]=max(0,watch_page[0]+delta)
        fill_watch()
    search.on_change=lambda e:(watch_page.__setitem__(0,0),fill_watch())
    def watchlist():
        fill_watch()
        return [ft.Row([heading("Watchlist (NIFTY 50)"),pill("50 stocks",True)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),search,ft.Row([ft.TextButton(text=n,on_click=lambda e,v=n:set_filter(v),style=ft.ButtonStyle(color=GOLD if watch_filter[0]==n else MUTED)) for n in ["All","Bullish","Bearish","Neutral"]],scroll=ft.ScrollMode.AUTO),ft.Row([add_symbol,ft.ElevatedButton("Add",on_click=add_watch,bgcolor=GOLD,color=BG)]),feedback,note(market_status+" • Prices indicative / may be delayed"),watch_list,pager]
    symbol=ft.Dropdown(label="Symbol",value="NIFTY",options=[ft.dropdown.Option(x) for x in ["NIFTY","BANKNIFTY","SENSEX"]],expand=True)
    timeframe=ft.Dropdown(label="Timeframe",value="5m",options=[ft.dropdown.Option(x) for x in ["1m","5m","15m","1h","1D"]],width=120)
    ema=ft.Switch(label="EMA 20 / 50",value=True,active_color=GREEN)
    vwap=ft.Switch(label="VWAP",value=True,active_color=GREEN)
    rsi=ft.Switch(label="RSI",value=False,active_color=GREEN)
    chart_tab=["Chart"]
    drawing_mode=["None"]
    compare_symbol=ft.Dropdown(label="Compare",value="BANKNIFTY",options=[ft.dropdown.Option(x) for x in ["NIFTY","BANKNIFTY","SENSEX","RELIANCE","HDFCBANK"]])
    macd=ft.Switch(label="MACD (12,26,9)",value=False,active_color=GREEN)
    volume=ft.Switch(label="Volume",value=True,active_color=GREEN)
    ema200=ft.Switch(label="EMA 200",value=False,active_color=GREEN)
    chart_message=txt("",12,MUTED)
    def choose_chart_tab(v):
        chart_tab[0]=v
        select(2)
    chart_style=["Candlestick"]
    chart_style_picker=ft.Dropdown(label="Chart type",value="Candlestick",options=[ft.dropdown.Option(x) for x in ["Candlestick","Line"]])
    def chart_style_apply(e):
        chart_style[0]=chart_style_picker.value
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
    def charts():
        content=[heading("Charts • Technical Analysis"),ft.Row([ft.TextButton(text=n,on_click=lambda e,v=n:choose_chart_tab(v),style=ft.ButtonStyle(color=GOLD if chart_tab[0]==n else MUTED)) for n in ["Chart","Indicators","Drawing","Compare","Levels","Signals"]],scroll=ft.ScrollMode.AUTO),ft.Row([symbol,timeframe]),ft.ElevatedButton("Apply / Refresh",on_click=lambda e:page.run_task(load_chart),bgcolor=GOLD,color=BG)]
        if chart_tab[0]=="Chart":
            content.extend([ft.Row([chart_style_picker,ft.ElevatedButton("Set chart type",on_click=chart_style_apply)]),section("Yahoo Candlestick Chart",chart_candles()),section("Price Trend",ft.Container(content=tiny_chart(symbol.value),height=120)),ft.Row([ft.TextButton("Indicators",on_click=lambda e:choose_chart_tab("Indicators")),ft.TextButton("Drawing",on_click=lambda e:choose_chart_tab("Drawing"))])])
        elif chart_tab[0]=="Indicators":
            content.append(section("Indicators • Toggle On / Off",ft.Column([ema,ema200,vwap,rsi,macd,volume,ft.ElevatedButton("Apply indicators",on_click=lambda e:select(2)),note("Selected: "+", ".join(n for n,c in [("EMA20/50",ema),("EMA200",ema200),("VWAP",vwap),("RSI",rsi),("MACD",macd),("Volume",volume)] if c.value)),note("Indicator calculations/overlays require separate implementation and validated candle history.")])))
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
    chain_symbol=ft.Dropdown(label="Index",value="NIFTY",options=[ft.dropdown.Option(x) for x in ["NIFTY","BANKNIFTY","FINNIFTY"]],expand=True)
    expiry=ft.TextField(label="Expiry (YYYY-MM-DD)",hint_text="Choose actual expiry",expand=True)
    option_tab=["Option Chain"]
    strategy_choice=[""]
    option_notice=txt("",12,MUTED)
    def choose_option_tab(v):
        option_tab[0]=v
        select(3)
    def choose_strategy(v):
        strategy_choice[0]=v
        select(3)
    def options():
        content=[heading("Options Chain & Flow Analysis"),ft.Row([ft.TextButton(text=n,on_click=lambda e,v=n:choose_option_tab(v),style=ft.ButtonStyle(color=GOLD if option_tab[0]==n else MUTED)) for n in ["Option Chain","OI Analysis","PCR","Premium Flow","Strategy"]],scroll=ft.ScrollMode.AUTO),ft.Row([chain_symbol,expiry]),ft.ElevatedButton("Apply selection",on_click=lambda e:select(3)),note("Selected: "+str(chain_symbol.value)+" • "+str(expiry.value or "expiry not set"))]
        if option_tab[0]=="Option Chain":
            content.extend([section("Option Chain",ft.Column([ft.Row([txt("CALL (CE)",14,GREEN,True),txt("STRIKE",14,GOLD,True),txt("PUT (PE)",14,RED,True)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),unavailable("Broker options market-data API required")]))])
        elif option_tab[0]=="OI Analysis":content.append(section("OI Analysis",unavailable("Live CE/PE open interest API not connected")))
        elif option_tab[0]=="PCR":content.append(section("Put Call Ratio",unavailable("PCR requires validated option-chain data")))
        elif option_tab[0]=="Premium Flow":content.append(section("Premium Money Flow",unavailable("Premium-flow API not connected")))
        else:
            content.append(section("Strategy Selector",ft.Column([ft.Row([ft.ElevatedButton(n,on_click=lambda e,v=n:choose_strategy(v)) for n in ["Bull Call Spread","Bear Put Spread","Iron Condor"]],wrap=True),note("Selected strategy: "+(strategy_choice[0] or "None")),note("Educational preview only; no orders are placed")])))
        return content
    mode=ft.Dropdown(label="Trading mode",value=prefs["mode"],options=[ft.dropdown.Option(x) for x in ["Paper","Manual","Semi-Auto","Auto"]])
    source=ft.Dropdown(label="Data provider",value=prefs["source"],options=[ft.dropdown.Option(x) for x in ["Yahoo Finance","Broker API"]])
    broker=ft.Dropdown(label="Broker",value="Angel One",options=[ft.dropdown.Option(x) for x in ["Angel One","Dhan","Zerodha Kite","Upstox","FYERS","Alice Blue","5paisa","ICICI Direct","Kotak Neo","Motilal Oswal","Custom API"]])
    api_url=ft.TextField(label="Broker API base URL",value=prefs["api_url"])
    api_key=ft.TextField(label="API key (local only)",value=prefs["api_key"],password=True,can_reveal_password=True)
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
            prefs.update(mode=mode.value,source=source.value,broker=broker.value,api_url=api_url.value,stop_loss=stop,target=take,max_trades=count,confidence=int(conf.value))
            save();status.value="Preferences saved locally. Live orders remain disabled.";status.color=GREEN
        except Exception:
            status.value="Invalid risk values. Check stop loss, target and max trades.";status.color=RED
        page.update()
    broker.value=prefs.get("broker","Angel One")
    settings_tab=["Trading Bot"]
    def choose_settings_tab(v):
        settings_tab[0]=v
        select(4)
    def settings():
        tabs=["Trading Bot","Broker & API","Risk & Money","Strategy","Alerts","Backtest"]
        content=[heading("Settings & Trading Bot"),ft.Row([ft.TextButton(text=n,on_click=lambda e,v=n:choose_settings_tab(v),style=ft.ButtonStyle(color=GOLD if settings_tab[0]==n else MUTED)) for n in tabs],scroll=ft.ScrollMode.AUTO)]
        if settings_tab[0]=="Trading Bot":
            content.extend([section("Trading Mode",ft.Column([mode,note("Paper mode only for simulated orders. Live execution disabled.")])),section("Paper Trading Controls",ft.Column([ft.Row([ft.ElevatedButton("BUY (Paper)",on_click=lambda e:paper_trade("BUY"),bgcolor=GREEN,color=BG),ft.ElevatedButton("SELL (Paper)",on_click=lambda e:paper_trade("SELL"),bgcolor=RED,color=WHITE),ft.OutlinedButton("EXIT",on_click=lambda e:paper_trade("EXIT"))],wrap=True),paper_status]))])
        elif settings_tab[0]=="Broker & API":
            content.append(section("Broker & Data Source",ft.Column([broker,source,api_url,note("Broker choices are for future integrations. No authentication or real orders are enabled. Do NOT enter live API keys here.") ])))
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
    pages=[dashboard,watchlist,charts,options,settings]
    icons=[ft.Icons.DASHBOARD,ft.Icons.STAR,ft.Icons.CANDLESTICK_CHART,ft.Icons.TABLE_CHART,ft.Icons.SETTINGS]
    names=["Dashboard","Watchlist","Charts","Options","Settings"]
    body=ft.Column(expand=True,scroll=ft.ScrollMode.AUTO,spacing=16)
    navbar=ft.Row(alignment=ft.MainAxisAlignment.SPACE_AROUND,scroll=ft.ScrollMode.AUTO)
    current=[0]
    def select(i):
        current[0]=i
        body.controls.clear()
        body.controls.extend(pages[i]())
        navbar.controls.clear()
        for j in range(5):
            navbar.controls.append(ft.TextButton(content=ft.Column([ft.Icon(icons[j],color=GOLD if i==j else MUTED,size=23),txt(names[j],10,GOLD if i==j else MUTED)],horizontal_alignment=ft.CrossAxisAlignment.CENTER,spacing=3),on_click=lambda e,k=j:select(k),style=ft.ButtonStyle(padding=6)))
        page.update()
    page.add(ft.Container(content=ft.Row([ft.Icon(ft.Icons.EMOJI_EVENTS,color=GOLD,size=35),ft.Column([txt("BOT KING",23,GOLD,True),note("AI Trading Assistant Pro • v3.0")],spacing=0),ft.Icon(ft.Icons.NOTIFICATIONS_NONE,color=GOLD)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),padding=ft.padding.only(left=16,right=16,top=15,bottom=12),bgcolor=BG),ft.Container(content=body,expand=True,padding=ft.padding.symmetric(horizontal=14,vertical=8)),ft.Container(content=navbar,bgcolor="#071A2B",padding=ft.padding.symmetric(vertical=8)))
    select(0)
    async def refresh_market():
        nonlocal market_status
        while True:
            if prefs.get("source")=="Yahoo Finance":
                successes=0
                for sym in list(dict.fromkeys(["NIFTY","BANKNIFTY","SENSEX"]+watch_symbols)):
                    try:
                        quotes[sym]=await asyncio.to_thread(get_yahoo,sym)
                        successes+=1
                    except Exception:
                        pass
                market_status=f"Yahoo Finance • {successes} instruments updated • "+datetime.now().strftime("%H:%M") if successes else "Yahoo Finance unavailable: check internet / rate limits"
                try:select(current[0])
                except Exception:pass
            await asyncio.sleep(120)
    page.run_task(refresh_market)

ft.app(target=main)
