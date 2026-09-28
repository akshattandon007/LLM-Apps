"""
OpenFDA API client for drug label, adverse events, and NDC lookups.

All endpoints are free and require no API key.
Rate limit: ~240 requests/minute with a User-Agent header.
"""

import math
from typing import Any

import httpx

BASE_URL = "https://api.fda.gov"
TIMEOUT_SECS = 15
MAX_PAGE_SIZE = 100


class OpenFDAClient:
    """Thin client wrapping the three main OpenFDA drug endpoints."""

    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self._http = http_client or httpx.Client(
            headers={"User-Agent": "MediMate-MCP/0.1"},
            timeout=TIMEOUT_SECS,
        )

    # ── Drug label endpoint ──────────────────────────────────────

    def search_drug(self, query: str, limit: int = 10) -> dict[str, Any]:
        """Search the drug/label endpoint by brand name, generic name, or active ingredient.

        Returns full label data including warnings, interactions, ingredients.
        """
        params = self._search_params(query, limit)
        return self._get("/drug/label.json", params)

    def get_by_ndc(self, ndc: str) -> dict[str, Any]:
        """Lookup drug product by exact NDC code via the NDC endpoint."""
        params = {"search": f"product_ndc:{ndc}", "limit": 5}
        return self._get("/drug/ndc.json", params)

    def get_label_by_ndc(self, ndc: str) -> dict[str, Any]:
        """Lookup drug label by NDC (packaged product code)."""
        params = {"search": f"openfda.package_ndc:{ndc}", "limit": 5}
        return self._get("/drug/label.json", params)

    def find_generic_brands(self, generic_name: str, limit: int = 20) -> dict[str, Any]:
        """Find brand-name drugs for a given generic/substance name."""
        params = {"search": f"openfda.substance_name:{generic_name}", "limit": limit}
        return self._get("/drug/label.json", params)

    def browse_ingredients(self, limit: int = 50, page: int = 1) -> dict[str, Any]:
        """Browse recently updated drug labels (pagination helper)."""
        skip = (page - 1) * limit
        params = {"limit": min(limit, MAX_PAGE_SIZE), "skip": skip}
        return self._get("/drug/label.json", params)

    # ── Adverse events endpoint ─────────────────────────────────

    def get_adverse_events(
        self, query: str, limit: int = 10
    ) -> dict[str, Any]:
        """Search the adverse drug event report database.

        ``query`` can be a drug name, active ingredient, or generic name.
        Returns patient-side effects, outcomes, and reporter info.
        """
        params = {
            "search": f"patient.drug.medicinalproduct:\"{query}\"",
            "limit": min(limit, MAX_PAGE_SIZE),
        }
        return self._get("/drug/event.json", params)

    def adverse_event_reactions(
        self, drug_name: str, limit: int = 10
    ) -> dict[str, Any]:
        """List most-reported adverse reactions for a drug."""
        params = {
            "search": f"patient.drug.medicinalproduct:\"{drug_name}\"",
            "limit": limit,
        }
        return self._get("/drug/event.json", params)

    # ── NDC product endpoint ────────────────────────────────────

    def search_ndc(self, query: str, limit: int = 10) -> dict[str, Any]:
        """Search the NDC directory for products matching brand or generic name."""
        params = self._search_params(query, limit)
        return self._get("/drug/ndc.json", params)

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _search_params(query: str, limit: int) -> dict[str, Any]:
        # httpx encodes space as %20 which OpenFDA accepts; avoid + which gets encoded as %2B
        return {
            "search": f"openfda.brand_name:\"{query}\" OR openfda.generic_name:\"{query}\"",
            "limit": min(limit, MAX_PAGE_SIZE),
        }

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{BASE_URL}{path}"
        resp = self._http.get(url, params=params)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        # Flatten results into a friendlier shape
        out = {"meta": data.get("meta", {}), "results": data.get("results", [])}
        out["total"] = out["meta"].get("results", {}).get("total", 0)
        out["pages"] = math.ceil(out["total"] / params.get("limit", 10))

        for r in out["results"]:
            self._enrich_result(r)

        return out

    @staticmethod
    def _enrich_result(result: dict[str, Any]) -> None:
        """Pull relevant summary fields to the top level for LLM readability."""
        ofda = result.get("openfda", {})
        if "brand_name" in ofda:
            result["_brand_name"] = ofda["brand_name"][0] if ofda["brand_name"] else "Unknown"
        if "generic_name" in ofda:
            result["_generic_name"] = ofda["generic_name"][0] if ofda["generic_name"] else ""
        if "substance_name" in ofda:
            result["_active_ingredients"] = ofda["substance_name"]
        if "manufacturer_name" in ofda:
            result["_manufacturer"] = ofda["manufacturer_name"][0] if ofda["manufacturer_name"] else ""

        # Drug label specific
        for field in ("warnings", "drug_interactions", "purpose", "do_not_use",
                       "stop_use", "questions", "pregnancy_or_breast_feeding"):
            if field in result:
                result[f"_{field}"] = "\n".join(result[field]) if isinstance(result[field], list) else result[field]

    def close(self) -> None:
        self._http.close()