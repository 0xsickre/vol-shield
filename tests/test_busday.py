"""Busday gap primitive tests."""
from __future__ import annotations

from datetime import date

from vol_shield.platform.busday import business_day_gap


def test_busday_gap_same_day():
    assert business_day_gap("2026-03-27", date(2026, 3, 27)) == 0


def test_busday_gap_skips_weekend():
    # Thu bar -> Mon ref = 2 business days (Fri, Mon)
    assert business_day_gap("2026-03-26", date(2026, 3, 30)) == 2
