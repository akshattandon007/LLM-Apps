"""Application entry point.

Run with::

    uvicorn flights_over_me.main:app --reload

or simply ``python -m flights_over_me`` (see ``__main__.py``).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api.deps import Services
from .api.routes import router as api_router
from .api.websocket import router as ws_router
from .config import get_settings
from .services.enrichment import EnrichmentClient
from .services.geocoding import Geocoder
from .services.llm import LLMClient
from .services.opensky import OpenSkyClient
from .services.tracker import Tracker

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    logger = logging.getLogger("flights_over_me")

    # One shared, pooled HTTP client for every outbound call.
    http = httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=10.0))
    opensky = OpenSkyClient(settings, http)
    enrichment = EnrichmentClient(settings, http)
    app.state.services = Services(
        settings=settings,
        geocoder=Geocoder(settings, http),
        opensky=opensky,
        enrichment=enrichment,
        tracker=Tracker(settings, opensky, enrichment),
        llm=LLMClient(settings, http),
    )
    logger.info(
        "Flights Over Me v%s ready — LLM=%s, OpenSky auth=%s",
        __version__,
        settings.llm_provider if settings.llm_enabled else "disabled",
        bool(settings.opensky_client_id),
    )
    try:
        yield
    finally:
        await http.aclose()
        logger.info("Shut down cleanly")


app = FastAPI(
    title="Flights Over Me",
    description="Real-time tracker for the aircraft passing overhead. ✈️",
    version=__version__,
    lifespan=lifespan,
)

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


# Serve the static frontend (JS/CSS) under /static.
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
