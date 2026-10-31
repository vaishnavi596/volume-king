import flet as ft
import random

def main(page: ft.Page):
    page.title = "Bot King Trade"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # --- GLOBAL STATE ---
    bot_list = []
    
    # --- INPUTS (Settings ke liye) ---
    api_key = ft.TextField(label="Angel API Key", password=True)
    client_id = ft.TextField(label="Client ID")
    mpin_input = ft.TextField(label="MPIN", password=True)
    totp_input = ft.TextField(label="TOTP Secret", password=True)
    capital_input = ft.TextField(label="Capital", value="100000", width=160)
    risk_input = ft.TextField(label="Risk %", value="2", width=100)
    auto_switch = ft.Switch(label="Auto Trading ON", value=False)
    mode_dropdown = ft.Dropdown(label="Bot Mode", value="Auto", options=[ft.dropdown.Option("Auto"), ft.dropdown.Option("Manual")], width=200)

    # --- PAGE 1: FRONT ---
    selected_symbol = ft.Text("BankNifty", size=20, weight=ft.FontWeight.BOLD)
    symbol_dropdown = ft.Dropdown(
        label="Indicator / Symbol", value="BankNifty",
        options=[ft.dropdown.Option("Nifty"), ft.dropdown.Option("BankNifty"), ft.dropdown.Option("Sensex"), ft.dropdown.Option("TCS"), ft.dropdown.Option("RELIANCE")],
        width=300
    )
    live_price = ft.Text("₹ 44,892.35 +1.24%", size=28, weight=ft.FontWeight.BOLD)
    sentiment_bar = ft.Row([
        ft.Container(width=120, height=12, bgcolor=ft.Colors.GREEN, border_radius=5),
        ft.Container(width=60, height=12, bgcolor=ft.Colors.RED_400, border_radius=5),
    ], spacing=0)

    premiums_column = ft.Column([])
    def refresh_premiums(e=None):
        premiums_column.controls.clear()
        for price in [92, 85, 81]:
            premiums_column.controls.append(
                ft.Card(content=ft.Container(
                    content=ft.Row([
                        ft.Column([ft.Text(f"{symbol_dropdown.value} {54600+price} CE", weight=ft.FontWeight.BOLD), ft.Text(f"@ ₹{price}", color="green")], expand=True),
                        ft.ElevatedButton("Buy", bgcolor="green", color="white"),
                        ft.OutlinedButton("Add to Bot", on_click=lambda _, s=f"{symbol_dropdown.value} {price} CE": add_to_bot(s))
                    ]), padding=10
                ))
            )
        page.update()

    def add_to_bot(symbol):
        bot_list.append(symbol)
        page.snack_bar = ft.SnackBar(ft.Text(f"Added to Bot: {symbol}"))
        page.snack_bar.open = True
        page.update()

    front_page = ft.Column([
        ft.Container(content=ft.Column([symbol_dropdown, ft.Row([ft.Text("Live Price: "), selected_symbol]), live_price,
            ft.Text("Market Sentiment", color="grey"), ft.Row([ft.Text("Bullish 68%", color="green"), ft.Text("Bearish 32%", color="red")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            sentiment_bar,
            ft.Divider(),
            ft.Row([ft.Text("Top Premiums ₹80-100", weight=ft.FontWeight.BOLD), ft.IconButton(icon=ft.Icons.REFRESH, on_click=refresh_premiums)]),
            premiums_column
        ]), padding=15, scroll=ft.ScrollMode.AUTO, expand=True)
    ], expand=True)

    # --- PAGE 2: INDICATORS ---
    indicator_list = ft.Column([ft.Text("Added Indicators:", weight=ft.FontWeight.BOLD)])
    new_indicator = ft.TextField(label="Indicator Name (e.g. RSI, EMA 20)")
    def add_indicator(e):
        indicator_list.controls.append(ft.ListTile(title=ft.Text(new_indicator.value), trailing=ft.Icon(ft.Icons.CHECK, color="green")))
        new_indicator.value = ""
        page.update()
    
    indicators_page = ft.Column([
        ft.Container(content=ft.Column([
            new_indicator,
            ft.ElevatedButton("Add Indicator", on_click=add_indicator),
            ft.Divider(),
            indicator_list
        ]), padding=15)
    ])

    # --- PAGE 3: BOT EDIT ---
    bot_edit_list = ft.Column([])
    def rebuild_bot_page():
        bot_edit_list.controls.clear()
        for b in bot_list:
            bot_edit_list.controls.append(ft.ListTile(title=ft.Text(b), trailing=ft.IconButton(icon=ft.Icons.DELETE, on_click=lambda _, x=b: remove_bot(x))))
        page.update()
    def remove_bot(sym):
        bot_list.remove(sym)
        rebuild_bot_page()

    bot_page = ft.Column([
        ft.Container(content=ft.Column([
            ft.Text("Bot Control", size=20, weight=ft.FontWeight.BOLD),
            mode_dropdown,
            auto_switch,
            ft.Row([capital_input, risk_input]),
            ft.Divider(),
            ft.Text("Bot me Add kiye hue Premiums:", weight=ft.FontWeight.BOLD),
            bot_edit_list,
            ft.ElevatedButton("Refresh List", on_click=lambda e: rebuild_bot_page())
        ]), padding=15, scroll=ft.ScrollMode.AUTO)
    ])

    # --- PAGE 4: SETTINGS ---
    settings_page = ft.Column([
        ft.Container(content=ft.Column([
            ft.Text("Settings", size=20, weight=ft.FontWeight.BOLD),
            api_key, client_id, mpin_input, totp_input,
            ft.ElevatedButton("Angel Login Test", bgcolor="green", color="white"),
            ft.Divider(),
            ft.Text("Telegram", weight=ft.FontWeight.BOLD),
            ft.TextField(label="Bot Token", password=True),
            ft.TextField(label="Chat ID"),
        ]), padding=15, scroll=ft.ScrollMode.AUTO)
    ])

    # --- NAVIGATION LOGIC ---
    pages = [front_page, indicators_page, bot_page, settings_page]
    content_area = ft.Container(content=pages[0], expand=True)

    def nav_change(e):
        content_area.content = pages[e.control.selected_index]
        if e.control.selected_index == 2:
            rebuild_bot_page()
        if e.control.selected_index == 0:
            refresh_premiums()
        page.update()

    nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Front"),
            ft.NavigationBarDestination(icon=ft.Icons.SHOW_CHART, label="Indicators"),
            ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY, label="Bot Edit"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings"),
        ],
        on_change=nav_change,
        selected_index=0
    )

    page.add(
        ft.Column([
            ft.Container(content=content_area, expand=True),
            nav_bar
        ], expand=True)
    )
    refresh_premiums()

ft.app(target=main)
