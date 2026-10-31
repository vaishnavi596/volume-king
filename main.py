import flet as ft

def main(page: ft.Page):
    page.title = "Bot King Trade"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10

    bot_list = []

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
        for s in ["Nifty", "BankNifty", "Sensex", "TCS"]:
            premiums_column.controls.append(
                ft.ListTile(
                    title=ft.Text(s),
                    trailing=ft.IconButton(icon=ft.Icons.ADD, data=s, on_click=add_to_bot)
                )
            )
        page.update()

    refresh_btn = ft.ElevatedButton("Refresh Premiums", on_click=refresh_premiums)
    
    page.add(
        symbol_dropdown,
        live_price,
        refresh_btn,
        premiums_column
    )
    refresh_premiums()

ft.app(target=main)
