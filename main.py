
import flet as ft
import asyncio
import json
import urllib.request
from datetime import datetime

BG = "#080D18"
PANEL = "#141F32"
PANEL2 = "#1B2940"
GOLD = "#F5C451"
WHITE = "#F4F7FC"
MUTED = "#9AA8BD"
GREEN = "#35C98A"
RED = "#F16D78"
BLUE = "#63A7FF"

SYMBOLS = {
    "NIFTY 50": "%5ENSEI",
    "BANK NIFTY": "%5ENSEBANK",
    "SENSEX": "%5EBSESN",
}

WATCHLIST = [
    "RELIANCE", "HDFCBANK", "ICICIBANK",
    "SBIN", "INFY", "TCS", "ITC", "LT",
    "AXISBANK", "KOTAKBANK", "BHARTIARTL"
]


def get_market_data(symbol):
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + symbol + "?range=1d&interval=5m"
    )
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req, timeout=12) as response:
        payload = json.loads(response.read().decode())

    result = payload["chart"]["result"][0]
    meta = result["meta"]

    price = meta.get("regularMarketPrice")
    previous = meta.get("previousClose")

    if price is None:
        raise ValueError("Price unavailable")

    change = price - previous if previous else None
    percent = (
        change / previous * 100
        if previous else None
    )

    return {
        "price": price,
        "change": change,
        "percent": percent
    }


def main(page: ft.Page):
    page.title = "BOT KING"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.spacing = 0

    page.scroll = ft.ScrollMode.AUTO

    watch = list(WATCHLIST)
    market = {}
    current_page = "Dashboard"

    body = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=12
    )

    nav = ft.Row(
        spacing=5,
        scroll=ft.ScrollMode.AUTO
    )

    nav_buttons = {}

    data_status = ft.Text(
        "DATA: CHECKING...",
        color=GOLD,
        size=11,
        weight=ft.FontWeight.BOLD
    )

    update_time = ft.Text(
        "Last update: --",
        color=MUTED,
        size=10
    )

    def txt(value, size=13, color=WHITE, bold=False):
        return ft.Text(
            str(value),
            size=size,
            color=color,
            weight=(
                ft.FontWeight.BOLD
                if bold else ft.FontWeight.NORMAL
            )
        )

    def card(title, *items):
        return ft.Container(
            content=ft.Column(
                [
                    txt(title, 13, GOLD, True),
                    *items
                ],
                spacing=9
            ),
            bgcolor=PANEL,
            padding=14,
            border_radius=14,
            border=ft.border.all(1, "#293A55")
        )

    def metric(title, value="--", subtitle="NO DATA"):
        return ft.Container(
            content=ft.Column(
                [
                    txt(title, 11, MUTED, True),
                    txt(value, 21, WHITE, True),
                    txt(subtitle, 9, GOLD)
                ],
                spacing=4
            ),
            bgcolor=PANEL2,
            padding=12,
            border_radius=12,
            expand=True
        )

    def info_row(label, value, color=MUTED):
        return ft.Row(
            [
                txt(label, 11, MUTED),
                ft.Container(expand=True),
                txt(value, 11, color, True)
            ]
        )

    def show(items):
        body.controls.clear()
        body.controls.extend(items)
        page.update()

    def price_value(name):
        data = market.get(name)
        if not data:
            return "--"
        return f"{data['price']:,.2f}"

    def change_value(name):
        data = market.get(name)
        if not data or data["change"] is None:
            return "NO DATA"

        return (
            f"{data['change']:+.2f} "
            f"({data['percent']:+.2f}%)"
        )

    def change_color(name):
        data = market.get(name)
        if not data or data["change"] is None:
            return GOLD
        return GREEN if data["change"] >= 0 else RED

    def dashboard():
        show([
            card(
                "BOT KING MARKET STATUS",
                ft.Row([
                    txt("● DATA STATUS", 11, GREEN, True),
                    ft.Container(expand=True),
                    txt("SIGNAL: WAIT", 11, GOLD, True)
                ]),
                data_status,
                update_time
            ),

            ft.Row([
                metric("NIFTY 50", price_value("NIFTY 50"),
                       change_value("NIFTY 50")),
                metric("BANK NIFTY", price_value("BANK NIFTY"),
                       change_value("BANK NIFTY"))
            ], spacing=8),

            ft.Row([
                metric("SENSEX", price_value("SENSEX"),
                       change_value("SENSEX")),
                metric("MARKET MODE", "WAIT", "NO TRADE SIGNAL")
            ], spacing=8),

            card(
                "INTRADAY LIVE SCANNER",
                txt("Timeframe", 11, MUTED),
                ft.Row([
                    ft.OutlinedButton("1 MIN"),
                    ft.OutlinedButton("5 MIN"),
                    ft.OutlinedButton("10 MIN"),
                    ft.OutlinedButton("15 MIN")
                ], wrap=True, spacing=4),
                info_row("World news sentiment", "20%", BLUE),
                info_row("Futures positioning", "40%", BLUE),
                info_row("Options premium / OI", "40%", BLUE),
                txt("SCANNER SCORE: WAITING FOR DATA",
                    11, GOLD, True)
            ),

            card(
                "CE / PE POSITIONING",
                info_row("CALL (CE) OI", "NO DATA"),
                info_row("PUT (PE) OI", "NO DATA"),
                info_row("PCR / MAX PAIN", "NO DATA"),
                txt(
                    "Options chain data मिलने पर ही "
                    "CE / PE analysis शुरू होगा।",
                    11, MUTED
                )
            ),

            card(
                "FUTURES BUILDUP",
                info_row("Price up + OI up", "LONG BUILDUP", GREEN),
                info_row("Price down + OI up", "SHORT BUILDUP", RED),
                info_row("Price up + OI down", "SHORT COVERING", GREEN),
                info_row("Price down + OI down", "LONG UNWINDING", GOLD)
            ),

            card(
                "SMART MARKET FILTERS",
                txt("Market Breadth • Sector Strength", 12),
                txt("Breakout Scanner • Volume Confirmation", 12),
                txt("OI Trap Alert • No Trade Zone", 12),
                txt("Signal History • Swing View", 12)
            ),

            ft.ElevatedButton(
                "REFRESH MARKET DATA",
                bgcolor=GOLD,
                color=BG,
                on_click=refresh_data
            )
        ])

    def watchlist_page():
        field = ft.TextField(
            hint_text="Stock symbol, e.g. TATASTEEL",
            text_size=13,
            expand=True
        )

        rows = []

        for symbol in watch:
            rows.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            txt(symbol, 13, WHITE, True),
                            txt("Price: -- | Change: --", 10, MUTED)
                        ], expand=True, spacing=3),
                        txt("NO DATA", 10, GOLD)
                    ]),
                    bgcolor=PANEL2,
                    padding=11,
                    border_radius=10
                )
            )

        def add_symbol(e):
            symbol = (field.value or "").strip().upper()
            if symbol and symbol not in watch:
                watch.append(symbol)
                watchlist_page()

        show([
            card(
                "MY WATCHLIST",
                txt("अपनी पसंद के स्टॉक जोड़ें।", 11, MUTED),
                ft.Row([
                    field,
                    ft.ElevatedButton(
                        "ADD",
                        bgcolor=GOLD,
                        color=BG,
                        on_click=add_symbol
                    )
                ])
            ),
            card("TRACKED STOCKS", *rows)
        ])

    def options_page():
        show([
            card(
                "OPTIONS ANALYSIS",
                txt("NIFTY / BANK NIFTY / SENSEX", 11, MUTED),
                ft.Row([
                    metric("PCR"),
                    metric("MAX PAIN")
                ]),
                ft.Row([
                    metric("ATM STRIKE"),
                    metric("IV")
                ])
            ),
            card(
                "OPEN INTEREST",
                info_row("CE OI BUILDUP", "NO DATA"),
                info_row("PE OI BUILDUP", "NO DATA"),
                info_row("CE PREMIUM CHANGE", "NO DATA"),
                info_row("PE PREMIUM CHANGE", "NO DATA")
            ),
            card(
                "TRADE SAFETY",
                txt(
                    "Options chain की पुष्टि के बिना "
                    "कोई BUY / SELL signal नहीं।",
                    12, GOLD
                )
            )
        ])

    def charts_page():
        show([
            card(
                "CHARTS & INDICATORS",
                txt("Selected symbol: NIFTY 50", 12, MUTED),
                ft.Row([
                    ft.OutlinedButton("1m"),
                    ft.OutlinedButton("5m"),
                    ft.OutlinedButton("15m"),
                    ft.OutlinedButton("1D")
                ], wrap=True),
                ft.Container(
                    content=ft.Column([
                        txt("PRICE / VOLUME CHART", 13, GOLD, True),
                        ft.Container(
                            content=txt("NO CHART DATA", 13, MUTED),
                            height=145,
                            alignment=ft.alignment.center,
                            bgcolor="#101827",
                            border_radius=10
                        )
                    ]),
                    bgcolor=PANEL2,
                    padding=12,
                    border_radius=12
                )
            ),
            card(
                "TECHNICAL INDICATORS",
                info_row("EMA 9 / EMA 21", "--"),
                info_row("RSI 14", "--"),
                info_row("VWAP", "--"),
                info_row("VOLUME", "--")
            )
        ])

    def alerts_page():
        show([
            card(
                "ALERT CENTER",
                info_row("Price alerts", "INACTIVE"),
                info_row("Breakout alerts", "INACTIVE"),
                info_row("OI trap alerts", "INACTIVE"),
                info_row("No-trade zone alerts", "INACTIVE")
            ),
            card(
                "PAPER TRADING",
                txt("Automatic order execution: DISABLED", 12, GREEN),
                txt(
                    "अभी कोई असली broker order नहीं भेजा जाता।",
                    11, MUTED
                )
            ),
            card(
                "SIGNAL HISTORY",
                txt("No signals recorded yet.", 12, MUTED)
            )
        ])

    def data_page():
        show([
            card(
                "DATA / API CONNECTION",
                info_row("Primary source", "NOT CONNECTED", RED),
                info_row("Yahoo backup", "CHECKING", GOLD),
                info_row("Last update", "--"),
                info_row("Data freshness", "UNKNOWN")
            ),
            card(
                "BROKER API OPTIONS",
                txt("ZERODHA • DHAN • UPSTOX", 12),
                txt("ANGEL ONE • CUSTOM API", 12),
                txt(
                    "Broker connection बाद के चरण में जोड़ा जाएगा।",
                    11, MUTED
                )
            ),
            card(
                "DATA PLAN",
                txt("1. Yahoo testing / backup data", 12),
                txt("2. Authorized market-data vendor", 12),
                txt("3. Live futures and options chain", 12),
                txt("4. Broker API integration", 12)
            ),
            card(
                "IMPORTANT",
                txt(
                    "Yahoo data delayed या unavailable हो सकता है। "
                    "इसे official NSE live data न समझें।",
                    11, GOLD
                )
            ),
            ft.ElevatedButton(
                "CHECK DATA AGAIN",
                bgcolor=GOLD,
                color=BG,
                on_click=refresh_data
            )
        ])

    pages = {
        "Dashboard": dashboard,
        "Watchlist": watchlist_page,
        "Options": options_page,
        "Charts": charts_page,
        "Alerts": alerts_page,
        "Data/API": data_page
    }

    def navigate(name):
        nonlocal current_page
        current_page = name

        for key, button in nav_buttons.items():
            selected = key == name
            button.bgcolor = GOLD if selected else PANEL2
            button.color = BG if selected else WHITE

        pages[name]()
        page.update()

    async def refresh_data(e=None):
        data_status.value = "DATA: CONNECTING..."
        data_status.color = GOLD
        page.update()

        success = 0

        for name, symbol in SYMBOLS.items():
            try:
                data = await asyncio.to_thread(
                    get_market_data, symbol
                )
                market[name] = data
                success += 1
            except Exception:
                market.pop(name, None)

        if success:
            data_status.value = (
                "SOURCE: YAHOO FINANCE | MAY BE DELAYED"
            )
            data_status.color = GREEN
            update_time.value = (
                "Received: " +
                datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            )
        else:
            data_status.value = "DATA: OFFLINE / NO DATA"
            data_status.color = RED
            update_time.value = "Last update: unavailable"

        pages[current_page]()
        page.update()

    for name in pages:
        button = ft.ElevatedButton(
            name,
            bgcolor=PANEL2,
            color=WHITE,
            on_click=lambda e, n=name: navigate(n),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=9),
                padding=8
            )
        )
        nav_buttons[name] = button
        nav.controls.append(button)

    header = ft.Container(
        content=ft.Row([
            ft.Column([
                txt("♛  BOT KING", 23, GOLD, True),
                txt("SMART MARKET SCANNER", 9, MUTED)
            ], expand=True, spacing=2),
            ft.Container(
                content=txt("PAPER MODE", 10, GREEN, True),
                bgcolor="#18372F",
                padding=9,
                border_radius=10
            )
        ]),
        padding=14,
        bgcolor=BG
    )

    bottom = ft.Container(
        content=nav,
        padding=8,
        bgcolor="#0E1524",
        border=ft.border.only(
            top=ft.BorderSide(1, "#293A55")
        )
    )

    page.add(
        ft.Column([
            header,
            ft.Container(
                content=body,
                expand=True,
                padding=12
            ),
            bottom
        ], expand=True, spacing=0)
    )

    navigate("Dashboard")
    page.run_task(refresh_data)


ft.app(target=main)
