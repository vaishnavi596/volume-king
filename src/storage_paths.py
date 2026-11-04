"""Use Flet's durable, app-private directory on packaged phones."""
import os
from pathlib import Path


def data_directory():
    supplied = os.environ.get("FLET_APP_STORAGE_DATA")
    if supplied:
        return Path(supplied)
    # Desktop fallback also keeps application data out of the source bundle.
    return Path.home() / ".bot_king"


def storage_paths():
    root = data_directory()
    return root / "settings.json", root / "market_cache.json"
