import flet as ft
import asyncio
import urllib.request
import json
from datetime import datetime


def main(page: ft.Page):
    page.title = "BOT KING"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#08111F"
    page.padding = 0
    page.spacing = 0

    GOLD = "#F5C542"
    CARD = "#111E30"
    MUTED = "#91A0B5"
    GREEN = "#20C997"
    RED = "#FF647C"

    selected_tab = "Dashboard"
    watchlist = ["NIFTY", "BANKNIFTY", "RELIANCE", "HDFCBANK"]
    quotes = {}
    received_time = "--"
    alerts_enabled = False

    content = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=12
    )

    status_text = ft.Text(
        "डेटा प्राप्त करने की तैयारी...",
        color=MUTED,
        size=11
    )

    symbol_input = ft.TextField(
        hint_text="जैसे: INFY, TCS, SBIN",
        expand=True,
        height=45,
        text_size=13,
        border_color="#34445B"
    )

    api_provider = ft.Dropdown(
        label="Broker चुनें",
        value="None",
        options=[
            ft.dropdown.Option("None"),
            ft.dropdown.Option("Zerodha"),
            ft.dropdown.Option("Dhan"),
            ft.dropdown.Option("Upstox"),
            ft.dropdown.Option("Angel One"),
            ft.dropdown.Option("Custom")
        ],
        text_size=13,
        border_color="#34445B"
    )

    def show_message(message):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message)
        )
        page.snack_bar.open = True
        page.update()

    def make_card(title, value, subtitle="", color=GOLD):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, color=MUTED, size=12),
                    ft.Text(
                        value,
                        size=23,
                        weight=ft.FontWeight.BOLD,
                        color=color
                    ),
                    ft.Text(subtitle, color=MUTED, size=10)
                ],
                spacing=5
            ),
            bgcolor=CARD,
            padding=15,
            border_radius=12,
            expand=True
        )

    def section_title(title, subtitle=""):
        return ft.Column(
            [
                ft.Text(
                    title,
                    size=19,
                    weight=ft.FontWeight.BOLD,
                    color=GOLD
                ),
                ft.Text(subtitle, size=11, color=MUTED)
            ],
            spacing=3
        )

    def get_quote(symbol):
        ticker = "^NSEI" if symbol == "NIFTY" else "^NSEBANK"

        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            + ticker
            + "?range=1d&interval=1m"
        )

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))

        result = data["chart"]["result"][0]
        meta = result.get("meta", {})

        price = meta.get("regularMarketPrice")
        previous = meta.get("chartPreviousClose")

        if previous is None:
            previous = meta.get("previousClose")

        if price is None:
            return None

        change = 0
        percent = 0

        if previous:
            change = price - previous
            percent = (change / previous) * 100

        return {
            "price": price,
            "change": change,
            "percent": percent
        }

    async def refresh_data(e=None):
        nonlocal received_time

        status_text.value = "डेटा लोड हो रहा है..."
        page.update()

        symbols = ["NIFTY", "BANKNIFTY"]

        for symbol in symbols:
            try:
                result = await asyncio.to_thread(
                    get_quote, symbol
                )
                quotes[symbol] = result
            except Exception:
                quotes[symbol] = None

        received_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        if any(quotes.get(s) for s in symbols):
            status_text.value = (
                "Yahoo Finance से डेटा प्राप्त हुआ | "
                + received_time
                + " | डेटा विलंबित हो सकता है"
            )
        else:
            status_text.value = (
                "डेटा उपलब्ध नहीं | इंटरनेट या डेटा स्रोत जाँचें"
            )

        render_screen()

    def quote_card(symbol, display_name):
        data = quotes.get(symbol)

        if not data:
            return make_card(
                display_name,
                "NO DATA",
                "भाव उपलब्ध नहीं",
                MUTED
            )

        price = data["price"]
        change = data["change"]
        percent = data["percent"]

        color = GREEN if change >= 0 else RED
        sign = "+" if change >= 0 else ""

        return make_card(
            display_name,
            f"{price:,.2f}",
            f"{sign}{change:,.2f} ({sign}{percent:.2f}%)",
            color
        )

    def render_dashboard():
        content.controls.extend(
            [
                section_title(
                    "MARKET DASHBOARD",
                    "भारतीय शेयर बाजार का डेटा"
                ),
                ft.Row(
                    [
                        quote_card("NIFTY", "NIFTY 50"),
                        quote_card("BANKNIFTY", "BANK NIFTY")
                    ],
                    spacing=10
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "DATA STATUS",
                                color=GOLD,
                                weight=ft.FontWeight.BOLD
                            ),
                            status_text,
                            ft.Text(
                                "भाव Yahoo Finance से हैं; "
                                "ये एक्सचेंज का प्रमाणित लाइव डेटा नहीं हैं।",
                                color=MUTED,
                                size=11
                            )
                        ],
                        spacing=7
                    ),
                    bgcolor=CARD,
                    padding=15,
                    border_radius=12
                ),
                ft.ElevatedButton(
                    "डेटा Refresh करें",
                    icon=ft.icons.REFRESH,
                    bgcolor=GOLD,
                    color="#08111F",
                    on_click=refresh_data
                ),
                section_title("MARKET GUIDE"),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Futures Buildup के नियम",
                                color=GOLD,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text("Price ↑ + OI ↑ = Long Buildup"),
                            ft.Text("Price ↓ + OI ↑ = Short Buildup"),
                            ft.Text("Price ↑ + OI ↓ = Short Covering"),
                            ft.Text("Price ↓ + OI ↓ = Long Unwinding")
                        ],
                        spacing=8
                    ),
                    bgcolor=CARD,
                    padding=15,
                    border_radius=12
                ),
                ft.Text(
                    "ध्यान दें: यह ऐप अभी ट्रेडिंग सिग्नल या "
                    "ऑर्डर निष्पादित नहीं करता।",
                    color=MUTED,
                    size=11
                )
            ]
        )

    def add_symbol(e):
        symbol = symbol_input.value.strip().upper()

        if not symbol:
            show_message("पहले शेयर का नाम लिखें")
            return

        if symbol in watchlist:
            show_message("यह शेयर पहले से Watchlist में है")
            return

        if not symbol.replace(".", "").isalnum():
            show_message("कृपया सही Symbol लिखें")
            return

        watchlist.append(symbol)
        symbol_input.value = ""
        render_screen()
        show_message(symbol + " Watchlist में जुड़ गया")

    def remove_symbol(symbol):
        if symbol in watchlist:
            watchlist.remove(symbol)
        render_screen()

    def render_watchlist():
        content.controls.extend(
            [
                section_title(
                    "MY WATCHLIST",
                    "अपने पसंदीदा शेयर जोड़ें या हटाएँ"
                ),
                ft.Row(
                    [
                        symbol_input,
                        ft.IconButton(
                            icon=ft.icons.ADD_CIRCLE,
                            icon_color=GOLD,
                            on_click=add_symbol
                        )
                    ],
                    spacing=5
                )
            ]
        )

        for symbol in watchlist:
            content.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                symbol,
                                expand=True,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                "डेटा मैपिंग उपलब्ध नहीं"
                                if symbol not in ["NIFTY", "BANKNIFTY"]
                                else "डेटा Dashboard में",
                                color=MUTED,
                                size=10
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                icon_color=RED,
                                on_click=lambda e, s=symbol: remove_symbol(s)
                            )
                        ]
                    ),
                    bgcolor=CARD,
                    padding=10,
                    border_radius=10
                )
            )

        content.controls.append(
            ft.Text(
                "नोट: अभी केवल NIFTY और BANK NIFTY के लिए "
                "भाव प्राप्त करने का प्रयास होता है। बाकी शेयरों "
                "के लिए डेटा मैपिंग आगे जोड़ी जाएगी।",
                color=MUTED,
                size=11
            )
        )

    def render_options():
        content.controls.extend(
            [
                section_title(
                    "OPTIONS CENTER",
                    "CE / PE और Options Chain"
                ),
                make_card(
                    "OPTIONS CHAIN",
                    "NO DATA",
                    "Options Chain API अभी कनेक्ट नहीं है",
                    MUTED
                ),
                make_card(
                    "CALL / PUT OI",
                    "NO DATA",
                    "Open Interest डेटा उपलब्ध नहीं",
                    MUTED
                ),
                make_card(
                    "PREMIUM",
                    "NO DATA",
                    "CE और PE प्रीमियम उपलब्ध नहीं",
                    MUTED
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Options डेटा के लिए आवश्यक",
                                color=GOLD,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text("• Underlying price"),
                            ft.Text("• CE / PE premium"),
                            ft.Text("• Open Interest और OI Change"),
                            ft.Text("• अधिकृत Options Data API")
                        ],
                        spacing=7
                    ),
                    bgcolor=CARD,
                    padding=15,
                    border_radius=12
                ),
                ft.Text(
                    "अभी कोई CE/PE खरीदने या बेचने का सिग्नल "
                    "नहीं दिया जा रहा है।",
                    color=MUTED,
                    size=11
                )
            ]
        )

    def render_charts():
        content.controls.extend(
            [
                section_title(
                    "CHARTS & SCANNER",
                    "Technical analysis"
                ),
                make_card(
                    "PRICE CHART",
                    "NO DATA",
                    "Candle data feed अभी कनेक्ट नहीं है",
                    MUTED
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "SCANNER TIMEFRAMES",
                                color=GOLD,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text("1 Minute  |  5 Minute"),
                            ft.Text("10 Minute | 15 Minute")
                        ],
                        spacing=8
                    ),
                    bgcolor=CARD,
                    padding=15,
                    border_radius=12
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "SCANNER MODULES",
                                color=GOLD,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text("• Market Breadth"),
                            ft.Text("• Sector Strength"),
                            ft.Text("• Breakout Scanner"),
                            ft.Text("• Volume Confirmation"),
                            ft.Text("• OI Trap Alert"),
                            ft.Text("• No Trade Zone"),
                            ft.Text("• Signal History")
                        ],
                        spacing=8
                    ),
                    bgcolor=CARD,
                    padding=15,
                    border_radius=12
                ),
                ft.Text(
                    "ये मॉड्यूल अभी तैयार नहीं हैं। "
                    "डेटा फीड मिलने के बाद इन्हें सक्रिय किया जाएगा।",
                    color=MUTED,
                    size=11
                )
            ]
        )

    def change_alert(e):
        nonlocal alerts_enabled
        alerts_enabled = e.control.value
        render_screen()

    def render_alerts():
        content.controls.extend(
            [
                section_title(
                    "ALERT CENTER",
                    "Alerts और Paper Trading"
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "PRICE / SIGNAL ALERTS",
                                color=GOLD,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Switch(
                                label="Alerts चालू / बंद",
                                value=alerts_enabled,
                                active_color=GOLD,
                                on_change=change_alert
                            ),
                            ft.Text(
                                "अभी वास्तविक मार्केट अलर्ट सेवा "
                                "कनेक्ट नहीं है।",
                                color=MUTED,
                                size=11
                            )
                        ],
                        spacing=10
                    ),
                    bgcolor=CARD,
                    padding=15,
                    border_radius=12
                ),
                section_title("PAPER TRADING"),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "यह केवल Demo संदेश है। "
                                "कोई वास्तविक ऑर्डर नहीं लगेगा।",
                                color=MUTED,
                                size=11
                            ),
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        "Demo CE",
                                        bgcolor=GREEN,
                                        color="#08111F",
                                        on_click=lambda e: show_message(
                                            "Demo CE: कोई ऑर्डर नहीं लगाया गया"
                                        )
                                    ),
                                    ft.ElevatedButton(
                                        "Demo PE",
                                        bgcolor=RED,
                                        color="#08111F",
                                        on_click=lambda e: show_message(
                                            "Demo PE: कोई ऑर्डर नहीं लगाया गया"
                                        )
                                    )
                                ]
                            )
                        ],
                        spacing=12
                    ),
                    bgcolor=CARD,
                    padding=15,
                    border_radius=12
                )
            ]
        )

    def render_api():
        content.controls.extend(
            [
                section_title(
                    "DATA / API SETTINGS",
                    "Broker और Market Data कनेक्शन"
                ),
                api_provider,
                ft.TextField(
                    label="API Key",
                    password=True,
                    can_reveal_password=True,
                    border_color="#34445B"
                ),
                ft.TextField(
                    label="API Secret",
                    password=True,
                    can_reveal_password=True,
                    border_color="#34445B"
                ),
                ft.TextField(
                    label="Redirect URL",
                    border_color="#34445B"
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "CONNECTION STATUS",
                                color=GOLD,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                "NOT CONNECTED",
                                color=RED,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                "ये फ़ील्ड अभी केवल UI हैं। "
                                "Broker API कनेक्शन लागू नहीं है।",
                                color=MUTED,
                                size=11
                            )
                        ],
                        spacing=7
                    ),
                    bgcolor=CARD,
                    padding=15,
                    border_radius=12
                ),
                ft.Text(
                    "सुरक्षा: असली API Key या Secret इस ऐप, "
                    "GitHub कोड या APK में सेव नहीं करना है। "
                    "आगे सुरक्षित HTTPS Backend और Broker OAuth "
                    "की जरूरत होगी।",
                    color=GOLD,
                    size=11
                )
            ]
        )

    def render_screen():
        content.controls.clear()

        if selected_tab == "Dashboard":
            render_dashboard()
        elif selected_tab == "Watchlist":
            render_watchlist()
        elif selected_tab == "Options":
            render_options()
        elif selected_tab == "Charts":
            render_charts()
        elif selected_tab == "Alerts":
            render_alerts()
        elif selected_tab == "Data/API":
            render_api()

        page.update()

    def select_tab(tab):
        nonlocal selected_tab
        selected_tab = tab
        render_screen()

    header = ft.Container(
        content=ft.Row(
            [
                ft.Text("👑", size=25),
                ft.Column(
                    [
                        ft.Text(
                            "BOT KING",
                            size=19,
                            weight=ft.FontWeight.BOLD,
                            color=GOLD
                        ),
                        ft.Text(
                            "SMART MARKET TERMINAL",
                            size=9,
                            color=MUTED
                        )
                    ],
                    spacing=0,
                    expand=True
                ),
                ft.IconButton(
                    icon=ft.icons.REFRESH,
                    icon_color=GOLD,
                    tooltip="Refresh Data",
                    on_click=refresh_data
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        bgcolor="#0D1929",
        padding=ft.padding.only(left=15, right=8, top=10, bottom=10)
    )

    nav_items = [
        ("Dashboard", ft.icons.DASHBOARD),
        ("Watchlist", ft.icons.STAR),
        ("Options", ft.icons.SHOW_CHART),
        ("Charts", ft.icons.CANDLESTICK_CHART),
        ("Alerts", ft.icons.NOTIFICATIONS),
        ("Data/API", ft.icons.SETTINGS)
    ]

    def make_nav_button(tab, icon):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=19, color=GOLD),
                    ft.Text(
                        tab,
                        size=9,
                        color=GOLD
                    )
                ],
                spacing=3,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=5,
            expand=True,
            on_click=lambda e: select_tab(tab)
        )

    bottom_menu = ft.Container(
        content=ft.Row(
            [
                make_nav_button(tab, icon)
                for tab, icon in nav_items
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            spacing=0
        ),
        bgcolor="#0D1929",
        padding=ft.padding.only(top=8, bottom=8)
    )

    page.add(
        ft.Column(
            [
                header,
                ft.Container(
                    content=content,
                    expand=True,
                    padding=12
                ),
                bottom_menu
            ],
            expand=True,
            spacing=0
        )
    )

    render_screen()
    page.run_task(refresh_data)


ft.app(target=main)
