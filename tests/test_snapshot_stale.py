"""Snapshot TTL helpers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from vol_shield.domain.data_freshness import is_snapshot_stale, snapshot_age_hours


def test_snapshot_age_hours_recent():
    ts = datetime.now(timezone.utc).isoformat()
    age = snapshot_age_hours(ts)
    assert age is not None
    assert age < 0.1


def test_is_snapshot_stale_old():
    old = (datetime.now(timezone.utc) - timedelta(hours=10)).isoformat()
    assert is_snapshot_stale(old, max_hours=6.0) is True


def test_is_snapshot_stale_fresh():
    fresh = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    assert is_snapshot_stale(fresh, max_hours=6.0) is False
