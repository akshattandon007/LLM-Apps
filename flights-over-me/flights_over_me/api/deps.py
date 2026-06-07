"""Dependency providers.

Services are constructed once at startup (see ``main.lifespan``) and stashed
on ``app.state``. These helpers expose them to route handlers via FastAPI's
``Depends`` while keeping the handlers free of construction logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from ..config import Settings
from ..services.enrichment import EnrichmentClient
from ..services.geocoding import Geocoder
from ..services.llm import LLMClient
from ..services.opensky import OpenSkyClient
from ..services.tracker import Tracker


@dataclass
class Services:
    settings: Settings
    geocoder: Geocoder
    opensky: OpenSkyClient
    enrichment: EnrichmentClient
    tracker: Tracker
    llm: LLMClient


def get_services(request: Request) -> Services:
    return request.app.state.services


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.services.settings
