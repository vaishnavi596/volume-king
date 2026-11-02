import flet as ft
import json
import traceback
import asyncio
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta
from pathlib import Path

BG="#03080E"; PANEL="#071821"; PANEL2="#0B2630"; GOLD="#FFCB12"; GREEN="#00E778"; RED="#FF405D"; WHITE="#F1F5FA"; MUTED="#9DB2BD"
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
    chart_position={"side":None,"symbol":None,"entry":None,"qty":0}
    chart_paper_status=txt("Paper position: FLAT",12,MUTED)
    def chart_paper_trade(side):
        if side=="EXIT":
            chart_position.update(side=None,symbol=None,entry=None,qty=0)
            chart_paper_status.value="Paper position closed."
        else:
            try:
                qty=int(chart_quantity.value)
                price=(quotes.get(symbol.value) or {}).get("price")
                if qty<1 or qty>100000 or price is None:raise ValueError()
                chart_position.update(side=side,symbol=symbol.value,entry=float(price),qty=qty)
                chart_paper_status.value="Paper "+side+" recorded. No real order."
            except (ValueError,TypeError):
                chart_paper_status.value="Valid quantity and available quote required."
        select(2)
    def chart_position_text():
        p=chart_position
        if not p["side"]:return "Paper position: FLAT"
        price=(quotes.get(p["symbol"]) or {}).get("price")
        pnl="P&L unavailable" if price is None else "Unrealized P&L ₹"+format((price-p["entry"])*p["qty"]*(1 if p["side"]=="BUY" else -1),",.2f")
        return "Paper "+p["side"]+" "+p["symbol"]+" ×"+str(p["qty"])+" @ ₹"+format(p["entry"],",.2f")+" • "+pnl
    def charts():
        content=[heading("Charts • Technical Analysis"),ft.Row([ft.TextButton(text=n,on_click=lambda e,v=n:choose_chart_tab(v),style=ft.ButtonStyle(color=GOLD if chart_tab[0]==n else MUTED)) for n in ["Chart","Indicators","Drawing","Compare","Levels","Signals"]],scroll=ft.ScrollMode.AUTO),ft.Row([symbol,timeframe]),ft.ElevatedButton("Apply / Refresh",on_click=lambda e:page.run_task(load_chart),bgcolor=GOLD,color=BG)]
        if chart_tab[0]=="Chart":
            content.append(section("Stock Details • "+symbol.value,ft.Column([
                txt("₹ "+quote_price(symbol.value),26,GOLD,True),
                txt("Change "+quote_change(symbol.value),14,price_color(symbol.value),True),
                note("Yahoo preview • delayed or unavailable"),
                chart_quantity,
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
        if e is not None:select(3)
    def add_option_symbol(e):
        sym=(option_add_symbol.value or "").strip().upper().replace(".NS","")
        if sym and sym.replace("-","").replace("&","").isalnum() and sym not in [o.key for o in chain_symbol.options]:
            chain_symbol.options.append(ft.dropdown.Option(sym))
        if sym and sym in [o.key for o in chain_symbol.options]:
            chain_symbol.value=sym
            option_add_symbol.value=""
            refresh_option_expiry()
        select(3)
    chain_symbol.on_change=refresh_option_expiry
    option_expiry_choice.on_change=refresh_option_expiry
    refresh_option_expiry()
    option_tab=["Option Chain"]
    strategy_choice=[""]
    option_notice=txt("",12,MUTED)
    def choose_option_tab(v):
        option_tab[0]=v
        select(3)
    def choose_strategy(v):
        strategy_choice[0]=v
        select(3)
    option_strike=ft.TextField(label="Strike price",hint_text="e.g. 25000",keyboard_type=ft.KeyboardType.NUMBER)
    option_side=ft.Dropdown(label="Contract",value="CE",options=[ft.dropdown.Option("CE"),ft.dropdown.Option("PE")],width=120)
    option_qty=ft.TextField(label="Lots (paper)",value="1",keyboard_type=ft.KeyboardType.NUMBER,width=120)
    option_paper_note=txt("Option paper entry requires verified premium and lot size.",12,MUTED)
    def option_paper_action(side):
        option_paper_note.value="Cannot "+side+": verified CE/PE premium, listed strike and lot size unavailable. No order placed."
        page.update()
    def options():
        content=[heading("Options Chain & Flow Analysis"),ft.Row([ft.TextButton(text=n,on_click=lambda e,v=n:choose_option_tab(v),style=ft.ButtonStyle(color=GOLD if option_tab[0]==n else MUTED)) for n in ["Option Chain","OI Analysis","PCR","Premium Flow","Strategy"]],scroll=ft.ScrollMode.AUTO),ft.Row([chain_symbol,option_expiry_choice]),ft.Row([expiry]),option_expiry_note,ft.Row([option_add_symbol,ft.ElevatedButton("Add",on_click=add_option_symbol)]),note("Stock options only where F&O contracts are listed; selection does not confirm availability."),ft.ElevatedButton("Apply selection",on_click=lambda e:select(3)),note("Selected: "+str(chain_symbol.value)+" • "+str(expiry.value or "expiry not set"))]
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
    emergency_stop=ft.Switch(label="Emergency stop: block new paper entries",value=bool(prefs.get("emergency_stop",False)),active_color=RED)
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
        select(4)
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
                try:select(current[0])
                except Exception:pass
            await asyncio.sleep(120)
    page.run_task(refresh_market)

def main(page: ft.Page):
    try:
        app_main(page)
    except Exception:
        error=traceback.format_exc()
        print("BOT KING STARTUP ERROR:\\n"+error,flush=True)
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
