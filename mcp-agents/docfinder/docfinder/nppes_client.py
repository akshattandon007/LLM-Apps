"""NPPES (NPI Registry) API client for DocFinder.

Provides a thread-safe interface to the US CMS NPPES public API.
All endpoints are zero-auth (public API). Rate limiting is per-IP;
this client keeps a shared httpx client with polite timeouts.

API docs: https://npiregistry.cms.hhs.gov/registry/help-api
"""

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

import httpx

BASE_URL = "https://npiregistry.cms.hhs.gov/api/"
TIMEOUT = 15.0


# ── domain types ───────────────────────────────────────────────────────────


@dataclass
class ProviderAddress:
    """A physical or mailing address for a provider."""
    address_1: str = ""
    address_2: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    telephone_number: str = ""
    fax_number: str = ""
    address_purpose: str = ""  # "LOCATION" or "MAILING"
    country_name: str = ""

    def formatted(self) -> str:
        parts = [self.address_1]
        if self.address_2:
            parts.append(self.address_2)
        parts.append(f"{self.city}, {self.state} {self.postal_code}")
        return "\n".join(parts)


@dataclass
class ProviderTaxonomy:
    """A taxonomy classification for a provider."""
    code: str = ""
    desc: str = ""
    primary: bool = False
    state: str = ""
    license_number: str = ""

    def formatted(self) -> str:
        label = self.desc or self.code
        if self.primary:
            label += " (primary)"
        if self.license_number:
            label += f" | License: {self.license_number}"
        return label


@dataclass
class Provider:
    """A healthcare provider record from the NPPES NPI Registry."""
    npi: str
    enumeration_type: str  # "NPI-1" (individual) or "NPI-2" (organization)
    
    # Individual fields (NPI-1)
    first_name: str = ""
    last_name: str = ""
    middle_name: str = ""
    credential: str = ""
    gender: str = ""
    
    # Organization fields (NPI-2)
    organization_name: str = ""
    authorized_official_name: str = ""
    
    # Common
    addresses: list[ProviderAddress] = field(default_factory=list)
    taxonomies: list[ProviderTaxonomy] = field(default_factory=list)
    sole_proprietor: str = ""
    status: str = ""
    enumeration_date: str = ""
    last_updated: str = ""

    @property
    def display_name(self) -> str:
        """The human-readable name for this provider."""
        if self.enumeration_type == "NPI-2" and self.organization_name:
            return self.organization_name
        parts = [p for p in [self.first_name, self.middle_name, self.last_name] if p]
        name = " ".join(parts) if parts else ""
        if self.credential:
            name += f", {self.credential}"
        return name or "Unknown Provider"

    @property
    def primary_taxonomy(self) -> ProviderTaxonomy | None:
        for t in self.taxonomies:
            if t.primary:
                return t
        return self.taxonomies[0] if self.taxonomies else None

    @property
    def location_address(self) -> ProviderAddress | None:
        """Return the LOCATION address, falling back to first available."""
        for a in self.addresses:
            if a.address_purpose == "LOCATION":
                return a
        return self.addresses[0] if self.addresses else None

    @property
    def phone(self) -> str:
        addr = self.location_address
        return addr.telephone_number if addr else ""

    @classmethod
    def from_api(cls, d: dict[str, Any]) -> "Provider":
        """Build a Provider from the NPPES API response dict."""
        basic = d.get("basic", {})
        enum_type = d.get("enumeration_type", "NPI-1")
        
        p = cls(
            npi=d.get("number", ""),
            enumeration_type=enum_type,
            first_name=basic.get("first_name", ""),
            last_name=basic.get("last_name", ""),
            middle_name=basic.get("middle_name", ""),
            credential=basic.get("credential", ""),
            gender=basic.get("gender", ""),
            organization_name=basic.get("organization_name", ""),
            sole_proprietor=basic.get("sole_proprietor", ""),
            status=basic.get("status", ""),
            enumeration_date=basic.get("enumeration_date", ""),
            last_updated=basic.get("last_updated", ""),
        )
        
        # Build authorized official name for organizations
        auth_first = basic.get("authorized_official_first_name", "")
        auth_last = basic.get("authorized_official_last_name", "")
        if auth_first or auth_last:
            p.authorized_official_name = f"{auth_first} {auth_last}".strip()
        
        # Parse addresses
        for addr in d.get("addresses", []):
            p.addresses.append(ProviderAddress(
                address_1=addr.get("address_1", ""),
                address_2=addr.get("address_2", ""),
                city=addr.get("city", ""),
                state=addr.get("state", ""),
                postal_code=addr.get("postal_code", ""),
                telephone_number=addr.get("telephone_number", ""),
                fax_number=addr.get("fax_number", ""),
                address_purpose=addr.get("address_purpose", ""),
                country_name=addr.get("country_name", ""),
            ))
        
        # Parse taxonomies
        for tax in d.get("taxonomies", []):
            p.taxonomies.append(ProviderTaxonomy(
                code=tax.get("code", ""),
                desc=tax.get("desc", ""),
                primary=tax.get("primary", False),
                state=tax.get("state", ""),
                license_number=tax.get("license", ""),
            ))
        
        return p

    def summary_line(self) -> str:
        """One-line summary for listings."""
        spec = ""
        pt = self.primary_taxonomy
        if pt:
            spec = f" — {pt.desc}" if pt.desc else ""
        loc = self.location_address
        loc_str = f" — {loc.city}, {loc.state}" if loc and loc.city else ""
        phone_str = f" — 📞 {self.phone}" if self.phone else ""
        return f"**{self.display_name}**{spec}{loc_str}{phone_str}"

    def full_report(self) -> str:
        """Multi-line detailed report."""
        lines = [f"🏥 **{self.display_name}**"]
        
        if self.enumeration_type == "NPI-2" and self.organization_name:
            if self.authorized_official_name:
                lines.append(f"   Contact: {self.authorized_official_name}")
        
        lines.append(f"   NPI: `{self.npi}`")
        if self.status:
            lines.append(f"   Status: {self.status}")
        if self.gender:
            lines.append(f"   Gender: {'Male' if self.gender == 'M' else 'Female' if self.gender == 'F' else self.gender}")
        if self.credential:
            lines.append(f"   Credential: {self.credential}")
        
        # Taxonomies
        if self.taxonomies:
            lines.append(f"\n   **Specialties:**")
            for t in self.taxonomies:
                marker = "⭐" if t.primary else "•"
                line = f"   {marker} {t.desc or t.code}"
                if t.license_number:
                    line += f" (License: {t.license_number})"
                lines.append(line)
        
        # Addresses
        for addr in self.addresses:
            purpose = f" ({addr.address_purpose})" if addr.address_purpose else ""
            lines.append(f"\n   **Address{purpose}:**")
            lines.append(f"   {addr.address_1}")
            if addr.address_2:
                lines.append(f"   {addr.address_2}")
            lines.append(f"   {addr.city}, {addr.state} {addr.postal_code}")
            if addr.telephone_number:
                lines.append(f"   📞 {addr.telephone_number}")
            if addr.fax_number:
                lines.append(f"   📠 {addr.fax_number}")
        
        # Identifiers (from raw data)
        raw = getattr(self, '_raw', {})
        identifiers = raw.get("identifiers", [])
        
        return "\n".join(lines)


# ── API client ─────────────────────────────────────────────────────────────


class NppesClient:
    """Thread-safe wrapper around the NPPES NPI Registry public API."""

    def __init__(self) -> None:
        self._client = httpx.Client(timeout=TIMEOUT, follow_redirects=True)

    # ── search endpoints ────────────────────────────────────────────────

    def search_providers(
        self,
        city: str = "",
        state: str = "",
        zip_code: str = "",
        taxonomy_description: str = "",
        taxonomy_code: str = "",
        first_name: str = "",
        last_name: str = "",
        organization_name: str = "",
        enumeration_type: str = "",
        limit: int = 10,
    ) -> tuple[list[Provider], int]:
        """Search the NPI Registry with the given criteria.
        
        Returns (providers, total_count).
        """
        params: dict[str, Any] = {"version": "2.1", "limit": min(limit, 200)}
        
        if city:
            params["city"] = city
        if state:
            params["state"] = state.upper()
        if zip_code:
            params["postal_code"] = zip_code
        if taxonomy_description:
            params["taxonomy_description"] = taxonomy_description
        if taxonomy_code:
            params["taxonomy_code"] = taxonomy_code
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
        if organization_name:
            params["organization_name"] = organization_name
        if enumeration_type:
            params["enumeration_type"] = enumeration_type.upper()

        resp = self._client.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        results = [Provider.from_api(r) for r in data.get("results", [])]
        # Attach raw data for full_report references
        for i, r in enumerate(data.get("results", [])):
            results[i]._raw = r
        
        return results, data.get("result_count", 0)

    def get_by_npi(self, npi: str) -> Provider | None:
        """Look up a single provider by NPI number."""
        resp = self._client.get(
            BASE_URL,
            params={"version": "2.1", "number": npi},
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None
        p = Provider.from_api(results[0])
        p._raw = results[0]
        return p

    def search_by_name(
        self,
        name: str,
        city: str = "",
        state: str = "",
        limit: int = 10,
    ) -> tuple[list[Provider], int]:
        """Search providers by name (matches first, last, or organization)."""
        params: dict[str, Any] = {"version": "2.1", "limit": min(limit, 200)}
        
        # Split name into parts — could be "first last" or organization
        parts = name.strip().split(None, 1)
        if len(parts) == 1:
            # Single word — could be last name or org name
            params["last_name"] = parts[0]
        elif len(parts) >= 2:
            params["first_name"] = parts[0]
            params["last_name"] = parts[1]
        
        if city:
            params["city"] = city
        if state:
            params["state"] = state.upper()

        resp = self._client.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        results = [Provider.from_api(r) for r in data.get("results", [])]
        for i, r in enumerate(data.get("results", [])):
            results[i]._raw = r
        
        return results, data.get("result_count", 0)

    def find_by_zip(
        self,
        zip_code: str,
        taxonomy_description: str = "",
        limit: int = 10,
    ) -> tuple[list[Provider], int]:
        """Find providers near a ZIP code, optionally filtering by specialty."""
        params: dict[str, Any] = {"version": "2.1", "postal_code": zip_code, "limit": min(limit, 200)}
        if taxonomy_description:
            params["taxonomy_description"] = taxonomy_description
        
        resp = self._client.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        results = [Provider.from_api(r) for r in data.get("results", [])]
        for i, r in enumerate(data.get("results", [])):
            results[i]._raw = r
        
        return results, data.get("result_count", 0)

    def close(self) -> None:
        self._client.close()