import flet as ft
import random
import threading
import time
try:
    from SmartApi import SmartConnect
    import pyotp
except:
    pass

def main(page: ft.Page):
    page.title = "Bot King Trade - Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 15

    # --- NEW FEATURE 1: INDICATOR SELECTOR ---
    selected_symbol = ft.Text("BankNifty", size=20, weight=ft.FontWeight.BOLD)
    
    symbol_dropdown = ft.Dropdown(
        label="Indicator / Symbol",
        value="BankNifty",
        options=[
            ft.dropdown.Option("Nifty"),
            ft.dropdown.Option("BankNifty"),
            ft.dropdown.Option("Sensex"),
            ft.dropdown.Option("TCS"),
            ft.dropdown.Option("HDFC Bank"),
            ft.dropdown.Option("RELIANCE"),
            ft.dropdown.Option("INFY"),
        ],
        width=300,
        on_change=lambda e: on_symbol_change(e)
    )

    def on_symbol_change(e):
        selected_symbol.value = f"{e.control.value}"
        page.update()
        # Yaha Angel API se live price fetch kar sakte ho

    # --- LIVE DATA ---
    live_price_txt = ft.Text("₹ 44,892.35 +1.24%", size=28, weight=ft.FontWeight.BOLD)
    nifty_txt = ft.Text("Nifty: Loading...", size=14)
    bank_txt = ft.Text("BankNifty: Loading...", size=14)
    sensex_txt = ft.Text("Sensex: Loading...", size=14)
    
    # --- NEW FEATURE 2: BULLISH/BEARISH METER ---
    bullish_pct = 68
    bearish_pct = 32
    
    market_sentiment_title = ft.Text("Market Sentiment", size=14, color="grey")
    bullish_txt = ft.Text(f"Bullish {bullish_pct}%", color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD)
    bearish_txt = ft.Text(f"Bearish {bearish_pct}%", color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD)
    
    sentiment_bar = ft.Row([
        ft.Container(width=200 * (bullish_pct/100), height=12, bgcolor=ft.Colors.GREEN, border_radius=5),
        ft.Container(width=200 * (bearish_pct/100), height=12, bgcolor=ft.Colors.RED_400, border_radius=5),
    ], spacing=0)

    # --- NEW FEATURE 3: TOP PREMIUMS 80-100 ---
    premiums_column = ft.Column([])
    bot_list = [] # Add to Bot wale yaha save honge

    def buy_premium(symbol):
        page.snack_bar = ft.SnackBar(ft.Text(f"BUY Order Placed: {symbol}"))
        page.snack_bar.open = True
        page.update()

    def add_to_bot(symbol):
        bot_list.append(symbol)
        page.snack_bar = ft.SnackBar(ft.Text(f"Added to Bot: {symbol} | Total: {len(bot_list)}"))
        page.snack_bar.open = True
        page.update()

    def refresh_premiums(e=None):
        # Yaha Angel API se Option Chain aayega - abhi demo data
        demo_premiums = [
            {"name": f"{symbol_dropdown.value} 54600 CE", "price": 92},
            {"name": f"{symbol_dropdown.value} 54700 CE", "price": 85},
            {"name": f"{symbol_dropdown.value} 54800 CE", "price": 81},
        ]
        premiums_column.controls.clear()
        for p in demo_premiums:
            # Filter 80-100
            if 80 <= p["price"] <= 100:
                premiums_column.controls.append(
                    ft.Card(content=ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(p["name"], weight=ft.FontWeight.BOLD, size=14),
                                ft.Text(f"@ ₹{p['price']}", color=ft.Colors.GREEN_400)
                            ], expand=True),
                            ft.ElevatedButton("Buy", bgcolor=ft.Colors.GREEN_600, color="white", 
                                              on_click=lambda _, s=p["name"]: buy_premium(s)),
                            ft.OutlinedButton("Add to Bot", 
                                              on_click=lambda _, s=p["name"]: add_to_bot(s)),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10
                    ))
                )
        page.update()

    # --- INPUTS ---
    capital_input = ft.TextField(label="Capital", value="100000", width=160)
    risk_input = ft.TextField(label="Risk %", value="2", width=100)
    api_key = ft.TextField(label="Angel One API Key", password=True)
    client_id = ft.TextField(label="Angel Client ID")
    mpin_input = ft.TextField(label="Angel MPIN", password=True)
    totp_input = ft.TextField(label="Angel TOTP Secret", password=True)
    telegram_token = ft.TextField(label="Telegram Bot Token", password=True)
    telegram_chat = ft.TextField(label="Telegram Chat ID")
    paper_mode = ft.Switch(label="Paper Trading Mode (Safe Test)", value=True)
    auto_trade_switch = ft.Switch(label="Auto Trading ON", value=False)

    # --- CHART DATA ---
    chart = ft.BarChart(
        bar_groups=[
            ft.BarChartGroup(x=i, bar_rods=[ft.BarChartRod(from_y=0, to_y=random.randint(50, 95), width=10, color=ft.Colors.GREEN if random.randint(70,100)>=80 else ft.Colors.RED)])
            for i in range(12)
        ],
        border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY)),
        left_axis=ft.ChartAxis(labels_size=40),
        bottom_axis=ft.ChartAxis(labels=[ft.ChartAxisLabel(value=i, label=ft.Text(f"{9+i//2}:30", size=10)) for i in range(0,12,2)]),
        horizontal_grid_lines=ft.ChartGridLines(interval=20, color=ft.Colors.GREY_800),
        expand=True,
        height=200
    )

    # --- ANGEL LOGIN ---
    def angel_login(e=None):
        try:
            if not api_key.value or not client_id.value or not mpin_input.value or not totp_input.value:
                page.snack_bar = ft.SnackBar(ft.Text("Pehle Angel ke 4 box bharo!"))
                page.snack_bar.open = True
                page.update()
                return
            totp = pyotp.TOTP(totp_input.value).now()
            obj = SmartConnect(api_key=api_key.value)
            data = obj.generateSession(client_id.value, mpin_input.value, totp)
            page.snack_bar = ft.SnackBar(ft.Text(f"Angel Login Success! {client_id.value}"))
            page.snack_bar.open = True
            refresh_premiums() # Login ke baad premium refresh karo
            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Login Fail: {ex}"))
            page.snack_bar.open = True
            page.update()

    login_btn = ft.ElevatedButton("Angel One Login Test", icon=ft.Icons.LOGIN, on_click=angel_login, bgcolor="green", color="white")

    # --- LAYOUT ---
    page.add(
        ft.Column([
            ft.Text("Bot King Trade", size=22, weight=ft.FontWeight.BOLD),
            symbol_dropdown,
            ft.Row([ft.Text("Live Price: ", size=16), selected_symbol]),
            live_price_txt,
            ft.Divider(),
            market_sentiment_title,
            ft.Row([bullish_txt, bearish_txt], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            sentiment_bar,
            ft.Divider(),
            ft.Row([
                ft.Text(f"Top Premiums ₹80-100", size=16, weight=ft.FontWeight.BOLD),
                ft.IconButton(icon=ft.Icons.REFRESH, on_click=refresh_premiums)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            premiums_column,
            ft.Divider(),
            ft.Text("Volume Chart - Today 9:15 to 3:30", size=12, color="grey"),
            chart,
            ft.Divider(),
            ft.Text("Settings", weight=ft.FontWeight.BOLD),
            ft.Row([capital_input, risk_input]),
            api_key, client_id, mpin_input, totp_input, login_btn,
            ft.Divider(),
            telegram_token, telegram_chat,
            paper_mode, auto_trade_switch,
            nifty_txt, bank_txt, sensex_txt,
        ], scroll=ft.ScrollMode.AUTO)
    )
    refresh_premiums()

ft.app(target=main)
