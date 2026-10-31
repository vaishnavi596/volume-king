import flet as ft

def main(page: ft.Page):
    page.title = "Bot King Trade"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10

    bot_list = []

    # --- Common ---
    symbol_dropdown = ft.Dropdown(
        label="Symbol", value="BankNifty",
        options=[ft.dropdown.Option("Nifty"), ft.dropdown.Option("BankNifty"), ft.dropdown.Option("Sensex"), ft.dropdown.Option("TCS")],
        width=300
    )
    live_price = ft.Text("₹ 44,892.35 +1.24%", size=26, weight=ft.FontWeight.BOLD)
    premiums_column = ft.Column(scroll=ft.ScrollMode.AUTO)

    def add_to_bot(e):
        sym = e.control.data
        bot_list.append(sym)
        page.snack_bar = ft.SnackBar(ft.Text(f"Added: {sym}"))
        page.snack_bar.open = True
        page.update()

    def refresh_premiums(e=None):
        premiums_column.controls.clear()
        for strike, price in [(54600,92), (54700,85), (54800,81)]:
            premiums_column.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(f"{symbol_dropdown.value} {strike} CE", weight=ft.FontWeight.BOLD),
                            ft.Text(f"@ ₹{price}", color=ft.Colors.GREEN_400)
                        ], expand=True),
                        ft.ElevatedButton("Buy", bgcolor="green", color="white"),
                        ft.OutlinedButton("Add to Bot", data=f"{symbol_dropdown.value} {strike} CE", on_click=add_to_bot)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=ft.Colors.GREY_900,
                    padding=10,
                    border_radius=10
                )
            )
        page.update()

    # --- 4 PAGES ---
    front_page = ft.Column([
        symbol_dropdown,
        live_price,
        ft.Text("Market Sentiment", color="grey"),
        ft.Row([ft.Text("Bullish 68%", color="green"), ft.Text("Bearish 32%", color="red")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Container(height=10, bgcolor="green", width=200, border_radius=5),
        ft.Divider(),
        ft.Row([ft.Text("Top Premiums ₹80-100", weight=ft.FontWeight.BOLD), ft.IconButton(icon=ft.Icons.REFRESH, on_click=refresh_premiums)]),
        premiums_column
    ], scroll=ft.ScrollMode.AUTO)

    indicators_page = ft.Column([
        ft.Text("Indicators", size=20, weight=ft.FontWeight.BOLD),
        ft.TextField(label="Add Indicator (RSI, EMA)"),
        ft.ElevatedButton("Add"),
    ])

    bot_edit_page = ft.Column([
        ft.Text("Bot Control", size=20, weight=ft.FontWeight.BOLD),
        ft.Dropdown(label="Mode", value="Auto", options=[ft.dropdown.Option("Auto"), ft.dropdown.Option("Manual")]),
        ft.Switch(label="Auto Trading ON"),
        ft.TextField(label="Capital", value="100000"),
        ft.Divider(),
        ft.Text("Bot List yaha dikhega jab Add to Bot karoge"),
    ])

    settings_page = ft.Column([
        ft.Text("Settings", size=20, weight=ft.FontWeight.BOLD),
        ft.TextField(label="Angel API Key", password=True),
        ft.TextField(label="Client ID"),
        ft.TextField(label="MPIN", password=True),
        ft.TextField(label="TOTP Secret", password=True),
        ft.ElevatedButton("Angel Login Test", bgcolor="green", color="white"),
    ])

    pages = [front_page, indicators_page, bot_edit_page, settings_page]
    content = ft.Column([pages[0]], expand=True, scroll=ft.ScrollMode.AUTO)

    def nav_change(e):
        idx = e.control.selected_index
        content.controls.clear()
        content.controls.append(pages[idx])
        if idx == 0:
            refresh_premiums()
        page.update()

    page.add(content)
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Front"),
            ft.NavigationBarDestination(icon=ft.Icons.SHOW_CHART, label="Indicators"),
            ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY, label="Bot Edit"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings"),
        ],
        on_change=nav_change
    )
    refresh_premiums()
    page.update()

ft.app(target=main)
