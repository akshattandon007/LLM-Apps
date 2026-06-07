"""REST endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from ..models import ChatRequest, ChatResponse, FlightsResponse, Location
from ..services.geocoding import GeocodeError
from ..services.llm import LLMError
from ..services.opensky import OpenSkyError
from .deps import Services, get_services

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
async def health(svc: Services = Depends(get_services)) -> dict:
    return {
        "status": "ok",
        "llm_enabled": svc.settings.llm_enabled,
        "llm_provider": svc.settings.llm_provider,
        "opensky_authenticated": bool(svc.settings.opensky_client_id),
    }


@router.get("/geocode", response_model=Location)
async def geocode(
    q: str = Query(..., description="Place name or 'lat,lon'"),
    svc: Services = Depends(get_services),
) -> Location:
    try:
        return await svc.geocoder.resolve(q)
    except GeocodeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/flights", response_model=FlightsResponse)
async def flights(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float | None = Query(None, gt=0),
    name: str | None = Query(None, description="Optional label for the point"),
    svc: Services = Depends(get_services),
) -> FlightsResponse:
    radius = radius_km or svc.settings.default_radius_km
    location = Location(name=name or f"{lat:.4f}, {lon:.4f}", lat=lat, lon=lon)
    try:
        return await svc.tracker.snapshot(location, radius)
    except OpenSkyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    svc: Services = Depends(get_services),
) -> ChatResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty")
    try:
        return await svc.llm.ask(payload.question, payload.flight)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
