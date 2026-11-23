"""Exact-identity, in-process last-good historical agreement for dashboard UI.

Only caches a successfully calculated HIST result. This is not a live signal,
not an independent engine vote and does not survive app uninstall.
"""
from collections import OrderedDict

class LastGoodHistoricalAgreement:
    def __init__(self,limit=220):
        self.records=OrderedDict()
        self.limit=limit

    def resolve(self, *, symbol,timeframe,generation,source,filter_signature,
                calculated=None,source_candle_time=None):
        if not isinstance(symbol,str) or not symbol or timeframe not in ("1m","3m","5m"):
            raise ValueError("Exact symbol and timeframe required")
        if type(generation) is not int or source!="Dhan":
            return None,False
        if not isinstance(filter_signature,tuple) or any(not isinstance(x,str) for x in filter_signature):
            raise ValueError("Filter signature required")
        key=(symbol,timeframe,generation,source,filter_signature)
        if calculated is not None:
            if (not isinstance(calculated,(tuple,list)) or len(calculated)!=3 or
                    any(type(n) is not int for n in calculated) or
                    min(calculated)<0 or calculated[0]+calculated[1]!=100 or
                    calculated[2]<1 or type(source_candle_time) not in (int,float) or
                    source_candle_time<=0):
                raise ValueError("Malformed historical vote")
            existing=self.records.get(key)
            # Older data may not overwrite a newer last-good state.
            if existing is None or source_candle_time>=existing["candle_time"]:
                self.records[key]={"votes":tuple(calculated),"candle_time":source_candle_time}
            self.records.move_to_end(key)
            while len(self.records)>self.limit:
                self.records.popitem(last=False)
            return self.records[key]["votes"],False
        old=self.records.get(key)
        if old:
            self.records.move_to_end(key)
            return old["votes"],True
        return None,False
