"""V2 app-owned offline bridge for reviewed V1 candle helpers.

No broker, network, credentials, provider fallback, or live-signal promotion.
Input is normalized completed, validated 1m candle evidence from V2 inbox.
"""
from candle_retention import retain_candle_history, retain_last_filter_votes
from dhan_three_minute import completed_three_minute_bars
from analysis_quality import quality_check, agreement_detail


def three_minute_from_local_history(history, symbol, *, selected_equities=(), now_epoch):
    """Resample only already accepted 1m bars; never fetch or advertise LIVE."""
    view = history.view(symbol, "1m", selected_equities=selected_equities)
    if view["status"] != "HIST":
        return {"status": "WAIT", "bars": (), "reason": "No completed cached one-minute history"}
    raw = [(b["timestamp"], b["open"], b["high"], b["low"], b["close"], b["volume"])
           for b in view["bars"]]
    bars = completed_three_minute_bars(raw, now_epoch=now_epoch)
    return {"status": "HIST" if bars else "WAIT", "bars": tuple(bars),
            "reason": "Resampled completed cached candles; unverified historical only"
            if bars else "No complete session-aligned three-minute candle"}
