import flet as ft

def main(page: ft.Page):
    page.title = "Volume King"
    page.bgcolor = "#121212"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    page.add(
        ft.Column([
            ft.Icon(name=ft.icons.VOLUME_UP, size=80, color="green"),
            ft.Text("Volume King", size=32, weight=ft.FontWeight.BOLD, color="white"),
            ft.Text("Ready to Boost!", size=18, color="white70"),
            ft.ElevatedButton("BOOST VOLUME", width=200, height=50, bgcolor="green", color="white")
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main)
