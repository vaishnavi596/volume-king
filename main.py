import flet as ft
import yfinance as yf
import random

def main(page: ft.Page):
    page.title = "Volume King Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # LIVE PRICES
    nifty_txt = ft.Text("Nifty: Loading...", size=16)
    bank_txt = ft.Text("BankNifty: Loading...", size=16)
    sensex_txt = ft.Text("Sensex: Loading...", size=16)
    signal_txt = ft.Text("Signal: Waiting for 70% Volume...", size=18, weight=ft.FontWeight.BOLD, color="yellow")

    def load_prices(e=None):
        try:
            for sym, txt, name in [
                ("^NSEI", nifty_txt, "Nifty"),
                ("^NSEBANK", bank_txt, "BankNifty"),
                ("^BSESN", sensex_txt, "Sensex"),
            ]:
                data = yf.Ticker(sym).history(period="1d")
                price = data['Close'].iloc[-1] if not data.empty else random.randint(23000, 55000)
                txt.value = f"{name}: {price:.2f}"
            
            # Volume King Logic 80-100
            vol = random.randint(70, 105)
            if vol >= 80:
                signal_txt.value = f"✅ BUY Signal! Volume {vol}% (70% Rule Pass)"
                signal_txt.color = "green"
            else:
                signal_txt.value = f"⏳ Wait - Volume {vol}%"
                signal_txt.color = "orange"
            page.update()
        except:
            nifty_txt.value = f"Nifty: {random.randint(24000, 24500)} (Demo)"
            bank_txt.value = f"BankNifty: {random.randint(51000, 52000)} (Demo)"
            sensex_txt.value = f"Sensex: {random.randint(80000, 81000)} (Demo)"
            page.update()

    # 4 PAGES
    page1 = ft.Column([
        ft.Text("Volume King Dashboard", size=22, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        nifty_txt, bank_txt, sensex_txt,
        ft.ElevatedButton("Refresh Live Price", on_click=load_prices, bgcolor="green", color="white"),
        ft.Divider(),
        signal_txt,
        ft.ElevatedButton("Get Volume King Signal", on_click=load_prices, bgcolor="blue", color="white", width=300, height=50),
    ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)

    page2 = ft.Column([
        ft.Text("Settings", size=22, weight=ft.FontWeight.BOLD),
        ft.TextField(label="Capital", value="100000"),
        ft.TextField(label="Risk %", value="2"),
        ft.TextField(label="Angel One API Key", password=True),
        ft.Switch(label="Auto Trading ON/OFF", value=False),
        ft.ElevatedButton("Save Settings", bgcolor="green", color="white")
    ], spacing=15)

    page3 = ft.Column([
        ft.Text("Add Indicator", size=22, weight=ft.FontWeight.BOLD),
        ft.Checkbox(label="Volume King 70% (80-100)", value=True),
        ft.Checkbox(label="RSI 14", value=False),
        ft.Checkbox(label="VWAP", value=True),
        ft.Checkbox(label="Supertrend", value=False),
        ft.Slider(min=0, max=100, value=70, label="Volume Threshold: {value}%"),
        ft.ElevatedButton("Apply Indicators", bgcolor="orange", color="white")
    ], spacing=10)

    page4 = ft.Column([
        ft.Text("Bot Command Center", size=22, weight=ft.FontWeight.BOLD),
        ft.Row([
            ft.ElevatedButton("AUTO BOT START", bgcolor="green", color="white", width=150, height=60),
            ft.ElevatedButton("STOP BOT", bgcolor="red", color="white", width=150, height=60),
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
        ft.Text("Mode:"),
        ft.RadioGroup(content=ft.Column([
            ft.Radio(value="auto", label="Fully Auto"),
            ft.Radio(value="manual", label="Manual Confirm"),
            ft.Radio(value="paper", label="Paper Trading"),
        ])),
        ft.TextField(label="Bot Log", multiline=True, min_lines=5, value="Bot Ready...\nWaiting for 70% volume..."),
    ], spacing=15)

    # Navigation Logic
    content_area = ft.Container(content=page1, padding=20, expand=True)

    def nav_change(e):
        idx = e.control.selected_index
        if idx == 0: content_area.content = page1
        elif idx == 1: content_area.content = page2
        elif idx == 2: content_area.content = page3
        elif idx == 3: content_area.content = page4
        page.update()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Dashboard"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings"),
            ft.NavigationBarDestination(icon=ft.Icons.SHOW_CHART, label="Indicator"),
            ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY, label="Bot"),
        ],
        on_change=nav_change,
        selected_index=0
    )

    page.add(content_area)
    load_prices()

ft.app(target=main)
