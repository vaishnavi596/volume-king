
import flet as ft
import asyncio
import json
import urllib.request
from datetime import datetime

BG = "#080D18"
CARD = "#172235"
GOLD = "#FFC857"
GREEN = "#35D6A0"
RED = "#FF7272"
WHITE = "#FFFFFF"
MUTED = "#AAB4C5"

def get_quote(symbol):
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + symbol + "?range=1d&interval=5m"
    )
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=12) as response:
        raw = json.loads(response.read().decode())

    result = raw["chart"]["result"][0]
    meta = result["meta"]
    price = meta.get("regularMarketPrice")
    previous = meta.get("previousClose")

    if price is None:
        raise ValueError("Price unavailable")

    change = price - previous if previous else None
    percent = change / previous * 100 if previous else None

    return {
        "price": price,
        "change": change,
        "percent": percent,
        "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }


def main(page: ft.Page):
    page.title = "BOT KING"
    page.bgcolor = BG
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.window_min_width = 320

    selected = 0
    watchlist = ["NIFTY", "BANKNIFTY", "RELIANCE", "HDFCBANK"]
    quotes = {}
    quote_status = "डेटा अभी लोड नहीं हुआ"

    header_status = ft.Text(
        "MARKET DATA: CHECKING",
        color=GOLD,
        size=11
    )

    title = ft.Text(
        "BOT KING",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=GOLD
    )

    content = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=12
    )

    def card(label, value, subtitle=None):
        items = [
            ft.Text(label, color=MUTED, size=12),
            ft.Text(
                value,
                color=WHITE,
                size=23,
                weight=ft.FontWeight.BOLD
            )
        ]
        if subtitle:
            items.append(ft.Text(subtitle, color=MUTED, size=11))

        return ft.Container(
            content=ft.Column(items, spacing=7),
            bgcolor=CARD,
            padding=15,
            border_radius=12,
            expand=True
        )

    def heading(text):
        return ft.Text(
            text,
            color=GOLD,
            size=17,
            weight=ft.FontWeight.BOLD
        )

    def quote_card(name, key):
        data = quotes.get(key)
        if not data:
            return card(name, "--", "डेटा उपलब्ध नहीं")

        change = data["change"]
        percent = data["percent"]

        if change is None:
            subtitle = "बदलाव उपलब्ध नहीं"
        else:
            subtitle = f"{change:+.2f} ({percent:+.2f}%)"

        color = GREEN if change is not None and change >= 0 else RED

        return ft.Container(
            content=ft.Column([
                ft.Text(name, color=MUTED, size=12),
                ft.Text(
                    f"{data['price']:,.2f}",
                    color=WHITE,
                    size=24,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(subtitle, color=color, size=13),
                ft.Text("Yahoo Finance • संभावित विलंबित डेटा",
                        color=MUTED, size=10)
            ], spacing=7),
            bgcolor=CARD,
            padding=15,
            border_radius=12,
            expand=True
        )

    async def refresh_data(e=None):
        nonlocal quote_status
        header_status.value = "MARKET DATA: LOADING..."
        quote_status = "डेटा लोड हो रहा है..."
        page.update()

        symbols = {
            "NIFTY": "^NSEI",
            "BANKNIFTY": "^NSEBANK"
        }

        results = await asyncio.gather(
            *[
                asyncio.to_thread(get_quote, symbol)
                for symbol in symbols.values()
            ],
            return_exceptions=True
        )

        for key, result in zip(symbols.keys(), results):
            if isinstance(result, Exception):
                quotes.pop(key, None)
            else:
                quotes[key] = result

        if quotes:
            header_status.value = "MARKET DATA: RECEIVED"
            header_status.color = GREEN
            quote_status = "Yahoo Finance डेटा प्राप्त हुआ। यह लाइव NSE डेटा होने की गारंटी नहीं है।"
        else:
            header_status.value = "MARKET DATA: UNAVAILABLE"
            header_status.color = RED
            quote_status = "डेटा नहीं मिला। इंटरनेट या डेटा स्रोत जाँचें।"

        render_page()

    def render_dashboard():
        content.controls = [
            heading("MARKET DASHBOARD"),
            ft.Row([
                quote_card("NIFTY 50", "NIFTY"),
                quote_card("BANK NIFTY", "BANKNIFTY")
            ]),
            card("MARKET STATUS", "डेटा स्रोत पर निर्भर",
                 "मार्केट खुला है या बंद, इसकी पुष्टि अलग से करें"),
            card("TRADING SIGNAL", "WAIT",
                 "अभी कोई सत्यापित लाइव सिग्नल उपलब्ध नहीं"),
            heading("INTRADAY SCANNER"),
            ft.Text("Timeframe चुनें:", color=MUTED),
            ft.Row([
                ft.OutlinedButton("1 MIN"),
                ft.OutlinedButton("5 MIN"),
                ft.OutlinedButton("10 MIN"),
                ft.OutlinedButton("15 MIN")
            ], wrap=True),
            card("SCANNER STATUS", "NOT CONNECTED",
                 "टाइमफ्रेम बटन अभी केवल विकल्प हैं; स्कैनिंग इंजन जुड़ा नहीं है।"),
            heading("FUTURES BUILDUP GUIDE"),
            card("LONG BUILDUP", "Price ↑  OI ↑"),
            card("SHORT BUILDUP", "Price ↓  OI ↑"),
            card("SHORT COVERING", "Price ↑  OI ↓"),
            card("LONG UNWINDING", "Price ↓  OI ↓"),
            ft.Text(quote_status, color=MUTED, size=11),
            ft.ElevatedButton(
                "REFRESH MARKET DATA",
                icon=ft.icons.REFRESH,
                on_click=refresh_data
            )
        ]
        page.update()

    symbol_input = ft.TextField(
        label="स्टॉक का नाम (जैसे INFY)",
        border_color="#40516B"
    )

    def add_symbol(e):
        symbol = (symbol_input.value or "").strip().upper()
        if symbol and symbol not in watchlist:
            watchlist.append(symbol)
            symbol_input.value = ""
            render_page()

    def remove_symbol(symbol):
        if symbol in watchlist:
            watchlist.remove(symbol)
            render_page()

    def render_watchlist():
        controls = [
            heading("MY WATCHLIST"),
            ft.TextField(
                label="नया स्टॉक जोड़ें",
                hint_text="उदाहरण: INFY, TCS, RELIANCE",
                on_submit=lambda e: add_symbol(e)
            ),
            ft.ElevatedButton("ADD STOCK", on_click=add_symbol)
        ]

        for symbol in watchlist:
            controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(symbol, color=WHITE, expand=True),
                        ft.IconButton(
                            icon=ft.icons.DELETE_OUTLINE,
                            icon_color=RED,
                            on_click=lambda e, s=symbol: remove_symbol(s)
                        )
                    ]),
                    bgcolor=CARD,
                    padding=10,
                    border_radius=10
                )
            )

        controls.append(
            ft.Text(
                "Watchlist के शेयरों के लाइव भाव का कनेक्शन अभी बाकी है।",
                color=MUTED,
                size=11
            )
        )
        content.controls = controls
        page.update()

    def render_options():
        content.controls = [
            heading("OPTIONS ANALYSIS"),
            card("PCR", "NO DATA",
                 "Options Chain API की जरूरत है"),
            card("MAX PAIN", "NO DATA",
                 "सत्यापित OI डेटा उपलब्ध नहीं"),
            card("CALL OI", "NO DATA"),
            card("PUT OI", "NO DATA"),
            card("ATM STRIKE", "NO DATA"),
            card("IV / PREMIUM", "NO DATA"),
            heading("CE / PE POSITIONING"),
            card("OPTIONS SIGNAL", "WAIT",
                 "बिना लाइव Options Chain के CE/PE सिग्नल नहीं दिखाया जाएगा।"),
            ft.Text(
                "Options ट्रेडिंग जोखिमपूर्ण है। यहां कोई असली ऑर्डर नहीं भेजा जाता।",
                color=MUTED,
                size=11
            )
        ]
        page.update()

    def render_charts():
        content.controls = [
            heading("MARKET CHARTS"),
            card("NIFTY CHART", "NO DATA",
                 "चार्ट डेटा फीड अभी कनेक्ट नहीं है"),
            card("BANK NIFTY CHART", "NO DATA",
                 "चार्ट डेटा फीड अभी कनेक्ट नहीं है"),
            card("VOLUME ANALYSIS", "NO DATA"),
            card("SUPPORT / RESISTANCE", "NO DATA"),
            card("BREAKOUT SCANNER", "NOT CONNECTED",
                 "लाइव कैंडल और वॉल्यूम डेटा की जरूरत है")
        ]
        page.update()

    alert_switch = ft.Switch(
        label="पेपर अलर्ट चालू करें",
        value=False,
        active_color=GREEN
    )

    def render_alerts():
        content.controls = [
            heading("ALERTS & PAPER TRADING"),
            card("ALERT STATUS",
                 "ON" if alert_switch.value else "OFF",
                 "यह केवल UI सेटिंग है; लाइव अलर्ट इंजन अभी जुड़ा नहीं है"),
            alert_switch,
            heading("SIMULATION"),
            ft.Row([
                ft.ElevatedButton(
                    "BUY CE (PAPER)",
                    bgcolor="#087F5B",
                    color=WHITE,
                    on_click=lambda e: show_message(
                        "CE पेपर सिमुलेशन चुना गया। असली ऑर्डर नहीं भेजा गया।"
                    )
                ),
                ft.ElevatedButton(
                    "BUY PE (PAPER)",
                    bgcolor="#B02A37",
                    color=WHITE,
                    on_click=lambda e: show_message(
                        "PE पेपर सिमुलेशन चुना गया। असली ऑर्डर नहीं भेजा गया।"
                    )
                )
            ], wrap=True),
            card("TRADE HISTORY", "NO TRADES",
                 "पेपर ट्रेडिंग रिकॉर्ड अभी शुरू नहीं हुआ")
        ]
        page.update()

    def show_message(message):
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        page.update()

    provider = ft.Dropdown(
        label="Broker / API Provider",
        value="None",
        options=[
            ft.dropdown.Option("None", "अभी कोई API नहीं"),
            ft.dropdown.Option("Zerodha", "Zerodha Kite"),
            ft.dropdown.Option("Dhan", "Dhan"),
            ft.dropdown.Option("Upstox", "Upstox"),
            ft.dropdown.Option("Angel One", "Angel One SmartAPI"),
            ft.dropdown.Option("Custom", "Custom API")
        ],
        border_color="#40516B"
    )

    api_key = ft.TextField(
        label="API Key",
        password=True,
        can_reveal_password=True,
        border_color="#40516B"
    )

    api_secret = ft.TextField(
        label="API Secret",
        password=True,
        can_reveal_password=True,
        border_color="#40516B"
    )

    redirect_url = ft.TextField(
        label="Redirect URL (यदि आवश्यक हो)",
        border_color="#40516B"
    )

    def save_api_settings(e):
        show_message(
            "सेटिंग इस स्क्रीन के लिए चुनी गई है। "
            "अभी API कनेक्शन या सुरक्षित सेविंग सक्रिय नहीं है।"
        )

    def render_data_api():
        content.controls = [
            heading("DATA / API SETTINGS"),
            card("MARKET DATA SOURCE", "Yahoo Finance",
                 "केवल सामान्य भाव; विलंब संभव है"),
            provider,
            api_key,
            api_secret,
            redirect_url,
            ft.ElevatedButton(
                "SAVE SETTINGS",
                icon=ft.icons.SAVE,
                on_click=save_api_settings
            ),
            ft.Divider(color="#34445C"),
            heading("CONNECTION STATUS"),
            card("BROKER CONNECTION", "NOT CONNECTED",
                 "अभी कोई ब्रोकर API प्रमाणित नहीं है"),
            card("OPTIONS CHAIN", "NOT CONNECTED",
                 "अधिकृत Options Chain डेटा स्रोत आवश्यक है"),
            ft.Text(
                "सुरक्षा: API Key और Secret को अभी इस ऐप में सेव या "
                "ब्रोकर को भेजा नहीं जाता। इन्हें चैट में भी साझा न करें। "
                "वास्तविक कनेक्शन के लिए सुरक्षित HTTPS बैकएंड और "
                "ब्रोकर की OAuth/API प्रक्रिया बनानी होगी।",
                color=GOLD,
                size=12
            ),
            ft.ElevatedButton(
                "REFRESH MARKET DATA",
                icon=ft.icons.REFRESH,
                on_click=refresh_data
            )
        ]
        page.update()

    renderers = [
        render_dashboard,
        render_watchlist,
        render_options,
        render_charts,
        render_alerts,
        render_data_api
    ]

    labels = [
        "Dashboard", "Watchlist", "Options",
        "Charts", "Alerts", "Data/API"
    ]

    icons = [
        ft.icons.DASHBOARD,
        ft.icons.STAR,
        ft.icons.SHOW_CHART,
        ft.icons.INSERT_CHART,
        ft.icons.NOTIFICATIONS,
        ft.icons.SETTINGS
    ]

    nav_row = ft.Row(spacing=0, alignment=ft.MainAxisAlignment.SPACE_AROUND)

    def select_tab(index):
        nonlocal selected
        selected = index
        update_nav()
        renderers[selected]()

    def update_nav():
        nav_row.controls = []
        for i, label in enumerate(labels):
            nav_row.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(
                            icons[i],
                            color=GOLD if selected == i else MUTED,
                            size=19
                        ),
                        ft.Text(
                            label,
                            size=9,
                            color=GOLD if selected == i else MUTED,
                            text_align=ft.TextAlign.CENTER
                        )
                    ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=5,
                    on_click=lambda e, idx=i: select_tab(idx),
                    bgcolor="#24334A" if selected == i else None,
                    border_radius=8
                )
            )

    header = ft.Container(
        content=ft.Column([
            ft.Row([
                title,
                ft.Container(expand=True),
                ft.Text("👑", size=23)
            ]),
            header_status
        ], spacing=3),
        bgcolor=BG,
        padding=ft.padding.only(left=14, right=14, top=12, bottom=8)
    )

    bottom_menu = ft.Container(
        content=nav_row,
        bgcolor="#101A2B",
        padding=6,
        border=ft.border.only(top=ft.BorderSide(1, "#34445C"))
    )

    update_nav()
    render_dashboard()

    page.add(
        ft.Column([
            header,
            ft.Container(
                content=content,
                expand=True,
                padding=12
            ),
            bottom_menu
        ], expand=True, spacing=0)
    )

    page.run_task(refresh_data)


ft.app(target=main)
