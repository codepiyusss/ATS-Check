"""Security helpers.

RateLimiter is a simple in-memory limiter carried over from the original app.
It is per-process and resets on restart, so it is only a stop-gap.
It will be replaced by Flask-Limiter (with proxy-aware IPs) in Phase 10.
"""
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, window_seconds=60, max_requests=5):
        self.window = window_seconds
        self.max_requests = max_requests
        self._hits = defaultdict(list)

    def is_limited(self, key):
        """Record a hit for `key`. Return True if it is over the limit."""
        now = time.time()
        recent = [t for t in self._hits[key] if now - t < self.window]
        if len(recent) >= self.max_requests:
            self._hits[key] = recent
            return True
        recent.append(now)
        self._hits[key] = recent
        return False

    def reset(self):
        self._hits.clear()
