"""
Tests for triallight — plain-language clinical trial assistant.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path so we can import src.* as a package
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.clinicaltrials import parse_studies, search_studies
from src.geo import format_location_query
from src.models import EligibilityCriterion, Location, StudyProtocol, StudyStatus


# ═══════════════════════════════════════════════════════════════════════
# SAMPLE DATA (matches real ClinicalTrials.gov v2 API structure)
# ═══════════════════════════════════════════════════════════════════════

SAMPLE_API_RESPONSE = {
    "studies": [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT12345678",
                    "briefTitle": "Study of Metformin for Type 2 Diabetes",
                    "officialTitle": "A Randomized Trial of Metformin in Type 2 Diabetes Patients",
                },
                "statusModule": {
                    "overallStatus": "RECRUITING",
                    "startDateStruct": {"date": "2024-01-15"},
                    "completionDateStruct": {"date": "2026-06-30"},
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "University of California", "class": "OTHER"}
                },
                "descriptionModule": {
                    "briefSummary": "This study evaluates the efficacy of metformin in managing blood glucose levels.",
                    "detailedDescription": "A 12-month randomized controlled trial across 5 US sites.",
                },
                "conditionsModule": {
                    "conditions": ["Type 2 Diabetes", "Insulin Resistance"]
                },
                "designModule": {
                    "studyType": "INTERVENTIONAL",
                    "phases": ["PHASE3"],
                    "enrollmentInfo": {"count": 200, "type": "ANTICIPATED"},
                },
                "eligibilityModule": {
                    "eligibilityCriteria": (
                        "Inclusion Criteria:\n"
                        "Diagnosed with type 2 diabetes\n"
                        "Age 18-75 years\n"
                        "Stable metformin dose for 3 months\n"
                        "Exclusion Criteria:\n"
                        "Pregnant or nursing\n"
                        "Severe kidney disease\n"
                        "History of diabetic ketoacidosis\n"
                    )
                },
                "contactsLocationsModule": {
                    "locations": [
                        {
                            "city": "San Francisco",
                            "state": "California",
                            "country": "United States",
                        }
                    ]
                },
            }
        }
    ]
}

SAMPLE_EMPTY_RESPONSE = {"studies": []}


# ═══════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestParseStudies:
    """parse_studies should convert API JSON to StudyProtocol objects."""

    def test_parse_basic(self):
        studies = parse_studies(SAMPLE_API_RESPONSE)
        assert len(studies) == 1
        study = studies[0]
        assert isinstance(study, StudyProtocol)
        assert study.nct_id == "NCT12345678"
        assert "Metformin" in study.brief_title
        assert study.status == StudyStatus.RECRUITING
        assert len(study.conditions) == 2
        assert study.enrollment_count == 200
        assert study.lead_sponsor == "University of California"
        assert "PHASE3" in study.phase

    def test_parse_eligibility_criteria(self):
        studies = parse_studies(SAMPLE_API_RESPONSE)
        study = studies[0]
        criteria = study.eligibility_criteria
        assert len(criteria) >= 4
        assert any(c.category == "INCLUSION" for c in criteria)
        assert any(c.category == "EXCLUSION" for c in criteria)

    def test_parse_locations(self):
        studies = parse_studies(SAMPLE_API_RESPONSE)
        study = studies[0]
        assert len(study.locations) == 1
        assert study.locations[0].city == "San Francisco"
        assert study.locations[0].state == "California"

    def test_parse_empty(self):
        studies = parse_studies(SAMPLE_EMPTY_RESPONSE)
        assert studies == []

    def test_parse_unknown_status(self):
        resp = json.loads(json.dumps(SAMPLE_API_RESPONSE))
        resp["studies"][0]["protocolSection"]["statusModule"]["overallStatus"] = "SOME_STATUS"
        studies = parse_studies(resp)
        assert studies[0].status == StudyStatus.UNKNOWN

    def test_parse_url(self):
        studies = parse_studies(SAMPLE_API_RESPONSE)
        assert studies[0].url == "https://clinicaltrials.gov/study/NCT12345678"


@patch("src.clinicaltrials.requests.get")
class TestSearchStudies:
    """search_studies should hit the ClinicalTrials.gov API."""

    def test_search_success(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.json.return_value = SAMPLE_API_RESPONSE

        result = search_studies("diabetes", page_size=5)
        # Should have studies
        assert "studies" in result
        mock_get.assert_called_once()
        called_params = mock_get.call_args[1]["params"]
        assert "query.cond" in called_params

    def test_search_with_location(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.json.return_value = SAMPLE_API_RESPONSE

        search_studies("asthma", page_size=3, location_query="San Francisco")
        called_params = mock_get.call_args[1]["params"]
        assert "query.locn" in called_params
        assert called_params["query.locn"] == "San Francisco"


class TestGeo:
    """Geo module tests."""

    def test_format_location_query(self):
        result = format_location_query("San Francisco")
        # URL-encoded spaces
        assert "San%20Francisco" in result
        assert "United%20States" in result or "United States" in result

    def test_format_location_query_special_chars(self):
        result = format_location_query("St. Louis")
        assert result


class TestModels:
    """Model data classes."""

    def test_study_protocol_defaults(self):
        s = StudyProtocol(nct_id="NCT000", brief_title="Test")
        assert s.status == StudyStatus.UNKNOWN
        assert s.conditions == []
        assert s.locations == []
        assert s.eligibility_criteria == []
        # url is set from nct_id during parse_studies, not the constructor

    def test_eligibility_criterion(self):
        c = EligibilityCriterion(category="INCLUSION", text="Must be 18+")
        assert c.category == "INCLUSION"
        assert c.text == "Must be 18+"

    def test_location(self):
        loc = Location(city="Boston", state="Massachusetts", country="USA")
        assert loc.city == "Boston"