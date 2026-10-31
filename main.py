import flet as ft

def main(page: ft.Page):
    page.title = "Volume King"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    
    page.appbar = ft.AppBar(title=ft.Text("Volume King"), bgcolor="green")

    def booster_clicked(e):
        page.show_snack_bar(ft.SnackBar(content=ft.Text("Volume Booster ON! 🔊"), bgcolor="green"))
        page.update()

    page.add(
        ft.Column([
            ft.Icon(ft.Icons.VOLUME_UP, size=120, color=ft.Colors.GREEN_400),
            ft.Text("Volume King", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Your Phone Volume Booster", size=16, color=ft.Colors.GREY_400),
            ft.Container(height=30),
            ft.ElevatedButton(
                "BOOST VOLUME", 
                icon=ft.Icons.ROCKET_LAUNCH,
                bgcolor="green", 
                color="white",
                width=200, 
                height=50,
                on_click=booster_clicked
            ),
            ft.Text("App is running successfully!", size=12, color=ft.Colors.GREEN)
        ], 
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

ft.app(target=main)
