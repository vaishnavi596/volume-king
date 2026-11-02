
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
    page.padding = 8
    page.scroll = ft.ScrollMode.HIDDEN

    watchlist = NIFTY50.copy()
    watch_visible_count = 10
    quotes = {}
    trades = []
    active_page = "Dashboard"
    alerts_enabled = False
    selected_broker = "None"
    scanner_threshold = 75

    status = ft.Text("BOT KING तैयार है", color=MUTED, size=11)
    body = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

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

    broker_dropdown = ft.Dropdown(label="Broker / Data Provider", value="None", options=[ft.dropdown.Option(x) for x in ["None", "Angel One", "Dhan", "Zerodha", "Upstox", "Custom"]])
    api_secret = ft.TextField(label="API Secret (do not enter yet)", password=True)
    redirect_url = ft.TextField(label="Redirect URL")
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
            "Broker का सुरक्षित Backend अभी तैयार नहीं है। "
            "अभी कोई कनेक्शन नहीं हुआ।"
        )
        page.update()

    def show_more_watchlist(e):
        nonlocal watch_visible_count
        watch_visible_count = min(len(watchlist), watch_visible_count + 10)
        render()

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
                ft.Container(content=ft.Column([ft.Text("Market Sentiment & Scanner", color=GOLD, size=16, weight=ft.FontWeight.BOLD), ft.Text("Bullish / Bearish confidence: NO DATA", color=MUTED), ft.Text("OI, Volume, Breadth और Momentum की पुष्टि के बाद ही संकेत उपलब्ध होंगे।", size=11, color=MUTED)], spacing=6), bgcolor=CARD, padding=12, border_radius=12),
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
            watch_column = ft.Column(spacing=8)

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

            for symbol in watchlist[:watch_visible_count]:
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

            if watch_visible_count < len(watchlist):
                watch_column.controls.append(ft.ElevatedButton(
                    f"और शेयर दिखाएँ ({watch_visible_count}/{len(watchlist)})",
                    on_click=show_more_watchlist, bgcolor=GOLD, color=BG
                ))

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
                option_column,
                ft.Container(content=ft.Column([ft.Text("OI & Premium Money Flow", color=GOLD, size=16, weight=ft.FontWeight.BOLD), ft.Text("Highest CE/PE OI • Change in OI • Traded Value • PCR", color=MUTED), ft.Text("NO DATA — Options Chain API आवश्यक है।", color=RED, size=11)], spacing=6), bgcolor=CARD, padding=12, border_radius=12)
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

        elif active_page == "Settings":
            body.controls = [
                ft.Text("Settings & Trading Tools", size=20, weight=ft.FontWeight.BOLD, color=GOLD),
                ft.Container(content=ft.Column([
                    ft.Text("Market Scanner", size=17, weight=ft.FontWeight.BOLD),
                    ft.Text("Bullish / Bearish • Breakout • Volume • Market Breadth • No-Trade Zone", size=12, color=MUTED),
                    ft.Text("Signal confidence filter: 70%–85% (planned)", color=GOLD),
                    ft.Text("NO DATA — सत्यापित लाइव डेटा और बैकटेस्ट के बिना कोई प्रतिशत या ट्रेड सिग्नल नहीं दिखाया जाएगा।", color=RED, size=11),
                ], spacing=8), bgcolor=CARD, padding=14, border_radius=12),
                ft.Container(content=ft.Column([
                    ft.Text("Paper Trading", size=17, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton("Open Paper Trading", on_click=lambda e: show_page("Paper"), bgcolor=GOLD, color=BG),
                    ft.Text("केवल simulation; असली ऑर्डर नहीं।", color=MUTED, size=11),
                ]), bgcolor=CARD, padding=14, border_radius=12),
                ft.Container(content=ft.Column([
                    ft.Text("Alerts & Notifications", size=17, weight=ft.FontWeight.BOLD),
                    ft.Switch(label="Paper Alerts ON/OFF", value=alerts_enabled, on_change=toggle_alert),
                    ft.Text("अभी Push Notifications सक्रिय नहीं हैं।", color=MUTED, size=11),
                ]), bgcolor=CARD, padding=14, border_radius=12),
                ft.Container(content=ft.Column([
                    ft.Text("Broker & API Integration", size=17, weight=ft.FontWeight.BOLD),
                    broker_dropdown,
                    ft.Text("Available: Angel One, Dhan, Zerodha, Upstox, Custom", color=MUTED, size=11),
                    ft.Text("NOT CONNECTED • केवल UI; अभी असली credentials न डालें।", color=RED, size=11),
                    ft.ElevatedButton("Connection Status", on_click=connect_angel_one, bgcolor=GOLD, color=BG),
                    ft.Text("API Key / Secret / PIN / TOTP के लिए सुरक्षित server-side login बाद में जोड़ा जाएगा।", color=MUTED, size=11),
                ]), bgcolor=CARD, padding=14, border_radius=12),
                ft.Text("BOT KING • Classic Dark & Gold", color=MUTED, size=11),
            ]

        page.update()

    tabs = [
        ("Dashboard", ft.icons.DASHBOARD),
        ("Watchlist", ft.icons.STAR),
        ("Charts", ft.icons.SHOW_CHART),
        ("Options", ft.icons.LIST_ALT),
        ("Settings", ft.icons.SETTINGS),
    ]

    def bottom_button(name, icon):
        selected = active_page == name
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=19, color=GOLD if selected else MUTED),
                    ft.Text(name, size=8, color=GOLD if selected else MUTED,
                            no_wrap=True),
                ],
                spacing=3,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
            padding=ft.padding.symmetric(vertical=8),
            bgcolor="#1D3049" if selected else "#0D1929",
            border_radius=6,
            on_click=lambda e, n=name: show_page(n),
        )

    bottom_menu = ft.Container(
        content=ft.Row(
            [bottom_button(name, icon) for name, icon in tabs],
            spacing=0,
        ),
        bgcolor="#0D1929",
        padding=ft.padding.symmetric(horizontal=2, vertical=4),
    )

    page.add(
        ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("BOT KING", size=26,
                                    weight=ft.FontWeight.BOLD, color=GOLD),
                            status,
                        ],
                        spacing=2,
                    ),
                    padding=ft.padding.only(bottom=6),
                ),
                ft.Container(content=body, expand=True),
                bottom_menu,
            ],
            expand=True,
            spacing=0,
        )
    )

    original_render = render

    def render():
        original_render()
        bottom_menu.content.controls = [
            bottom_button(name, icon) for name, icon in tabs
        ]
        page.update()

    render()
    page.run_task(refresh_market)


ft.app(target=main)
