"""Confirmed, long-only/manual LIMIT orders. Never retry an uncertain submit."""
import hashlib
import json
import math
import os
import secrets
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from market_feed import AngelFeed, FeedError, SessionExpired

IST = timezone(timedelta(hours=5, minutes=30))


class TradingError(FeedError):
    pass


class BrokerRejected(TradingError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


class AngelTradingFeed(AngelFeed):
    TRADE_PATHS = {
        "orders": ("GET", "/rest/secure/angelbroking/order/v1/getOrderBook"),
        "positions": ("GET", "/rest/secure/angelbroking/order/v1/getPosition"),
        "funds": ("GET", "/rest/secure/angelbroking/user/v1/getRMS"),
        "place": ("POST", "/rest/secure/angelbroking/order/v1/placeOrder"),
        "cancel": ("POST", "/rest/secure/angelbroking/order/v1/cancelOrder"),
    }

    def trade_request(self, kind, payload=None):
        if not self.connected or kind not in self.TRADE_PATHS:
            raise TradingError("Connect Angel One first")
        method, path = self.TRADE_PATHS[kind]
        headers = {"Content-Type": "application/json", "Accept": "application/json",
                   "X-PrivateKey": self.key, "X-UserType": "USER", "X-SourceID": "WEB",
                   "X-ClientLocalIP": self.local_ip, "X-ClientPublicIP": self.public_ip,
                   "X-MACAddress": self.mac, "Authorization": "Bearer " + self.token}
        request = urllib.request.Request(self.ROOT + path, headers=headers, method=method,
                                         data=json.dumps(payload).encode() if method == "POST" else None)
        # No automatic retry, including for timeout, 5xx, malformed JSON or redirect.
        try:
            with self.lock:
                with urllib.request.build_opener(NoRedirect()).open(request, timeout=15) as response:
                    data = json.loads(response.read(4 * 1024 * 1024))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise BrokerRejected("Broker access denied; verify API permissions/static IP") from None
            raise TradingError("Broker response uncertain; reconcile orders before retrying") from None
        except Exception:
            raise TradingError("Broker response uncertain; reconcile orders before retrying") from None
        if data.get("status") is not True:
            if str(data.get("errorcode")) in ("AG8001", "AG8002"):
                raise SessionExpired("Broker session expired")
            raise BrokerRejected("Broker rejected the request; check Angel One order book")
        return data.get("data")

    def order_book(self): return self.trade_request("orders") or []
    def positions(self): return self.trade_request("positions") or []
    def funds(self): return self.trade_request("funds") or {}
    def place_limit(self, payload): return self.trade_request("place", payload)
    def cancel_order(self, order_id): return self.trade_request("cancel", {"variety": "NORMAL", "orderid": order_id})


class OrderJournal:
    """Durable idempotency boundary, written before a broker side effect."""
    def __init__(self, path):
        self.path = str(path)
        self.lock = threading.RLock()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("CREATE TABLE IF NOT EXISTS orders (account TEXT, request_id TEXT, day TEXT, state TEXT, payload TEXT, broker_id TEXT DEFAULT '', filled INTEGER DEFAULT 0, average_price TEXT DEFAULT '', PRIMARY KEY(account, request_id))")
        os.chmod(self.path, 0o600)

    def connection(self):
        return sqlite3.connect(self.path, timeout=5)

    def rows(self, account):
        with self.lock, self.connection() as db:
            data = db.execute("SELECT request_id,day,state,payload,broker_id,filled,average_price FROM orders WHERE account=? ORDER BY rowid DESC LIMIT 200", (account,)).fetchall()
        return [dict(request_id=r[0], day=r[1], state=r[2], payload=json.loads(r[3]), broker_id=r[4], filled=r[5], average_price=r[6]) for r in data]

    def reserve(self, account, request_id, day, payload):
        with self.lock, self.connection() as db:
            db.execute("INSERT INTO orders(account,request_id,day,state,payload) VALUES(?,?,?,?,?)",
                       (account, request_id, day, "SUBMITTING", json.dumps(payload, sort_keys=True)))

    def update(self, account, request_id, state, broker_id="", filled=0, average_price=""):
        with self.lock, self.connection() as db:
            db.execute("UPDATE orders SET state=?,broker_id=?,filled=?,average_price=? WHERE account=? AND request_id=?",
                       (state, str(broker_id), int(filled), str(average_price), account, request_id))


class LiveTrading:
    TERMINAL = {"COMPLETE", "REJECTED", "CANCELLED"}
    UNCERTAIN = {"SUBMITTING", "UNKNOWN", "CANCEL_UNKNOWN"}

    def __init__(self, feed, journal, enabled=False, clock=time.time,
                 max_order_value=25000, max_entries=2):
        self.feed, self.journal, self.enabled, self.clock = feed, journal, bool(enabled), clock
        self.max_value = Decimal(str(max_order_value))
        self.max_entries = int(max_entries)
        if not self.max_value.is_finite() or not 0 < self.max_value <= 1000000 or not 1 <= self.max_entries <= 20:
            raise ValueError("Invalid live risk limits")
        self.armed_until = 0
        self.account = ""
        self.previews = {}
        self.lock = threading.RLock()

    def bind_account(self, client):
        self.account = hashlib.sha256(client.strip().upper().encode()).hexdigest()
        self.disarm()

    def disarm(self):
        self.armed_until = 0
        self.previews.clear()

    def capabilities(self):
        return {"enabled": self.enabled, "armed": self.enabled and self.clock() < self.armed_until,
                "armed_until": self.armed_until, "max_order_value": str(self.max_value),
                "max_daily_entries": self.max_entries, "order_types": ["LIMIT"],
                "product": "INTRADAY", "automatic_protection": False,
                "account_hint": self.feed.client[-4:] if self.feed.connected else ""}

    def arm(self, phrase):
        if not self.enabled or not self.feed.connected or not self.account:
            raise TradingError("Live trading is not enabled on this server/session")
        if phrase != "ENABLE LIVE TRADING":
            raise TradingError("Type ENABLE LIVE TRADING to arm real-money orders")
        self.armed_until = self.clock() + 900
        return self.capabilities()

    def require_armed(self):
        if not self.enabled or not self.feed.connected or not self.account or self.clock() >= self.armed_until:
            raise TradingError("Arm live trading for this session before reviewing or submitting an order")

    @staticmethod
    def amount(value):
        try:
            value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            raise TradingError("Invalid order number") from None
        if not value.is_finite() or value <= 0:
            raise TradingError("Order numbers must be positive and finite")
        return value

    def market_time(self, side):
        now = datetime.fromtimestamp(self.clock(), IST)
        end = (15, 25) if side == "BUY" else (15, 29)
        if now.weekday() >= 5 or not (9, 15) <= (now.hour, now.minute) < end:
            raise TradingError("Outside live order hours; no after-market order will be sent")
        return now.date().isoformat()

    def contract(self, intent):
        matches = []
        for row in self.feed.master():
            if intent["segment"] == "Cash":
                if row.get("exch_seg") != "NSE" or row.get("symbol") != intent["symbol"] + "-EQ": continue
            else:
                if row.get("exch_seg") not in ("NFO", "BFO") or row.get("name") != intent["symbol"]: continue
                if row.get("instrumenttype") not in ("OPTIDX", "OPTSTK") or not row.get("symbol", "").endswith(intent["option_type"]): continue
                try:
                    expiry = datetime.strptime(row["expiry"], "%d%b%Y").date().isoformat()
                    if expiry != intent.get("expiry") or Decimal(row["strike"]) / 100 != self.amount(intent.get("strike")): continue
                except (KeyError, ValueError, InvalidOperation): continue
            matches.append(row)
        if len(matches) != 1:
            raise TradingError("Choose one exact broker-listed cash/option contract")
        return matches[0]

    def prepare(self, intent):
        self.require_armed()
        day = self.market_time(intent["side"])
        if intent["segment"] == "Options":
            if not intent.get("expiry") or intent["expiry"] < day:
                raise TradingError("Select a current broker-listed expiry")
        contract = self.contract(intent)
        price = self.amount(intent["limit_price"])
        lot_size = int(contract["lotsize"]) if intent["segment"] == "Options" else 1
        units = int(intent["units"])
        if units != intent["units"] or lot_size <= 0 or not 1 <= units <= (5 if intent["segment"] == "Options" else 1000):
            raise TradingError("Enter 1–5 lots or 1–1000 cash shares")
        quantity = units * lot_size
        tick = self.amount(contract.get("tick_size")) / 100
        if price % tick:
            raise TradingError("Limit price must match the listed contract tick size")
        notional = price * quantity
        if notional > self.max_value:
            raise TradingError("Order exceeds the server's per-order value limit")
        quotes = self.feed.quotes(contract["exch_seg"], [str(contract["token"])])
        if len(quotes) != 1:
            raise TradingError("Verified broker quote unavailable")
        quote = quotes[0]
        stamp = self.feed.timestamp(quote.get("exchFeedTime"))
        if stamp is None or not 0 <= self.clock() - stamp <= 90:
            raise TradingError("Broker quote is stale; live order blocked")
        ltp = self.amount(quote.get("ltp"))
        if abs(price - ltp) / ltp > Decimal("0.10"):
            raise TradingError("Limit price differs more than 10% from the verified broker quote")
        rows = self.journal.rows(self.account)
        if any(r["state"] in self.UNCERTAIN for r in rows):
            raise TradingError("An earlier order is uncertain; reconcile before sending another order")
        if intent["side"] == "BUY":
            entries = sum(r["day"] == day and r["payload"]["transactiontype"] == "BUY" and r["state"] != "REJECTED" for r in rows)
            if entries >= self.max_entries:
                raise TradingError("Daily live entry limit reached")
            available = Decimal(str(self.feed.funds().get("availablecash", "0")))
            if not available.is_finite() or available < notional * Decimal("1.01"):
                raise TradingError("Available broker cash does not cover order value plus the cash buffer")
        else:
            positions = self.feed.positions()
            owned = sum(int(p.get("netqty", 0)) for p in positions
                        if str(p.get("symboltoken")) == str(contract["token"]) and p.get("exchange") == contract["exch_seg"] and p.get("producttype") == "INTRADAY")
            reserved = 0
            for order in self.feed.order_book():
                if str(order.get("symboltoken")) == str(contract["token"]) and order.get("exchange") == contract["exch_seg"] and order.get("transactiontype") == "SELL" and order.get("producttype") == "INTRADAY" and str(order.get("status", "")).upper() not in self.TERMINAL:
                    reserved += max(0, int(order.get("quantity", 0)) - int(order.get("filledshares", 0)))
            if quantity > owned - reserved:
                raise TradingError("SELL is allowed only to close confirmed long intraday quantity not reserved by another exit")
        payload = {"variety": "NORMAL", "tradingsymbol": contract["symbol"],
                   "symboltoken": str(contract["token"]), "transactiontype": intent["side"],
                   "exchange": contract["exch_seg"], "ordertype": "LIMIT", "producttype": "INTRADAY",
                   "duration": "DAY", "price": str(price), "squareoff": "0", "stoploss": "0", "quantity": str(quantity)}
        return payload, {"symbol": contract["symbol"], "exchange": contract["exch_seg"],
                         "side": intent["side"], "quantity": quantity, "lot_size": lot_size,
                         "limit_price": str(price), "notional": str(notional), "ltp": str(ltp),
                         "quote_timestamp": stamp, "product": "INTRADAY", "order_type": "LIMIT",
                         "attached_sl_target": False, "account_hint": self.feed.client[-4:]}

    def preview(self, intent):
        with self.lock:
            self.reconcile()
            _, summary = self.prepare(intent)
            now = self.clock()
            self.previews = {k: v for k, v in self.previews.items() if now < v["expires"]}
            if len(self.previews) >= 5: self.previews.clear()
            ticket = secrets.token_urlsafe(24)
            self.previews[ticket] = {"intent": dict(intent), "expires": now + 60, "account": self.account}
            return dict(summary, ticket=ticket, expires_at=now + 60)

    def submit(self, ticket, request_id, confirm):
        if confirm != "PLACE REAL ORDER":
            raise TradingError("Explicit real-order confirmation required")
        with self.lock:
            # A duplicate request returns the durable result even after ticket/session arm expiry.
            previous = next((r for r in self.journal.rows(self.account) if r["request_id"] == request_id), None)
            if previous:
                return self.public_order(previous)
            self.require_armed()
            review = self.previews.pop(ticket, None)
            if not review or review["account"] != self.account or self.clock() >= review["expires"]:
                raise TradingError("Review expired; obtain a new preview and confirm again")
            payload, summary = self.prepare(review["intent"])
            payload["ordertag"] = "BK" + secrets.token_hex(8)
            day = self.market_time(payload["transactiontype"])
            self.journal.reserve(self.account, request_id, day, payload)
            try:
                response = self.feed.place_limit(payload)
                order_id = response.get("orderid") if isinstance(response, dict) else None
                if not order_id:
                    raise TradingError("Missing broker order acknowledgement")
                self.journal.update(self.account, request_id, "ACKNOWLEDGED", str(order_id))
            except BrokerRejected:
                self.journal.update(self.account, request_id, "REJECTED")
            except Exception:
                self.journal.update(self.account, request_id, "UNKNOWN")
            return self.public_order(next(r for r in self.journal.rows(self.account) if r["request_id"] == request_id))

    @staticmethod
    def public_order(row):
        payload = row["payload"]
        return {k: row[k] for k in ("request_id", "day", "state", "broker_id", "filled", "average_price")} | {
            "symbol": payload["tradingsymbol"], "side": payload["transactiontype"],
            "quantity": int(payload["quantity"]), "limit_price": payload["price"],
            "exchange": payload["exchange"], "product": payload["producttype"]}

    def reconcile(self):
        if not self.account: raise TradingError("Connect a broker account first")
        book = self.feed.order_book()  # Failure is propagated; never invent order/position state.
        for row in self.journal.rows(self.account):
            match = next((o for o in book if (row["broker_id"] and str(o.get("orderid")) == row["broker_id"]) or o.get("ordertag") == row["payload"].get("ordertag")), None)
            if match:
                state = str(match.get("status", "UNKNOWN")).upper().replace(" ", "_")
                if state not in self.TERMINAL | {"OPEN", "TRIGGER_PENDING", "VALIDATION_PENDING", "PUT_ORDER_REQ_RECEIVED", "MODIFY_PENDING", "CANCEL_PENDING"}:
                    state = "BROKER_PENDING"
                self.journal.update(self.account, row["request_id"], state, str(match.get("orderid", row["broker_id"])),
                                    int(match.get("filledshares") or 0), str(match.get("averageprice") or ""))
        return [self.public_order(r) for r in self.journal.rows(self.account)]

    def positions_summary(self):
        if not self.account:raise TradingError("Connect a broker account first")
        fields = ("tradingsymbol", "exchange", "producttype", "netqty", "pnl", "ltp", "buyavgprice", "sellavgprice")
        return [{k: str(row.get(k, ""))[:80] for k in fields} for row in self.feed.positions()]

    def cancel(self, request_id, confirm):
        if not self.enabled or confirm != "CANCEL REAL ORDER":
            raise TradingError("Explicit live cancellation confirmation required")
        with self.lock:
            self.reconcile()
            row = next((r for r in self.journal.rows(self.account) if r["request_id"] == request_id), None)
            if not row or not row["broker_id"]:
                raise TradingError("Broker order ID unavailable; reconcile in Angel One")
            if row["state"] in self.TERMINAL | {"CANCEL_REQUESTED", "CANCEL_UNKNOWN"}:
                return self.public_order(row)
            self.journal.update(self.account, request_id, "CANCEL_REQUESTED", row["broker_id"], row["filled"], row["average_price"])
            try:
                self.feed.cancel_order(row["broker_id"])
            except Exception:
                self.journal.update(self.account, request_id, "CANCEL_UNKNOWN", row["broker_id"], row["filled"], row["average_price"])
            return self.public_order(next(r for r in self.journal.rows(self.account) if r["request_id"] == request_id))
