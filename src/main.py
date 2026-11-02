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
    def dashboard():
        def index(name):
            return ft.Container(content=ft.Column([txt(name,13,MUTED,True),txt(quote_price(name),20,GOLD,True),txt(quote_change(name),11,price_color(name),True)]),bgcolor=PANEL2,border_radius=14,padding=12,expand=True)
        return [heading("Market Dashboard • YAHOO PREVIEW"),ft.Row([pill("NIFTY 50",True),pill("BANK NIFTY"),pill("FIN NIFTY")],scroll=ft.ScrollMode.AUTO),card(ft.Row([txt("NIFTY 50",20,WHITE,True),pill("Yahoo preview" if "NIFTY" in quotes else "Offline")],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),txt(quote_price("NIFTY"),36,GOLD,True),txt(quote_change("NIFTY"),16,price_color("NIFTY"),True),note(market_status),ft.Row([note("Source: Yahoo Finance"),note("Indicative / may be delayed")],alignment=ft.MainAxisAlignment.SPACE_BETWEEN)),ft.Row([index("NIFTY"),index("BANKNIFTY"),index("SENSEX")]),section("Market Sentiment",ft.Column([txt("Bullish —   /   Bearish —",17),unavailable("breadth and historical data required")])),section("Market Breadth",note("Advances —   Declines —   A/D ratio —")),section("Today's Setup",ft.Column([note("Bias: unavailable"),note("Support / Resistance: unavailable"),note("Signals are disabled until backtested")])),section("Trading Tools",ft.Row([pill("OI Data"),pill("Scanner"),pill("Signals"),pill("Paper Trade")],wrap=True)),section("Top Movers",unavailable("live NIFTY 50 constituent feed required"))]
    search=ft.TextField(hint_text="Search symbol (e.g. RELIANCE)",border_color="#294158",color=WHITE,bgcolor=PANEL2)
    watch_symbols=["RELIANCE","HDFCBANK","ICICIBANK","TCS","INFY","BHARTIARTL","SBIN","ITC"]
    watch_list=ft.Column(spacing=8)
    def fill_watch(_=None):
        watch_list.controls.clear()
        for sym in watch_symbols:
            if search.value and search.value.upper() not in sym:continue
            watch_list.controls.append(ft.Container(content=ft.Row([ft.Icon(ft.Icons.STAR_BORDER,color=GOLD),ft.Column([txt(sym,15,WHITE,True),note("NSE")],expand=True,spacing=1),ft.Column([txt(quote_price(sym),16,price_color(sym),True),txt(quote_change(sym),11,price_color(sym))],horizontal_alignment=ft.CrossAxisAlignment.END)]),bgcolor=PANEL,border_radius=12,padding=14))
        page.update()
    search.on_change=fill_watch
    def watchlist():
        fill_watch()
        return [ft.Row([heading("Watchlist (NIFTY 50)"),pill("NIFTY 50",True)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),search,ft.Row([pill("All",True),pill("Bullish"),pill("Bearish"),pill("Neutral"),pill("Filters")],scroll=ft.ScrollMode.AUTO),note(market_status+" • Prices indicative / may be delayed"),watch_list]
    symbol=ft.Dropdown(label="Symbol",value="NIFTY",options=[ft.dropdown.Option(x) for x in ["NIFTY","BANKNIFTY","SENSEX"]],expand=True)
    timeframe=ft.Dropdown(label="Timeframe",value="5m",options=[ft.dropdown.Option(x) for x in ["1m","5m","15m","1h","1D"]],width=120)
    ema=ft.Switch(label="EMA 20 / 50",value=True,active_color=GREEN)
    vwap=ft.Switch(label="VWAP",value=True,active_color=GREEN)
    rsi=ft.Switch(label="RSI",value=False,active_color=GREEN)
    def charts():
        return [heading("Charts • Technical Analysis"),ft.Row([pill("Chart",True),pill("Indicators"),pill("Drawing"),pill("Compare"),pill("Levels"),pill("Signals")],scroll=ft.ScrollMode.AUTO),ft.Row([symbol,timeframe]),card(ft.Container(content=ft.Column([ft.Icon(ft.Icons.CANDLESTICK_CHART,size=72,color=GOLD),heading("Candlestick chart"),note("Yahoo Finance candles • may be delayed"),note(market_status)],horizontal_alignment=ft.CrossAxisAlignment.CENTER,alignment=ft.MainAxisAlignment.CENTER),height=180,alignment=ft.alignment.center)),section("Yahoo Chart Preview",ft.Container(content=tiny_chart(symbol.value),height=160)),section("Indicators",ft.Column([ema,vwap,rsi])),section("Analysis",note("Yahoo Finance preview only. Trading signals and broker execution are disabled until verified."))]
    chain_symbol=ft.Dropdown(label="Index",value="NIFTY",options=[ft.dropdown.Option(x) for x in ["NIFTY","BANKNIFTY","FINNIFTY"]],expand=True)
    expiry=ft.TextField(label="Expiry (YYYY-MM-DD)",hint_text="Choose actual expiry",expand=True)
    def options():
        return [heading("Options Chain & Flow Analysis"),ft.Row([chain_symbol,expiry]),card(ft.Row([pill("PCR —"),pill("Total OI —"),pill("Chg OI —")],wrap=True),unavailable("licensed option-chain API required")),card(ft.Row([txt("CALL (CE)",14,GREEN,True),txt("STRIKE",14,GOLD,True),txt("PUT (PE)",14,RED,True)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),ft.Divider(color="#294158"),note("OI     LTP       —       LTP     OI"),unavailable("no option prices or strikes received")),section("Premium Money Flow",note("Traded value: —   PCR: —   Highest CE/PE OI: —")),section("OI Change & PCR Trend",unavailable("historical options API required")),section("Intraday Options Setup",unavailable("no validated live data / backtest")),section("Popular Strategies",ft.Row([pill("Bull Call Spread"),pill("Bear Put Spread"),pill("Iron Condor")],wrap=True))]
    mode=ft.Dropdown(label="Trading mode",value=prefs["mode"],options=[ft.dropdown.Option(x) for x in ["Paper","Manual","Semi-Auto","Auto"]])
    source=ft.Dropdown(label="Data provider",value=prefs["source"],options=[ft.dropdown.Option(x) for x in ["Yahoo Finance","Broker API"]])
    api_url=ft.TextField(label="Broker API base URL",value=prefs["api_url"])
    api_key=ft.TextField(label="API key (local only)",value=prefs["api_key"],password=True,can_reveal_password=True)
    sl=ft.TextField(label="Stop loss %",value=str(prefs["stop_loss"]),keyboard_type=ft.KeyboardType.NUMBER)
    target=ft.TextField(label="Target %",value=str(prefs["target"]),keyboard_type=ft.KeyboardType.NUMBER)
    limit=ft.TextField(label="Max trades per day",value=str(prefs["max_trades"]),keyboard_type=ft.KeyboardType.NUMBER)
    conf=ft.Slider(min=70,max=85,divisions=15,value=prefs["confidence"],label="{value}%")
    status=txt("Trading disabled until authenticated API, validation and explicit confirmation.",12,RED)
    def save_settings(_):
        try:
            stop=float(sl.value);take=float(target.value);count=int(limit.value)
            if not (0<stop<=100 and 0<take<=100 and 1<=count<=50):raise ValueError()
            prefs.update(mode=mode.value,source=source.value,api_url=api_url.value,api_key=api_key.value,stop_loss=stop,target=take,max_trades=count,confidence=int(conf.value))
            save();status.value="Preferences saved locally. Live orders remain disabled.";status.color=GREEN
        except Exception:
            status.value="Invalid risk values. Check stop loss, target and max trades.";status.color=RED
        page.update()
    def settings():
        return [heading("Settings & Trading Bot"),ft.Row([pill("Trading Bot",True),pill("Broker & API"),pill("Risk & Money"),pill("Strategy"),pill("Alerts"),pill("Backtest")],scroll=ft.ScrollMode.AUTO),section("Trading Mode",ft.Column([mode,note("Paper is simulation. Live order execution is NOT implemented.")])),section("Risk Management",ft.Column([ft.Row([sl,target]),limit,txt("Signal confidence filter (70–85%)",14),conf,note("Bullish/Bearish confidence is not available without validated signals")])),section("Market Data & API",ft.Column([source,api_url,api_key,note("Never publish API secrets in GitHub. Credentials here are local app preferences; use secure storage for production.")])),ft.ElevatedButton("Save settings",on_click=save_settings,bgcolor=GOLD,color=BG),status,section("Safety",note("No real-money orders, auto-trading, guaranteed signals, or invented live prices. Broker integration requires a separate authenticated backend."))]
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
    page.add(ft.Container(content=ft.Row([ft.Icon(ft.Icons.EMOJI_EVENTS,color=GOLD,size=35),ft.Column([txt("BOT KING",23,GOLD,True),note("AI Trading Assistant Pro • v3.0")],spacing=0),ft.Icon(ft.Icons.NOTIFICATIONS_NONE,color=GOLD)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),padding=ft.padding.only(left=16,right=16,top=15,bottom=12),bgcolor=BG),ft.Container(content=ft.Row([ft.TextButton(text=n,on_click=lambda e,k=j:select(k),style=ft.ButtonStyle(color=GOLD if current[0]==j else MUTED)) for j,n in enumerate(names)],scroll=ft.ScrollMode.AUTO),padding=6),ft.Container(content=body,expand=True,padding=ft.padding.symmetric(horizontal=14,vertical=8)),ft.Container(content=navbar,bgcolor="#071A2B",padding=ft.padding.symmetric(vertical=8)))
    select(0)
    async def refresh_market():
        nonlocal market_status
        while True:
            if prefs.get("source")=="Yahoo Finance":
                successes=0
                for sym in ["NIFTY","BANKNIFTY","SENSEX"]+watch_symbols:
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
