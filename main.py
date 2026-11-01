import flet as ft

def main(page: ft.Page):
    page.title = "Bot King Trade"
    page.bgcolor = "#121212"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # --- GLOBAL SETTINGS (ye Settings page se change hoga) ---
    api_key = ft.TextField(label="Angel One API Key", password=True, color="white")
    client_id = ft.TextField(label="Client ID", color="white")
    premium_min = ft.TextField(label="Min Premium (Rs)", value="80", color="white")
    premium_max = ft.TextField(label="Max Premium (Rs)", value="100", color="white")
    stop_loss = ft.TextField(label="Stop Loss %", value="20", color="white")
    target = ft.TextField(label="Target %", value="40", color="white")
    auto_mode = ft.Switch(label="Auto Trading ON/OFF", value=False)

    stock_list = ["NIFTY", "BANKNIFTY", "SENSEX", "TCS", "HDFC", "ICICI", "RELIANCE", "INFY"]
    selected_stock = ft.Dropdown(label="Stock/Option Select", options=[ft.dropdown.Option(s) for s in stock_list], value="BANKNIFTY", color="white")
    custom_stock = ft.TextField(label="Add Custom Stock (e.g. SBIN)", color="white")

    nifty_txt = ft.Text("Nifty: 23053.10", size=18, color="white")
    vol_txt = ft.Text("Wait - Volume 78%", size=22, weight=ft.FontWeight.BOLD, color="#FFA500")
    bot_status = ft.Text("Bot Status: Manual Mode", color="white")

    # --- FUNCTIONS ---
    def add_stock(e):
        if custom_stock.value:
            stock_list.append(custom_stock.value.upper())
            selected_stock.options.append(ft.dropdown.Option(custom_stock.value.upper()))
            page.update()

    def refresh_price(e):
        import random
        nifty_txt.value = f"{selected_stock.value}: {random.uniform(80,100):.2f} Premium (Live)"
        page.update()

    def get_signal(e):
        import random
        v = random.randint(65, 99)
        if v >= 70 and 80 <= float(nifty_txt.value.split(":")[1].split()[0]) <= 100 if ":" in nifty_txt.value else True:
            vol_txt.value = f"BUY Signal - Volume {v}% - GO! Premium in Range"
            vol_txt.color = "#4CAF50"
            if auto_mode.value:
                bot_status.value = f"AUTO BOT: BUY {selected_stock.value} @ {nifty_txt.value} | SL: {stop_loss.value}% | Target: {target.value}%"
                # Yaha Angel One API Call Lagega: smartApi.placeOrder(...)
        else:
            vol_txt.value = f"Wait - Volume {v}%"
            vol_txt.color = "#FFA500"
        page.update()

    # --- PAGES ---
    dashboard_page = ft.Column([
        ft.Text("Bot King Trade", size=26, weight=ft.FontWeight.BOLD, color="white"),
        ft.Text("70% Volume 80-100 Bot Ready", size=13, color="#4CAF50"),
        ft.Divider(color="#333"),
        nifty_txt, vol_txt,
        ft.ElevatedButton("Refresh Live Price", bgcolor="#4CAF50", color="white", on_click=refresh_price),
        ft.ElevatedButton("Get Volume Signal", width=340, bgcolor="#2196F3", color="white", on_click=get_signal),
        bot_status
    ], spacing=12)

    settings_page = ft.Column([
        ft.Text("Settings - API & Logic", size=22, weight=ft.FontWeight.BOLD, color="white"),
        api_key, client_id, 
        ft.Row([premium_min, premium_max]),
        ft.Row([stop_loss, target]),
        auto_mode,
        ft.Text("Angel One SmartAPI free hai - apko angelone.in se API Key lena hai", size=11, color="grey")
    ], spacing=12, scroll=ft.ScrollMode.AUTO)

    indicator_page = ft.Column([
        ft.Text("Indicators - All Stocks", size=22, weight=ft.FontWeight.BOLD, color="white"),
        selected_stock,
        ft.Row([custom_stock, ft.IconButton(ft.Icons.ADD, on_click=add_stock)]),
        ft.Text("NIFTY: 23053.10  | Vol 72%\nBANKNIFTY: 54686.95 | Vol 85% BUY\nSENSEX: 74459.53 | Vol 68%\nTCS: 3450.20 | Vol 81% BUY\nHDFC: 1650.10 | Vol 78% WAIT", color="white", size=14)
    ], spacing=10)

    bot_page = ft.Column([
        ft.Text("Bot - Auto / Manual", size=22, weight=ft.FontWeight.BOLD, color="white"),
        bot_status,
        ft.ElevatedButton("START AUTO BOT", bgcolor="#4CAF50", color="white", on_click=lambda e: setattr(bot_status, 'value', 'Bot Started - Auto Trading...') or page.update()),
        ft.ElevatedButton("STOP BOT / SELL ALL", bgcolor="#FF5252", color="white"),
        ft.Text("Logic: Premium 80-100 Rs + Volume >=70% + Bearish Market = Auto BUY + Auto SL/Target", color="grey", size=12)
    ], spacing=15)

    # --- NAVIGATION LOGIC ---
    content_area = ft.Container(content=dashboard_page, expand=True, padding=20)

    def nav_change(e):
        idx = e.control.selected_index
        if idx == 0: content_area.content = dashboard_page
        elif idx == 1: content_area.content = settings_page
        elif idx == 2: content_area.content = indicator_page
        elif idx == 3: content_area.content = bot_page
        page.update()

    nav = ft.NavigationBar(
        bgcolor="#1E1E1E",
        on_change=nav_change,
        selected_index=0,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Dashboard"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings"),
            ft.NavigationBarDestination(icon=ft.Icons.CHECK, label="Indicator"),
            ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY, label="Bot"),
        ]
    )

    page.add(ft.Column([content_area, nav], expand=True, spacing=0))

ft.app(target=main)
