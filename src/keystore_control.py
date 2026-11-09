"""Flet 0.25.2 Android secure storage control. Requires registered Flutter control.

Do not ship unless the custom Flutter package is actually included in the APK.
"""
from flet.core.control import Control
from secure_credentials import SecureStorageUnavailable

_ALLOWED_KEY = "botking.dhan.server_access.v1"


class KeystoreControl(Control):
    def _get_control_name(self):
        return "botkingkeystore"

    async def get(self, key: str):
        if key != _ALLOWED_KEY:
            raise ValueError("Unsupported credential slot")
        return await self.invoke_method_async("get", {"key": key}, wait_for_result=True)

    async def set(self, key: str, value: str):
        if key != _ALLOWED_KEY or not isinstance(value, str) or not value:
            raise ValueError("Invalid secure credential")
        result = await self.invoke_method_async(
            "set", {"key": key, "value": value}, wait_for_result=True
        )
        if result != "1":
            raise SecureStorageUnavailable("Native Keystore write failed")

    async def delete(self, key: str):
        if key != _ALLOWED_KEY:
            raise ValueError("Unsupported credential slot")
        result = await self.invoke_method_async(
            "delete", {"key": key}, wait_for_result=True
        )
        if result != "1":
            raise SecureStorageUnavailable("Native Keystore delete failed")
