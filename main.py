import flet as ft

def main(page: ft.Page):
    page.title = "Volume King"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.padding = 20

    title = ft.Text("VOLUME KING", size=32, weight=ft.FontWeight.BOLD, color="#4CAF50")
    status = ft.Text("Ready to Boost 🔊", size=18, color="white")
    
    slider = ft.Slider(min=0, max=150, divisions=15, value=50, active_color="#4CAF50", label="{value}%")
    slider_text = ft.Text("Volume: 50%", size=16, color="white")

    def on_slider_change(e):
        slider_text.value = f"Volume: {int(e.control.value)}%"
        if e.control.value > 100:
            status.value = f"BOOSTED to {int(e.control.value)}% 🚀🔊"
            status.color = "#4CAF50"
        else:
            status.value = f"Volume: {int(e.control.value)}%"
            status.color = "white"
        page.update()

    slider.on_change = on_slider_change

    def boost_click(e):
        slider.value = 150
        slider_text.value = "Volume: 150%"
        status.value = "BOOSTED to 150% MAX! 🔊🔥"
        status.color = "#4CAF50"
        page.snack_bar = ft.SnackBar(ft.Text("Volume Boosted to 150%! 🔊"), bgcolor="#4CAF50")
        page.snack_bar.open = True
        page.update()

    boost_btn = ft.ElevatedButton(
        text="BOOST 150% 🔊",
        bgcolor="#4CAF50",
        color="white",
        width=350,
        height=60,
        style=ft.ButtonStyle(text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD)),
        on_click=boost_click
    )

    page.add(
        title,
        ft.Text("Agar ye dikh raha hai to APK sahi hai", size=16, color="white"),
        ft.Container(height=20),
        boost_btn,
        ft.Container(height=20),
        slider_text,
        slider,
        ft.Container(height=20),
        status,
        ft.Text("Speaker & Headphone Boost Supported", size=12, color="grey")
    )

ft.app(target=main)
