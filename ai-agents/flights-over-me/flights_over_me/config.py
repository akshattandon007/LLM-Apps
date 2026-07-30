"""Application configuration.

All settings are environment-driven (12-factor). Copy ``.env.example`` to
``.env`` and tweak. Nothing here requires a paid account — every default
points at a free, public data source.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Flights Over Me."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="FOM_",
        extra="ignore",
    )

    # ----- Server -----------------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # ----- Flight data: OpenSky Network ------------------------------------
    # Anonymous access works but is heavily rate-limited (~400 credits/day and
    # 10s resolution). Supplying OAuth2 client credentials raises the ceiling.
    # https://openskynetwork.github.io/opensky-api/
    opensky_base_url: str = "https://opensky-network.org/api"
    opensky_token_url: str = (
        "https://auth.opensky-network.org/auth/realms/"
        "opensky-network/protocol/openid-connect/token"
    )
    opensky_client_id: str | None = None
    opensky_client_secret: str | None = None

    # ----- Enrichment: adsbdb.com (callsign -> route + aircraft type) -------
    adsbdb_base_url: str = "https://api.adsbdb.com/v0"

    # ----- Geocoding: OpenStreetMap Nominatim ------------------------------
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    # Nominatim's usage policy requires an identifying User-Agent.
    user_agent: str = "flights-over-me/1.0 (https://github.com/you/flights-over-me)"

    # ----- Search geometry --------------------------------------------------
    # How far around the point we consider "overhead", in kilometres.
    default_radius_km: float = 50.0
    max_radius_km: float = 250.0
    # How often the live WebSocket pushes a fresh snapshot, in seconds.
    poll_interval_s: float = 10.0

    # ----- LLM (the "ask about this flight" feature) ------------------------
    llm_provider: Literal["anthropic", "openai", "none"] = "anthropic"
    llm_model: str = "claude-sonnet-4-5"
    anthropic_api_key: str | None = Field(default=None)
    openai_api_key: str | None = Field(default=None)
    openai_base_url: str = "https://api.openai.com/v1"
    llm_max_tokens: int = 700

    @property
    def llm_enabled(self) -> bool:
        if self.llm_provider == "none":
            return False
        if self.llm_provider == "anthropic":
            return bool(self.anthropic_api_key)
        if self.llm_provider == "openai":
            return bool(self.openai_api_key)
        return False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
