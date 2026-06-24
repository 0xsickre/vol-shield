"""SQLite backend."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager

from vol_shield.platform.settings import get_sqlite_db_path


@contextmanager
def get_connection():
    path = get_sqlite_db_path()
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_schema() -> None:
    from vol_shield.data.schema import SCHEMA_SQL

    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
