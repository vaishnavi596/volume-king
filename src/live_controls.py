"""Manual real-money controls. Every submit/cancel requires its own confirmation."""
import asyncio
import math
import uuid

import flet as ft
from market_feed import FeedError, SessionExpired
from server_feed import LiveOperationError


class LiveOrderControls:
    def __init__(self, page, feed):
        self.page, self.feed = page, feed
        self.busy = False
        self.generation = 0
        self.capabilities = {}
        self.review = None
        self.dialog = None
        self.linked_options = False
        self.on_contract_change = None
        self.on_segment_change = None
        self.ack = ft.Checkbox(label="I understand: real money, intraday LIMIT orders, no automatic SL/target", value=False)
        self.phrase = ft.TextField(label="Type ENABLE LIVE TRADING to arm for 15 minutes")
        self.segment = ft.Dropdown(label="Live segment", value="Options", options=[ft.dropdown.Option(x) for x in ("Options", "Cash")])
        self.symbol = ft.TextField(label="Live underlying symbol", value="NIFTY")
        self.expiry = ft.TextField(label="Live option expiry YYYY-MM-DD")
        self.strike = ft.TextField(label="Live option strike", keyboard_type=ft.KeyboardType.NUMBER)
        self.option_type = ft.Dropdown(label="Live option type", value="CE", options=[ft.dropdown.Option(x) for x in ("CE", "PE")])
        self.side = ft.Dropdown(label="Live action", value="BUY", options=[ft.dropdown.Option(x) for x in ("BUY", "SELL")])
        self.units = ft.TextField(label="Live lots (options) / shares (cash)", value="1", keyboard_type=ft.KeyboardType.NUMBER)
        self.price = ft.TextField(label="Live LIMIT price (INR)", keyboard_type=ft.KeyboardType.NUMBER)
        self.status = ft.Text("Live trading OFF. Connect through your server, check capabilities, then arm explicitly.", color="#FFCB12", size=13)
        self.limit_text = ft.Text("Server limits and current account will appear after checking live access.", size=12)
        self.orders = ft.Column(spacing=6)
        self.positions = ft.Column(spacing=6)
        self.submit_busy = ft.Text("", size=12)
        for field in (self.segment, self.symbol, self.expiry, self.strike, self.option_type, self.side, self.units, self.price):
            field.on_change = self.edited
        self.segment.on_change = self.segment_changed
        self.segment_changed(None)

    def task(self, fn, *args):
        self.page.run_task(fn, *args)

    def update(self):
        self.page.update()

    def edited(self, e=None):
        self.generation += 1
        self.review = None
        self.close_dialog()
        if self.on_contract_change:self.on_contract_change()

    def segment_changed(self, e=None):
        if e is not None:
            self.price.value="";self.units.value="1"
        for field in (self.expiry, self.strike, self.option_type):
            field.visible = self.segment.value == "Options" and not (self.linked_options and field is self.expiry)
            wrapper = getattr(field, "_bk_help_wrapper", None)
            if wrapper is not None:wrapper.visible = field.visible
        self.edited()
        self.symbol.visible = not (self.linked_options and self.segment.value == "Options")
        wrapper=getattr(self.symbol,"_bk_help_wrapper",None)
        if wrapper is not None:wrapper.visible=self.symbol.visible
        if e is not None and self.on_segment_change:self.on_segment_change()
        if e is not None:self.update()

    def close_dialog(self):
        if self.dialog:
            if hasattr(self.page, "close"):self.page.close(self.dialog)
            else:self.dialog.open = False
            self.dialog = None

    def reset(self, message="Live trading disarmed. Existing broker orders/positions remain at Angel One."):
        self.generation += 1
        self.review = None
        self.capabilities = {}
        self.phrase.value = ""
        self.ack.value = False
        self.status.value = message
        self.close_dialog()

    def pause(self):
        self.reset("App backgrounded: live controls disarmed locally. Recheck broker orders and arm again after returning.")
        if self.feed.connected and self.feed.server:self.task(self.disarm)

    def error(self, exc):
        if isinstance(exc, SessionExpired):
            self.reset("Broker session expired. Reconnect and recheck orders before arming again.")
        elif isinstance(exc, LiveOperationError):
            self.status.value = str(exc)
        else:
            self.status.value = "Operation could not be verified. Refresh real broker orders before reviewing another order."

    async def refresh(self):
        if self.busy:return
        self.busy = True
        generation, epoch = self.generation, self.feed.epoch
        try:
            caps = await asyncio.to_thread(self.feed.live, "capabilities")
            if (generation, epoch) != (self.generation, self.feed.epoch):return
            self.capabilities = caps
            if not caps.get("enabled"):
                self.status.value = "Live trading is disabled on this server. Market data/Paper remain available."
                return
            self.limit_text.value = ("Account ending " + caps.get("account_hint", "") + " • maximum INR " + caps["max_order_value"]
                                     + "/order • " + str(caps["max_daily_entries"]) + " BUY entries/day • INTRADAY LIMIT only")
            rows = await asyncio.to_thread(self.feed.live, "orders")
            positions = await asyncio.to_thread(self.feed.live, "positions")
            if (generation, epoch) != (self.generation, self.feed.epoch):return
            self.orders.controls = []
            for row in rows:
                text = (row["symbol"] + " • " + row["side"] + " " + str(row["quantity"]) + " @ " + row["limit_price"]
                        + " • " + row["state"] + " • filled " + str(row["filled"]) + " • broker ID " + (row["broker_id"] or "unknown"))
                self.orders.controls.append(ft.Text(text, size=12))
                if row["broker_id"] and row["state"] not in ("COMPLETE", "REJECTED", "CANCELLED"):
                    self.orders.controls.append(ft.OutlinedButton("Review cancellation", on_click=lambda e, r=dict(row): self.review_cancel(r)))
            if not rows:self.orders.controls = [ft.Text("No BOT KING live order records for this account.", size=12)]
            self.positions.controls = [ft.Text(" • ".join(str(row.get(k, "")) for k in ("tradingsymbol", "producttype", "netqty", "pnl")), size=12) for row in positions] or [ft.Text("Broker returned no open positions.", size=12)]
            self.status.value = "Live controls " + ("ARMED for this session" if caps.get("armed") else "DISARMED") + ". Order acknowledgement is not a fill; check filled quantity and broker positions."
        except Exception as exc:
            if (generation, epoch) == (self.generation, self.feed.epoch):self.error(exc)
        finally:
            self.busy = False
            self.update()

    async def arm(self):
        if self.busy:return
        if not self.ack.value or self.phrase.value != "ENABLE LIVE TRADING":
            self.status.value = "Read the real-money acknowledgement and type ENABLE LIVE TRADING exactly."
            self.update();return
        self.busy = True
        generation, epoch = self.generation, self.feed.epoch
        try:
            caps = await asyncio.to_thread(self.feed.live, "arm", {"confirmation": self.phrase.value})
            if (generation, epoch) != (self.generation, self.feed.epoch):
                # A background/reset event can overtake the HTTP response. Undo an
                # obsolete arm on the same session without touching a newer login.
                if epoch == self.feed.epoch:
                    try:await asyncio.to_thread(self.feed.live, "disarm")
                    except Exception:pass
                return
            self.capabilities = caps
            self.phrase.value = ""
            self.status.value = "Live orders ARMED for 15 minutes. Each order still requires a fresh review and explicit confirmation."
        except Exception as exc:
            if (generation, epoch) == (self.generation, self.feed.epoch):self.error(exc)
        finally:self.busy = False;self.update()

    async def disarm(self):
        self.reset()
        try:await asyncio.to_thread(self.feed.live, "disarm")
        except Exception:
            self.status.value = "Disarmed locally; server could not be reached. Existing orders remain at broker. Recheck before trading."
        self.update()

    def use_options(self, symbol, expiry, strike, option_type):
        self.segment.value = "Options";self.segment_changed()
        self.symbol.value = symbol;self.expiry.value = expiry;self.strike.value = str(strike or "");self.option_type.value = option_type
        self.price.value = ""  # Never turn a historical option premium into an automatic live limit.
        self.review = None
        if self.on_contract_change:self.on_contract_change()
        self.status.value = "Selected option copied. Enter your live limit price, then review; no order has been sent."

    async def preview(self):
        if self.busy:return
        self.review = None
        if not self.ack.value:
            self.status.value = "Acknowledge the real-money controls before reviewing a live order."
            self.update();return
        self.busy = True
        generation = self.generation
        try:
            price = float(self.price.value)
            units = int(self.units.value)
            if not math.isfinite(price) or price <= 0 or units < 1:raise ValueError()
            intent = {"symbol": self.symbol.value.strip().upper(), "segment": self.segment.value,
                      "side": self.side.value, "units": units, "limit_price": price, "option_type": self.option_type.value}
            if self.segment.value == "Options":intent.update(expiry=self.expiry.value.strip(), strike=float(self.strike.value))
            epoch = self.feed.epoch
            data = await asyncio.to_thread(self.feed.live, "preview", intent)
            if epoch != self.feed.epoch or generation != self.generation or not self.ack.value:return
            self.review = {"data": data, "request_id": uuid.uuid4().hex, "epoch": epoch}
            summary = ("REAL MONEY — account ending " + data["account_hint"] + "\n" + data["side"] + " " + data["symbol"]
                       + "\nQuantity: " + str(data["quantity"]) + " (lot size " + str(data["lot_size"]) + ")"
                       + "\nLIMIT INR " + data["limit_price"] + " • value INR " + data["notional"]
                       + "\nINTRADAY • verified quote INR " + data["ltp"]
                       + "\nNo attached SL/target or automatic monitoring. This review expires in 60 seconds.")
            self.dialog = ft.AlertDialog(modal=True, title=ft.Text("Confirm real broker order"), content=ft.Text(summary), actions=[
                ft.TextButton("Back", on_click=lambda e:self.close_dialog()),
                ft.ElevatedButton("PLACE REAL ORDER", bgcolor="#FF5B7F", color="#080F18", on_click=lambda e:self.task(self.submit))])
            if hasattr(self.page, "open"):self.page.open(self.dialog)
            else:self.page.dialog=self.dialog;self.dialog.open=True
        except (ValueError, TypeError):self.status.value="Enter a valid quantity, limit price and listed option strike/expiry."
        except Exception as exc:self.error(exc)
        finally:self.busy=False;self.update()

    async def submit(self):
        if self.busy or not self.review:return
        review = self.review
        self.review = None  # One click consumes the local review, including on network failure.
        self.close_dialog()
        if review["epoch"] != self.feed.epoch:
            self.status.value="Session changed. Reconnect and review again.";self.update();return
        self.busy=True
        self.submit_busy.value="Submitting once. Do not create another order while the response is uncertain."
        try:
            result=await asyncio.to_thread(self.feed.live,"submit",{"ticket":review["data"]["ticket"],"request_id":review["request_id"],"confirmation":"PLACE REAL ORDER"})
            self.status.value="Broker submission: "+result["state"]+" • ID "+(result["broker_id"] or "unknown")+". Refresh orders to verify fills."
        except Exception as exc:self.error(exc)
        finally:self.busy=False;self.submit_busy.value="";self.update()
        await self.refresh()

    def review_cancel(self, row):
        self.close_dialog()
        self.dialog=ft.AlertDialog(modal=True,title=ft.Text("Cancel real broker order?"),content=ft.Text(row["symbol"]+" • "+row["side"]+" • broker ID "+row["broker_id"]+"\nAlready-filled quantity cannot be cancelled."),actions=[
            ft.TextButton("Back",on_click=lambda e:self.close_dialog()),
            ft.ElevatedButton("CANCEL REAL ORDER",on_click=lambda e:self.task(self.cancel,row["request_id"]))])
        if hasattr(self.page,"open"):self.page.open(self.dialog)
        else:self.page.dialog=self.dialog;self.dialog.open=True;self.update()

    async def cancel(self, request_id):
        if self.busy:return
        self.close_dialog();self.busy=True
        try:
            result=await asyncio.to_thread(self.feed.live,"cancel",{"request_id":request_id,"confirmation":"CANCEL REAL ORDER"})
            self.status.value="Cancellation request: "+result["state"]+". Refresh to verify final broker state."
        except Exception as exc:self.error(exc)
        finally:self.busy=False;self.update()
        await self.refresh()

    def content(self):
        return ft.Column([self.status,self.limit_text,self.ack,self.phrase,
            ft.Row([ft.ElevatedButton("Arm live orders",on_click=lambda e:self.task(self.arm)),ft.OutlinedButton("Disarm live orders",on_click=lambda e:self.task(self.disarm))],wrap=True),
            self.segment,self.symbol,self.expiry,self.strike,self.option_type,self.side,self.units,self.price,
            ft.ElevatedButton("REVIEW LIVE ORDER",on_click=lambda e:self.task(self.preview),bgcolor="#FFCB12",color="#080F18"),self.submit_busy,
            ft.OutlinedButton("Refresh real orders / positions",on_click=lambda e:self.task(self.refresh)),
            ft.Text("BOT KING real order records",weight=ft.FontWeight.BOLD),self.orders,
            ft.Text("Current broker positions • symbol / product / net quantity / P&L",weight=ft.FontWeight.BOLD),self.positions,
            ft.Text("SELL closes confirmed long INTRADAY quantity only. No opening shorts, AMO, automatic re-entry, attached SL/target or unattended protection. Manage protective orders in Angel One.",size=12)],spacing=8,horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
