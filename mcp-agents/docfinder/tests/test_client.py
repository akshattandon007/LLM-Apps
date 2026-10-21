"""Tests for the NPPES API client."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docfinder.nppes_client import NppesClient, Provider, ProviderAddress, ProviderTaxonomy


SAMPLE_PROVIDER_RAW = {
    "number": "1942649421",
    "enumeration_type": "NPI-2",
    "basic": {
        "organization_name": "1 CARE INC.",
        "authorized_official_first_name": "MERLIN",
        "authorized_official_last_name": "KELSICK",
        "first_name": "",
        "last_name": "",
        "credential": "",
        "gender": "",
        "status": "A",
        "enumeration_date": "2013-06-18",
        "last_updated": "2013-06-18",
    },
    "addresses": [
        {
            "address_1": "4800 S CHICAGO BEACH DR",
            "address_2": "SUITE 901N",
            "city": "CHICAGO",
            "state": "IL",
            "postal_code": "606157032",
            "telephone_number": "773-251-4625",
            "fax_number": "773-289-0888",
            "address_purpose": "LOCATION",
            "country_name": "United States",
        }
    ],
    "taxonomies": [
        {
            "code": "101YM0800X",
            "desc": "Counselor, Mental Health",
            "primary": False,
        },
        {
            "code": "208D00000X",
            "desc": "General Practice",
            "primary": True,
        },
    ],
}

SAMPLE_INDIVIDUAL_RAW = {
    "number": "1366148975",
    "enumeration_type": "NPI-1",
    "basic": {
        "first_name": "RACHEL",
        "last_name": "AMSEL",
        "credential": "DDS",
        "gender": "F",
        "status": "A",
        "enumeration_date": "2020-03-17",
    },
    "addresses": [
        {
            "address_1": "123 MAIN ST",
            "city": "STONY BROOK",
            "state": "NY",
            "postal_code": "117903213",
            "telephone_number": "757-724-7291",
            "address_purpose": "LOCATION",
            "country_name": "United States",
        }
    ],
    "taxonomies": [
        {
            "code": "1223G0001X",
            "desc": "Dentist, Pediatric Dentistry",
            "primary": True,
            "license": "123456",
        }
    ],
}


class TestProvider:
    def test_from_api_organization(self):
        """Parse an organization provider."""
        p = Provider.from_api(SAMPLE_PROVIDER_RAW)
        assert p.npi == "1942649421"
        assert p.enumeration_type == "NPI-2"
        assert p.organization_name == "1 CARE INC."
        assert p.display_name == "1 CARE INC."
        assert len(p.addresses) == 1
        assert len(p.taxonomies) == 2
        assert p.primary_taxonomy is not None
        assert p.primary_taxonomy.desc == "General Practice"
        assert p.phone == "773-251-4625"

    def test_from_api_individual(self):
        """Parse an individual provider."""
        p = Provider.from_api(SAMPLE_INDIVIDUAL_RAW)
        assert p.npi == "1366148975"
        assert p.enumeration_type == "NPI-1"
        assert p.first_name == "RACHEL"
        assert p.last_name == "AMSEL"
        assert p.display_name == "RACHEL AMSEL, DDS"
        assert p.credential == "DDS"
        assert p.gender == "F"
        assert len(p.taxonomies) == 1
        assert p.primary_taxonomy is not None
        assert p.primary_taxonomy.desc == "Dentist, Pediatric Dentistry"
        assert p.phone == "757-724-7291"

    def test_summary_line(self):
        """Summary line format."""
        p = Provider.from_api(SAMPLE_INDIVIDUAL_RAW)
        summary = p.summary_line()
        assert "RACHEL AMSEL" in summary
        assert "Dentist" in summary
        assert "1366148975" not in summary  # NPI should not be in summary

    def test_full_report(self):
        """Full report format."""
        p = Provider.from_api(SAMPLE_PROVIDER_RAW)
        report = p.full_report()
        assert "1 CARE INC." in report
        assert "1942649421" in report
        assert "CHICAGO" in report
        assert "773-251-4625" in report
        assert "Mental Health" in report
        assert "General Practice" in report

    def test_no_address(self):
        """Provider with no addresses."""
        raw = dict(SAMPLE_INDIVIDUAL_RAW)
        raw["addresses"] = []
        p = Provider.from_api(raw)
        assert p.phone == ""
        assert p.location_address is None


class TestNppesClient:
    @pytest.fixture
    def mock_client(self):
        with patch("httpx.Client") as mock:
            yield mock

    def test_search_providers(self, mock_client):
        """Search providers builds correct params."""
        instance = mock_client.return_value
        instance.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"result_count": 1, "results": [SAMPLE_PROVIDER_RAW]},
            raise_for_status=lambda: None,
        )
        
        client = NppesClient()
        providers, total = client.search_providers(
            city="Chicago", state="IL", taxonomy_description="counselor", limit=5
        )
        
        # Verify request was made
        instance.get.assert_called_once()
        call_args = instance.get.call_args[1]
        assert call_args["params"]["city"] == "Chicago"
        assert call_args["params"]["state"] == "IL"
        assert call_args["params"]["taxonomy_description"] == "counselor"
        assert call_args["params"]["limit"] == 5
        assert call_args["params"]["version"] == "2.1"
        
        assert total == 1
        assert len(providers) == 1
        assert providers[0].npi == "1942649421"

    def test_get_by_npi(self, mock_client):
        """Get by NPI builds correct params."""
        instance = mock_client.return_value
        instance.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"result_count": 1, "results": [SAMPLE_INDIVIDUAL_RAW]},
            raise_for_status=lambda: None,
        )
        
        client = NppesClient()
        p = client.get_by_npi("1366148975")
        
        instance.get.assert_called_once_with(
            "https://npiregistry.cms.hhs.gov/api/",
            params={"version": "2.1", "number": "1366148975"},
        )
        
        assert p is not None
        assert p.npi == "1366148975"

    def test_get_by_npi_not_found(self, mock_client):
        """Get by NPI returns None when not found."""
        instance = mock_client.return_value
        instance.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"result_count": 0, "results": []},
            raise_for_status=lambda: None,
        )
        
        client = NppesClient()
        p = client.get_by_npi("0000000000")
        assert p is None

    def test_search_by_name(self, mock_client):
        """Search by name."""
        instance = mock_client.return_value
        instance.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"result_count": 2, "results": [SAMPLE_INDIVIDUAL_RAW, SAMPLE_PROVIDER_RAW]},
            raise_for_status=lambda: None,
        )
        
        client = NppesClient()
        providers, total = client.search_by_name("Rachel Amsel", state="NY", limit=5)
        
        args = instance.get.call_args[1]["params"]
        assert args["first_name"] == "Rachel"
        assert args["last_name"] == "Amsel"
        assert args["state"] == "NY"
        
        assert total == 2
        assert len(providers) == 2

    def test_find_by_zip(self, mock_client):
        """Find by ZIP code."""
        instance = mock_client.return_value
        instance.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"result_count": 3, "results": [SAMPLE_PROVIDER_RAW]},
            raise_for_status=lambda: None,
        )
        
        client = NppesClient()
        providers, total = client.find_by_zip("60601", taxonomy_description="dentist", limit=3)
        
        args = instance.get.call_args[1]["params"]
        assert args["postal_code"] == "60601"
        assert args["taxonomy_description"] == "dentist"
        
        assert total == 3