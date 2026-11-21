"""Offline Android BUILDING capacity probe. Synthetic data only; no auth/network/provider."""
import asyncio
import json
import math
import time
import traceback
import flet as ft
from clone_day2_apply_queue import SmartApplyQueue, Update

INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")
FILTERS = ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")
SIZES = (10, 35, 54, 73)

def fixture(count):
    names = list(INDEXES) + ["TEST_EQ_%02d" % n for n in range(1, count - 2)]
    result = {}
    for i, symbol in enumerate(names):
        price = 100.0 + i * 1.7
        bars = []
        for j in range(180):
            opening = price + math.sin(j / 7) * 2
            close = opening + math.sin(j / 11) * 0.7
            bars.append({"t": 1700000000 + j * 60, "o": round(opening, 4),
                         "h": round(max(opening, close) + 0.4, 4),
                         "l": round(min(opening, close) - 0.4, 4),
                         "c": round(close, 4), "v": 1000 + j})
        result[symbol] = {"price": price, "1m": bars,
            "3m": [bars[x + 2] for x in range(0, 180, 3)],
            "5m": [bars[x + 4] for x in range(0, 180, 5)],
            "filters": {name: "WAIT / SYNTHETIC" for name in FILTERS}}
    return result

def prepare(count):
    t0 = time.perf_counter()
    payload = fixture(count)
    t1 = time.perf_counter()
    stock = {}
    for symbol, record in payload.items():
        for frame in ("1m", "3m", "5m"):
            bars = record[frame]
            assert bars and all(b["l"] <= b["o"] <= b["h"] and b["l"] <= b["c"] <= b["h"] for b in bars)
        stock[symbol] = record
    t2 = time.perf_counter()
    metrics = {}
    for symbol, record in stock.items():
        metrics[symbol] = {"direction": "UP" if record["3m"][-1]["c"] >= record["3m"][-2]["c"] else "DOWN",
                           "last": record["1m"][-1]["c"], "filters": record["filters"]}
    t3 = time.perf_counter()
    queue = SmartApplyQueue(max_pending=512)
    incoming = []
    for symbol, record in stock.items():
        specs = [("quote", "", record["price"])]
        specs += [("candle", frame, len(record[frame])) for frame in ("1m", "3m", "5m")]
        specs += [("filter_" + name, "", "WAIT") for name in FILTERS]
        specs.append(("assessment", "", metrics[symbol]["direction"]))
        for kind, frame, value in specs:
            incoming.append(Update("watchlist", symbol, kind, 1, value,
                                   timeframe=frame, completed=(kind == "candle")))
    r = queue.ingest_burst(incoming, batch_size=128)
    t4 = time.perf_counter()
    times = {"generate_ms": (t1-t0)*1000, "validate_stock_ms": (t2-t1)*1000,
             "synthetic_compute_ms": (t3-t2)*1000,
             "queue_ms": (t4-t3)*1000, "total_python_ms": (t4-t0)*1000}
    return stock, metrics, times, queue.health(), len(r.applied)

def main(page: ft.Page):
    page.title = "BOT KING V3 BUILDING CAPACITY TEST"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 12
    page.window_width = 430
    page.window_height = 820
    heading = ft.Text("BOT KING V3 | BUILDING CAPACITY LAB", size=19, weight=ft.FontWeight.BOLD, color="#D8B75E")
    note = ft.Text("OFFLINE TEST ONLY • 3 indexes + equities • 180 fake 1m candles each • five filter slots WAIT • zero Dhan requests", size=12)
    status = ft.Text("Select an instrument count to start", size=13)
    output = ft.Text("", size=12, selectable=True)
    items = ft.Column(spacing=3)
    timings = {}
    active = {"count": 0, "ready": False}
    ack = ft.ElevatedButton("SCREEN VISIBLE — STOP TIMER", disabled=True)

    async def run_case(e, count):
        ack.disabled = True
        active["ready"] = False
        status.value = "Preparing %s instruments..." % count
        items.controls.clear()
        output.value = ""
        page.update()
        await asyncio.sleep(0.05)
        try:
            start = time.perf_counter()
            stock, metrics, measures, health, applied = await asyncio.to_thread(prepare, count)
            after_python = time.perf_counter()
            # Create actual Flet controls; unlike dictionary-only GitHub benchmark.
            new_rows = []
            for sym, record in stock.items():
                row = ft.Container(
                    content=ft.Column([
                        ft.Text(sym + " | " + ("%.2f" % record["price"]) + " | 1m/3m/5m", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("3m " + metrics[sym]["direction"] + " | 5 filters WAIT | 180 source candles", size=11)
                    ], spacing=1), border=ft.border.all(1, "#555555"), border_radius=5, padding=6)
                new_rows.append(row)
            after_construct = time.perf_counter()
            items.controls = new_rows
            status.value = "Rendered controls submitted: %d / %d. Tap SCREEN VISIBLE after last row appears." % (len(new_rows), count)
            queue_issues = health["counts"]
            report = {
                "probe": "BOT_KING_V3_BUILDING_PHONE_TEST",
                "kind": "offline synthetic (not actual Dhan data, not real filter score)",
                "instruments": count, "equities": count - 3, "indexes": 3,
                "candles_per_instrument": {"1m": 180, "3m": 60, "5m": 36},
                "filter_slots": "five WAIT, sixth absent",
                "python_stages_ms": {k: round(v, 3) for k, v in measures.items()},
                "thread_wall_ms": round((after_python-start)*1000, 3),
                "flet_controls_construct_ms": round((after_construct-after_python)*1000, 3),
                "queue": queue_issues, "applied": applied,
                "note": "page.update is submission, NOT confirmed rendered pixels"}
            output.value = json.dumps(report, indent=2)
            page.update()
            submitted = time.perf_counter()
            timings.clear()
            timings.update({"start": start, "submitted": submitted, "report": report})
            active["count"] = count
            active["ready"] = True
            ack.disabled = False
            page.update()
        except Exception:
            status.value = "ERROR — test interrupted"
            output.value = traceback.format_exc()
            page.update()

    async def on_ack(e):
        if not active["ready"]:
            return
        clicked = time.perf_counter()
        data = timings["report"]
        data["flet_submit_until_ack_ms"] = round((clicked-timings["submitted"])*1000, 3)
        data["test_start_until_ack_ms"] = round((clicked-timings["start"])*1000, 3)
        data["ack_definition"] = "manual user tap after observing final row; includes human reaction time, NOT exact Flutter raster duration"
        status.value = "ACK recorded for %d instruments. Review timings below." % active["count"]
        output.value = json.dumps(data, indent=2)
        ack.disabled = True
        active["ready"] = False
        page.update()

    ack.on_click = on_ack
    buttons = ft.Row(wrap=True, spacing=5)
    for count in SIZES:
        async def click(e, n=count):
            await run_case(e, n)
        buttons.controls.append(ft.ElevatedButton(str(count) + " instruments", on_click=click))
    page.add(heading, note, buttons, status, ack,
             ft.Text("ERROR / HEALTH DOCTOR REPORT (select text)", weight=ft.FontWeight.BOLD),
             output, ft.Text("ACTUAL MOUNTED WATCHLIST ROWS", weight=ft.FontWeight.BOLD), items)

ft.app(target=main)
