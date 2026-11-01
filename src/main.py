import flet as ft

def main(page: ft.Page):
    page.title = "Volume King"
    page.bgcolor = "#0F0F0F"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    page.add(
        ft.Column([
            ft.Text("VOLUME KING 97", size=30, weight=ft.FontWeight.BOLD, color="amber"),
            ft.ElevatedButton("START SCAN", bgcolor="green", color="white", width=250, height=50)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main)
