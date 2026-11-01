import flet as ft

BG = "#0B1020"
PANEL = "#151D31"
GOLD = "#F5C451"
MUTED = "#9AA8C2"
GREEN = "#35C98A"
RED = "#F06A75"

WATCHLIST = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "SBIN",
    "INFY", "TCS", "ITC", "LT", "AXISBANK",
    "KOTAKBANK", "BHARTIARTL", "TATAMOTORS",
    "MARUTI", "SUNPHARMA", "WIPRO"
]

FILTERS = [
    "Price Trend", "Volume Surge", "OI Change", "PCR",
    "Option Premium Change", "Futures Long/Short Buildup",
    "VWAP", "EMA 9/21", "RSI", "World News Sentiment",
    "Market Breadth", "Sector Strength", "Breakout Scanner",
    "Volume Confirmation", "OI Trap Alert", "No Trade Zone"
]


def main(page: ft.Page):
    page.title = "BOT KING"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 12
    page.scroll = ft.ScrollMode.AUTO

    watchlist = WATCHLIST.copy()
    timeframe = "5 min"

    title = ft.Text(
        "BOT KING / DASHBOARD",
        size=21,
        weight=ft.FontWeight.BOLD,
        color=GOLD
    )

    content = ft.Column(spacing=12)

    def text(value, size=13, color="white", bold=False):
        return ft.Text(
            value,
            size=size,
            color=color,
            weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL
        )

    def panel(heading, controls):
        return ft.Container(
            content=ft.Column(
                [text(heading, 16, GOLD, True)] + controls,
                spacing=9
            ),
            bgcolor=PANEL,
            border_radius=12,
            padding=13
        )

    def metric(name, value="--", note="NO DATA"):
        return ft.Container(
            content=ft.Column([
                text(name, 11, MUTED),
                text(value, 19, GOLD, True),
                text(note, 10, MUTED)
            ], spacing=4),
            bgcolor="#202A40",
            border_radius=9,
            padding=9,
            expand=True
        )

    def row(*controls):
        return ft.Row(list(controls), spacing=8, wrap=True)

    def show_dashboard():
        content.controls = [
            ft.Container(
                content=text(
                    "DATA: NOT CONNECTED  |  SIGNAL: WAIT / NO DATA",
                    11, RED, True
                ),
                bgcolor="#321F2B",
                padding=10,
                border_radius=8
            ),

            panel("INTRADAY LIVE SCANNER", [
                text("Select scanning timeframe", 12, MUTED),
                row(*[
                    ft.ElevatedButton(
                        t,
                        bgcolor=GOLD if t == timeframe else "#26334D",
                        color="#101727" if t == timeframe else "white",
                        on_click=lambda e, v=t: change_timeframe(v)
                    )
                    for t in ["1 min", "5 min", "10 min", "15 min"]
                ]),
                text("Selected: " + timeframe, 12, GOLD),
                row(metric("NIFTY 50"), metric("BANK NIFTY")),
                row(metric("SENSEX"), metric("INDIA VIX"))
            ]),

            panel("MARKET SCORE MODEL", [
                text("Model score is not a probability or guarantee.", 11, MUTED),
                row(
                    metric("World News", "20%", "WEIGHT"),
                    metric("Futures", "40%", "WEIGHT"),
                    metric("Options / OI", "40%", "WEIGHT")
                ),
                row(
                    metric("Bullish Score"),
                    metric("Bearish Score")
                )
            ]),

            panel("CE / PE POSITIONING", [
                row(metric("CE OI Change"), metric("PE OI Change")),
                row(metric("CE Premium"), metric("PE Premium")),
                text("CE/PE positioning requires underlying price, premium and OI confirmation.", 11, MUTED)
            ]),

            panel("FUTURES LONG / SHORT BUILDUP", [
                row(metric("Long Buildup"), metric("Short Buildup")),
                text("Price and OI interpretation:", 12, GOLD, True),
                text("Price up + OI up = Long buildup"),
                text("Price down + OI up = Short buildup"),
                text("Price up + OI down = Short covering"),
                text("Price down + OI down = Long unwinding")
            ]),

            panel("SCANNER FILTERS", [
                text("Filters ready; results need a connected market-data feed.", 11, MUTED)
            ] + [
                text("○  " + f, 12) for f in FILTERS
            ]),

            panel("SWING VIEW", [
                text("Swing timeframe: Daily / Weekly", 12, MUTED),
                row(metric("Swing Trend"), metric("Breakout"), metric("Swing RSI")),
                text("Swing analysis will appear after data connection.", 11, MUTED)
            ]),

            panel("DATA STATUS", [
                text("Market prices: NOT CONNECTED", 12, RED),
                text("Options / Futures OI: NOT CONNECTED", 12, RED),
                text("World news sentiment: NOT CONNECTED", 12, RED),
                text("Yahoo Finance: planned for testing; may be delayed.", 11, MUTED),
                text("NSE-authorized vendor: planned primary live source.", 11, MUTED),
                text("Broker API: optional, last development stage.", 11, MUTED)
            ])
        ]
        page.update()

    def change_timeframe(value):
        nonlocal timeframe
        timeframe = value
        show_dashboard()

    def show_watchlist():
        symbol_input = ft.TextField(
            label="Stock symbol (example: TATAMOTORS)",
            expand=True
        )
        stock_rows = ft.Column(spacing=5)

        def refresh():
            stock_rows.controls = []
            for symbol in watchlist:
                stock_rows.controls.append(
                    ft.Container(
                        content=ft.Row([
                            text(symbol, 13, "white", True),
                            ft.Container(expand=True),
                            text("NO DATA", 10, MUTED),
                            ft.TextButton(
                                "REMOVE",
                                on_click=lambda e, s=symbol: remove_stock(s)
                            )
                        ]),
                        bgcolor="#202A40",
                        padding=8,
                        border_radius=8
                    )
                )
            page.update()

        def remove_stock(symbol):
            if symbol in watchlist:
                watchlist.remove(symbol)
            refresh()

        def add_stock(e):
            symbol = (symbol_input.value or "").strip().upper()
            if symbol and symbol not in watchlist:
                watchlist.append(symbol)
            symbol_input.value = ""
            refresh()

        content.controls = [
            panel("MY WATCHLIST", [
                text("Add or remove stocks from your list.", 11, MUTED),
                row(
                    symbol_input,
                    ft.ElevatedButton("ADD", on_click=add_stock, bgcolor=GOLD, color="#101727")
                ),
                stock_rows
            ])
        ]
        refresh()

    def show_options():
        content.controls = [
            panel("OPTIONS & OI CHAIN", [
                text("Options data is not connected. Values are intentionally blank.", 11, MUTED),
                row(metric("PCR"), metric("MAX PAIN"), metric("ATM STRIKE")),
                row(metric("Total CE OI"), metric("Total PE OI")),
                row(metric("CE Premium Change"), metric("PE Premium Change"))
            ])
        ]
        page.update()

    def show_charts():
        content.controls = [
            panel("CHART ANALYTICS", [
                text("Selected timeframe: " + timeframe, 12, GOLD),
                row(metric("EMA 9"), metric("EMA 21")),
                row(metric("RSI"), metric("VWAP")),
                metric("PRICE / VOLUME CHART", "--", "DATA NOT CONNECTED"),
                text("Indicators will calculate after price-feed connection.", 11, MUTED)
            ])
        ]
        page.update()

    def show_alerts():
        content.controls = [
            panel("ALERTS & SIGNAL HISTORY", [
                text("Alert-only / paper mode. Automatic order execution is disabled.", 12, GREEN, True),
                row(metric("Today's Signals", "0"), metric("Win Rate", "--", "NOT CALCULATED")),
                text("No signals generated. No trades will be invented without data.", 11, MUTED)
            ])
        ]
        page.update()

    def show_data():
        content.controls = [
            panel("DATA SOURCES & API", [
                text("Primary live source: NSE-authorized data vendor (planned)", 12),
                text("Testing source: Yahoo Finance (may be delayed)", 12),
                text("Options and Futures OI: NOT CONNECTED", 12, RED),
                text("World news sentiment: NOT CONNECTED", 12, RED),
                text("Broker API: optional, planned for last stage", 12),
                ft.Divider(),
                text("Live market data requires a suitable licensed data feed.", 12, GOLD, True),
                text("This version is an interface only. No credentials are stored and no orders are placed.", 11, MUTED)
            ])
        ]
        page.update()

    def navigate(name):
        title.value = "BOT KING / " + name.upper()
        pages[name]()
        page.update()

    pages = {
        "Dashboard": show_dashboard,
        "Watchlist": show_watchlist,
        "Options": show_options,
        "Charts": show_charts,
        "Alerts": show_alerts,
        "Data/API": show_data
    }

    navigation = ft.Row(
        [
            ft.ElevatedButton(
                name,
                on_click=lambda e, n=name: navigate(n),
                bgcolor="#26334D",
                color="white"
            )
            for name in pages
        ],
        wrap=True,
        spacing=5
    )

    page.add(
        ft.Column([
            title,
            text("INDIAN MARKET SCANNER  |  INTRADAY + SWING", 10, MUTED),
            navigation,
            ft.Divider(),
            content
        ], spacing=10)
    )

    show_dashboard()


ft.app(target=main)
