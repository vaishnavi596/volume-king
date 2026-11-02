
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

WATCH_DEFAULT = [
    "NIFTY", "BANKNIFTY", "RELIANCE", "HDFCBANK",
    "ICICIBANK", "SBIN", "INFY", "TCS", "ITC"
]

SYMBOLS = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN"
}


def yahoo_symbol(symbol):
    symbol = symbol.strip().upper()
    return SYMBOLS.get(symbol, symbol if symbol.startswith("^") else symbol + ".NS")


def yahoo_data(symbol, interval="5m", period="1d"):
    ticker = yahoo_symbol(symbol)
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + ticker
        + f"?range={period}&interval={interval}"
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def get_quote(symbol):
    try:
        data = yahoo_data(symbol, "5m", "1d")
        result = data["chart"]["result"][0]
        meta = result["meta"]
        price = meta.get("regularMarketPrice")
        previous = meta.get("chartPreviousClose") or meta.get("previousClose")

        if price is None:
            return None

        change = None
        if previous:
            change = ((price - previous) / previous) * 100

        return {
            "price": float(price),
            "change": change
        }
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

    watch = WATCH_DEFAULT.copy()
    quotes = {}
    trades = []
    active = "Dashboard"
    alerts = False

    status = ft.Text("Market data तैयार है", color=MUTED, size=11)
    body = ft.Column(spacing=12)

    addfield = ft.TextField(
        label="Stock Symbol",
        hint_text="जैसे TATAMOTORS",
        expand=True,
        text_size=13
    )

    chartsym = ft.TextField(
        value="NIFTY",
        label="Chart Symbol",
        width=160
    )

    interval = ft.Dropdown(
        label="Timeframe",
        width=120,
        value="5m",
        options=[
            ft.dropdown.Option("1m"),
            ft.dropdown.Option("5m"),
            ft.dropdown.Option("15m"),
            ft.dropdown.Option("30m"),
            ft.dropdown.Option("60m")
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
    prem = ft.TextField(label="Entry / Exit Premium", value="100", width=160)
    qty = ft.TextField(label="Quantity", value="1", width=100)

    qcards = ft.Column(spacing=8)
    watchcol = ft.Column(spacing=8)
    chartcol = ft.Column(spacing=6)
    optcol = ft.Column(spacing=8)
    tradecol = ft.Column(spacing=8)

    def card(title, value, subtitle=""):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, color=MUTED, size=11),
                ft.Text(value, color=GOLD, size=20, weight=ft.FontWeight.BOLD),
                ft.Text(subtitle, color=MUTED, size=10)
            ], spacing=3),
            bgcolor=CARD,
            padding=12,
            border_radius=10
        )

    async def loadquote(symbol):
        status.value = f"{symbol} का भाव लोड हो रहा है..."
        page.update()

        result = await asyncio.to_thread(get_quote, symbol)
        if result:
            quotes[symbol] = result
            status.value = f"{symbol} का डेटा अपडेट हुआ"
        else:
            status.value = f"{symbol}: डेटा उपलब्ध नहीं"

        render()

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
                glyph[min(7, int((v - low) / (high - low) * 7))]
                if high > low else "▄"
                for v in values
            )

            chartcol.controls = [
                ft.Text(spark, size=24, color=GOLD),
                ft.Text(
                    "Time    Open    High    Low    Close    Volume",
                    size=10,
                    color=MUTED
                )
            ]

            for x in rows[-15:]:
                chartcol.controls.append(
                    ft.Text(
                        f'{x["time"]}  {x["open"]:.2f}  '
                        f'{x["high"]:.2f}  {x["low"]:.2f}  '
                        f'{x["close"]:.2f}  {x["volume"]}',
                        size=10
                    )
                )

        except Exception:
            chartcol.controls = [
                ft.Text(
                    "NO DATA • Yahoo candle data उपलब्ध नहीं है।",
                    color=RED
                )
            ]

        page.update()

    async def loadoptions(e=None):
        optcol.controls = [
            ft.Text(
                "इस संस्करण में NSE Options Chain का भरोसेमंद स्रोत जुड़ा नहीं है।",
                color=RED
            ),
            ft.Text(
                "इसलिए PCR, Max Pain, CE/PE Premium और OI को NO DATA दिखाया जाएगा। "
                "गलत या नकली ट्रेडिंग डेटा नहीं दिखाया जाएगा।",
                color=MUTED,
                size=11
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
        status.value = (
            "Paper Alerts ON" if alerts else "Paper Alerts OFF"
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
                ft.Text("Market Dashboard", size=20, weight=ft.FontWeight.BOLD),
                qcards,
                ft.ElevatedButton(
                    "↻ Refresh Market",
                    on_click=lambda e: page.run_task(refresh),
                    bgcolor=GOLD,
                    color=BG
                ),
                ft.Text(
                    "डेटा Yahoo Finance से आता है। यह आधिकारिक NSE/BSE "
                    "लाइव फीड नहीं है; भाव में देरी हो सकती है।",
                    color=MUTED,
                    size=11
                )
            ]

        elif active == "Watchlist":
            body.controls = [
                ft.Text("Watchlist", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([
                    addfield,
                    ft.ElevatedButton(
                        "Add",
                        on_click=addstock,
                        bgcolor=GOLD,
                        color=BG
                    )
                ]),
                watchcol
            ]

            watchcol.controls = []

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
                        bgcolor=CARD,
                        padding=8,
                        border_radius=8
                    )
                )

        elif active == "Charts":
            body.controls = [
                ft.Text("Market Charts", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([chartsym, interval], wrap=True),
                ft.ElevatedButton(
                    "Load Chart",
                    on_click=loadchart,
                    bgcolor=GOLD,
                    color=BG
                ),
                chartcol
            ]

        elif active == "Options":
            body.controls = [
                ft.Text("Options Chain", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([
                    optsym,
                    ft.ElevatedButton(
                        "Load Chain",
                        on_click=loadoptions,
                        bgcolor=GOLD,
                        color=BG
                    )
                ], wrap=True),
                optcol
            ]

        elif active == "Paper":
            opened = sum(t["exit"] is None for t in trades)
            pnl = sum(
                (t["exit"] - t["entry"]) * t["qty"]
                for t in trades if t["exit"] is not None
            )

            tradecol.controls = [
                card("Open Trades", str(opened)),
                card("Realized P&L", f"₹{pnl:,.2f}"),
                ft.Text("नया Paper Trade", weight=ft.FontWeight.BOLD),
                ft.Row([tsym, side], wrap=True),
                ft.Row([prem, qty], wrap=True),
                ft.ElevatedButton(
                    "BUY (PAPER)",
                    on_click=buy,
                    bgcolor=GOLD,
                    color=BG
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
                        trade["exit"] - trade["entry"]
                    ) * trade["qty"]

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
                ft.Text("Paper Trading", size=20, weight=ft.FontWeight.BOLD),
                tradecol,
                ft.Text(
                    "यह केवल simulation है। कोई वास्तविक order नहीं जाता। "
                    "App बंद करने पर trades reset हो सकते हैं।",
                    size=10,
                    color=MUTED
                )
            ]

        elif active == "Alerts":
            body.controls = [
                ft.Text("Alerts", size=20, weight=ft.FontWeight.BOLD),
                ft.Switch(
                    label="Paper Alerts ON/OFF",
                    value=alerts,
                    on_change=toggle_alert
                ),
                ft.Text(
                    "यह switch केवल preference है। Push notifications "
                    "इस संस्करण में शामिल नहीं हैं।",
                    color=MUTED,
                    size=11
                )
            ]

        page.update()

    def nav(name):
        nonlocal active
        active = name
        render()

    page.add(
        ft.Column([
            ft.Text(
                "BOT KING",
                size=26,
                weight=ft.FontWeight.BOLD,
                color=GOLD
            ),
            status,
            ft.Row([
                ft.TextButton(
                    name,
                    on_click=lambda e, n=name: nav(n)
                )
                for name in [
                    "Dashboard", "Watchlist", "Charts",
                    "Options", "Paper", "Alerts"
                ]
            ], wrap=True),
            ft.Divider(color="#34445B"),
            body
        ], expand=True, scroll=ft.ScrollMode.AUTO)
    )

    render()
    page.run_task(refresh)


ft.app(target=main)
