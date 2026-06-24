"""Rate limiter for Massive REST (4 req / 60s)."""
from __future__ import annotations

import threading
import time
from collections import deque

_MAX_REQUESTS = 4
_WINDOW_SECONDS = 60.0

_lock = threading.Lock()
_timestamps: deque[float] = deque()


def acquire_massive_slot() -> None:
    while True:
        with _lock:
            now = time.monotonic()
            while _timestamps and now - _timestamps[0] >= _WINDOW_SECONDS:
                _timestamps.popleft()
            if len(_timestamps) < _MAX_REQUESTS:
                _timestamps.append(now)
                return
            wait_s = _WINDOW_SECONDS - (now - _timestamps[0])
        time.sleep(max(0.05, wait_s))


def reset_massive_rate_limiter_for_tests() -> None:
    with _lock:
        _timestamps.clear()
