"""WebSocket live stream.

The client opens ``/ws/flights?lat=..&lon=..&radius_km=..`` and receives a
fresh ``FlightsResponse`` JSON every ``poll_interval_s`` seconds until it
disconnects. One OpenSky poll per tick, shared shape with the REST endpoint.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ..models import Location
from ..services.opensky import OpenSkyError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/flights")
async def ws_flights(
    websocket: WebSocket,
    lat: float = Query(...),
    lon: float = Query(...),
    radius_km: float | None = Query(None),
    name: str | None = Query(None),
) -> None:
    await websocket.accept()
    svc = websocket.app.state.services
    radius = radius_km or svc.settings.default_radius_km
    location = Location(name=name or f"{lat:.4f}, {lon:.4f}", lat=lat, lon=lon)
    interval = svc.settings.poll_interval_s

    try:
        while True:
            try:
                snapshot = await svc.tracker.snapshot(location, radius)
                await websocket.send_json(
                    {"type": "snapshot", "data": snapshot.model_dump()}
                )
            except OpenSkyError as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
            await asyncio.sleep(interval)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected (%.4f, %.4f)", lat, lon)
    except Exception:  # pragma: no cover - defensive
        logger.exception("Unexpected WebSocket error; closing")
        await websocket.close(code=1011)
