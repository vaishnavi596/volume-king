import flet as ft

def main(page: ft.Page):
    page.title = "Bot King Trade"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 15

    # --- Data ---
    bot_list = []

    # --- UI Controls ---
    symbol_dropdown = ft.Dropdown(
        label="Select Symbol",
        value="BTCUSDT",
        options=[
            ft.dropdown.Option("BTCUSDT"),
            ft.dropdown.Option("ETHUSDT"),
            ft.dropdown.Option("BNBUSDT"),
        ],
        width=300,
    )

    live_price = ft.Text("Live Price: --", size=16)
    premiums_column = ft.Column()
    bot_column = ft.Column(scroll=ft.ScrollMode.AUTO, height=300)

    # --- Functions ---
    def refresh_premiums(e=None):
        premiums_column.controls.clear()
        for i, s in enumerate(["5.2%", "3.8%", "7.1%"]):
            premiums_column.controls.append(
                ft.ListTile(
                    title=ft.Text(f"Market {i+1}: {s}"),
                    trailing=ft.IconButton(
                        icon=ft.icons.ADD,
                        data=s,
                        on_click=add_to_bot
                    )
                )
            )
        live_price.value = f"Live Price: {symbol_dropdown.value} - $65000"
        page.update()

    def add_to_bot(e):
        sel = e.control.data
        bot_list.append(sel)
        bot_column.controls.append(
            ft.ListTile(
                title=ft.Text(f"Bot #{len(bot_list)} : {sel}"),
                trailing=ft.IconButton(icon=ft.icons.DELETE)
            )
        )
        page.update()

    refresh_btn = ft.ElevatedButton("Refresh Premiums", icon=ft.icons.REFRESH, on_click=refresh_premiums)

    # --- Layout ---
    page.add(
        ft.Text("Bot King Trade", size=30, weight=ft.FontWeight.BOLD),
        symbol_dropdown,
        live_price,
        refresh_btn,
        ft.Divider(),
        ft.Text("Market Premiums:", size=18, weight=ft.FontWeight.BOLD),
        premiums_column,
        ft.Divider(),
        ft.Text("My Bot List:", size=18, weight=ft.FontWeight.BOLD),
        bot_column
    )

    refresh_premiums()
