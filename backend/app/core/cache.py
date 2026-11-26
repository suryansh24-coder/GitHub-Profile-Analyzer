from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass
class _Entry:
    value: object
    expires_at: float


class TTLCache:
    def __init__(self, ttl_seconds: int, max_entries: int) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: dict[str, _Entry] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> object | None:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return None
            if entry.expires_at <= time.monotonic():
                self._entries.pop(key, None)
                self._misses += 1
                return None
            self._hits += 1
            return entry.value

    def set(self, key: str, value: object, ttl_seconds: int | None = None) -> None:
        with self._lock:
            if self.max_entries <= 0:
                return
            if len(self._entries) >= self.max_entries and key not in self._entries:
                now = time.monotonic()
                stale = [k for k, v in self._entries.items() if v.expires_at <= now]
                for k in stale[: max(1, self.max_entries // 10)]:
                    self._entries.pop(k, None)
                while len(self._entries) >= self.max_entries:
                    self._entries.pop(next(iter(self._entries)))
            lifetime = self.ttl_seconds if ttl_seconds is None else ttl_seconds
            self._entries[key] = _Entry(value=value, expires_at=time.monotonic() + lifetime)

    def clear(self) -> int:
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            return count

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "entries": len(self._entries),
                "maxEntries": self.max_entries,
                "hits": self._hits,
                "misses": self._misses,
                "ttlSeconds": self.ttl_seconds,
            }
