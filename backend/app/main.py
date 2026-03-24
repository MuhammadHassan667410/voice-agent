from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.api.routes import router
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging, log_event
from app.core.middleware import RequestTimingMiddleware, TraceIdMiddleware

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(settings.app_name)

app = FastAPI(title="AI Shopify Assistant API", version="0.1.0")

app.add_middleware(TraceIdMiddleware)
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or "pending"
    log_event(
        logger,
        "info",
        "http.request.received",
        "request received",
        trace_id=trace_id,
        method=request.method,
        path=request.url.path,
    )
    response = await call_next(request)
    final_trace_id = response.headers.get("X-Trace-Id", trace_id)
    log_event(
        logger,
        "info",
        "http.request.completed",
        "request completed",
        trace_id=final_trace_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )
    return response


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    trace_id = getattr(request.state, "trace_id", "tr_unknown")
    log_event(
        logger,
        "error",
        "http.request.failed",
        exc.message,
        trace_id=trace_id,
        code=exc.code,
        status_code=exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "trace_id": trace_id,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "retryable": exc.retryable,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    trace_id = getattr(request.state, "trace_id", "tr_unknown")
    return JSONResponse(
        status_code=400,
        content={
            "trace_id": trace_id,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "request validation failed",
                "details": {"errors": exc.errors()},
                "retryable": False,
            },
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", "tr_unknown")
    log_event(
        logger,
        "error",
        "http.request.failed",
        "unhandled exception",
        trace_id=trace_id,
        error=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={
            "trace_id": trace_id,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "internal server error",
                "details": {},
                "retryable": False,
            },
        },
    )


app.include_router(router)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
