import flet as ft

def main(page: ft.Page):
    page.title = "VOLUME KING V10"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#080A12"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    page.add(
        ft.Column([
            ft.Text("VOLUME KING V10 ULTIMATE", size=24, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER),
            ft.Text("NIFTY 24500 CE @ 124.5 -> TARGET 165.8", size=18, color="#00E676", text_align=ft.TextAlign.CENTER),
            ft.ElevatedButton("BUY CE 24500 CE", bgcolor="#00E676", color="white", width=250, height=50)
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20
        )
    )
    page.update()
