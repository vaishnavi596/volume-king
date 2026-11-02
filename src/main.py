
import flet as ft
import asyncio
import json
import urllib.request
from datetime import datetime

BG = "#08111F"
CARD = "#142238"
GOLD = "#F5C542"
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

INDEX_SYMBOLS = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN"
}


def yahoo_symbol(symbol):
    symbol = symbol.strip().upper()
    if symbol in INDEX_SYMBOLS:
        return INDEX_SYMBOLS[symbol]
    if symbol.startswith("^"):
        return symbol
    return symbol + ".NS"


def fetch_yahoo(symbol, interval="5m", period="1d"):
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + yahoo_symbol(symbol)
        + f"?range={period}&interval={interval}"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def get_quote(symbol):
    try:
        data = fetch_yahoo(symbol)
        result = data["chart"]["result"][0]
        meta = result["meta"]

        price = meta.get("regularMarketPrice")
        previous = (
            meta.get("chartPreviousClose")
            or meta.get("previousClose")
        )

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
    data = fetch_yahoo(symbol, interval, "1d")
    result = data["chart"]["result"][0]

    timestamps = result.get("timestamp", [])
    quote = result["indicators"]["quote"][0]

    rows = []

    for i, stamp in enumerate(timestamps):
        try:
            close = quote["close"][i]
            if close is None:
                continue

            rows.append({
                "time": datetime.fromtimestamp(stamp).strftime("%H:%M"),
                "open": float(quote["open"][i] or 0),
                "high": float(quote["high"][i] or 0),
                "low": float(quote["low"][i] or 0),
                "close": float(close),
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

    watchlist = NIFTY50.copy()
    quotes = {}
    trades = []
    active_page = "Dashboard"
    alerts_enabled = False

    status = ft.Text("BOT KING तैयार है", color=MUTED, size=11)
    body = ft.Column(spacing=12)

    add_symbol = ft.TextField(
        label="Stock Symbol",
        hint_text="जैसे TATAMOTORS",
        expand=True
    )

    chart_symbol = ft.TextField(
        label="Chart Symbol",
        value="NIFTY",
        width=160
    )

    timeframe = ft.Dropdown(
        label="Timeframe",
        value="5m",
        width=120,
        options=[
            ft.dropdown.Option(x)
            for x in ["1m", "5m", "15m", "30m", "60m"]
        ]
    )

    option_symbol = ft.TextField(
        label="Options Symbol",
        value="NIFTY",
        width=160
    )

    trade_symbol = ft.TextField(
        label="Symbol",
        value="NIFTY",
        width=150
    )

    trade_side = ft.Dropdown(
        label="CE / PE",
        value="CE",
        width=100,
        options=[
            ft.dropdown.Option("CE"),
            ft.dropdown.Option("PE")
        ]
    )

    premium = ft.TextField(
        label="Premium",
        value="100",
        width=120
    )

    quantity = ft.TextField(
        label="Quantity",
        value="1",
        width=100
    )

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

    watch_column = ft.Column(spacing=8)
    chart_column = ft.Column(spacing=6)
    option_column = ft.Column(spacing=8)
    trade_column = ft.Column(spacing=8)
    quote_cards = ft.Column(spacing=8)

    def make_card(title, value, subtitle=""):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, color=MUTED, size=11),
                    ft.Text(
                        value,
                        color=GOLD,
                        size=20,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(subtitle, color=MUTED, size=10)
                ],
                spacing=3
            ),
            bgcolor=CARD,
            padding=12,
            border_radius=10
        )

    async def refresh_market(e=None):
        status.value = "Market data अपडेट हो रहा है..."
        page.update()

        symbols = ["NIFTY", "BANKNIFTY", "SENSEX"]

        results = await asyncio.gather(
            *[
                asyncio.to_thread(get_quote, symbol)
                for symbol in symbols
            ],
            return_exceptions=True
        )

        for symbol, result in zip(symbols, results):
            if isinstance(result, dict):
                quotes[symbol] = result

        status.value = "Market refresh पूरा हुआ"
        render()

    async def load_quote(symbol):
        status.value = f"{symbol} लोड हो रहा है..."
        page.update()

        result = await asyncio.to_thread(get_quote, symbol)

        if result:
            quotes[symbol] = result
            status.value = f"{symbol} अपडेट हुआ"
        else:
            status.value = f"{symbol}: डेटा उपलब्ध नहीं"

        render()

    async def load_chart(e=None):
        chart_column.controls = [
            ft.Text("Chart लोड हो रहा है...", color=MUTED)
        ]
        page.update()

        try:
            rows = await asyncio.to_thread(
                get_candles,
                chart_symbol.value,
                timeframe.value
            )

            if not rows:
                raise ValueError("No chart data")

            values = [row["close"] for row in rows]
            low = min(values)
            high = max(values)
            blocks = "▁▂▃▄▅▆▇█"

            sparkline = "".join(
                blocks[
                    min(7, int((value - low) / (high - low) * 7))
                ] if high > low else "▄"
                for value in values
            )

            chart_column.controls = [
                ft.Text(sparkline, size=24, color=GOLD),
                ft.Text(
                    "Time  Open  High  Low  Close  Volume",
                    size=10,
                    color=MUTED
                )
            ]

            for row in rows[-15:]:
                chart_column.controls.append(
                    ft.Text(
                        f'{row["time"]}  {row["open"]:.2f}  '
                        f'{row["high"]:.2f}  {row["low"]:.2f}  '
                        f'{row["close"]:.2f}  {row["volume"]}',
                        size=10
                    )
                )

        except Exception:
            chart_column.controls = [
                ft.Text(
                    "NO DATA • Chart data उपलब्ध नहीं है।",
                    color=RED
                )
            ]

        page.update()

    async def load_options(e=None):
        option_column.controls = [
            ft.Text(
                "NO DATA • असली Options Chain API अभी नहीं जुड़ी है।",
                color=RED
            ),
            ft.Text(
                "Strike, Premium, OI और PCR के लिए "
                "विश्वसनीय डेटा स्रोत जोड़ना बाकी है।",
                color=MUTED,
                size=11
            )
        ]
        page.update()

    def buy_paper_trade(e):
        try:
            price = float(premium.value)
            qty = int(quantity.value)

            if price <= 0 or qty <= 0:
                raise ValueError()

            trades.append({
                "symbol": trade_symbol.value.strip().upper(),
                "side": trade_side.value,
                "qty": qty,
                "entry": price,
                "exit": None
            })

            status.value = "Paper trade खुल गया"
            render()

        except Exception:
            status.value = "Premium और Quantity सही डालें"
            page.update()

    def exit_paper_trade(index):
        try:
            price = float(premium.value)

            if price <= 0:
                raise ValueError()

            trades[index]["exit"] = price
            status.value = "Paper trade बंद हुआ"
            render()

        except Exception:
            status.value = "Exit Premium सही डालें"
            page.update()

    def add_stock(e):
        symbol = add_symbol.value.strip().upper()

        if symbol and symbol not in watchlist:
            watchlist.append(symbol)
            add_symbol.value = ""
            render()
        else:
            status.value = "Symbol खाली है या पहले से मौजूद है"
            page.update()

    def remove_stock(symbol):
        if symbol in watchlist:
            watchlist.remove(symbol)
        render()

    def toggle_alert(e):
        nonlocal alerts_enabled
        alerts_enabled = e.control.value

        status.value = (
            "Paper Alerts ON"
            if alerts_enabled else "Paper Alerts OFF"
        )
        page.update()

    def connect_angel_one(e):
        status.value = (
            "Angel One का सुरक्षित Backend अभी तैयार नहीं है। "
            "अभी कोई कनेक्शन नहीं हुआ।"
        )
        page.update()

    def show_page(name):
        nonlocal active_page
        active_page = name
        render()

    def render():
        body.controls = []

        if active_page == "Dashboard":
            quote_cards.controls = []

            for symbol in ["NIFTY", "BANKNIFTY", "SENSEX"]:
                quote = quotes.get(symbol)

                if quote:
                    change = (
                        f'{quote["change"]:+.2f}%'
                        if quote["change"] is not None
                        else "Change N/A"
                    )

                    quote_cards.controls.append(
                        make_card(
                            symbol,
                            f'{quote["price"]:,.2f}',
                            change
                        )
                    )
                else:
                    quote_cards.controls.append(
                        make_card(symbol, "NO DATA", "Refresh दबाएँ")
                    )

            body.controls = [
                ft.Text(
                    "Market Dashboard",
                    size=20,
                    weight=ft.FontWeight.BOLD
                ),
                quote_cards,
                ft.ElevatedButton(
                    "Refresh Market",
                    on_click=refresh_market,
                    bgcolor=GOLD,
                    color=BG
                ),
                ft.Text(
                    "Yahoo Finance डेटा है। यह आधिकारिक NSE/BSE "
                    "लाइव फीड नहीं है और इसमें देरी हो सकती है।",
                    color=MUTED,
                    size=11
                )
            ]

        elif active_page == "Watchlist":
            watch_column.controls = []

            body.controls = [
                ft.Text(
                    "NIFTY 50 Watchlist",
                    size=20,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    f"कुल शेयर: {len(watchlist)}",
                    color=GOLD
                ),
                ft.Row(
                    [
                        add_symbol,
                        ft.ElevatedButton(
                            "Add",
                            on_click=add_stock,
                            bgcolor=GOLD,
                            color=BG
                        )
                    ],
                    wrap=True
                ),
                watch_column
            ]

            for symbol in watchlist:
                quote = quotes.get(symbol)

                price = (
                    f'{quote["price"]:,.2f}'
                    if quote else "--"
                )

                change = (
                    f'{quote["change"]:+.2f}%'
                    if quote and quote["change"] is not None
                    else "भाव के लिए Load दबाएँ"
                )

                watch_column.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            symbol,
                                            weight=ft.FontWeight.BOLD
                                        ),
                                        ft.Text(
                                            change,
                                            size=10,
                                            color=MUTED
                                        )
                                    ],
                                    expand=True,
                                    spacing=2
                                ),
                                ft.Text(price, color=GOLD),
                                ft.TextButton(
                                    "Load",
                                    on_click=lambda e, s=symbol:
                                        page.run_task(load_quote, s)
                                ),
                                ft.TextButton(
                                    "×",
                                    on_click=lambda e, s=symbol:
                                        remove_stock(s)
                                )
                            ]
                        ),
                        bgcolor=CARD,
                        padding=8,
                        border_radius=8
                    )
                )

        elif active_page == "Charts":
            body.controls = [
                ft.Text(
                    "Market Charts",
                    size=20,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Row(
                    [chart_symbol, timeframe],
                    wrap=True
                ),
                ft.ElevatedButton(
                    "Load Chart",
                    on_click=load_chart,
                    bgcolor=GOLD,
                    color=BG
                ),
                chart_column
            ]

        elif active_page == "Options":
            body.controls = [
                ft.Text(
                    "Options Chain",
                    size=20,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Row(
                    [
                        option_symbol,
                        ft.ElevatedButton(
                            "Load Chain",
                            on_click=load_options,
                            bgcolor=GOLD,
                            color=BG
                        )
                    ],
                    wrap=True
                ),
                option_column
            ]

        elif active_page == "Paper":
            opened = sum(
                trade["exit"] is None for trade in trades
            )

            pnl = sum(
                (trade["exit"] - trade["entry"]) * trade["qty"]
                for trade in trades
                if trade["exit"] is not None
            )

            trade_column.controls = [
                make_card("Open Trades", str(opened)),
                make_card("Realized P&L", f"₹{pnl:,.2f}"),
                ft.Text(
                    "नया Paper Trade",
                    weight=ft.FontWeight.BOLD
                ),
                ft.Row([trade_symbol, trade_side], wrap=True),
                ft.Row([premium, quantity], wrap=True),
                ft.ElevatedButton(
                    "BUY (PAPER)",
                    on_click=buy_paper_trade,
                    bgcolor=GOLD,
                    color=BG
                ),
                ft.Text(
                    "Trade History",
                    weight=ft.FontWeight.BOLD
                )
            ]

            for i, trade in enumerate(trades):
                line = (
                    f'{trade["symbol"]} {trade["side"]} | '
                    f'Qty {trade["qty"]} | '
                    f'Entry ₹{trade["entry"]:.2f}'
                )

                if trade["exit"] is None:
                    trade_column.controls.append(
                        ft.Row(
                            [
                                ft.Text(line, size=11, expand=True),
                                ft.TextButton(
                                    "Exit",
                                    on_click=lambda e, j=i:
                                        exit_paper_trade(j)
                                )
                            ]
                        )
                    )
                else:
                    value = (
                        trade["exit"] - trade["entry"]
                    ) * trade["qty"]

                    trade_column.controls.append(
                        ft.Text(
                            line
                            + f' | Exit ₹{trade["exit"]:.2f}'
                            + f' | P&L ₹{value:,.2f}',
                            size=11,
                            color=GREEN if value >= 0 else RED
                        )
                    )

            if not trades:
                trade_column.controls.append(
                    ft.Text(
                        "अभी कोई Paper Trade नहीं है।",
                        color=MUTED
                    )
                )

            body.controls = [
                ft.Text(
                    "Paper Trading",
                    size=20,
                    weight=ft.FontWeight.BOLD
                ),
                trade_column,
                ft.Text(
                    "यह केवल simulation है। वास्तविक order नहीं जाता। "
                    "ऐप बंद होने पर trades reset हो सकते हैं।",
                    size=10,
                    color=MUTED
                )
            ]

        elif active_page == "Alerts":
            body.controls = [
                ft.Text(
                    "Alerts",
                    size=20,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Switch(
                    label="Paper Alerts ON/OFF",
                    value=alerts_enabled,
                    on_change=toggle_alert
                ),
                ft.Text(
                    "Push notifications अभी शामिल नहीं हैं।",
                    color=MUTED,
                    size=11
                )
            ]

        elif active_page == "Angel One":
            body.controls = [
                ft.Text(
                    "Angel One SmartAPI",
                    size=20,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    "यह अभी केवल जानकारी भरने का इंटरफेस है। "
                    "वास्तविक कनेक्शन सक्रिय नहीं है।",
                    color=MUTED,
                    size=11
                ),
                api_key,
                client_code,
                pin,
                totp,
                ft.ElevatedButton(
                    "Connect Angel One",
                    on_click=connect_angel_one,
                    bgcolor=GOLD,
                    color=BG
                ),
                ft.Text(
                    "सुरक्षित Backend और आधिकारिक SmartAPI "
                    "लॉगिन जोड़े बिना credentials न डालें।",
                    color=RED,
                    size=11
                )
            ]

        page.update()

    nav_buttons = []

    for name in [
        "Dashboard",
        "Watchlist",
        "Charts",
        "Options",
        "Paper",
        "Alerts",
        "Angel One"
    ]:
        nav_buttons.append(
            ft.TextButton(
                name,
                on_click=lambda e, n=name: show_page(n)
            )
        )

    page.add(
        ft.Column(
            [
                ft.Text(
                    "BOT KING",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color=GOLD
                ),
                status,
                ft.Divider(color="#34445B"),
                ft.Row(
                    nav_buttons,
                    wrap=True,
                    spacing=2
                ),
                ft.Divider(color="#34445B"),
                body
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )
    )

    render()
    page.run_task(refresh_market)


ft.app(target=main)
