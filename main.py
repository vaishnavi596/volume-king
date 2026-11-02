import flet as ft

BG, PANEL, PANEL2 = "#090D18", "#141C2D", "#1B2740"
GOLD, WHITE, MUTED = "#F5C451", "#F4F7FC", "#9AA8BD"
GREEN, RED, BLUE = "#35C98A", "#F16D78", "#63A7FF"

WATCHLIST = ["RELIANCE", "HDFCBANK", "ICICIBANK", "SBIN", "INFY", "TCS",
             "ITC", "LT", "AXISBANK", "KOTAKBANK", "BHARTIARTL",
             "TATAMOTORS", "MARUTI", "SUNPHARMA", "WIPRO"]

def main(page: ft.Page):
    page.title = "BOT KING"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.spacing = 0

    body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=12)
    nav = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=5)
    watch = list(WATCHLIST)
    nav_buttons = {}

    def t(s, size=13, color=WHITE, weight=ft.FontWeight.NORMAL):
        return ft.Text(str(s), size=size, color=color, weight=weight)

    def card(title, *items):
        return ft.Container(
            content=ft.Column([t(title, 13, GOLD, ft.FontWeight.BOLD), *items], spacing=9),
            bgcolor=PANEL, padding=14, border_radius=14,
            border=ft.border.all(1, "#26334B"))

    def metric(name):
        return ft.Container(
            content=ft.Column([t(name, 11, MUTED, ft.FontWeight.BOLD),
                               t("--", 21, WHITE, ft.FontWeight.BOLD),
                               t("NO LIVE DATA", 10, GOLD)], spacing=4),
            bgcolor=PANEL2, padding=12, border_radius=12, expand=True)

    def row(a, b, c=MUTED):
        return ft.Row([t(a, 12, MUTED), ft.Container(expand=True),
                       t(b, 12, c, ft.FontWeight.BOLD)])

    def show(items):
        body.controls.clear()
        body.controls.extend(items)
        page.update()

    def dashboard():
        show([
            card("MARKET STATUS",
                 ft.Row([t("DATA: DISCONNECTED", 12, RED, ft.FontWeight.BOLD),
                         ft.Container(expand=True), t("SIGNAL: WAIT", 12, GOLD, ft.FontWeight.BOLD)]),
                 t("Live feed connect hone par hi prices aur signals dikhenge.", 11, MUTED)),
            ft.Row([metric("NIFTY 50"), metric("BANK NIFTY")], spacing=10),
            ft.Row([metric("SENSEX"), metric("INDIA VIX")], spacing=10),
            card("INTRADAY LIVE SCANNER",
                 t("Timeframe", 12, MUTED),
                 ft.Row([ft.OutlinedButton("1 MIN"), ft.OutlinedButton("5 MIN"),
                         ft.OutlinedButton("10 MIN"), ft.OutlinedButton("15 MIN")],
                        wrap=True, spacing=5),
                 row("World news sentiment", "20%", BLUE),
                 row("Futures positioning", "40%", BLUE),
                 row("Options premium / OI", "40%", BLUE),
                 t("MODEL SCORE: WAITING FOR AUTHORIZED DATA", 11, GOLD, ft.FontWeight.BOLD)),
            card("CE / PE POSITIONING", row("CALL (CE) OI", "NO DATA"),
                 row("PUT (PE) OI", "NO DATA"), row("PCR / MAX PAIN", "NO DATA"),
                 t("OI aur premium confirmation ke bina trade signal nahi banega.", 11, MUTED)),
            card("FUTURES BUILDUP GUIDE",
                 row("Price up + OI up", "LONG BUILDUP", GREEN),
                 row("Price down + OI up", "SHORT BUILDUP", RED),
                 row("Price up + OI down", "SHORT COVERING", GREEN),
                 row("Price down + OI down", "LONG UNWINDING", GOLD)),
            card("SMART FILTERS",
                 t("Market Breadth • Sector Strength • Breakout", 12),
                 t("Volume Confirmation • OI Trap • No Trade Zone", 12),
                 t("Signal History • Data Freshness • Swing View", 12))
        ])

    def watchlist_page():
        field = ft.TextField(hint_text="Stock symbol, e.g. TATASTEEL", text_size=13)
        rows = [ft.Container(content=ft.Row([
            ft.Column([t(s, 13, WHITE, ft.FontWeight.BOLD), t("Price: --  Change: --", 10, MUTED)],
                      spacing=3, expand=True), t("NO DATA", 10, GOLD)]),
            bgcolor=PANEL2, padding=10, border_radius=10) for s in watch]
        def add(e):
            symbol = (field.value or "").strip().upper()
            if symbol and symbol not in watch:
                watch.append(symbol)
                watchlist_page()
        show([card("MY WATCHLIST", t("Stocks add kar sakte hain. Data abhi disconnected hai.", 11, MUTED),
                   ft.Row([ft.Container(content=field, expand=True),
                           ft.ElevatedButton("ADD", on_click=add, bgcolor=GOLD, color=BG)])),
              card("TRACKED STOCKS", *rows)])

    def options_page():
        show([card("OPTIONS ANALYSIS", t("NIFTY / BANK NIFTY / SENSEX", 12, MUTED),
                   ft.Row([metric("PCR"), metric("MAX PAIN")]),
                   ft.Row([metric("ATM STRIKE"), metric("IV")])),
              card("OPEN INTEREST", row("CE OI buildup", "NO DATA"),
                   row("PE OI buildup", "NO DATA"), row("CE premium change", "NO DATA"),
                   row("PE premium change", "NO DATA"),
                   t("Options chain feed connect hone par analysis active hoga.", 11, MUTED)),
              card("TRADE SAFETY", t("Abhi koi CE/PE BUY ya SELL recommendation nahi di jayegi.", 12, GOLD))])

    def charts_page():
        show([card("CHARTS & INDICATORS", t("Selected symbol: NIFTY 50", 12, MUTED),
                   ft.Row([ft.OutlinedButton("1m"), ft.OutlinedButton("5m"),
                           ft.OutlinedButton("15m"), ft.OutlinedButton("1D")], wrap=True),
                   ft.Container(content=ft.Column([t("PRICE / VOLUME CHART", 14, GOLD),
                       t("Chart will appear after data connection.", 12, MUTED),
                       ft.Container(content=t("NO CHART DATA", 13, MUTED), height=110,
                                    alignment=ft.alignment.center, bgcolor="#101827",
                                    border_radius=10)], spacing=10),
                       bgcolor=PANEL2, padding=12, border_radius=12)),
              card("TECHNICAL INDICATORS", row("EMA 9 / EMA 21", "--"),
                   row("RSI 14", "--"), row("VWAP", "--"), row("Volume", "--"))])

    def alerts_page():
        show([card("ALERT CENTER", row("Price alerts", "INACTIVE"),
                   row("Breakout alerts", "INACTIVE"), row("OI trap alerts", "INACTIVE"),
                   row("No-trade zone alerts", "INACTIVE")),
              card("PAPER TRADING MODE", t("Automatic order execution: DISABLED", 12, GREEN),
                   t("Pehle data aur paper testing verify honge. Real orders place nahi honge.", 11, MUTED)),
              card("SIGNAL HISTORY", t("No signals recorded yet.", 12, MUTED))])

    def data_page():
        show([card("DATA / API CONNECTION", row("Primary source", "NOT CONNECTED", RED),
                   row("Backup / testing source", "NOT CONNECTED", RED),
                   row("Last update", "--"), row("Data freshness", "UNKNOWN")),
              card("CONNECTION PLAN", t("1. Authorized NSE market-data vendor", 12),
                   t("2. Delayed/test data for UI testing", 12),
                   t("3. Live futures and options chain feed", 12),
                   t("4. Broker API optional — last stage", 12)),
              card("IMPORTANT", t("Public feeds may be delayed and may not provide reliable live options OI. Live trading ke liye licensed data source zaroori hai.", 11, GOLD))])

    pages = {"Dashboard": dashboard, "Watchlist": watchlist_page, "Options": options_page,
             "Charts": charts_page, "Alerts": alerts_page, "Data/API": data_page}

    def navigate(name):
        for key, button in nav_buttons.items():
            button.bgcolor = GOLD if key == name else PANEL2
            button.color = BG if key == name else WHITE
        pages[name]()
        page.update()

    for name in pages:
        b = ft.ElevatedButton(name, bgcolor=PANEL2, color=WHITE,
            on_click=lambda e, n=name: navigate(n),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=9))
        nav_buttons[name] = b
        nav.controls.append(b)

    header = ft.Container(content=ft.Row([
        ft.Column([t("♛  BOT KING", 22, GOLD, ft.FontWeight.BOLD),
                   t("SMART MARKET SCANNER", 9, MUTED)], spacing=2, expand=True),
        ft.Container(content=t("PAPER MODE", 10, GREEN, ft.FontWeight.BOLD),
                     bgcolor="#18372F", padding=9, border_radius=10)]),
        padding=14, bgcolor=BG)
    bottom = ft.Container(content=nav, padding=8, bgcolor="#0E1524",
                          border=ft.border.only(top=ft.BorderSide(1, "#26334B")))
    page.add(ft.Column([header, ft.Container(content=body, expand=True, padding=12), bottom],
                       expand=True, spacing=0))
    navigate("Dashboard")

ft.app(target=main)
