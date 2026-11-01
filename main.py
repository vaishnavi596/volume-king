import flet as ft
import random

def main(page: ft.Page):
    page.title = "Bot King Trade"
    page.bgcolor = "#121212"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.vertical_alignment = ft.MainAxisAlignment.START

    # --- GLOBAL DATA ---
    stocks_data = {
        "NIFTY": "23053 | Vol 72%",
        "BANKNIFTY": "54686 | Vol 85% BUY",
        "SENSEX": "74459 | Vol 68%",
        "TCS": "3450 | Vol 81% BUY",
    }

    # --- COMMON CONTROLS ---
    pnl_txt = ft.Text("P&L: + ₹1,250.50 (+2.4%)", size=18, color="#4CAF50", weight=ft.FontWeight.BOLD)
    pos_txt = ft.Text("Position: BANKNIFTY 54500 CE x2 | LTP 92.5", size=14, color="white")
    trend_txt = ft.Text("Trend: 70% Bullish 🟢 | Bearish 30%", size=14, color="#4CAF50")
    vol_txt = ft.Text("Wait - Volume 78%", size=26, weight=ft.FontWeight.BOLD, color="#FFA500")

    # --- FUNCTIONS ---
    def get_signal(e):
        v = random.randint(65, 98)
        bull = random.randint(45, 95)
        if v >= 80:
            vol_txt.value = f"BUY Signal - Volume {v}% - GO!"
            vol_txt.color = "#4CAF50"
        else:
            vol_txt.value = f"Wait - Volume {v}%"
            vol_txt.color = "#FFA500"
        trend_txt.value = f"Trend: {bull}% Bullish {'🟢' if bull>60 else '🔴'} | Bearish {100-bull}%"
        pnl_txt.value = f"P&L: {'+' if random.random()>0.5 else '-'} ₹{random.uniform(100,2500):.2f} ({random.uniform(0.5,4.5):.1f}%)"
        page.update()

    def refresh_price(e):
        vol_txt.value = "Wait - Volume 78%"
        vol_txt.color = "#FFA500"
        page.update()

    # --- DASHBOARD PAGE ---
    chart_box = ft.Container(
        bgcolor="#1E1E1E",
        border_radius=12,
        padding=15,
        content=ft.Column([
            ft.Text("NIFTY Live Chart (Candlestick)", size=12, color="#888888"),
            ft.Text("📈 23050 -> 23100 -> 23080 -> 23120", size=20, color="#4CAF50"),
            ft.Text("Volume Bars: ||||| |||||| |||", size=14, color="#2196F3"),
        ], spacing=8)
    )

    dashboard = ft.Column([
        ft.Text("Bot King Trade", size=28, weight=ft.FontWeight.BOLD, color="white"),
        ft.Text("70% Volume 80-100 Bot Ready", size=14, color="#4CAF50"),
        chart_box,
        ft.Container(bgcolor="#1E1E1E", border_radius=12, padding=15, content=ft.Column([pos_txt, pnl_txt, trend_txt, vol_txt], spacing=10)),
        ft.Row([
            ft.ElevatedButton("Refresh Live Price", bgcolor="#4CAF50", color="white", expand=True, on_click=refresh_price),
            ft.ElevatedButton("Get Volume Signal", bgcolor="#2196F3", color="white", expand=True, on_click=get_signal),
        ], spacing=10),
        ft.Text("My Trades: Today 3 Trade | Win 2 | Loss 1", size=12, color="grey")
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

    # --- SETTINGS PAGE ---
    settings = ft.Column([
        ft.Text("Settings - API & Logic", size=26, weight=ft.FontWeight.BOLD, color="white"),
        ft.TextField(label="Angel One API Key", border_color="#333333"),
        ft.TextField(label="Client ID", border_color="#333333"),
        ft.TextField(label="TOTP Secret", border_color="#333333"),
        ft.Divider(color="#333333"),
        ft.Text("Telegram Settings", size=16, color="#4CAF50", weight=ft.FontWeight.BOLD),
        ft.TextField(label="Telegram Bot Token", border_color="#333333"),
        ft.TextField(label="Telegram Channel ID", border_color="#333333"),
        ft.TextField(label="Custom Signal Webhook URL", border_color="#333333"),
        ft.Divider(color="#333333"),
        ft.Text("Trading Logic", size=16, color="#4CAF50", weight=ft.FontWeight.BOLD),
        ft.Row([ft.TextField(label="Min Premium", value="80", width=170, border_color="#333333"), ft.TextField(label="Max Premium", value="100", width=170, border_color="#333333")]),
        ft.Row([ft.TextField(label="Stop Loss %", value="20", width=170, border_color="#333333"), ft.TextField(label="Target %", value="40", width=170, border_color="#333333")]),
        ft.Switch(label="Auto Trading ON/OFF", value=False),
        ft.Switch(label="Telegram Signal ON/OFF", value=True),
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

    # --- INDICATOR PAGE ---
    stock_dropdown = ft.Dropdown(label="Stock/Option Select", value="BANKNIFTY", border_color="#333333", options=[ft.dropdown.Option(k) for k in stocks_data.keys()])
    custom_stock_field = ft.TextField(label="Add Custom Stock", expand=True, border_color="#333333")
    indicator_name_field = ft.TextField(label="Indicator Name e.g. RSI, MACD", expand=True, border_color="#333333")
    stock_list_column = ft.Column(spacing=8)

    def rebuild_list():
        stock_list_column.controls.clear()
        for k, v in stocks_data.items():
            stock_list_column.controls.append(
                ft.Container(bgcolor="#1E1E1E", border_radius=10, padding=12, content=ft.Row([
                    ft.Text(f"{k}: {v}", color="white", expand=True, size=16),
                    ft.IconButton(icon=ft.Icons.EDIT, icon_color="#90CAF9", icon_size=20),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color="#90CAF9", icon_size=20, data=k, on_click=lambda e: delete_stock(e.control.data)),
                ]))
            )
        stock_dropdown.options = [ft.dropdown.Option(k) for k in stocks_data.keys()]
        page.update()

    def add_stock(e):
        name = custom_stock_field.value.strip().upper()
        if name != "":
            stocks_data[name] = f"{random.randint(300,60000)} | Vol {random.randint(60,90)}% WAIT"
            custom_stock_field.value = ""
            rebuild_list()

    def delete_stock(name):
        if name in stocks_data:
            del stocks_data[name]
            rebuild_list()

    indicator = ft.Column([
        ft.Text("Indicators - All Stocks", size=24, weight=ft.FontWeight.BOLD),
        stock_dropdown,
        ft.Row([ft.Text("Add/Edit Stock", size=16, color="white", expand=True), ft.ElevatedButton("ADD", bgcolor="#2196F3", color="white", on_click=add_stock), ft.ElevatedButton("EDIT", bgcolor="#FFA500", color="white")]),
        ft.Text("Add Custom Indicator:", size=14, color="#4CAF50"),
        ft.Row([indicator_name_field, ft.ElevatedButton("Add Indicator")]),
        stock_list_column
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
    rebuild_list()

    # --- BOT PAGE ---
    bot = ft.Column([
        ft.Text("Bot - Auto / Manual", size=26, weight=ft.FontWeight.BOLD),
        ft.Container(bgcolor="#1E1E1E", border_radius=12, padding=15, content=ft.Column([ft.Text("Bot Started - Auto Trading...", color="white"), pnl_txt, trend_txt, pos_txt], spacing=8)),
        ft.ElevatedButton("START AUTO BOT", bgcolor="#4CAF50", color="white", width=400, height=55),
        ft.ElevatedButton("STOP BOT / SELL ALL", bgcolor="#FF5252", color="white", width=400, height=55),
        ft.Row([ft.ElevatedButton("Manual BUY", bgcolor="#4CAF50", color="white", expand=True), ft.ElevatedButton("Manual SELL", bgcolor="#FF5252", color="white", expand=True)]),
        ft.Text("Logic: Premium 80-100 + Vol >=70% + Bearish = Auto BUY + SL/Target", size=12, color="grey"),
        ft.TextField(label="Add Custom Bot Logic", border_color="#333333"),
        ft.ElevatedButton("Save Bot Logic"),
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

    # --- NAVIGATION ---
    content_area = ft.Container(content=dashboard, expand=True, padding=15)

    def nav_change(e):
        idx = e.control.selected_index
        if idx == 0: content_area.content = dashboard
        elif idx == 1: content_area.content = settings
        elif idx == 2: content_area.content = indicator
        elif idx == 3: content_area.content = bot
        page.update()

    page.navigation_bar = ft.NavigationBar(
        bgcolor="#1E1E1E",
        selected_index=0,
        on_change=nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Dashboard"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings"),
            ft.NavigationBarDestination(icon=ft.Icons.CHECK_CIRCLE, label="Indicator"),
            ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY, label="Bot"),
        ]
    )
    page.add(content_area)

ft.app(target=main)
