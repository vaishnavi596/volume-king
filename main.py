import flet as ft

def main(page: ft.Page):
    page.title = "Bot King Trade"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.scroll = ft.ScrollMode.AUTO

    bot_list = []

    symbol_dropdown = ft.Dropdown(
        label="Symbol",
        value="BankNifty",
        options=[
            ft.dropdown.Option("Nifty"),
            ft.dropdown.Option("BankNifty"),
            ft.dropdown.Option("Sensex"),
            ft.dropdown.Option("TCS"),
        ],
        width=300
    )

    live_price = ft.Text("₹ 44,892.35 +1.24%", size=26, weight=ft.FontWeight.BOLD)
    
    premiums_column = ft.Column(scroll=ft.ScrollMode.AUTO, height=400)
    bot_column = ft.Column()

    def add_to_bot(e):
        sym = e.control.data
        if sym not in bot_list:
            bot_list.append(sym)
            bot_column.controls.append(ft.Text(f"✅ {sym} added to Bot"))
            page.snack_bar = ft.SnackBar(content=ft.Text(f"Added: {sym} to Bot List"))
            page.snack_bar.open = True
            page.update()

    def refresh_premiums(e=None):
        premiums_column.controls.clear()
        for s in ["Nifty", "BankNifty", "Sensex", "TCS"]:
            premiums_column.controls.append(
                ft.ListTile(
                    title=ft.Text(s, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text("Premium: ₹ 120.5"),
                    trailing=ft.IconButton(
                        icon=ft.icons.ADD,  # ye chhota 'i' wala hai, 0.27.6 ke liye
                        data=s,
                        on_click=add_to_bot
                    )
                )
            )
        page.update()

    refresh_btn = ft.ElevatedButton("Refresh Premiums", icon=ft.icons.REFRESH, on_click=refresh_premiums)
    
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

ft.app(target=main)
