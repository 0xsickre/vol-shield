"""Secret resolution — env only."""
from __future__ import annotations

import os
from typing import Optional


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    v = (os.environ.get(key) or os.environ.get(key.upper()) or "").strip()
    if v:
        return v
    return default
