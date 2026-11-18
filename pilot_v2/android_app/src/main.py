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
from watchlist_search import filtered_watchlist_symbols
from legacy_technical_bridge import historical_scanner_analysis
from historical_chart_context import chart_points, historical_shortlist, choose_historical_shortlist_symbol
from chart_window import DEFAULT_WINDOW, WINDOWS, window_from_dropdown
from candle_option_views import candle_geometry
from v1_visual_style import apply_v1_theme, v1_header, v1_card, GOLD, MUTED, WHITE, PANEL2
from local_help_doctor import diagnose, help_for
from shared_filter_context import shared_filter_context
from local_analysis_slots import LocalAnalysisSlots, AnalysisSlotError
from local_settings_backup import export_local_backup, parse_local_backup, LocalBackupError
from paper_preview import preview_manual_paper_risk

def main(page: ft.Page):
    page.title = "BOT KING Version 2"
    apply_v1_theme(page, ft)
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

    analysis_key = "botking.v2.analysis_slots.v1"
    try:
        saved_analysis = page.client_storage.get(analysis_key)
        analysis_slots = [LocalAnalysisSlots.from_saved(saved_analysis, state)
                          if saved_analysis is not None else LocalAnalysisSlots()]
        analysis_error = ""
    except (AnalysisSlotError, OSError, ValueError, TypeError, RuntimeError):
        analysis_slots = [LocalAnalysisSlots()]
        analysis_error = "Saved analysis selection invalid; original save preserved"

    def save_analysis():
        if analysis_error:
            return False
        try:
            page.client_storage.set(analysis_key, analysis_slots[0].saved_state())
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
    watch_search = [""]  # Session-local display query; never changes selected roster.
    help_topic = ["Dashboard"]  # UI-only; never persisted as server preference.
    chart_window = [DEFAULT_WINDOW]  # Local history display only.
    backup_text = [""]
    backup_confirm = [False]  # Explicit consent for replacing local preferences.
    paper_inputs = {"side": "BUY", "entry": "100", "quantity": "1",
                    "stop_pct": "2", "target_pct": "4",
                    "capital": "10000", "max_risk": "1000", "risk_pct": "5"}
    paper_result = ["Manual paper-only calculation; no orders or market data"]

    def open_help(topic):
        """Jump to app-owned Settings Help, without a server request."""
        help_topic[0] = topic
        current[0] = 2
        page.navigation_bar.selected_index = 2
        render()
        page.update()

    status = ft.Text(storage_error or "Offline pilot — no verified market data", size=14, color=MUTED)
    content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def render():
        if analysis_slots[0].reconcile(state):
            save_analysis()
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
            def change_chart_window(e):
                try:
                    chart_window[0] = window_from_dropdown(e.control.value)
                    status.value = "Historical chart window updated locally"
                except ValueError:
                    status.value = "Unsupported chart history window"
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
            def select_historical_candidate(symbol):
                """Open the selected historical equity in Scanner, without fetching."""
                try:
                    selected = choose_historical_shortlist_symbol(
                        candle_history, state.selected, symbol,
                        timeframe="3m")
                    scanner[0] = choose(scanner[0], state, symbol=selected,
                                        timeframe="3m")
                    status.value = ("Historical shortlist selection saved locally"
                                    if save_scanner() else
                                    "Historical shortlist choice changed for session only")
                except (ScannerError, ValueError):
                    status.value = "Historical shortlist selection unavailable"
                render()
                page.update()
            def open_index_chart(symbol):
                """Use the existing independent 1m index view without a Dhan fetch."""
                if symbol not in INDEXES:
                    status.value = "Unsupported Dashboard index"
                    render()
                    page.update()
                    return
                try:
                    scanner[0] = choose(scanner[0], state, symbol=symbol,
                                        timeframe="1m")
                    status.value = ("Index 1m chart selected locally"
                                    if save_scanner() else
                                    "Index 1m chart selected for session")
                except ScannerError:
                    status.value = "Index chart selection unavailable"
                render()
                page.update()
            def select_analysis_slot(e, slot):
                try:
                    analysis_slots[0].select(slot, e.control.value, state)
                    status.value = ("Dashboard analysis choice saved locally"
                                    if save_analysis() else
                                    "Dashboard analysis choice kept for session")
                except AnalysisSlotError:
                    status.value = "Invalid Dashboard analysis selection"
                render()
                page.update()
            def open_analysis_chart(symbol):
                try:
                    scanner[0] = choose(scanner[0], state, symbol=symbol,
                                        timeframe="1m")
                    status.value = ("Analysis 1m chart selected locally"
                                    if save_scanner() else
                                    "Analysis 1m chart selected for session")
                except ScannerError:
                    status.value = "Analysis symbol is no longer selected"
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
                ft.Row([
                    ft.Text("Dashboard", size=19, color=GOLD,
                            weight=ft.FontWeight.BOLD, expand=True),
                    ft.IconButton(icon=ft.Icons.HELP_OUTLINE, icon_color=GOLD,
                                  tooltip="Dashboard Help",
                                  on_click=lambda e: open_help("Dashboard")),
                ]),
                *[v1_card(ft, [
                        ft.Text(card["symbol"], color=GOLD, weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(card["price_label"], size=15),
                        ft.Text(card["candle_label"], size=13),
                        ft.Text("1m signals · " + " / ".join(
                            value for _, value in card["filters"])),
                        ft.Text(card["factor_coverage"], color=MUTED, size=14),
                        ft.TextButton("1m Chart",
                                      on_click=lambda e, symbol=card["symbol"]:
                                      open_index_chart(symbol)),
                    ]) for card in index_cards],
                ft.Text("Three analysis panels · saved locally · historical only",
                        color=GOLD, size=16, weight=ft.FontWeight.BOLD),
                *[v1_card(ft, [
                    ft.Dropdown(label=f"Analysis {slot+1} · index/equity",
                                width=290, value=analysis_slots[0].slots[slot],
                                options=[ft.dropdown.Option(item, item)
                                         for item in selectable_symbols(state)],
                                on_change=lambda e, slot=slot: select_analysis_slot(e, slot)),
                    ft.Text(quote_view.display(symbol, state.selected), color=WHITE),
                    ft.Text(candle_history.summary(
                        symbol, "1m", selected_equities=state.selected),
                        color=MUTED, size=14),
                    ft.Text(shared_filter_context(filter_evidence, symbol, "1m",
                            selected_equities=state.selected)["coverage_label"],
                            color=MUTED, size=14),
                    ft.TextButton("1m Chart",
                                  on_click=lambda e, symbol=symbol:
                                  open_analysis_chart(symbol)),
                ]) for slot, symbol in enumerate(analysis_slots[0].slots)],
                v1_card(ft, [
                    ft.Text("System Health", color=GOLD, weight=ft.FontWeight.BOLD),
                    ft.Text(str(health["index_quote_coverage"]) +
                            "/3 index histories available", color=WHITE, size=14),
                    ft.Text(health["feed"], color=MUTED, size=14),
                ]),
                ft.Divider(),
                ft.Text("Five filters — source-gated, no fabricated percentage", color=MUTED),
                *[ft.Text(f"{label}: {value}") for label, value in
                  filter_evidence.rows("NIFTY", "1m")[:5]],
                ft.Text("Sixth filter: reserved / blank", color=MUTED),
                ft.Row([
                    ft.Text("Scanner", size=17, color=GOLD,
                            weight=ft.FontWeight.BOLD, expand=True),
                    ft.IconButton(icon=ft.Icons.HELP_OUTLINE, icon_color=GOLD,
                                  tooltip="Scanner Help",
                                  on_click=lambda e: open_help("Scanner")),
                ]),
                ft.Dropdown(label="Scanner symbol", width=240, value=scanner[0].symbol,
                            options=[ft.dropdown.Option(s, s) for s in selectable_symbols(state)],
                            on_change=select_scanner_symbol),
                ft.Dropdown(label="Scanner timeframe", width=180, value=scanner[0].timeframe,
                            options=[ft.dropdown.Option(tf, tf) for tf in ("1m", "3m", "5m")],
                            on_change=select_scanner_timeframe),
                ft.Dropdown(label="Chart history bars", width=190,
                            value=str(chart_window[0]),
                            options=[ft.dropdown.Option(str(n), str(n) + " bars")
                                     for n in WINDOWS],
                            on_change=change_chart_window),
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
                                             selected_equities=state.selected,
                                             limit=chart_window[0]))],
                            stroke_width=2, curved=False)],
                        expand=True),
                    height=150, padding=5,
                )] if len(chart_points(
                    candle_history, scanner[0].symbol, scanner[0].timeframe,
                    selected_equities=state.selected,
                    limit=chart_window[0])) >= 2 else
                   [ft.Text("Scanner chart WAIT · completed candle history unavailable")]),
                ft.Text("Completed OHLC candles · historical / unverified",
                        size=14, color=MUTED),
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
                        size=14, color=MUTED),
                *[ft.Text(f"{label}: {value}") for label, value in
                  filter_evidence.rows(scanner[0].symbol, scanner[0].timeframe,
                                       selected_equities=state.selected)[:5]],
                ft.Text("Sixth filter: reserved / blank"),
                ft.Text(shared_filter_context(
                    filter_evidence, scanner[0].symbol, scanner[0].timeframe,
                    selected_equities=state.selected)["coverage_label"],
                    color=MUTED, size=14),
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
                ft.Row([
                    ft.Text("CE / PE option-chain · historical only",
                            color=GOLD, size=16,
                            weight=ft.FontWeight.BOLD, expand=True),
                    ft.IconButton(icon=ft.Icons.HELP_OUTLINE, icon_color=GOLD,
                                  tooltip="Options Help",
                                  on_click=lambda e: open_help("Options")),
                ]),
                ft.Text("Trusted completed cache only", color=MUTED, size=14),
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
                ft.Row([
                    ft.Text("Super Five · verified signals WAIT", color=GOLD,
                            size=16, weight=ft.FontWeight.BOLD, expand=True),
                    ft.IconButton(icon=ft.Icons.HELP_OUTLINE, icon_color=GOLD,
                                  tooltip="Super Five Help",
                                  on_click=lambda e: open_help("Super Five")),
                ]),
                ft.Text("Historical technical shortlist · not Super Five signals",
                        color=MUTED, size=14),
                *[v1_card(ft, [
                    ft.Text(item["label"], size=14, color=WHITE),
                    ft.Text(shared_filter_context(
                        filter_evidence, item["symbol"], "3m",
                        selected_equities=state.selected)["coverage_label"],
                        color=MUTED, size=14),
                    ft.TextButton("View historical 3m chart",
                                  on_click=lambda e, symbol=item["symbol"]:
                                  select_historical_candidate(symbol)),
                ]) for item in historical_shortlist(
                    candle_history, state.selected, timeframe="3m")],
                ft.Text("Shortlist unavailable · no validated historical votes",
                        color=MUTED, size=14) if not historical_shortlist(
                    candle_history, state.selected, timeframe="3m") else
                ft.Text("Historical selection only · not a live trade signal",
                        color=MUTED, size=14),
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
            def open_watchlist_chart(symbol):
                """Select an approved equity in Scanner without a data fetch."""
                try:
                    scanner[0] = choose(scanner[0], state, symbol=symbol,
                                        timeframe="3m")
                    status.value = ("Watchlist 3m chart selected locally"
                                    if save_scanner() else
                                    "Watchlist 3m chart selected for session")
                    current[0] = 0
                    page.navigation_bar.selected_index = 0
                except ScannerError:
                    status.value = "Share no longer selected for chart"
                render()
                page.update()
            def switch_group(e):
                group[0] = int(e.control.value)
                watch_search[0] = ""
                render()
                page.update()
            def apply_search(e):
                query = e.control.value or ""
                if len(query) > 64:
                    status.value = "Search text too long (64 characters max)"
                    return
                watch_search[0] = query
                render()
                page.update()
            content.controls = [
                ft.Row([
                    ft.Text("Watchlist", size=19, color=GOLD,
                            weight=ft.FontWeight.BOLD, expand=True),
                    ft.IconButton(icon=ft.Icons.HELP_OUTLINE, icon_color=GOLD,
                                  tooltip="Watchlist Help",
                                  on_click=lambda e: open_help("Watchlist")),
                ]),
                ft.Text(f"{selected_equity_plan(state)['equity_count']}/70 unique equities · 3 indexes separate"),
                ft.Dropdown(label="Watchlist", width=190, value=str(group[0]),
                            options=[ft.dropdown.Option(str(i), f"Watchlist {i+1}") for i in range(5)],
                            on_change=switch_group),
                ft.Row([symbol, ft.ElevatedButton("Add", on_click=add)]),
                ft.TextField(label="Search in selected list",
                             hint_text="e.g. HDFCBANK",
                             value=watch_search[0],
                             dense=True, text_size=16,
                             on_submit=apply_search),
                ft.Text("Search locally · press Enter · no network request",
                        color=MUTED, size=14),
                *[v1_card(ft, [
                        ft.Row([
                            ft.Text(row["symbol"] + "  " + row["price"],
                                    color=GOLD, size=16,
                                    weight=ft.FontWeight.BOLD, expand=True),
                            ft.TextButton("Chart",
                                          on_click=lambda e, item=row["symbol"]:
                                          open_watchlist_chart(item)),
                            ft.TextButton("Remove",
                                          on_click=lambda e, item=row["symbol"]: remove(e, item)),
                        ], spacing=4),
                        ft.Text(row["candle"], size=14, color=WHITE),
                        ft.Text(row["filter_text"], size=14, color=MUTED),
                    ]) for row in watchlist_rows(
                    filtered_watchlist_symbols(state.groups[group[0]], watch_search[0]),
                    quote_view, evidence_inbox,
                    selected_equities=state.selected)],
            ]
        else:
            def choose_help(e):
                selected = e.control.value
                if selected in ("Dashboard", "Watchlist", "Scanner", "Super Five",
                                "Options", "Filters", "Settings"):
                    help_topic[0] = selected
                render()
                page.update()

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
            def calculate_paper_preview(e):
                try:
                    result = preview_manual_paper_risk(
                        paper_inputs["side"], paper_inputs["entry"],
                        paper_inputs["quantity"], paper_inputs["stop_pct"],
                        paper_inputs["target_pct"], paper_inputs["capital"],
                        paper_inputs["max_risk"], paper_inputs["risk_pct"])
                    paper_result[0] = (
                        "PAPER ONLY · Stop ₹" + f'{result["stop"]:,.2f}' +
                        " · Target ₹" + f'{result["target"]:,.2f}' +
                        " · Planned risk ₹" + f'{result["planned_risk"]:,.2f}' +
                        " · No orders")
                except (ValueError, TypeError, OverflowError):
                    paper_result[0] = "Invalid paper inputs / risk exceeds limit; no orders"
                render()
                page.update()
            def prepare_local_backup(e):
                backup_text[0] = export_local_backup(
                    state, scanner[0], smart[0], analysis_slots[0])
                backup_confirm[0] = False
                status.value = "Local preference backup prepared; copy it yourself"
                render()
                page.update()
            def restore_local_backup(e):
                if not backup_confirm[0]:
                    status.value = "Confirm local-only restore before applying"
                    page.update()
                    return
                if storage_error or smart_error or scanner_error or analysis_error:
                    status.value = "Current local save is invalid; existing backup preserved"
                    page.update()
                    return
                try:
                    new_watchlists, new_scanner, new_smart, new_slots = (
                        parse_local_backup(backup_text[0]))
                except LocalBackupError:
                    status.value = "Rejected malformed or nonlocal preference backup"
                    page.update()
                    return
                # Every section is validated BEFORE any state replacement.
                state.groups = new_watchlists.groups
                scanner[0] = new_scanner
                smart[0] = new_smart
                analysis_slots[0] = new_slots
                quote_view.forget_removed(state.selected)
                evidence_inbox.forget_removed(state.selected)
                watch_search[0] = ""
                group[0] = 0
                backup_confirm[0] = False
                backup_text[0] = ""
                saved = all((save_local(), save_scanner(),
                             save_smart(), save_analysis()))
                status.value = ("Local preferences restored on device" if saved
                                else "Restored for session; some device saves failed")
                render()
                page.update()
            content.controls = [
                ft.Text("Settings", size=19, color=GOLD, weight=ft.FontWeight.BOLD),
                ft.Text("Smart Data & Master Control — app-owned", color=MUTED),
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
                ft.Text("Master Device Control", size=16, color=GOLD,
                        weight=ft.FontWeight.BOLD),
                ft.Text("4-phone target: 1 Master + 3 delegated · offline policy only"),
                ft.Text("Enable / Disable / Revoke require verified device login"),
                ft.Text("Dhan token renewal only via authorized Master workflow"),
                ft.Text("Manual PAPER risk preview · no execution", color=GOLD,
                        weight=ft.FontWeight.BOLD),
                ft.Dropdown(label="Paper side", value=paper_inputs["side"],
                            width=160,
                            options=[ft.dropdown.Option("BUY", "BUY"),
                                     ft.dropdown.Option("SELL", "SELL")],
                            on_change=lambda e: paper_inputs.__setitem__(
                                "side", e.control.value)),
                ft.Row([
                    ft.TextField(label=label, value=paper_inputs[key],
                                 width=138, text_size=14,
                                 on_change=lambda e, key=key:
                                 paper_inputs.__setitem__(key, e.control.value or ""))
                    for key, label in (
                        ("entry", "Manual entry ₹"),
                        ("quantity", "Quantity"),
                        ("stop_pct", "Stop %"),
                        ("target_pct", "Target %"),
                        ("capital", "Paper capital ₹"),
                        ("max_risk", "Max planned risk ₹"),
                        ("risk_pct", "Max risk %"),
                    )
                ], wrap=True, spacing=5),
                ft.TextButton("Calculate paper risk (no orders)",
                              on_click=calculate_paper_preview),
                ft.Text(paper_result[0], size=14, color=MUTED),
                ft.Text("No BUY/SELL/EXIT, no broker, no automatic paper bot",
                        size=14, color=MUTED),
                ft.Text("System Health / Error Doctor", color=GOLD, weight=ft.FontWeight.BOLD),
                ft.Text("OFFLINE / provider not connected", color=MUTED),
                ft.Text("Error Doctor: " + " · ".join(diagnose(storage_error or smart_error or "unavailable")[:2]), color=MUTED),
                ft.Text("Next: " + diagnose(storage_error or smart_error or "unavailable")[2], color=MUTED),
                ft.Text("Help Doctor — local guide", color=GOLD, weight=ft.FontWeight.BOLD),
                ft.Dropdown(label="Help topic", width=250, value=help_topic[0],
                            options=[ft.dropdown.Option(topic, topic) for topic in
                                     ("Dashboard", "Watchlist", "Scanner", "Super Five",
                                      "Options", "Filters", "Settings")],
                            on_change=choose_help),
                v1_card(ft, [ft.Text(help_topic[0], color=GOLD, weight=ft.FontWeight.BOLD),
                             ft.Text(help_for(help_topic[0]), color=WHITE)]),
                ft.Text("Local preferences backup / restore", color=GOLD,
                        weight=ft.FontWeight.BOLD),
                ft.Text("Watchlists, Scanner, Smart Data, 3 analysis slots only. "
                        "No broker credentials, orders or server settings.",
                        color=MUTED, size=14),
                ft.TextButton("Prepare local backup", on_click=prepare_local_backup),
                ft.TextField(label="Local preference backup JSON",
                             value=backup_text[0], multiline=True,
                             min_lines=3, max_lines=5,
                             on_change=lambda e: backup_text.__setitem__(
                                 0, e.control.value or "")),
                ft.Checkbox(label="Confirm local-only restore",
                            value=backup_confirm[0],
                            on_change=lambda e: backup_confirm.__setitem__(
                                0, bool(e.control.value))),
                ft.TextButton("Restore local preferences",
                              on_click=restore_local_backup),
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
    page.add(v1_header(ft, APP_VERSION_NAME), status, ft.Divider(), content)
    render()
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
