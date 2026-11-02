
import flet as ft
import asyncio
import json
import urllib.request
from datetime import datetime

GOLD = "#F5C542"
BG = "#08111F"
CARD = "#142238"
MUTED = "#AAB7C8"
GREEN = "#22C55E"
RED = "#EF4444"

NIFTY50 = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT",
    "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV",
    "BEL", "BHARTIARTL", "CIPLA", "COALINDIA",
    "DRREDDY", "EICHERMOT", "ETERNAL", "GRASIM",
    "HCLTECH", "HDFCBANK", "HDFCLIFE", "HINDALCO",
    "HINDUNILVR", "ICICIBANK", "INDUSINDBK", "INFY",
    "ITC", "JIOFIN", "JSWSTEEL", "KOTAKBANK",
    "LT", "M&M", "MARUTI", "NESTLEIND",
    "NTPC", "ONGC", "POWERGRID", "RELIANCE",
    "SBILIFE", "SBIN", "SHRIRAMFIN", "SUNPHARMA",
    "TATACONSUM", "TATAMOTORS", "TATASTEEL", "TCS",
    "TECHM", "TITAN", "TRENT", "ULTRACEMCO",
    "WIPRO", "MAXHEALTH"
]

SYMBOLS = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN"
}


def yahoo_symbol(symbol):
    symbol = symbol.strip().upper()
    return SYMBOLS.get(
        symbol, symbol if symbol.startswith("^") else symbol + ".NS"
    )


def yahoo_data(symbol, interval="5m", period="1d"):
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + yahoo_symbol(symbol)
        + f"?range={period}&interval={interval}"
    )
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def get_quote(symbol):
    try:
        data = yahoo_data(symbol)
        result = data["chart"]["result"][0]
        meta = result["meta"]
        price = meta.get("regularMarketPrice")
        previous = (
            meta.get("chartPreviousClose") or meta.get("previousClose")
        )
        if price is None:
            return None
        change = (
            ((price - previous) / previous) * 100
            if previous else None
        )
        return {"price": float(price), "change": change}
    except Exception:
        return None


def get_candles(symbol, interval):
    data = yahoo_data(symbol, interval, "1d")
    result = data["chart"]["result"][0]
    timestamps = result.get("timestamp", [])
    quote = result["indicators"]["quote"][0]
    rows = []
    for i, stamp in enumerate(timestamps):
        try:
            if quote["close"][i] is None:
                continue
            rows.append({
                "time": datetime.fromtimestamp(stamp).strftime("%H:%M"),
                "open": float(quote["open"][i] or 0),
                "high": float(quote["high"][i] or 0),
                "low": float(quote["low"][i] or 0),
                "close": float(quote["close"][i]),
                "volume": int(quote["volume"][i] or 0)
            })
        except Exception:
            continue
    return rows


def main(page: ft.Page):
    page.title = "BOT KING"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 12
    page.scroll = ft.ScrollMode.AUTO

    watch = NIFTY50.copy()
    quotes = {}
    trades = []
    active = "Dashboard"
    alerts = False

    status = ft.Text("BOT KING तैयार है", color=MUTED, size=11)
    body = ft.Column(spacing=12)

    addfield = ft.TextField(
        label="Stock Symbol",
        hint_text="जैसे TATAMOTORS",
        expand=True
    )

    chartsym = ft.TextField(value="NIFTY", label="Chart Symbol", width=160)
    interval = ft.Dropdown(
        label="Timeframe",
        width=120,
        value="5m",
        options=[
            ft.dropdown.Option(x)
            for x in ["1m", "5m", "15m", "30m", "60m"]
        ]
    )

    optsym = ft.TextField(value="NIFTY", label="Options Symbol", width=180)
    tsym = ft.TextField(value="NIFTY", label="Symbol", width=150)
    side = ft.Dropdown(
        label="CE / PE",
        value="CE",
        width=110,
        options=[
            ft.dropdown.Option("CE"),
            ft.dropdown.Option("PE")
        ]
    )
    prem = ft.TextField(label="Premium", value="100", width=130)
    qty = ft.TextField(label="Quantity", value="1", width=100)

    api_key = ft.TextField(
        label="Angel One API Key",
        password=True,
        can_reveal_password=True
    )
    client_code = ft.TextField(label="Client Code")
    pin = ft.TextField(
        label="PIN",
        password=True,
        can_reveal_password=True
    )
    totp = ft.TextField(
        label="TOTP",
        password=True,
        can_reveal_password=True
    )

    qcards = ft.Column(spacing=8)
    watchcol = ft.Column(spacing=8)
    chartcol = ft.Column(spacing=6)
    optcol = ft.Column(spacing=8)
    tradecol = ft.Column(spacing=8)

    def card(title, value, subtitle=""):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, color=MUTED, size=11),
                ft.Text(
                    value, color=GOLD, size=20,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(subtitle, color=MUTED, size=10)
            ], spacing=3),
            bgcolor=CARD,
            padding=12,
            border_radius=10
        )

    async def refresh(e=None):
        status.value = "Market data अपडेट हो रहा है..."
        page.update()
        symbols = ["NIFTY", "BANKNIFTY", "SENSEX"]
        results = await asyncio.gather(
            *[asyncio.to_thread(get_quote, s) for s in symbols],
            return_exceptions=True
        )
        for symbol, result in zip(symbols, results):
            if isinstance(result, dict):
                quotes[symbol] = result
        status.value = "Refresh पूरा हुआ"
        render()

    async def loadquote(symbol):
        status.value = f"{symbol} लोड हो रहा है..."
        page.update()
        result = await asyncio.to_thread(get_quote, symbol)
        if result:
            quotes[symbol] = result
            status.value = f"{symbol} अपडेट हुआ"
        else:
            status.value = f"{symbol}: डेटा उपलब्ध नहीं"
        render()

    async def loadchart(e=None):
        chartcol.controls = [
            ft.Text("चार्ट लोड हो रहा है...", color=MUTED)
        ]
        page.update()
        try:
            rows = await asyncio.to_thread(
                get_candles, chartsym.value, interval.value
            )
            if not rows:
                raise ValueError("No candles")
            values = [x["close"] for x in rows]
            low, high = min(values), max(values)
            glyph = "▁▂▃▄▅▆▇█"
            spark = "".join(
                glyph[min(7, int((v-low)/(high-low)*7))]
                if high > low else "▄" for v in values
            )
            chartcol.controls = [
                ft.Text(spark, size=24, color=GOLD),
                ft.Text("Time  Open  High  Low  Close  Volume",
                        size=10, color=MUTED)
            ]
            for x in rows[-15:]:
                chartcol.controls.append(
                    ft.Text(
                        f'{x["time"]} {x["open"]:.2f} '
                        f'{x["high"]:.2f} {x["low"]:.2f} '
                        f'{x["close"]:.2f} {x["volume"]}',
                        size=10
                    )
                )
        except Exception:
            chartcol.controls = [
                ft.Text("NO DATA • Candle data उपलब्ध नहीं।", color=RED)
            ]
        page.update()

    async def loadoptions(e=None):
        optcol.controls = [
            ft.Text("NO DATA • असली Options Chain API अभी जुड़ी नहीं है।",
                    color=RED),
            ft.Text(
                "CE/PE Premium, Strike, OI और PCR के लिए "
                "विश्वसनीय डेटा स्रोत जोड़ना बाकी है।",
                color=MUTED, size=11
            )
        ]
        page.update()

    def buy(e):
        try:
            price = float(prem.value)
            number = int(qty.value)
            if price <= 0 or number <= 0:
                raise ValueError()
            trades.append({
                "symbol": tsym.value.upper(),
                "side": side.value,
                "qty": number,
                "entry": price,
                "exit": None
            })
            status.value = "Paper trade खुल गया"
            render()
        except Exception:
            status.value = "Premium और Quantity सही डालें"
            page.update()

    def exittrade(index):
        try:
            price = float(prem.value)
            if price < 0:
                raise ValueError()
            trades[index]["exit"] = price
            status.value = "Paper trade बंद हुआ"
            render()
        except Exception:
            status.value = "Exit Premium सही डालें"
            page.update()

    def addstock(e):
        symbol = addfield.value.strip().upper()
        if symbol and symbol not in watch:
            watch.append(symbol)
            addfield.value = ""
            render()
        else:
            status.value = "Symbol खाली है या पहले से मौजूद है"
            page.update()

    def remove(symbol):
        if symbol in watch:
            watch.remove(symbol)
        render()

    def toggle_alert(e):
        nonlocal alerts
        alerts = e.control.value
        status.value = "Paper Alerts ON" if alerts else "Paper Alerts OFF"
        page.update()

    def broker_connect(e):
        status.value = (
            "अभी सुरक्षित Backend कनेक्शन तैयार होना बाकी है। "
            "Credentials सेव नहीं किए गए।"
        )
        page.update()

    def render():
        body.controls = []

        if active == "Dashboard":
            qcards.controls = []
            for symbol in ["NIFTY", "BANKNIFTY", "SENSEX"]:
                q = quotes.get(symbol)
                if q:
                    change = (
                        f'{q["change"]:+.2f}%'
                        if q["change"] is not None else "Change N/A"
                    )
                    qcards.controls.append(
                        card(symbol, f'{q["price"]:,.2f}', change)
                    )
                else:
                    qcards.controls.append(
                        card(symbol, "NO DATA", "Refresh दबाएँ")
                    )
            body.controls = [
                ft.Text("Market Dashboard", size=20,
                        weight=ft.FontWeight.BOLD),
                qcards,
                ft.ElevatedButton(
                    "↻ Refresh Market",
                    on_click=lambda e: page.run_task(refresh),
                    bgcolor=GOLD, color=BG
                ),
                ft.Text(
                    "Yahoo Finance डेटा है। यह आधिकारिक NSE/BSE "
                    "लाइव फीड नहीं है; देरी हो सकती है।",
                    color=MUTED, size=11
                )
            ]

        elif active == "Watchlist":
            watchcol.controls = []
            body.controls = [
                ft.Text("NIFTY 50 Watchlist", size=20,
                        weight=ft.FontWeight.BOLD),
                ft.Text(f"कुल शेयर: {len(watch)}", color=GOLD),
                ft.Row([
                    addfield,
                    ft.ElevatedButton(
                        "Add", on_click=addstock,
                        bgcolor=GOLD, color=BG
                    )
                ]),
                watchcol
            ]
            for symbol in watch:
                q = quotes.get(symbol)
                price = f'{q["price"]:,.2f}' if q else "--"
                change = (
                    f'{q["change"]:+.2f}%'
                    if q and q["change"] is not None
                    else "भाव के लिए Load दबाएँ"
                )
                watchcol.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(symbol, weight=ft.FontWeight.BOLD),
                                ft.Text(change, size=10, color=MUTED)
                            ], expand=True, spacing=2),
                            ft.Text(price, color=GOLD),
                            ft.TextButton(
                                "Load",
                                on_click=lambda e, s=symbol:
                                    page.run_task(loadquote, s)
                            ),
                            ft.TextButton(
                                "×",
                                on_click=lambda e, s=symbol: remove(s)
                            )
                        ]),
                        bgcolor=CARD, padding=8, border_radius=8
                    )
                )

        elif active == "Charts":
            body.controls = [
                ft.Text("Market Charts", size=20,
                        weight=ft.FontWeight.BOLD),
                ft.Row([chartsym, interval], wrap=True),
                ft.ElevatedButton(
                    "Load Chart", on_click=loadchart,
                    bgcolor=GOLD, color=BG
                ),
                chartcol
            ]

        elif active == "Options":
            body.controls = [
                ft.Text("Options Chain", size=20,
                        weight=ft.FontWeight.BOLD),
                ft.Row([
                    optsym,
                    ft.ElevatedButton(
                        "Load Chain", on_click=loadoptions,
                        bgcolor=GOLD, color=BG
                    )
                ], wrap=True),
                optcol
            ]

        elif active == "Paper":
            opened = sum(t["exit"] is None for t in trades)
            pnl = sum(
                (t["exit"]-t["entry"])*t["qty"]
                for t in trades if t["exit"] is not None
            )
            tradecol.controls = [
                card("Open Trades", str(opened)),
                card("Realized P&L", f"₹{pnl:,.2f}"),
                ft.Text("नया Paper Trade", weight=ft.FontWeight.BOLD),
                ft.Row([tsym, side], wrap=True),
                ft.Row([prem, qty], wrap=True),
                ft.ElevatedButton(
                    "BUY (PAPER)", on_click=buy,
                    bgcolor=GOLD, color=BG
                ),
                ft.Text("Trade History", weight=ft.FontWeight.BOLD)
            ]
            for i, trade in enumerate(trades):
                line = (
                    f'{trade["symbol"]} {trade["side"]} | '
                    f'Qty {trade["qty"]} | Entry ₹{trade["entry"]:.2f}'
                )
                if trade["exit"] is None:
                    tradecol.controls.append(
                        ft.Row([
                            ft.Text(line, size=11, expand=True),
                            ft.TextButton(
                                "Exit",
                                on_click=lambda e, j=i: exittrade(j)
                            )
                        ])
                    )
                else:
                    value = (
                        trade["exit"]-trade["entry"]
                    )*trade["qty"]
                    tradecol.controls.append(
                        ft.Text(
                            line + f' | Exit ₹{trade["exit"]:.2f}'
                            + f' | P&L ₹{value:,.2f}',
                            size=11,
                            color=GREEN if value >= 0 else RED
                        )
                    )
            if not trades:
                tradecol.controls.append(
                    ft.Text("अभी कोई Paper Trade नहीं है।", color=MUTED)
                )
            body.controls = [
                ft.Text("Paper Trading", size=20,
                        weight=ft.FontWeight.BOLD),
                tradecol,
                ft.Text(
                    "यह simulation है। वास्तविक order नहीं जाता। "
                    "ऐप बंद होने पर trades reset हो सकते हैं।",
                    size=10, color=MUTED
                )
            ]

        elif active == "Alerts":
            body.controls = [
                ft.Text("Alerts", size=20, weight=ft.FontWeight.BOLD),
                ft.Switch(
                    label="Paper Alerts ON/OFF",
                    value=alerts, on_change=toggle_alert
                ),
                ft.Text(
                    "Push notifications अभी शामिल नहीं हैं।",
                    color=MUTED, size=11
                )
            ]

        elif active == "Angel One":
            body.controls = [
                ft.Text("Angel One SmartAPI", size=20,
                        weight=ft.FontWeight.BOLD),
                ft.Text(
                    "अपनी API जानकारी यहाँ भरने का इंटरफेस। "
                    "अभी कनेक्शन सक्रिय नहीं है।",
                    color=MUTED, size=11
                ),
                api_key,
                client_code,
                pin,
                totp,
                ft.ElevatedButton(
                    "Connect Angel One",
                    on_click=broker_connect,
                    bgcolor=GOLD, color=BG
                ),
                ft.Text(
                    "सुरक्षित Backend और आधिकारिक SmartAPI लॉगिन "
                    "जोड़ने के बाद ही यह बटन काम करेगा। "
                    "अभी जानकारी सेव नहीं होती।",
                    color=RED, size=11
                )
            ]

    def nav_change(e):
        nonlocal active
        active = e.control.selected
        render()

    destinations = [
        ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
        ft.NavigationBarDestination(icon=ft.Icons.LIST, label="Watch"),
        ft.NavigationBarDestination(icon=ft.Icons.SHOW_CHART, label="Charts"),
        ft.NavigationBarDestination(icon=ft.Icons.CANDlestick_chart,
                                     label="Options"),
        ft.NavigationBarDestination(icon=ft.Icons.ACCOUNT_BALANCE_WALLET,
                                     label="Paper"),
        ft.NavigationBarDestination(icon=ft.Icons.NOTIFICATIONS,
                                     label="Alerts"),
        ft.NavigationBarDestination(icon=ft.Icons.LINK, label="Angel One")
    ]

    page.navigation_bar = ft.NavigationBar(
        destinations=destinations,
        selected_index=0,
        on_change=nav_change
    )

    page.add(
        ft.Column([
            ft.Text("BOT KING", size=26,
                    weight=ft.FontWeight.BOLD, color=GOLD),
            status,
            ft.Divider(color="#34445B"),
            body
        ], expand=True, scroll=ft.ScrollMode.AUTO)
    )

    render()
    page.run_task(refresh)


ft.app(target=main)
