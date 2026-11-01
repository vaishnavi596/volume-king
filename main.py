import flet as ft
import random

def main(page: ft.Page):
    page.title = "Bot King Trade"
    page.bgcolor = "#121212"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # --- GLOBAL DATA ---
    pnl = ft.Text("P&L: + ₹1,250.50 (+2.4%)", size=18, color="#4CAF50", weight=ft.FontWeight.BOLD)
    position_txt = ft.Text("Position: BANKNIFTY 54500 CE x2 | LTP 92.5", size=14, color="white")
    trend_txt = ft.Text("Trend: 70% Bullish 🟢 | Bearish 30%", size=14, color="#4CAF50")
    vol_txt = ft.Text("Wait - Volume 78%", size=24, weight=ft.FontWeight.BOLD, color="#FFA500")
    
    # --- DASHBOARD WITH CHART ---
    chart = ft.Container(
        height=180,
        bgcolor="#1E1E1E",
        border_radius=10,
        padding=10,
        content=ft.Column([
            ft.Text("NIFTY Live Chart (Candlestick)", color="grey", size=12),
            ft.Text("📈 23050 -> 23100 -> 23080 -> 23120", color="#4CAF50", size=20),
            ft.Text("Volume Bars: ||||| |||||| |||", color="#2196F3")
        ])
    )

    def get_signal(e):
        v = random.randint(65, 98)
        bull = random.randint(50, 95)
        if v >= 80:
            vol_txt.value = f"BUY Signal - Volume {v}% - GO!"
            vol_txt.color = "#4CAF50"
        else:
            vol_txt.value = f"Wait - Volume {v}%"
            vol_txt.color = "#FFA500"
        trend_txt.value = f"Trend: {bull}% Bullish {'🟢' if bull>60 else '🔴'} | Bearish {100-bull}%"
        pnl.value = f"P&L: {'+' if random.random()>0.4 else '-'} ₹{random.uniform(100,2000):.2f}"
        page.update()

    dashboard = ft.Column([
        ft.Text("Bot King Trade", size=28, weight=ft.FontWeight.BOLD, color="white"),
        ft.Text("70% Volume 80-100 Bot Ready", size=13, color="#4CAF50"),
        chart,
        ft.Container(bgcolor="#1E1E1E", border_radius=10, padding=12, content=ft.Column([
            position_txt,
            pnl,
            trend_txt,
            vol_txt,
        ], spacing=8)),
        ft.Row([
            ft.ElevatedButton("Refresh Live Price", bgcolor="#4CAF50", color="white", expand=True),
            ft.ElevatedButton("Get Volume Signal", bgcolor="#2196F3", color="white", expand=True, on_click=get_signal),
        ]),
        ft.Text("My Trades: Today 3 Trade | Win 2 | Loss 1", color="grey", size=12)
    ], spacing=12, scroll=ft.ScrollMode.AUTO)

    # --- SETTINGS - FULL ---
    settings = ft.Column([
        ft.Text("Settings - API & Logic", size=24, weight=ft.FontWeight.BOLD),
        ft.TextField(label="Angel One API Key", border_color="#333"),
        ft.TextField(label="Client ID", border_color="#333"),
        ft.TextField(label="TOTP Secret", border_color="#333"),
        ft.Divider(color="#333"),
        ft.Text("Telegram Settings", color="#4CAF50", weight=ft.FontWeight.BOLD),
        ft.TextField(label="Telegram Bot Token", border_color="#333"),
        ft.TextField(label="Telegram Channel ID", border_color="#333"),
        ft.TextField(label="Custom Signal Webhook URL", border_color="#333"),
        ft.Divider(color="#333"),
        ft.Text("Trading Logic", color="#4CAF50", weight=ft.FontWeight.BOLD),
        ft.Row([ft.TextField(label="Min Premium", value="80", width=150), ft.TextField(label="Max Premium", value="100", width=150)]),
        ft.Row([ft.TextField(label="Stop Loss %", value="20", width=150), ft.TextField(label="Target %", value="40", width=150)]),
        ft.TextField(label="Volume Logic (e.g. >=70%)", value="Volume >=70%", border_color="#333"),
        ft.Switch(label="Auto Trading ON/OFF", value=False),
        ft.Switch(label="Telegram Signal ON/OFF", value=True),
        ft.ElevatedButton("Save All Settings", bgcolor="#4CAF50", color="white", width=400)
    ], spacing=10, scroll=ft.ScrollMode.AUTO)

    # --- INDICATOR - FULL EDIT ---
    stocks = {"NIFTY": "23053 | Vol 72%", "BANKNIFTY": "54686 | Vol 85% BUY", "SENSEX": "74459 | Vol 68%", "TCS": "3450 | Vol 81% BUY"}
    stock_list_col = ft.Column()
    def refresh_list():
        stock_list_col.controls = [ft.Container(bgcolor="#1E1E1E", padding=10, border_radius=8, content=ft.Row([ft.Text(f"{k}: {v}", color="white", expand=True), ft.IconButton(ft.Icons.EDIT, icon_size=18), ft.IconButton(ft.Icons.DELETE, icon_size=18)])) for k,v in stocks.items()]
        page.update()
    refresh_list()
    
    indicator = ft.Column([
        ft.Text("Indicators - All Stocks", size=24, weight=ft.FontWeight.BOLD),
        ft.Dropdown(label="Stock/Option Select", value="BANKNIFTY", options=[ft.dropdown.Option(k) for k in stocks]),
        ft.Row([ft.TextField(label="Add/Edit Stock", expand=True, border_color="#333"), ft.ElevatedButton("ADD", bgcolor="#2196F3", color="white"), ft.ElevatedButton("EDIT", bgcolor="#FFA500", color="white")]),
        ft.Text("Add Custom Indicator:", color="#4CAF50"),
        ft.Row([ft.TextField(label="Indicator Name e.g. RSI, MACD", expand=True), ft.ElevatedButton("Add Indicator")]),
        stock_list_col
    ], spacing=10, scroll=ft.ScrollMode.AUTO)

    # --- BOT - FULL ---
    bot = ft.Column([
        ft.Text("Bot - Auto / Manual", size=24, weight=ft.FontWeight.BOLD),
        ft.Container(bgcolor="#1E1E1E", padding=15, border_radius=10, content=ft.Column([
            ft.Text("Bot Started - Auto Trading...", color="white"),
            pnl, trend_txt, position_txt
        ])),
        ft.ElevatedButton("START AUTO BOT", bgcolor="#4CAF50", color="white", width=400, height=50),
        ft.ElevatedButton("STOP BOT / SELL ALL", bgcolor="#FF5252", color="white", width=400, height=50),
        ft.Row([ft.ElevatedButton("Manual BUY", bgcolor="#4CAF50", color="white", expand=True), ft.ElevatedButton("Manual SELL", bgcolor="#FF5252", color="white", expand=True)]),
        ft.Text("Logic: Premium 80-100 + Vol >=70% + Bearish = Auto BUY + SL/Target", color="grey", size=12),
        ft.TextField(label="Add Custom Bot Logic", border_color="#333"),
        ft.ElevatedButton("Save Bot Logic")
    ], spacing=12, scroll=ft.ScrollMode.AUTO)

    content = ft.Container(content=dashboard, expand=True, padding=15)
    def nav_change(e):
        idx = e.control.selected_index
        content.content = [dashboard, settings, indicator, bot][idx]
        page.update()

    page.navigation_bar = ft.NavigationBar(bgcolor="#1E1E1E", on_change=nav_change, selected_index=0, destinations=[
        ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Dashboard"),
        ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings"),
        ft.NavigationBarDestination(icon=ft.Icons.CHECK, label="Indicator"),
        ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY, label="Bot"),
    ])
    page.add(content)

ft.app(target=main)
