"""BOT KING V2 Flet offline app; app owns settings, no live Dhan/Oracle calls."""
import flet as ft
from app_state import LocalWatchlists, SelectionError

def main(page: ft.Page):
    page.title = "BOT KING Version 2"
    page.padding = 12
    storage_key = "botking.v2.watchlists.v1"
    try:
        saved = page.client_storage.get(storage_key)
        state = LocalWatchlists.from_saved(saved) if saved is not None else LocalWatchlists()
        storage_error = ""
    except (SelectionError, OSError, ValueError, TypeError, RuntimeError) as exc:
        state = LocalWatchlists()
        storage_error = "Saved watchlists could not be loaded; previous save not overwritten"

    def save_local():
        if storage_error:
            return False
        try:
            page.client_storage.set(storage_key, state.saved_state())
            return True
        except (OSError, ValueError, TypeError, RuntimeError):
            return False

    current = [0]
    group = [0]
    status = ft.Text(storage_error or "Offline pilot — no verified market data", size=13)
    content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def render():
        if current[0] == 0:
            content.controls = [
                ft.Text("Dashboard", size=19, weight=ft.FontWeight.BOLD),
                ft.Text("NIFTY  —  WAIT"),
                ft.Text("BANKNIFTY  —  WAIT"),
                ft.Text("SENSEX  —  WAIT"),
                ft.Text("Index signals: 1m · source unavailable"),
                ft.Divider(),
                ft.Text("Five filters: WAIT (no verified evidence)"),
                ft.Text("Sixth filter: reserved / blank"),
                ft.Text("Scanner and Super Five: data not connected"),
            ]
        elif current[0] == 1:
            symbol = ft.TextField(label="NSE equity symbol", hint_text="TCS", expand=True)
            def add(_):
                try:
                    state.add(group[0], (symbol.value or "").strip().upper())
                    status.value = ("Saved on this device; server not contacted" if save_local() else "Selection changed for this session; local save unavailable")
                    symbol.value = ""
                except SelectionError as exc:
                    status.value = str(exc)
                render()
                page.update()
            def remove(_, item):
                state.remove(group[0], item)
                status.value = ("Removed from device storage" if save_local() else "Removed for this session; local save unavailable")
                render()
                page.update()
            def switch_group(e):
                group[0] = int(e.control.value)
                render()
                page.update()
            content.controls = [
                ft.Text("Watchlist", size=19, weight=ft.FontWeight.BOLD),
                ft.Text(f"{len(state.selected)}/70 unique equities · 3 indexes separate"),
                ft.Dropdown(label="Watchlist", width=190, value=str(group[0]),
                            options=[ft.dropdown.Option(str(i), f"Watchlist {i+1}") for i in range(5)],
                            on_change=switch_group),
                ft.Row([symbol, ft.ElevatedButton("Add", on_click=add)]),
                *[ft.Row([ft.Text(s, expand=True), ft.Text("WAIT"),
                          ft.TextButton("Remove", on_click=lambda e, item=s: remove(e,item))])
                  for s in state.groups[group[0]]],
                ft.Text("3m candles unavailable · no fabricated prices"),
            ]
        else:
            content.controls = [
                ft.Text("Settings", size=19, weight=ft.FontWeight.BOLD),
                ft.Text("Smart Data and Master Control belong in this app"),
                ft.Text("Market polling window: 09:10–15:45 IST"),
                ft.Text("Outside hours: manual data refresh only"),
                ft.Text("Five watchlists · 70 unique equities total"),
                ft.Text("Device access, login and Dhan connection: not yet integrated"),
                ft.Text("No automatic server changes or trading orders"),
            ]

    def navigate(e):
        current[0] = e.control.selected_index
        render()
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0, on_change=navigate,
        destinations=[
            ft.NavigationDestination(icon=ft.icons.DASHBOARD_OUTLINED, label="Dashboard"),
            ft.NavigationDestination(icon=ft.icons.LIST_ALT_OUTLINED, label="Watchlist"),
            ft.NavigationDestination(icon=ft.icons.SETTINGS_OUTLINED, label="Settings"),
        ])
    page.add(ft.Text("BOT KING Version 2", size=20, weight=ft.FontWeight.BOLD),
             status, ft.Divider(), content)
    render()
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
