"""Tests for the fetcher module — CIK resolution and filing search."""

import json
from datetime import date
from unittest.mock import patch

import httpx
import pytest

from mintdocs.fetcher import Fetcher, FetcherError


class TestCIKResolution:
    """Tests for resolving ticker -> CIK."""

    def test_simulate_cik(self):
        """Simulated mode should return a hardcoded CIK."""
        fetcher = Fetcher(simulate=True)
        cik = fetcher.resolve_cik("AAPL")
        assert cik == "0000320193"
        fetcher.close()

    def test_simulate_company_name(self):
        """Simulated mode returns a formatted company name."""
        fetcher = Fetcher(simulate=True)
        name = fetcher.resolve_company_name("AAPL")
        assert "Simulated" in name
        fetcher.close()

    @patch.object(Fetcher, "_load_cik_map")
    def test_real_cik_resolution(self, mock_load):
        """Resolve CIK from the loaded ticker map."""
        mock_load.return_value = {
            "AAPL": {"cik": "0000320193", "name": "Apple Inc."},
            "MSFT": {"cik": "0000789019", "name": "Microsoft Corporation"},
        }
        fetcher = Fetcher(simulate=False)
        cik = fetcher.resolve_cik("AAPL")
        assert cik == "0000320193"
        fetcher.close()

    @patch.object(Fetcher, "_load_cik_map")
    def test_case_insensitive_ticker(self, mock_load):
        """Ticker lookup should be case-insensitive."""
        mock_load.return_value = {
            "AAPL": {"cik": "0000320193", "name": "Apple Inc."},
        }
        fetcher = Fetcher(simulate=False)
        cik = fetcher.resolve_cik("aapl")
        assert cik == "0000320193"
        fetcher.close()

    @patch.object(Fetcher, "_load_cik_map")
    def test_unknown_ticker_raises(self, mock_load):
        """Unknown tickers should raise FetcherError."""
        mock_load.return_value = {}
        fetcher = Fetcher(simulate=False)
        with pytest.raises(FetcherError, match="not found"):
            fetcher.resolve_cik("ZZZZ")
        fetcher.close()


class TestFilingSearch:
    """Tests for searching filings via EFTS."""

    def test_simulate_search(self):
        """Simulated search returns realistic fake results."""
        fetcher = Fetcher(simulate=True)
        results = fetcher.search_filings("AAPL", quarters=4)
        assert len(results) == 4
        assert all(r["ticker"] == "AAPL" for r in results)
        assert all(r["cik"] == "0000320193" for r in results)
        assert any(r["filing_type"] == "10-K" for r in results)
        assert any(r["filing_type"] == "10-Q" for r in results)
        fetcher.close()

    def test_simulate_search_custom_forms(self):
        """Simulated search respects custom form types."""
        fetcher = Fetcher(simulate=True)
        results = fetcher.search_filings("MSFT", forms=["10-K"], quarters=4)
        assert len(results) == 4
        assert all(r["ticker"] == "MSFT" for r in results)
        fetcher.close()


class TestFilingFetch:
    """Tests for filing text download."""

    def test_simulate_fetch_10k(self):
        """Simulated 10-K fetch returns realistic text with Item sections."""
        fetcher = Fetcher(simulate=True)
        filing = {
            "filing_type": "10-K",
            "company_name": "Apple Inc.",
            "filing_date": "2024-10-31",
            "cik": "0000320193",
            "ticker": "AAPL",
            "accession_number": "000032019324000001",
            "primary_doc": "https://www.sec.gov/Archives/edgar/data/0000320193/...",
        }
        text = fetcher.fetch_filing_text(filing)
        assert "Item 1. Business" in text
        assert "Item 1A. Risk Factors" in text
        assert "Item 7. Management" in text
        fetcher.close()

    def test_simulate_fetch_10q(self):
        """Simulated 10-Q fetch returns realistic text."""
        fetcher = Fetcher(simulate=True)
        filing = {
            "filing_type": "10-Q",
            "company_name": "Apple Inc.",
            "filing_date": "2024-07-27",
            "cik": "0000320193",
            "ticker": "AAPL",
            "accession_number": "000032019324000002",
            "primary_doc": "",
        }
        text = fetcher.fetch_filing_text(filing)
        assert "FORM 10-Q" in text
        assert "Item 1. Financial" in text
        assert "Item 2. Management" in text
        fetcher.close()


class TestFetchAll:
    """Tests for the high-level fetch_all method."""

    def test_simulate_fetch_all(self):
        """fetch_all returns FilingMetadata objects in simulated mode."""
        fetcher = Fetcher(simulate=True)
        metadata_list = fetcher.fetch_all("AAPL", quarters=3)
        assert len(metadata_list) == 3
        for m in metadata_list:
            assert m.ticker == "AAPL"
            assert m.cik == "0000320193"
            assert m.company_name == "AAPL Inc. (Simulated)"
            assert m.filing_type in ("10-K", "10-Q")
            assert isinstance(m.filing_date, date)
        fetcher.close()