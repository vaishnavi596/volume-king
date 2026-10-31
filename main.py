import flet as ft

def main(page: ft.Page):
    page.title = "Volume King"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    
    page.add(
        ft.Column([
            ft.Text("Volume King", size=30, weight="bold"),
            ft.Text("App Working! No Crash!", size=16),
            ft.ElevatedButton("BOOST", on_click=lambda e: print("Boosted"))
        ], alignment="center", horizontal_alignment="center")
    )

ft.app(target=main)
