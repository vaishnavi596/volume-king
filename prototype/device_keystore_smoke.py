"""Manual Android device smoke test for the registered Flet Keystore control.

Run only with the experimental Flet client that registers botkingkeystore.
No real BOT KING server key or broker token is used.
"""
import secrets
import flet as ft
from keystore_control import KeystoreControl

KEY = "botking.dhan.server_access.v1"


def main(page: ft.Page):
    page.title = "BOT KING Keystore Device Test"
    page.scroll = ft.ScrollMode.AUTO
    native = KeystoreControl()
    page.overlay.append(native)
    status = ft.Text("Ready. Uses random temporary test data, never a broker credential.")
    expected = [None]
    # Do not treat an arbitrary smoke-prefixed value as proof of persistence.
    # The user retains this non-secret fingerprint across an app restart.
    fingerprint = ft.TextField(label="Expected test fingerprint (copy before restart)", width=400)
    # Random test tokens are deliberately not stored in app preferences.

    async def write_test(_):
        token = "smoke-" + secrets.token_hex(16)
        try:
            await native.set(KEY, token)
            expected[0] = token
            fingerprint.value = token[-8:]
            status.value = "Encrypted write succeeded. Keep the 8-character fingerprint for restart verification."
        except Exception:
            expected[0] = None
            status.value = "Encrypted write FAILED. Native bridge not ready."
        page.update()

    async def read_test(_):
        try:
            saved = await native.get(KEY)
            proof = (fingerprint.value or "").strip().lower()
            if expected[0] is not None and saved == expected[0]:
                status.value = "Read verified: stored value matches temporary test token."
            elif (expected[0] is None and len(proof) == 8
                  and all(c in "0123456789abcdef" for c in proof)
                  and isinstance(saved, str) and saved.startswith("smoke-")
                  and len(saved) == 38 and saved.endswith(proof)):
                status.value = "Read after restart verified against user-retained fingerprint."
            else:
                status.value = "Read NOT verified: enter the original fingerprint after restart."
        except Exception:
            status.value = "Encrypted read FAILED."
        page.update()

    async def delete_test(_):
        try:
            await native.delete(KEY)
            saved = await native.get(KEY)
            expected[0] = None
            status.value = "Delete verified." if saved is None else "Delete FAILED: data remains."
        except Exception:
            status.value = "Encrypted delete FAILED."
        page.update()

    page.add(
        ft.Text("BOT KING — Native Keystore smoke test", size=20),
        ft.Text("Experimental app only. Do not enter a real access key."),
        ft.ElevatedButton("1. Write random test token", on_click=write_test),
        fingerprint,
        ft.ElevatedButton("2. Read and compare (also after app restart)", on_click=read_test),
        ft.ElevatedButton("3. Delete and verify", on_click=delete_test),
        status,
    )


ft.app(target=main)
