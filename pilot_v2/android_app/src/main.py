"""BOT KING V2 Flet offline app; app owns settings, no live Dhan/Oracle calls."""
import flet as ft
from app_identity import APP_VERSION_NAME, APP_VERSION_CODE
from app_state import LocalWatchlists, SelectionError
from smart_data import SmartDataSettings, SmartDataError, selected_equity_plan
from scanner_state import ScannerSelection, ScannerError, selectable_symbols, choose, for_visible_roster
from feed_inbox import DeviceFeedInbox
from evidence_inbox import DeviceEvidenceInbox
from option_evidence import OptionEvidenceError
from dashboard_parity import INDEXES, index_card_model, status_overview
from watchlist_parity import watchlist_rows
from legacy_technical_bridge import historical_scanner_analysis
from historical_chart_context import chart_points, historical_shortlist
from candle_option_views import candle_geometry

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
    evidence_inbox = DeviceEvidenceInbox()  # Offline, authenticated data client NOT connected.
    candle_history = evidence_inbox.candles
    filter_evidence = evidence_inbox.filters
    option_evidence = evidence_inbox.options
    expiry_choices = evidence_inbox.expiries
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
                    evidence_inbox.select_expiry(
                        scanner[0].symbol, e.control.value,
                        selected_equities=state.selected)
                    status.value = "Selected existing verified expiry locally"
                except OptionEvidenceError as exc:
                    status.value = str(exc)
                render()
                page.update()
            index_cards = [index_card_model(symbol, quote_view, evidence_inbox,
                                            state.selected) for symbol in INDEXES]
            health = status_overview(state.selected, quote_view, evidence_inbox)
            content.controls = [
                ft.Text("Dashboard", size=19, weight=ft.FontWeight.BOLD),
                *[ft.Container(
                    content=ft.Column([
                        ft.Text(card["symbol"], weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(card["price_label"], size=15),
                        ft.Text(card["candle_label"], size=13),
                        ft.Text("1m signals · " + " / ".join(
                            value for _, value in card["filters"])),
                    ], spacing=3),
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=8, padding=10,
                ) for card in index_cards],
                ft.Text("System Health · " +
                        str(health["index_quote_coverage"]) + "/3 index histories available",
                        size=13),
                ft.Text(health["feed"], size=12),
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
                ft.Text(historical_scanner_analysis(
                    candle_history, scanner[0].symbol, scanner[0].timeframe,
                    selected_equities=state.selected)["summary"], size=13),
                *([ft.Container(
                    content=ft.LineChart(
                        data_series=[ft.LineChartData(
                            data_points=[ft.LineChartDataPoint(i, price)
                                         for i, price in enumerate(chart_points(
                                             candle_history, scanner[0].symbol,
                                             scanner[0].timeframe,
                                             selected_equities=state.selected))],
                            stroke_width=2, curved=False)],
                        expand=True),
                    height=150, padding=5,
                )] if len(chart_points(
                    candle_history, scanner[0].symbol, scanner[0].timeframe,
                    selected_equities=state.selected)) >= 2 else
                   [ft.Text("Scanner chart WAIT · completed candle history unavailable")]),
                ft.Text("Completed OHLC candles · historical / unverified",
                        size=12),
                ft.Row([
                    ft.Stack([
                        ft.Container(width=2, height=c["wick_height"],
                                     bgcolor=ft.Colors.GREEN if c["up"] else ft.Colors.RED,
                                     top=c["wick_top"], left=5),
                        ft.Container(width=12, height=c["body_height"],
                                     bgcolor=ft.Colors.GREEN if c["up"] else ft.Colors.RED,
                                     top=c["body_top"], left=0),
                    ], width=12, height=116) for c in candle_geometry(
                        candle_history, scanner[0].symbol, scanner[0].timeframe,
                        selected_equities=state.selected)
                ], scroll=ft.ScrollMode.AUTO, spacing=4),
                ft.Text("Historical close-price chart · NOT live / not a verified trade signal",
                        size=12),
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
                ft.Text("CE / PE option-chain strikes (trusted completed cache only)",
                        size=13, weight=ft.FontWeight.BOLD),
                *([ft.Row([
                    ft.Text("CE OI", width=75),
                    ft.Text("CE ₹", width=75),
                    ft.Text("STRIKE", width=90),
                    ft.Text("PE ₹", width=75),
                    ft.Text("PE OI", width=75),
                ], spacing=2)] + [
                    ft.Row([
                        ft.Text(f'{r["ce_oi"]:,.0f}', width=75),
                        ft.Text(f'{r["ce_price"]:,.2f}', width=75),
                        ft.Text(f'{r["strike"]:,.0f}', width=90),
                        ft.Text(f'{r["pe_price"]:,.2f}', width=75),
                        ft.Text(f'{r["pe_oi"]:,.0f}', width=75),
                    ], spacing=2) for r in evidence_inbox.strikes.visible(
                        scanner[0].symbol,
                        expiry_choices.selected(scanner[0].symbol,
                                                selected_equities=state.selected),
                        expiry_choices, selected_equities=state.selected)["rows"]
                ] if evidence_inbox.strikes.visible(
                    scanner[0].symbol,
                    expiry_choices.selected(scanner[0].symbol,
                                            selected_equities=state.selected),
                    expiry_choices, selected_equities=state.selected)["status"] == "HIST"
                  else [ft.Text("CE/PE strikes WAIT · no trusted selected expiry / rows")]),
                ft.Text("Option-chain HIST only; OI/PCR is not a trading signal",
                        size=12),
                ft.Text("Super Five — verified live ranking WAIT"),
                ft.Text("Historical technical shortlist (not Super Five signals)",
                        size=13, weight=ft.FontWeight.BOLD),
                *[ft.Text(item["label"], size=12) for item in historical_shortlist(
                    candle_history, state.selected, timeframe="3m")],
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
                evidence_inbox.forget_removed(state.selected)
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
                *[ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(row["symbol"] + "  " + row["price"],
                                    weight=ft.FontWeight.BOLD, expand=True),
                            ft.TextButton("Remove",
                                          on_click=lambda e, item=row["symbol"]: remove(e, item)),
                        ], spacing=4),
                        ft.Text(row["candle"], size=13),
                        ft.Text(row["filter_text"], size=12),
                    ], spacing=3),
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=8, padding=8,
                ) for row in watchlist_rows(
                    state.groups[group[0]], quote_view, evidence_inbox,
                    selected_equities=state.selected)],
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
                ft.Text(f"Installed app label: BOT KING V2 v{APP_VERSION_NAME} (code {APP_VERSION_CODE})"),
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
                ft.Text("Master Device Control", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("4-phone target: 1 Master + 3 delegated · offline policy only"),
                ft.Text("Enable / Disable / Revoke require verified device login"),
                ft.Text("Dhan token renewal only via authorized Master workflow"),
                ft.Text("System Health / Error Doctor: no authenticated provider data"),
                ft.Text("Live orders disabled"),
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
    page.add(ft.Text(f"BOT KING V2 · v{APP_VERSION_NAME}", size=18, weight=ft.FontWeight.BOLD),
             status, ft.Divider(), content)
    render()
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
