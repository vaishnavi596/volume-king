"""Separate BOT KING V2 Flet offline shell; no live prices or broker access."""
import flet as ft

def main(page:ft.Page):
    page.title="BOT KING V2"
    page.padding=14
    page.scroll=ft.ScrollMode.AUTO
    page.add(
      ft.Text("BOT KING V2",size=22,weight=ft.FontWeight.BOLD),
      ft.Text("Pilot 2.0.100 — Gateway disconnected / offline"),
      ft.Text("NIFTY · BANKNIFTY · SENSEX"),
      ft.Text("No verified quote or candle data available"),
      ft.Divider(),
      ft.Text("Watchlist · Scanner · Super Five"),
      ft.Text("Master/device pairing and live data are not enabled"),
      ft.Text("Five filters: WAIT; sixth filter: reserved"),
    )

if __name__=="__main__":
    ft.app(target=main)
