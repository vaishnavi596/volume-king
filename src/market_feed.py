"""Read-only Angel One adapter. Never sends orders or logs credentials."""
import json
import math
import socket
import time
import threading
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

IST=timezone(timedelta(hours=5,minutes=30))
class FeedError(RuntimeError): pass
class SessionExpired(FeedError): pass

class AngelFeed:
    ROOT="https://apiconnect.angelone.in"
    PATHS={
        "login":"/rest/auth/angelbroking/user/v1/loginByPassword",
        "quote":"/rest/secure/angelbroking/market/v1/quote",
        "candles":"/rest/secure/angelbroking/historical/v1/getCandleData",
        "search":"/rest/secure/angelbroking/order/v1/searchScrip",
    }
    def __init__(self):
        self.key="";self.token="";self.client=""
        self.lock=threading.RLock();self.last=0.;self.instruments=None
        self.public_ip="";self.local_ip="127.0.0.1";self.mac="";self.epoch=0
        self.resolved={}
    @property
    def connected(self):return bool(self.key and self.token)
    def disconnect(self):
        self.epoch+=1;self.key="";self.token="";self.client=""
    def request(self,kind,payload,key=None,token=None):
        if kind not in self.PATHS:raise FeedError("Unsupported read operation")
        headers={"Content-Type":"application/json","Accept":"application/json",
            "X-PrivateKey":key or self.key,"X-UserType":"USER","X-SourceID":"WEB",
            "X-ClientLocalIP":self.local_ip,"X-ClientPublicIP":self.public_ip,
            "X-MACAddress":self.mac}
        auth=self.token if token is None else token
        if auth:headers["Authorization"]="Bearer "+auth
        # Serialize requests below the documented historical API rate limit.
        with self.lock:
            time.sleep(max(0,.4-(time.monotonic()-self.last)))
            self.last=time.monotonic()
            req=urllib.request.Request(self.ROOT+self.PATHS[kind],
                    data=json.dumps(payload).encode(),headers=headers,method="POST")
            try:
                with urllib.request.urlopen(req,timeout=12) as response:data=json.load(response)
            except urllib.error.HTTPError as exc:
                if exc.code in (401,403):
                    self.disconnect()
                    raise SessionExpired("Broker session expired; reconnect") from None
                raise FeedError("Broker HTTP request failed; retry later") from None
            except Exception:raise FeedError("Broker request failed; check connection/session") from None
        if data.get("status") is not True:
            if kind!="login" and str(data.get("errorcode") or data.get("errorCode")) in ("AG8001","AG8002"):
                self.disconnect()
                raise SessionExpired("Broker session expired; reconnect")
            raise FeedError("Broker rejected request; reconnect or verify contract")
        return data.get("data")
    def connect(self,key,client,pin,totp):
        import uuid
        if not all((key,client,pin,totp)) or not totp.isdigit() or len(totp)!=6:
            raise FeedError("Enter API Key, Client Code, MPIN and current 6-digit TOTP")
        generation=self.epoch
        self.mac=":".join(f"{(uuid.getnode()>>shift)&255:02x}" for shift in range(40,-1,-8))
        try:
            with urllib.request.urlopen("https://api.ipify.org?format=json",timeout=8) as r:
                self.public_ip=json.load(r)["ip"]
            import ipaddress
            ipaddress.ip_address(self.public_ip)
            self.local_ip=socket.gethostbyname(socket.gethostname())
        except Exception:raise FeedError("Unable to determine network address; check internet") from None
        data=self.request("login",{"clientcode":client,"password":pin,"totp":totp},key=key,token="")
        if generation!=self.epoch:raise FeedError("Connection cancelled")
        if not data or not data.get("jwtToken"):raise FeedError("No authenticated session returned")
        self.key=key;self.client=client;self.token=data["jwtToken"]
    def master(self):
        if self.instruments is None:
            req=urllib.request.Request("https://margincalculator.angelone.in/OpenAPI_File/files/OpenAPIScripMaster.json",
                                      headers={"User-Agent":"BOT KING"})
            with urllib.request.urlopen(req,timeout=25) as r:data=json.load(r)
            if not isinstance(data,list):raise FeedError("Instrument list unavailable")
            self.instruments=data
        return self.instruments
    def resolve(self,symbol):
        if symbol in self.resolved:return self.resolved[symbol]
        # Resolve exact cash symbols/index names; never guess a derivative token.
        aliases={"NIFTY":"Nifty 50","BANKNIFTY":"Nifty Bank","FINNIFTY":"Nifty Fin Service","SENSEX":"SENSEX"}
        search=aliases.get(symbol,symbol+"-EQ")
        exchange="BSE" if symbol=="SENSEX" else "NSE"
        data=self.request("search",{"exchange":exchange,"searchscrip":search}) or []
        matches=[r for r in data if str(r.get("tradingsymbol","")).upper()==search.upper()]
        if len(matches)!=1:raise FeedError("Exact broker symbol unavailable")
        result=(exchange,str(matches[0]["symboltoken"]))
        self.resolved[symbol]=result
        return result
    def expiries(self,symbol):
        result=set();now=datetime.now(IST)
        for r in self.master():
            if r.get("name")!=symbol or r.get("instrumenttype") not in ("OPTIDX","OPTSTK"):continue
            try:d=datetime.strptime(r.get("expiry",""),"%d%b%Y").date()
            except ValueError:continue
            if d>now.date() or (d==now.date() and (now.hour,now.minute)<(15,30)):result.add(d.isoformat())
        return sorted(result)
    @staticmethod
    def number(value):
        value=float(value)
        if not math.isfinite(value):raise FeedError("Invalid numeric quote")
        return value
    @classmethod
    def nonnegative(cls,value):
        value=cls.number(value)
        if value<0:raise FeedError("Negative market value rejected")
        return value
    @staticmethod
    def timestamp(value):
        if not value:return None
        for fmt in ("%d-%b-%Y %H:%M:%S","%Y-%m-%dT%H:%M:%S%z","%Y-%m-%d %H:%M:%S"):
            try:
                d=datetime.strptime(str(value),fmt)
                return (d if d.tzinfo else d.replace(tzinfo=IST)).timestamp()
            except ValueError:pass
        return None
    def quotes(self,exchange,tokens):
        data=self.request("quote",{"mode":"FULL","exchangeTokens":{exchange:tokens}}) or {}
        return data.get("fetched") or []
    def history(self,symbol,interval,period):
        if not self.connected:raise FeedError("Broker not connected")
        exchange,token=self.resolve(symbol)
        mapping={"1m":"ONE_MINUTE","3m":"THREE_MINUTE","5m":"FIVE_MINUTE","15m":"FIFTEEN_MINUTE","30m":"THIRTY_MINUTE","1h":"ONE_HOUR","1d":"ONE_DAY"}
        now=datetime.now(IST);days={"1d":1,"5d":5,"7d":7,"1mo":30,"3mo":90}.get(period,7)
        if interval=="1m":days=min(days,30)
        data=self.request("candles",{"exchange":exchange,"symboltoken":token,
            "interval":mapping[interval],"fromdate":(now-timedelta(days=days)).strftime("%Y-%m-%d %H:%M"),
            "todate":now.strftime("%Y-%m-%d %H:%M")}) or []
        bars=[]
        for row in data:
            ts=self.timestamp(row[0])
            if ts is not None:bars.append([ts]+[self.number(v) for v in row[1:6]])
        if not bars:raise FeedError("Broker candles unavailable")
        q=self.quotes(exchange,[token])
        if not q:raise FeedError("Broker quote unavailable")
        q=q[0];stamp=self.timestamp(q.get("exchFeedTime"))
        # Off-hours quotes are normally old. Keep genuine historical candles
        # visible but never label an old quote as fresh/live.
        if stamp is None:raise FeedError("Broker quote timestamp unavailable")
        fresh=0<=time.time()-stamp<=90
        return {"price":self.number(q["ltp"]),"change":self.number(q.get("percentChange",0)),
            "high":q.get("high"),"low":q.get("low"),"bars":bars,"source":"Angel One",
            "quote_timestamp":stamp,"quote_fresh":fresh,
            "fetched_at":time.time(),"time":datetime.now(IST).strftime("%H:%M IST")}
    def option_chain(self,symbol,expiry,spot):
        if not self.connected:raise FeedError("Connect Angel One for live CE/PE data; Yahoo fallback has no verified option chain")
        contracts=[]
        for r in self.master():
            if r.get("name")!=symbol or r.get("exch_seg") not in ("NFO","BFO"):continue
            if r.get("instrumenttype") not in ("OPTIDX","OPTSTK"):continue
            try:d=datetime.strptime(r.get("expiry",""),"%d%b%Y").date().isoformat()
            except ValueError:continue
            if d==expiry:contracts.append(r)
        if not contracts:raise FeedError("No listed contracts for selected expiry; choose a broker-listed date")
        strikes=sorted({self.number(r["strike"])/100 for r in contracts})
        if spot is None:raise FeedError("Refresh underlying price before loading option chain")
        chosen=set(sorted(strikes,key=lambda x:abs(x-spot))[:9])
        contracts=[r for r in contracts if self.number(r["strike"])/100 in chosen]
        tokens=[str(r["token"]) for r in contracts]
        if len(tokens)>50:raise FeedError("Contract window too large")
        exchange=contracts[0]["exch_seg"]
        fetched=self.quotes(exchange,tokens);by_token={str(r["symbolToken"]):r for r in fetched}
        rows=[]
        for c in contracts:
            q=by_token.get(str(c["token"]))
            if not q:continue
            rows.append({"strike":self.number(c["strike"])/100,
                "side":"CE" if c["symbol"].endswith("CE") else "PE",
                "premium":self.nonnegative(q["ltp"]),"oi":self.nonnegative(q["opnInterest"]) if q.get("opnInterest") is not None else None,
                "volume":self.nonnegative(q["tradeVolume"]) if q.get("tradeVolume") is not None else None,"timestamp":self.timestamp(q.get("exchFeedTime")),
                "token":str(c["token"]),"lot_size":int(c["lotsize"])})
        if not rows:raise FeedError("No option quotes returned")
        return {"symbol":symbol,"expiry":expiry,"source":"Angel One","rows":rows,
                "complete":len(rows)==len(contracts),"fetched_at":time.time()}
    def option_history(self,symbol,expiry,strike,side):
        if not self.connected:raise FeedError("Broker disconnected")
        candidates=[]
        for row in self.master():
            if row.get("name")!=symbol or row.get("exch_seg") not in ("NFO","BFO"):continue
            if row.get("instrumenttype") not in ("OPTIDX","OPTSTK") or not row.get("symbol","").endswith(side):continue
            try:d=datetime.strptime(row.get("expiry",""),"%d%b%Y").date().isoformat()
            except ValueError:continue
            if d==expiry and self.number(row["strike"])/100==float(strike):candidates.append(row)
        if len(candidates)!=1:raise FeedError("Exact listed option contract unavailable")
        c=candidates[0];now=datetime.now(IST)
        data=self.request("candles",{"exchange":c["exch_seg"],"symboltoken":str(c["token"]),"interval":"FIVE_MINUTE",
            "fromdate":(now-timedelta(days=7)).strftime("%Y-%m-%d %H:%M"),"todate":now.strftime("%Y-%m-%d %H:%M")}) or []
        bars=[]
        for row in data:
            stamp=self.timestamp(row[0])
            if stamp is not None:bars.append([stamp]+[self.number(v) for v in row[1:6]])
        if len(bars)<2:raise FeedError("Option premium history unavailable")
        return bars

