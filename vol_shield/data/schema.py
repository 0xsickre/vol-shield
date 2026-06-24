"""SQLite DDL for vol-shield."""
from __future__ import annotations

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS shield_signal (
    as_of TEXT NOT NULL PRIMARY KEY,
    vix_shock INTEGER,
    ovx_shock INTEGER,
    dxy_trend TEXT,
    bond_liq_shock INTEGER,
    shield_active INTEGER,
    trust TEXT,
    gate_tier TEXT,
    computed_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shield_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fetched_at TEXT NOT NULL,
    as_of TEXT,
    fence_tag TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shield_price_bars (
    ticker TEXT NOT NULL,
    bar_date TEXT NOT NULL,
    close REAL,
    source TEXT,
    fetched_at TEXT,
    PRIMARY KEY (ticker, bar_date)
);
"""
