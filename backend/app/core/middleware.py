from __future__ import annotations

import time
import uuid
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = request.headers.get("X-Trace-Id") or f"tr_{uuid.uuid4().hex}"
        request.state.trace_id = trace_id

        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response
