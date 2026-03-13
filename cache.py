"""SQLite cache for DOI-keyed API responses."""

import os
import sqlite3
import time
from pathlib import Path

_TTLS = {
    "paper_details": 30 * 86400,  # 30 days
    "bibtex": 90 * 86400,         # 90 days
}

_DEFAULT_PATH = os.path.expanduser("~/.cache/scholark-1/papers.db")


class CacheDB:
    def __init__(self, db_path: str = _DEFAULT_PATH):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS cache ("
            "  key TEXT PRIMARY KEY,"
            "  value TEXT NOT NULL,"
            "  source TEXT NOT NULL,"
            "  created_at REAL NOT NULL"
            ")"
        )
        self._conn.commit()

    def _ttl_for_key(self, key: str) -> int | None:
        prefix = key.split(":")[0] if ":" in key else None
        return _TTLS.get(prefix)

    def get(self, key: str) -> str | None:
        ttl = self._ttl_for_key(key)
        if ttl is None:
            return None
        row = self._conn.execute(
            "SELECT value, created_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
        if not row:
            return None
        value, created_at = row
        if time.time() - created_at > ttl:
            return None
        return value

    def put(self, key: str, value: str, source: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO cache (key, value, source, created_at) VALUES (?, ?, ?, ?)",
            (key, value, source, time.time()),
        )
        self._conn.commit()
