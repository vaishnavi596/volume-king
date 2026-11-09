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
    # Random test tokens are deliberately not stored in app preferences.

    async def write_test(_):
        token = "smoke-" + secrets.token_hex(16)
        try:
            await native.set(KEY, token)
            expected[0] = token
            status.value = "Encrypted write succeeded. Now test read."
        except Exception:
            expected[0] = None
            status.value = "Encrypted write FAILED. Native bridge not ready."
        page.update()

    async def read_test(_):
        try:
            saved = await native.get(KEY)
            status.value = (
                "Read verified: stored value matches temporary test token."
                if expected[0] is not None and saved == expected[0]
                else ("Read after restart verified: test token persisted."\n                      if expected[0] is None and isinstance(saved, str) and saved.startswith("smoke-") and len(saved) == 38\n                      else "Read not verified: missing or unexpected test token.")
            )
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
        ft.ElevatedButton("2. Read and compare (also after app restart)", on_click=read_test),
        ft.ElevatedButton("3. Delete and verify", on_click=delete_test),
        status,
    )


ft.app(target=main)
