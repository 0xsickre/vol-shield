"""EOD price bar cache for shield tickers."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from vol_shield.data.backend import ensure_schema, get_connection


def upsert_price_bars(ticker: str, series: pd.Series, *, source: str = "yahoo") -> int:
    if series is None or series.empty:
        return 0
    ensure_schema()
    fetched_at = datetime.now(timezone.utc).isoformat()
    n = 0
    with get_connection() as conn:
        for ts, val in series.items():
            if pd.isna(val):
                continue
            bar_date = str(pd.Timestamp(ts).date())
            conn.execute(
                """
                INSERT INTO shield_price_bars (ticker, bar_date, close, source, fetched_at)
                VALUES (?,?,?,?,?)
                ON CONFLICT(ticker, bar_date) DO UPDATE SET
                    close=excluded.close,
                    source=excluded.source,
                    fetched_at=excluded.fetched_at
                """,
                (ticker, bar_date, float(val), source, fetched_at),
            )
            n += 1
    return n


def load_price_series(ticker: str, *, limit: int = 120) -> pd.Series:
    ensure_schema()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT bar_date, close FROM shield_price_bars
            WHERE ticker = ? ORDER BY bar_date DESC LIMIT ?
            """,
            (ticker, limit),
        ).fetchall()
    if not rows:
        return pd.Series(dtype=float)
    rows = list(reversed(rows))
    idx = pd.to_datetime([r[0] for r in rows])
    vals = [float(r[1]) for r in rows]
    return pd.Series(vals, index=idx, dtype=float)
