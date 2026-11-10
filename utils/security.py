"""Security helpers.

RateLimiter is a simple in-memory limiter. It is per-process and resets when the
app restarts or sleeps, so it is a stop-gap. Flask-Limiter replaces it in Phase 10.
"""
import ipaddress
import threading
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, window_seconds=60, max_requests=5):
        self.window = window_seconds
        self.max_requests = max_requests
        self._hits = defaultdict(list)
        self._lock = threading.Lock()  # gunicorn runs several threads

    def is_limited(self, key):
        """Record a hit for `key`. Return True if it is over the limit."""
        now = time.time()
        with self._lock:
            if len(self._hits) > 5000:  # stop memory growing forever
                self._prune(now)
            recent = [t for t in self._hits[key] if now - t < self.window]
            if len(recent) >= self.max_requests:
                self._hits[key] = recent
                return True
            recent.append(now)
            self._hits[key] = recent
            return False

    def _prune(self, now):
        for k in [k for k, v in self._hits.items() if not v or now - v[-1] >= self.window]:
            del self._hits[k]

    def reset(self):
        with self._lock:
            self._hits.clear()


def get_client_ip(req, trust_proxy=False):
    """Best-effort visitor IP for rate limiting.

    Behind Render, every request arrives from Render's proxy, so `remote_addr`
    is the same for everyone. Render sits behind Cloudflare, which sets the
    `True-Client-IP` header; a visitor cannot forge it. We only read it when
    TRUST_PROXY is on, because on a server NOT behind such a proxy anyone could
    send a fake header and dodge the limit.
    """
    if trust_proxy:
        candidate = (req.headers.get("True-Client-IP") or "").strip()
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            pass  # missing or malformed: fall back
    return req.remote_addr or "unknown"
