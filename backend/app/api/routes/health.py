from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.models.schemas import HealthResponse

router = APIRouter()


@router.get("/")
def app_home() -> dict[str, Any]:
    return {
        "name": "PitchPro Voice Agent Backend",
        "status": "ok",
        "message": "App backend is running. Use API routes for integrations.",
    }


@router.get("/auth/callback")
def auth_callback_placeholder() -> dict[str, Any]:
    return {
        "status": "ok",
        "message": "Auth callback placeholder reached.",
    }


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    trace_id = request.state.trace_id
    return HealthResponse(trace_id=trace_id, status="ok", version="0.1.0")
