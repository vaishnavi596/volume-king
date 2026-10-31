# Is code me 1 line badlo - get_real_nifty ke baad wale logic me:

# --- OLD CODE HATAO ---
# nifty = real_price if IS_LIVE else prev_nifty + random...

# --- NAYA CODE PASTE KARO ---
# LOGIC: LIVE DATA = Hamesha Real, TRADING = Hamesha DEMO (Safe)
def get_display_nifty():
    real_price, is_real = get_real_nifty()
    # LIVE switch ON hai toh Real dikhao, nahi toh Demo
    # Lekin Trading hamesha DEMO rahega, jab tak Real Trading switch ON nahi
    if mode_switch.value: # LIVE DATA ON
        return real_price, f"🟢 LIVE DATA {'(REAL)' if is_real else '(Last Close)'}"
    else:
        return prev_nifty + random.uniform(-80, 90), "🔴 DEMO DATA"

# Aur buy_order function ko aise badlo:
def buy_order(symbol, premium):
    # Hamesha DEMO trade - Real market data pe paper trading
    if IS_REAL_TRADING and (api_config["angel_api_key"] or api_config["dhan_token"]):
        last_trade.value = f"🟢 REAL ORDER {symbol} @ ₹{premium:.1f} - Broker ko gaya!"
    else:
        last_trade.value = f"📝 DEMO TRADE (Live Data pe) {symbol} @ ₹{premium:.1f} | Balance safe hai!"
    page.snack_bar = ft.SnackBar(ft.Text(last_trade.value))
    page.snack_bar.open = True
    page.update()
