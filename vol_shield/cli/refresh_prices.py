"""Fetch EOD bars for shield + gate tickers."""
from __future__ import annotations

import sys

from vol_shield.core.reference_data import REFRESH_TICKERS, SHIELD_TICKERS
from vol_shield.data.repositories.price_repository import upsert_price_bars
from vol_shield.domain.shield_engine import get_global_shield_status
from vol_shield.providers.price_source import history_close_series


def refresh_all_prices(*, period: str = "400d") -> dict[str, int]:
    counts: dict[str, int] = {}
    for ticker in REFRESH_TICKERS:
        try:
            s = history_close_series(ticker, period=period, interval="1d")
            counts[ticker] = upsert_price_bars(ticker, s)
        except Exception as e:
            print(f"WARN {ticker}: {e}", file=sys.stderr)
            counts[ticker] = 0
    return counts


def main(argv: list[str] | None = None) -> int:
    counts = refresh_all_prices()
    get_global_shield_status.clear()
    total = sum(counts.values())
    shield_ok = any(counts.get(t, 0) > 0 for t in SHIELD_TICKERS)
    print(f"vol-shield-refresh: upserted {total} bars across {len(counts)} tickers")
    for t, n in counts.items():
        print(f"  {t}: {n}")
    return 0 if shield_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
