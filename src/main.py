import flet as ft

def main(page: ft.Page):
    page.title = "Volume King 97"
    page.bgcolor = "#0F0F0F"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(
        ft.Column([
            ft.Text("VOLUME KING 97", size=28, weight="bold", color="amber"),
            ft.Text("Real Market - Bullish Bearish", color="white70"),
            ft.ElevatedButton("START SCAN", bgcolor="green", color="white", width=300)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main)
