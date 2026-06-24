"""Streamlit cache fence for Yahoo-backed shield fetches."""
from __future__ import annotations

from datetime import datetime, timezone


def yahoo_streamlit_cache_fence(*, now_utc: datetime | None = None, historical: bool = False) -> str:
    if historical:
        return "yahoo_historical"
    ref = now_utc if now_utc is not None else datetime.now(timezone.utc)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)
    day = ref.strftime("%Y-%m-%d")
    slot = int((ref.hour * 60 + ref.minute) // 30)
    return f"{day}_w30_{slot}"
