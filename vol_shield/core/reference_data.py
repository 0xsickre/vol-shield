"""Shield and gate ticker symbols."""
from __future__ import annotations

SHIELD_TICKERS: tuple[str, ...] = ("^VIX", "^VIX3M", "DX-Y.NYB", "^OVX", "^MOVE")

CRITICAL_MACRO_TICKERS: tuple[str, ...] = ("^VIX", "^MOVE", "HG=F", "DX-Y.NYB")

REFRESH_TICKERS: tuple[str, ...] = SHIELD_TICKERS + ("HG=F",)

# Massive routing (^VIX only for vol-shield scope).
MASSIVE_TICKER_MAP: dict[str, str] = {
    "^VIX": "I:VIX",
}

PRICE_YAHOO_ONLY: frozenset[str] = frozenset(
    {
        "^VIX3M",
        "^OVX",
        "^MOVE",
        "DX-Y.NYB",
        "HG=F",
    }
)


def massive_symbol_for(yahoo_ticker: str) -> str | None:
    sym = str(yahoo_ticker or "").strip()
    if not sym or sym in PRICE_YAHOO_ONLY:
        return None
    return MASSIVE_TICKER_MAP.get(sym)
