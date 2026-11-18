"""BOT KING V2 Flet offline app; app owns settings, no live Dhan/Oracle calls."""
import flet as ft
from app_state import LocalWatchlists, SelectionError
from smart_data import SmartDataSettings, SmartDataError, selected_equity_plan
from scanner_state import ScannerSelection, ScannerError, selectable_symbols, choose, for_visible_roster
from feed_inbox import DeviceFeedInbox
from candle_history import LocalCandleHistory
from filter_evidence import LocalFilterEvidence
from option_evidence import LocalOptionEvidence, LocalExpiryChoices, OptionEvidenceError

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

    smart_key = "botking.v2.smartdata.v1"
    try:
        saved_smart = page.client_storage.get(smart_key)
        smart = [SmartDataSettings.from_saved(saved_smart) if saved_smart is not None else SmartDataSettings()]
        smart_error = ""
    except (SmartDataError, OSError, ValueError, TypeError, RuntimeError):
        smart = [SmartDataSettings()]
        smart_error = "Smart Data save could not be loaded; previous settings not overwritten"

    def save_smart():
        if smart_error:
            return False
        try:
            page.client_storage.set(smart_key, smart[0].saved_state())
            return True
        except (OSError, ValueError, TypeError, RuntimeError):
            return False

    scanner_key = "botking.v2.scanner.v1"
    try:
        saved_scan = page.client_storage.get(scanner_key)
        scanner = [ScannerSelection.from_saved(saved_scan, state) if saved_scan is not None
                   else ScannerSelection()]
        scanner_error = ""
    except (ScannerError, OSError, ValueError, TypeError, RuntimeError):
        scanner = [ScannerSelection()]
        scanner_error = "Saved Scanner selection unavailable; original save preserved"

    def save_scanner():
        if scanner_error:
            return False
        try:
            page.client_storage.set(scanner_key, scanner[0].saved_state())
            return True
        except (OSError, ValueError, TypeError, RuntimeError):
            return False

    quote_view = DeviceFeedInbox()  # Separate equity/index revisions; no network producer yet.
    candle_history = LocalCandleHistory()  # No fabricated candles; accepts validated local input only.
    filter_evidence = LocalFilterEvidence()  # No source-gated evidence yet; all five WAIT.
    option_evidence = LocalOptionEvidence()  # Actual Dhan option evidence unavailable.
    expiry_choices = LocalExpiryChoices()  # No invented or default expiry.
    current = [0]
    group = [0]
    status = ft.Text(storage_error or "Offline pilot — no verified market data", size=13)
    content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def render():
        if current[0] == 0:
            scanner[0] = for_visible_roster(scanner[0], state)
            def select_scanner_symbol(e):
                try:
                    scanner[0] = choose(scanner[0], state, symbol=e.control.value)
                    status.value = ("Scanner choice saved locally" if save_scanner()
                                    else "Scanner choice changed for session only")
                except ScannerError as exc:
                    status.value = str(exc)
                render()
                page.update()
            def select_scanner_timeframe(e):
                try:
                    scanner[0] = choose(scanner[0], state, timeframe=e.control.value)
                    status.value = ("Scanner timeframe saved locally" if save_scanner()
                                    else "Scanner timeframe changed for session only")
                except ScannerError as exc:
                    status.value = str(exc)
                render()
                page.update()
            def select_expiry(e):
                try:
                    expiry_choices.choose(scanner[0].symbol, e.control.value,
                                          selected_equities=state.selected)
                    status.value = "Selected existing verified expiry locally"
                except OptionEvidenceError as exc:
                    status.value = str(exc)
                render()
                page.update()
            content.controls = [
                ft.Text("Dashboard", size=19, weight=ft.FontWeight.BOLD),
                ft.Text(quote_view.display("NIFTY", state.selected)),
                ft.Text(quote_view.display("BANKNIFTY", state.selected)),
                ft.Text(quote_view.display("SENSEX", state.selected)),
                *[ft.Text(candle_history.summary(s, "1m")) for s in ("NIFTY", "BANKNIFTY", "SENSEX")],
                ft.Text("Index signals: 1m · source unavailable"),
                ft.Divider(),
                ft.Text("Five filters — source-gated, no fabricated percentage"),
                *[ft.Text(f"{label}: {value}") for label, value in
                  filter_evidence.rows("NIFTY", "1m")[:5]],
                ft.Text("Sixth filter: reserved / blank"),
                ft.Text("Scanner", size=17, weight=ft.FontWeight.BOLD),
                ft.Dropdown(label="Scanner symbol", width=240, value=scanner[0].symbol,
                            options=[ft.dropdown.Option(s, s) for s in selectable_symbols(state)],
                            on_change=select_scanner_symbol),
                ft.Dropdown(label="Scanner timeframe", width=180, value=scanner[0].timeframe,
                            options=[ft.dropdown.Option(tf, tf) for tf in ("1m", "3m", "5m")],
                            on_change=select_scanner_timeframe),
                ft.Text(quote_view.display(scanner[0].symbol, state.selected)),
                ft.Text(candle_history.summary(scanner[0].symbol, scanner[0].timeframe,
                                               selected_equities=state.selected)),
                *[ft.Text(f"{label}: {value}") for label, value in
                  filter_evidence.rows(scanner[0].symbol, scanner[0].timeframe,
                                       selected_equities=state.selected)[:5]],
                ft.Text("Sixth filter: reserved / blank"),
                ft.Dropdown(
                    label="Option expiry (verified Dhan only)", width=260,
                    value=expiry_choices.selected(scanner[0].symbol,
                                                  selected_equities=state.selected),
                    options=[ft.dropdown.Option(x, x) for x in
                             expiry_choices.available(scanner[0].symbol,
                                                      selected_equities=state.selected)],
                    disabled=not bool(expiry_choices.available(
                        scanner[0].symbol, selected_equities=state.selected)),
                    on_change=select_expiry),
                ft.Text(option_evidence.summary(
                    scanner[0].symbol,
                    expiry_choices.selected(scanner[0].symbol,
                                            selected_equities=state.selected) or "",
                    selected_equities=state.selected)),
                ft.Text("Super Five: no verified history / ranking data"),
                ft.Text(scanner_error or "Scanner selection stored on this device"),
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
                quote_view.forget_removed(state.selected)
                candle_history.forget_removed(state.selected)
                filter_evidence.forget_removed(state.selected)
                option_evidence.forget_removed(state.selected)
                expiry_choices.forget_removed(state.selected)
                status.value = ("Removed from device storage" if save_local() else "Removed for this session; local save unavailable")
                render()
                page.update()
            def switch_group(e):
                group[0] = int(e.control.value)
                render()
                page.update()
            content.controls = [
                ft.Text("Watchlist", size=19, weight=ft.FontWeight.BOLD),
                ft.Text(f"{selected_equity_plan(state)['equity_count']}/70 unique equities · 3 indexes separate"),
                ft.Dropdown(label="Watchlist", width=190, value=str(group[0]),
                            options=[ft.dropdown.Option(str(i), f"Watchlist {i+1}") for i in range(5)],
                            on_change=switch_group),
                ft.Row([symbol, ft.ElevatedButton("Add", on_click=add)]),
                *[ft.Row([ft.Text(quote_view.display(s, state.selected), expand=True),
                          ft.TextButton("Remove", on_click=lambda e, item=s: remove(e,item))])
                  for s in state.groups[group[0]]],
                *[ft.Text(candle_history.summary(s, "3m", selected_equities=state.selected))
                  for s in state.groups[group[0]]],
                *[ft.Text(filter_evidence.compact(s, "3m", selected_equities=state.selected))
                  for s in state.groups[group[0]]],
            ]
        else:
            def change_auto(e):
                smart[0] = SmartDataSettings(bool(e.control.value), smart[0].equity_seconds)
                status.value = ("Smart Data setting saved on device" if save_smart()
                                else "Changed for session only; local save unavailable")
                render()
                page.update()
            def change_interval(e):
                try:
                    smart[0] = SmartDataSettings(smart[0].auto_refresh, int(e.control.value))
                    status.value = ("Smart Data interval saved on device" if save_smart()
                                    else "Changed for session only; local save unavailable")
                except (SmartDataError, TypeError, ValueError):
                    status.value = "Invalid refresh interval"
                render()
                page.update()
            content.controls = [
                ft.Text("Settings", size=19, weight=ft.FontWeight.BOLD),
                ft.Text("Smart Data & Master Control — app-owned"),
                ft.Switch(label="Automatic market refresh", value=smart[0].auto_refresh,
                          on_change=change_auto),
                ft.Dropdown(label="Selected equity quote interval", width=240,
                            value=str(smart[0].equity_seconds),
                            options=[ft.dropdown.Option(str(n), f"{n} seconds") for n in (180, 300, 600)],
                            on_change=change_interval),
                ft.Text("09:10–15:45 IST; auto requires confirmed market session"),
                ft.Text("Outside hours: manual data refresh only"),
                ft.Text(f"{len(state.selected)} selected equities; 3 independent indexes"),
                ft.Text(smart_error or "Stored on this device, never in Oracle settings"),
                ft.Text("Data connection and manual fetch not yet enabled"),
                ft.Text("Device access/login not integrated; live orders disabled"),
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
