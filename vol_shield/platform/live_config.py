"""Cache TTL and snapshot read flags."""
from __future__ import annotations

STREAMLIT_YAHOO_CACHE_TTL_SEC = 300


def read_vol_shield_snapshot_enabled() -> bool:
    import os

    raw = (os.environ.get("VOL_SHIELD_READ_SNAPSHOT") or "1").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    return True
