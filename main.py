import flet as ft

BG = "#0B1220"
CARD = "#151F30"
GOLD = "#F5B942"
WHITE = "#FFFFFF"
MUTED = "#9AA9BD"


def main(page: ft.Page):
    page.title = "BOT KING"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.spacing = 0

    def heading(title, subtitle=""):
        return ft.Column([
            ft.Text(title, size=24, weight="bold", color=GOLD),
            ft.Text(subtitle, size=12, color=MUTED)
        ], spacing=4)

    def panel(title, value, note=""):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, color=MUTED, size=12),
                ft.Text(value, color=WHITE, size=22, weight="bold"),
                ft.Text(note, color=GOLD, size=11)
            ], spacing=5),
            bgcolor=CARD,
            padding=15,
            border_radius=12,
            expand=True
        )

    def section(title, controls):
        return ft.Column([
            ft.Text(title, color=GOLD, size=16, weight="bold"),
            *controls
        ], spacing=10)

    # PAGE 1: DASHBOARD
    dashboard = ft.Column([
        heading("BOT KING", "INDIAN MARKET DASHBOARD"),
        ft.Row([
            panel("NIFTY 50", "--", "Live data not connected"),
            panel("BANK NIFTY", "--", "Live data not connected")
        ]),
        section("MARKET SENTIMENT", [
            panel("Market Trend", "WAIT", "Data source required"),
            ft.Row([
                panel("PCR", "--", "Pending OI data"),
                panel("India VIX", "--", "Pending data")
            ])
        ]),
        section("IMPORTANT LEVELS", [
            ft.Row([
                panel("Support", "--"),
                panel("Resistance", "--")
            ]),
            panel("Market Update", "Not connected",
                  "Connect a market data provider for live values")
        ])
    ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

    # PAGE 2: OI CHAIN
    oi_page = ft.Column([
        heading("OI CHAIN", "OPEN INTEREST ANALYSIS"),
        ft.Row([
            panel("PCR", "--", "Pending live data"),
            panel("Max Pain", "--", "Pending live data")
        ]),
        section("CALL / PUT DATA", [
            ft.Text(
                "Strike       CE OI       PE OI       Change",
                color=GOLD, size=13
            ),
            *[
                ft.Container(
                    content=ft.Text(
                        f"{strike}       --       --       --",
                        color=WHITE, size=13
                    ),
                    bgcolor=CARD, padding=14, border_radius=8
                )
                for strike in ["ATM - 200", "ATM - 100", "ATM",
                               "ATM + 100", "ATM + 200"]
            ],
            ft.Text(
                "Live options-chain data is not connected yet.",
                color=MUTED, size=12
            )
        ])
    ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

    # PAGE 3: CHART ANALYTICS
    chart_page = ft.Column([
        heading("CHART ANALYTICS", "TECHNICAL INDICATORS"),
        ft.Row([
            ft.OutlinedButton("1m"),
            ft.OutlinedButton("5m"),
            ft.OutlinedButton("15m"),
            ft.OutlinedButton("1H"),
            ft.OutlinedButton("1D")
        ], wrap=True),
        panel("PRICE CHART", "Chart pending",
              "Connect a chart data provider"),
        section("INDICATORS", [
            ft.Row([
                panel("EMA 9", "--"),
                panel("EMA 21", "--")
            ]),
            ft.Row([
                panel("RSI", "--"),
                panel("VWAP", "--")
            ]),
            panel("Volume", "--", "Pending market data")
        ])
    ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

    # PAGE 4: AUTO BOT
    auto_page = ft.Column([
        heading("AUTO BOT", "TRADING STRATEGY"),
        panel("BOT STATUS", "STOPPED",
              "Auto trading is disabled by default"),
        ft.Switch(
            label="Enable Auto Bot",
            value=False,
            active_color=GOLD
        ),
        section("TRADE SETTINGS", [
            ft.TextField(
                label="Target (Points)",
                value="30",
                keyboard_type=ft.KeyboardType.NUMBER
            ),
            ft.TextField(
                label="Stop Loss (Points)",
                value="15",
                keyboard_type=ft.KeyboardType.NUMBER
            ),
            ft.TextField(
                label="Entry Threshold",
                value="70",
                keyboard_type=ft.KeyboardType.NUMBER
            ),
            panel("Today's MTM", "₹0",
                  "Demo display only")
        ]),
        ft.Text(
            "Broker connection and live order execution are not "
            "implemented. Do not use this for live trading yet.",
            color=MUTED, size=12
        )
    ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

    # PAGE 5: SETTINGS
    settings_page = ft.Column([
        heading("SETTINGS / API", "BROKER CONFIGURATION"),
        section("BROKER", [
            ft.Dropdown(
                label="Select Broker",
                options=[
                    ft.dropdown.Option("Angel One"),
                    ft.dropdown.Option("Zerodha"),
                    ft.dropdown.Option("Dhan"),
                    ft.dropdown.Option("Upstox")
                ]
            ),
            ft.TextField(label="Client ID"),
            ft.TextField(label="API Key", password=True),
            ft.TextField(label="API Secret", password=True),
            ft.TextField(label="Access Token", password=True),
            ft.ElevatedButton(
                "Save Settings",
                bgcolor=GOLD,
                color=BG
            )
        ]),
        section("WATCHLIST", [
            panel("NIFTY 50", "Not connected"),
            panel("BANK NIFTY", "Not connected")
        ]),
        ft.Text(
            "Credentials are not saved or sent anywhere in this "
            "starter version. Broker integration is still pending.",
            color=MUTED, size=12
        )
    ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

    pages = [
        dashboard, oi_page, chart_page, auto_page, settings_page
    ]

    body = ft.Container(
        content=dashboard,
        expand=True,
        padding=16
    )

    def change_page(e):
        index = e.control.selected_index
        body.content = pages[index]
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=change_page,
        bgcolor=CARD,
        indicator_color="#59451D",
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.icons.HOME_OUTLINED,
                selected_icon=ft.icons.HOME,
                label="Home"
            ),
            ft.NavigationBarDestination(
                icon=ft.icons.LIST_ALT,
                label="OI Chain"
            ),
            ft.NavigationBarDestination(
                icon=ft.icons.SHOW_CHART,
                label="Chart"
            ),
            ft.NavigationBarDestination(
                icon=ft.icons.SMART_TOY,
                label="Auto Bot"
            ),
            ft.NavigationBarDestination(
                icon=ft.icons.SETTINGS,
                label="Settings"
            )
        ]
    )

    page.add(body)


ft.app(target=main)
