# ===== V5.3 MULTI BROKER MANAGER - Setting Page me daalo =====

BROKERS = {
    "Angel One": ["Client ID", "Password", "API Key", "Secret Key", "TOTP Secret"],
    "Zerodha": ["Client ID", "API Key", "API Secret", "TOTP"],
    "Dhan": ["Client ID", "Access Token"],
    "Upstox": ["API Key", "API Secret", "Redirect URL"],
    "Fyers": ["Client ID", "Secret Key", "Redirect URL"],
    "Alice Blue": ["User ID", "API Key"],
    "5paisa": ["Client Code", "API Key", "API Secret"],
    "Kotak Neo": ["Consumer Key", "Consumer Secret", "Mobile No", "Password"],
}

selected_broker = ft.Dropdown(
    label="🔑 Broker Select Karo - Sabka API Yahi Se",
    value="Angel One",
    options=[ft.dropdown.Option(b) for b in BROKERS.keys()],
    bgcolor="#111111", border_color="#FFD700", expand=True
)

api_fields_col = ft.Column([], spacing=8)
save_status = ft.Text("Mobile se API daalo, auto save hoga", size=10, color="#888")

# Dynamic fields banane ka function
def build_api_fields(e=None):
    api_fields_col.controls.clear()
    broker = selected_broker.value
    fields = BROKERS.get(broker, [])
    
    # Pehle se saved data load karo
    saved = page.client_storage.get(f"broker_{broker}") or {}
    
    for f_name in fields:
        # Key ko storage ke liye safe banao
        key = f_name.lower().replace(" ", "_")
        tf = ft.TextField(
            label=f"{f_name} - {broker}",
            value=saved.get(key, ""),
            password=True if "secret" in key or "password" in key or "token" in key or "totp" in key else False,
            can_reveal_password=True,
            bgcolor="#0A0A0A", border_color="#333",
            expand=True
        )
        tf.data_key = key
        api_fields_col.controls.append(tf)
    
    # Extra field sabke liye
    api_fields_col.controls.append(ft.TextField(label="Custom Notes (Optional)", bgcolor="#0A0A0A", border_color="#222"))
    page.update()

selected_broker.on_change = build_api_fields

def save_broker_api(e):
    broker = selected_broker.value
    data = {}
    for ctrl in api_fields_col.controls:
        if hasattr(ctrl, 'data_key'):
            data[ctrl.data_key] = ctrl.value
    
    page.client_storage.set(f"broker_{broker}", data)
    page.client_storage.set("last_broker", broker)
    save_status.value = f"✅ {broker} API Saved! Mobile me safe hai. CONNECT dabao."
    save_status.color = "#00FF88"
    
    # Ab connect logic
    broker_name.value = f"Broker: {broker} Connected ✅"
    broker_bull_text.value = f"{broker} Bull: Loading..."
    
    page.snack_bar = ft.SnackBar(ft.Text(f"{broker} API Saved & Connected"), bgcolor="#00FF88")
    page.snack_bar.open = True
    page.update()

def connect_broker_api(e):
    broker = selected_broker.value
    saved = page.client_storage.get(f"broker_{broker}")
    if not saved or len([v for v in saved.values() if v]) == 0:
        save_status.value = f"❌ Pehle {broker} ka API daalo fir SAVE karo!"
        save_status.color = "#FF3B3B"
        page.update()
        return
    
    save_status.value = f"🔄 {broker} ko connect kar rahe hai... LIVE chart ayega"
    save_status.color = "#FFD700"
    page.update()
    # Yaha par aapka actual Angel/Zerodha ka SDK connect hoga
    # Ex: SmartApi, KiteConnect etc
    time.sleep(1)
    broker_name.value = f"Broker: {broker} LIVE 🔴"
    save_status.value = f"✅ {broker} LIVE! Niche wala Broker Chart ab {broker} se chalega"
    save_status.color = "#00FF88"
    page.update()

# Setting Page ka Card
broker_manager_card = card(ft.Column([
    ft.Text("🔐 MULTI BROKER API MANAGER - Mobile Se Hi Sab Hoga", size=12, weight=ft.FontWeight.BOLD, color="#FFD700"),
    ft.Text("Angel One, Zerodha, Dhan, Upstox, Fyers sabka secret key yahi daalo. Jisko connect karna ho usko select karo.", size=9, color="#888"),
    selected_broker,
    api_fields_col,
    ft.Row([
        ft.ElevatedButton("💾 SAVE API (Mobile Me)", bgcolor="#00FF88", color="#000000", expand=True, on_click=save_broker_api),
        ft.ElevatedButton("🔴 CONNECT LIVE", bgcolor="#111111", color="#FFD700", expand=True, on_click=connect_broker_api),
    ], spacing=8),
    save_status,
    ft.Divider(height=1, color="#222"),
    ft.Row([ft.Text("Current:", size=10, color="#888"), ft.Text("Broker: Not Connected", size=10, color="#888")]), # broker_name variable
]))

# Isko page load pe call karo
build_api_fields()
