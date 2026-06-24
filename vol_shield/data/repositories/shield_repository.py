"""shield_signal and shield_snapshots persistence."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from vol_shield.data.backend import ensure_schema, get_connection


def upsert_shield_signal(row: dict) -> None:
    ensure_schema()
    payload = row.get("payload") or {
        "shield": row.get("shield"),
        "gate": row.get("gate"),
    }
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO shield_signal (
                as_of, vix_shock, ovx_shock, dxy_trend, bond_liq_shock,
                shield_active, trust, gate_tier, computed_at, payload_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(as_of) DO UPDATE SET
                vix_shock=excluded.vix_shock,
                ovx_shock=excluded.ovx_shock,
                dxy_trend=excluded.dxy_trend,
                bond_liq_shock=excluded.bond_liq_shock,
                shield_active=excluded.shield_active,
                trust=excluded.trust,
                gate_tier=excluded.gate_tier,
                computed_at=excluded.computed_at,
                payload_json=excluded.payload_json
            """,
            (
                row["as_of"],
                int(bool(row.get("vix_shock"))),
                int(bool(row.get("ovx_shock"))),
                row.get("dxy_trend"),
                int(bool(row.get("bond_liq_shock"))),
                int(bool(row.get("shield_active"))),
                row.get("trust"),
                row.get("gate_tier"),
                row.get("computed_at"),
                json.dumps(payload, default=str),
            ),
        )


def insert_shield_snapshot(payload: dict, *, as_of: str | None = None, fence_tag: str | None = None) -> None:
    ensure_schema()
    fetched_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO shield_snapshots (fetched_at, as_of, fence_tag, payload_json)
            VALUES (?,?,?,?)
            """,
            (fetched_at, as_of, fence_tag, json.dumps(payload, default=str)),
        )
