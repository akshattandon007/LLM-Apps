"""Pydantic models for MarketFinder data types."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Program(str, Enum):
    """Federal food assistance programs for market filtering."""

    SNAP = "SNAP"
    WIC = "WIC"
    WICcash = "WICcash"
    SFMNP = "SFMNP"
    all = "all"


class Market(BaseModel):
    """A farmers market, on-farm market, or food hub."""

    id: str = ""
    market_name: str = ""
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance: Optional[str] = None
    accepts_snap: bool = False
    accepts_wic: bool = False
    accepts_wic_cash: bool = False
    accepts_sfmnp: bool = False
    organic: bool = False
    products: Optional[str] = None
    season_dates: Optional[str] = None
    season_hours: Optional[str] = None
    website: Optional[str] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    youtube: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class MarketDetails(Market):
    """Extended market info including schedule, directions, and links."""

    schedule: Optional[str] = None
    directions: Optional[str] = None
    market_link: Optional[str] = None


class CSALocation(BaseModel):
    """A Community Supported Agriculture pickup or farm location."""

    id: str = ""
    operation_name: str = ""
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    distance: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    website: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None


class MarketSearchResult(BaseModel):
    """Result wrapper for a ZIP-based market search."""

    count: int = 0
    zip: str = ""
    radius_miles: int = 10
    markets: list[Market] = Field(default_factory=list)


class CSASearchResult(BaseModel):
    """Result wrapper for a CSA location search."""

    count: int = 0
    zip: str = ""
    csa_locations: list[CSALocation] = Field(default_factory=list)