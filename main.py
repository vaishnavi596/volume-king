import flet as ft

def main(page: ft.Page):
    page.title = "Bot King Trade"
    page.bgcolor = "#121212"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    nifty_txt = ft.Text("Nifty: 23053.10", size=18, color="white")
    bank_txt = ft.Text("BankNifty: 54686.95", size=18, color="white")
    sensex_txt = ft.Text("Sensex: 74459.53", size=18, color="white")
    vol_txt = ft.Text("Wait - Volume 78%", size=22, weight=ft.FontWeight.BOLD, color="#FFA500")

    def refresh_click(e):
        nifty_txt.value = "Nifty: 23100.50 (Live)"
        page.update()

    def signal_click(e):
        vol_txt.value = "BUY Signal - Volume 85% - GO!"
        vol_txt.color = "#4CAF50"
        page.update()

    page.add(
        ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("Bot King Trade", size=26, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("70% Volume 80-100 Bot Ready", size=13, color="#4CAF50"),
                    ft.Divider(color="#333333")
                ]),
                padding=15
            ),
            ft.Container(
                content=ft.Column([
                    nifty_txt, bank_txt, sensex_txt,
                    ft.ElevatedButton("Refresh Live Price", bgcolor="#4CAF50", color="white", on_click=refresh_click)
                ], spacing=15),
                padding=20
            ),
            ft.Divider(color="#333333"),
            ft.Container(
                content=ft.Column([
                    vol_txt,
                    ft.ElevatedButton("Get Volume Signal", width=340, height=50, bgcolor="#2196F3", color="white", on_click=signal_click)
                ], spacing=15),
                padding=20
            )
        ], expand=True)
    )

ft.app(target=main)
