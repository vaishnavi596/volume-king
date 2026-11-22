"""V3-only quarantine for retired Angel One/Yahoo adapter paths.

This intentionally does not import legacy market_feed.ServerAngelFeed or
contact Angel One/Yahoo. Keep the old production V1 backend modules untouched.
Never substitute synthetic quotes or login credentials.
"""
class V3DisabledLegacyBroker:
    def __init__(self):
        self.epoch = 0
        self.key = ""
        self.token = ""
        self.client = ""
        self.server = ""

    @property
    def connected(self):
        return False

    def disconnect(self):
        self.epoch += 1
        self.key = self.token = self.client = self.server = ""

    def revoke(self):
        self.disconnect()

    def __getattr__(self, name):
        # Catch any overlooked old quote/history/option/login callback.
        if name.startswith("_"):
            raise AttributeError(name)
        def blocked(*_args, **_kwargs):
            raise RuntimeError(
                "V3 Dhan-only: retired broker transport disabled; no request sent")
        return blocked
