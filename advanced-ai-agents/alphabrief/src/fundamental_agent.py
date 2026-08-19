"""Fundamental Agent — fetches SEC EDGAR filings and extracts key changes.

Module-level _client singleton pattern for injectable test mocks.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Optional

import httpx

from .models import FundamentalChange, FundamentalReport

logger = logging.getLogger(__name__)

_client: Optional["FakeSECish"] = None
_httpx_client: Optional[httpx.Client] = None


def set_client(client) -> None:
    global _client
    _client = client


def reset_client() -> None:
    global _client
    _client = None


SEC_HEADERS = {
    "User-Agent": "AlphaBrief/1.0 (contact@alphabrief.example.com)",
    "Accept-Encoding": "gzip, deflate",
}


def _get_http() -> httpx.Client:
    global _httpx_client
    if _httpx_client is None:
        _httpx_client = httpx.Client(headers=SEC_HEADERS, timeout=30.0)
    return _httpx_client


class FundamentalAgent:
    """Extracts fundamental changes from SEC EDGAR filings."""

    def __init__(self, tickers: list[str]) -> None:
        self.tickers = tickers

    def _get_cik(self, ticker: str) -> Optional[str]:
        """Look up SEC CIK number for a ticker via the EDGAR ticker map."""
        if _client is not None:
            return _client.get_cik(ticker)
        try:
            http = _get_http()
            resp = http.get("https://www.sec.gov/files/company_tickers.json")
            resp.raise_for_status()
            data = resp.json()
            for entry in data.values():
                if entry.get("ticker", "").upper() == ticker.upper():
                    return str(entry["cik_str"]).zfill(10)
        except Exception as exc:
            logger.warning("CIK lookup failed for %s: %s", ticker, exc)
        return None

    def _fetch_filings(self, cik: str, filing_types: Optional[list[str]] = None) -> list[dict]:
        """Fetch recent SEC filings for a CIK via EDGAR RSS/submissions."""
        if _client is not None:
            return _client.get_filings(cik, filing_types)
        filing_types = filing_types or ["10-K", "10-Q", "8-K"]
        try:
            http = _get_http()
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            resp = http.get(url)
            resp.raise_for_status()
            data = resp.json()
            recent = data.get("filings", {}).get("recent", {})
            if not recent:
                return []
            results: list[dict] = []
            forms = recent.get("form", [])
            dates = recent.get("filingDate", [])
            primaries = recent.get("primaryDocument", [])
            descs = recent.get("primaryDocDescription", [])
            for i, form in enumerate(forms):
                if form in filing_types:
                    results.append({
                        "form": form,
                        "date": dates[i] if i < len(dates) else "",
                        "primary_doc": primaries[i] if i < len(primaries) else "",
                        "description": descs[i] if i < len(descs) else "",
                        "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{primaries[i].replace('.txt', '')}/{primaries[i]}" if i < len(primaries) else "",
                    })
            return results[:10]  # limit to 10 most recent
        except Exception as exc:
            logger.warning("EDGAR filing fetch failed for CIK %s: %s", cik, exc)
        return []

    def _parse_summary(self, filing: dict, ticker: str) -> FundamentalChange:
        """Extract key changes from filing metadata."""
        filing_type = filing.get("form", "")
        filing_date_str = filing.get("date", "")
        try:
            fd = date.fromisoformat(filing_date_str) if filing_date_str else date.today()
        except ValueError:
            fd = date.today()
        description = filing.get("description", filing_type)
        key_changes: list[str] = []
        risk_factors: list[str] = []

        if filing_type == "8-K":
            key_changes.append("Material event reported (8-K filed)")
            if description:
                # Try to extract what the event was about
                desc_lower = description.lower()
                if "earnings" in desc_lower:
                    key_changes.append("Earnings release / financial results")
                    risk_factors.append("Earnings surprise risk")
                if "acquisition" in desc_lower or "merger" in desc_lower:
                    key_changes.append("M&A activity announced")
                    risk_factors.append("Integration risk from M&A")
                if "resignation" in desc_lower or "appointment" in desc_lower:
                    key_changes.append("Executive/board change")
                    risk_factors.append("Management transition risk")
                if "dividend" in desc_lower:
                    key_changes.append("Dividend declared or changed")
                if "bankruptcy" in desc_lower or "restructuring" in desc_lower:
                    key_changes.append("Restructuring or bankruptcy filing")
                    risk_factors.append("Solvency risk")
        elif filing_type in ("10-Q", "10-K"):
            period = "annual" if filing_type == "10-K" else "quarterly"
            key_changes.append(f"{period} financial report filed")
            key_changes.append(f"Review for material changes in {period} results")
            risk_factors.append(f"Financial performance risk ({period} variance)")

        return FundamentalChange(
            ticker=ticker, filing_type=filing_type, filing_date=fd,
            summary=description or f"{filing_type} filing on {filing_date_str}",
            key_changes=key_changes, risk_factors=risk_factors,
        )

    def run(self) -> FundamentalReport:
        filings: list[FundamentalChange] = []
        alerts: list[str] = []
        for ticker in self.tickers:
            try:
                cik = self._get_cik(ticker)
                if not cik:
                    alerts.append(f"[{ticker}] Could not find SEC CIK — skipping fundamental analysis")
                    continue
                raw_filings = self._fetch_filings(cik)
                for rf in raw_filings:
                    fc = self._parse_summary(rf, ticker)
                    filings.append(fc)
                    parts = [f"[{ticker}] {fc.filing_type} filed {fc.filing_date}"]
                    if fc.key_changes:
                        parts.append("; ".join(fc.key_changes[:3]))
                    alerts.append(": ".join(parts))
            except Exception as exc:
                logger.warning("Fundamental analysis failed for %s: %s", ticker, exc)
                alerts.append(f"[{ticker}] Fundamental analysis error: {exc}")
        return FundamentalReport(filings=filings, alerts=alerts)