"""ASGI security controls: request-size limit, per-client rate limit, response headers.

Pure ASGI middleware (no BaseHTTPMiddleware) so the limits apply before any route or body
parsing runs, and so responses produced by the limits themselves also carry the headers.

- `BodySizeLimit` counts the bytes actually received, so a chunked request without a
  Content-Length header cannot bypass the limit. A declared Content-Length above the limit
  (or one that is not a plain integer) is refused before the body is read.
- `RateLimit` is an in-process token bucket per client key with a bounded number of keys
  (least recently used keys are evicted). The client key comes from `client_key()`:
  with `trusted_proxy_hops == 0` it is the TCP peer address; with N > 0 it is the N-th
  entry from the right of X-Forwarded-For, which is the address appended by the N-th
  trusted proxy and cannot be forged by the client (a client can only prepend entries).
  Anything unusable falls back to the TCP peer, then to one shared "unknown" bucket, so a
  malformed header can never grant a fresh bucket per request.
- `SecurityHeaders` adds CSP, nosniff and Referrer-Policy everywhere; in public-demo mode it
  also adds HSTS and Permissions-Policy, and it always drops any `server` header the app
  sets. (Uvicorn's own `server` header is turned off with `--no-server-header`.)
"""

from __future__ import annotations

import ipaddress
import json
import math
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable, MutableMapping, Sequence
from typing import Any

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
)
HSTS = "max-age=31536000; includeSubDomains"
PERMISSIONS_POLICY = (
    "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), "
    "microphone=(), payment=(), usb=(), interest-cohort=()"
)


async def _send_json(
    send: Send,
    status: int,
    body: dict[str, object],
    extra: Sequence[tuple[bytes, bytes]] = (),
) -> None:
    payload = json.dumps(body).encode()
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(payload)).encode()),
        *extra,
    ]
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": payload, "more_body": False})


def _header(scope: Scope, name: bytes) -> bytes | None:
    for k, v in scope.get("headers") or []:
        if k.lower() == name:
            return bytes(v)
    return None


class BodySizeLimit:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declared = _header(scope, b"content-length")
        if declared is not None:
            text = declared.decode("latin-1").strip()
            if not text.isdigit() or int(text) > self.max_bytes:
                await _send_json(send, 413, {"detail": "request body too large"})
                return
        # Read the whole (small) body up front, counting received bytes, then replay it.
        chunks: list[bytes] = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body = message.get("body", b"") or b""
            size += len(body)
            if size > self.max_bytes:
                await _send_json(send, 413, {"detail": "request body too large"})
                return
            chunks.append(body)
            if not message.get("more_body", False):
                break
        replay: list[Message] = [
            {"type": "http.request", "body": b"".join(chunks), "more_body": False}
        ]

        async def replay_receive() -> Message:
            if replay:
                return replay.pop()
            return await receive()

        await self.app(scope, replay_receive, send)


def client_key(scope: Scope, trusted_proxy_hops: int) -> str:
    peer = scope.get("client")
    peer_host = peer[0] if peer else None
    if trusted_proxy_hops > 0:
        raw = _header(scope, b"x-forwarded-for")
        if raw is not None:
            hops = [h.strip() for h in raw.decode("latin-1").split(",") if h.strip()]
            if len(hops) >= trusted_proxy_hops:
                candidate = hops[-trusted_proxy_hops]
                try:
                    return str(ipaddress.ip_address(candidate))
                except ValueError:
                    pass
    if peer_host:
        try:
            return str(ipaddress.ip_address(peer_host))
        except ValueError:
            return "unknown"
    return "unknown"


class RateLimit:
    def __init__(
        self,
        app: ASGIApp,
        per_minute: int,
        burst: int,
        trusted_proxy_hops: int = 0,
        max_clients: int = 10_000,
        prefix: str = "/api/",
        exempt: frozenset[str] = frozenset({"/api/health", "/api/ready"}),
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if per_minute <= 0 or burst <= 0 or max_clients <= 0:
            raise ValueError("rate limit values must be positive")
        self.app = app
        self.rate = per_minute / 60.0
        self.burst = float(burst)
        self.hops = trusted_proxy_hops
        self.max_clients = max_clients
        self.prefix = prefix
        self.exempt = exempt
        self.clock = clock
        self.buckets: OrderedDict[str, tuple[float, float]] = OrderedDict()

    def _take(self, key: str) -> float:
        """Spend one token; return 0 if allowed, else seconds until a token is available."""
        now = self.clock()
        tokens, last = self.buckets.pop(key, (self.burst, now))
        tokens = min(self.burst, tokens + (now - last) * self.rate)
        wait = 0.0
        if tokens >= 1.0:
            tokens -= 1.0
        else:
            wait = (1.0 - tokens) / self.rate
        self.buckets[key] = (tokens, now)
        while len(self.buckets) > self.max_clients:
            self.buckets.popitem(last=False)
        return wait

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        if scope["type"] != "http" or not path.startswith(self.prefix) or path in self.exempt:
            await self.app(scope, receive, send)
            return
        wait = self._take(client_key(scope, self.hops))
        if wait > 0:
            retry = str(max(1, math.ceil(wait))).encode()
            await _send_json(
                send, 429, {"detail": "rate limit exceeded"}, [(b"retry-after", retry)]
            )
            return
        await self.app(scope, receive, send)


class SecurityHeaders:
    def __init__(self, app: ASGIApp, public_demo: bool) -> None:
        self.app = app
        self.public_demo = public_demo

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        added = [
            (b"content-security-policy", CSP.encode()),
            (b"x-content-type-options", b"nosniff"),
            (b"referrer-policy", b"no-referrer"),
        ]
        if self.public_demo:
            added += [
                (b"strict-transport-security", HSTS.encode()),
                (b"permissions-policy", PERMISSIONS_POLICY.encode()),
            ]
        names = {k for k, _ in added} | {b"server"}

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                kept = [(k, v) for k, v in message.get("headers", []) if k.lower() not in names]
                message["headers"] = kept + added
            await send(message)

        await self.app(scope, receive, send_with_headers)
