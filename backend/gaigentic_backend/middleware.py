"""Custom middlewares for the application."""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter per client IP."""

    def __init__(self, app, max_requests: int, window_sec: int = 60) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_sec
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        client = request.client.host if request.client else "anonymous"
        now = time.time()
        req_times = self.requests[client]
        req_times[:] = [t for t in req_times if now - t < self.window]
        if len(req_times) >= self.max_requests:
            return Response(status_code=429)
        req_times.append(now)
        return await call_next(request)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record request latency for Prometheus metrics."""

    def __init__(self, app, histogram) -> None:
        super().__init__(app)
        self.histogram = histogram

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start = time.time()
        response = await call_next(request)
        self.histogram.labels(request.method, request.url.path).observe(time.time() - start)
        return response

