import flet as ft

def main(page: ft.Page):
    page.title = "Boating Trading Bot"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f172a"
    
    status_text = ft.Text("BOT STOPPED", color="red", size=20, weight="bold")
    log_text = ft.Text("Bot ready... Waiting for START", color="white")
    pcr_text = ft.Text("PCR: 1.15 Bullish", size=18, color="green")
    
    def start_bot(e):
        status_text.value = "BOT RUNNING - LIVE"
        status_text.color = "green"
        log_text.value = "LIVE: NIFTY 23000 CE 93% STRONG BUY\nLIVE: Fetching OI Data..."
        page.update()
    
    def stop_bot(e):
        status_text.value = "BOT STOPPED"
        status_text.color = "red"
        log_text.value = "Bot Stopped"
        page.update()

    page.add(
        ft.Column([
            ft.Text("BOATING - OI AUTO TRADING", size=24, weight="bold", color="white"),
            ft.Divider(),
            status_text,
            ft.Row([
                ft.ElevatedButton("START", bgcolor="green", color="white", on_click=start_bot),
                ft.ElevatedButton("STOP", bgcolor="red", color="white", on_click=stop_bot),
            ]),
            ft.Container(height=20),
            pcr_text,
            ft.Container(
                content=log_text,
                bgcolor="#1e293b",
                padding=10,
                border_radius=10,
                height=200,
                width=400
            ),
            ft.Text("Page 2: Indicator | Page 3: OI Chain | Page 4: Bot Setting - Coming in LIVE version", color="grey")
        ])
    )

ft.app(target=main)
