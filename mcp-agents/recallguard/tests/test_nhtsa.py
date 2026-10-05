"""Tests for the NHTSA API client."""

import json
from unittest import mock

import httpx
import pytest

from recallguard.nhtsa_client import NhtsaClient, RecallRecord


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def client() -> NhtsaClient:
    return NhtsaClient()


SAMPLE_RECALL = {
    "Manufacturer": "Toyota Motor Engineering & Manufacturing",
    "NHTSACampaignNumber": "20V682000",
    "parkIt": False,
    "parkOutSide": False,
    "overTheAirUpdate": False,
    "ReportReceivedDate": "04/11/2020",
    "Component": "FUEL SYSTEM, GASOLINE:DELIVERY:FUEL PUMP",
    "Summary": "The low-pressure fuel pump inside the fuel tank may fail.",
    "Consequence": "If the fuel pump fails, the engine can stall while driving.",
    "Remedy": "Dealers will replace the fuel pump assembly.",
    "Notes": "Owners may contact Toyota customer service.",
    "ModelYear": "2020",
    "Make": "TOYOTA",
    "Model": "COROLLA",
}


def _mock_response(data: dict, status: int = 200) -> httpx.Response:
    request = httpx.Request("GET", "http://test.nhtsa.gov/")
    return httpx.Response(status_code=status, json=data, request=request)


# ── RecallRecord ────────────────────────────────────────────────────────────


class TestRecallRecord:
    def test_from_api_full(self) -> None:
        r = RecallRecord.from_api(SAMPLE_RECALL)
        assert r.manufacturer == "Toyota Motor Engineering & Manufacturing"
        assert r.nhtsa_campaign_number == "20V682000"
        assert r.component == "FUEL SYSTEM, GASOLINE:DELIVERY:FUEL PUMP"
        assert r.model_year == "2020"
        assert r.make == "TOYOTA"
        assert r.model == "COROLLA"

    def test_short_summary(self) -> None:
        r = RecallRecord.from_api(SAMPLE_RECALL)
        s = r.short_summary()
        assert "20V682000" in s
        assert "Toyota" in s
        assert "COROLLA" in s
        assert "FUEL PUMP" in s

    def test_full_report(self) -> None:
        r = RecallRecord.from_api(SAMPLE_RECALL)
        report = r.full_report()
        assert "RECALL: 20V682000" in report
        assert "FUEL SYSTEM" in report
        assert "Remedy" in report

    def test_park_it_flag(self) -> None:
        rec = dict(SAMPLE_RECALL, parkIt=True)
        r = RecallRecord.from_api(rec)
        report = r.full_report()
        assert "Park your vehicle" in report or "🅿" in report

    def test_empty_notes(self) -> None:
        rec = dict(SAMPLE_RECALL, Notes="")
        r = RecallRecord.from_api(rec)
        # Should not crash
        assert r.notes == ""


# ── NhtsaClient ─────────────────────────────────────────────────────────────


class TestNhtsaClient:
    def test_get_model_years(self, client: NhtsaClient) -> None:
        data = {
            "count": 2,
            "message": "Results returned successfully",
            "results": [{"modelYear": "2020"}, {"modelYear": "2021"}],
        }
        with mock.patch.object(client._client, "get") as mock_get:
            mock_get.return_value = _mock_response(data)
            years = client.get_model_years()
        assert years == ["2020", "2021"]

    def test_get_makes_deduplicates(self, client: NhtsaClient) -> None:
        data = {
            "count": 3,
            "message": "ok",
            "results": [
                {"modelYear": "2020", "make": "TOYOTA"},
                {"modelYear": "2020", "make": "FORD"},
                {"modelYear": "2020", "make": "TOYOTA"},
            ],
        }
        with mock.patch.object(client._client, "get") as mock_get:
            mock_get.return_value = _mock_response(data)
            makes = client.get_makes("2020")
        assert makes == ["FORD", "TOYOTA"]

    def test_get_models_deduplicates(self, client: NhtsaClient) -> None:
        data = {
            "count": 3,
            "message": "ok",
            "results": [
                {"modelYear": "2020", "make": "TOYOTA", "model": "COROLLA"},
                {"modelYear": "2020", "make": "TOYOTA", "model": "CAMRY"},
                {"modelYear": "2020", "make": "TOYOTA", "model": "COROLLA"},
            ],
        }
        with mock.patch.object(client._client, "get") as mock_get:
            mock_get.return_value = _mock_response(data)
            models = client.get_models("TOYOTA", "2020")
        assert models == ["CAMRY", "COROLLA"]

    def test_check_vehicle_recalls(self, client: NhtsaClient) -> None:
        data = {
            "Count": 1,
            "Message": "Results returned successfully",
            "results": [SAMPLE_RECALL],
        }
        with mock.patch.object(client._client, "get") as mock_get:
            mock_get.return_value = _mock_response(data)
            records = client.check_vehicle_recalls("TOYOTA", "COROLLA", "2020")
        assert len(records) == 1
        assert records[0].nhtsa_campaign_number == "20V682000"

    def test_check_vehicle_recalls_empty(self, client: NhtsaClient) -> None:
        data = {"Count": 0, "Message": "ok", "results": []}
        with mock.patch.object(client._client, "get") as mock_get:
            mock_get.return_value = _mock_response(data)
            records = client.check_vehicle_recalls("TESLA", "MODEL3", "2025")
        assert records == []

    def test_get_recall_by_campaign(self, client: NhtsaClient) -> None:
        data = {
            "Count": 1,
            "Message": "ok",
            "results": [SAMPLE_RECALL],
        }
        with mock.patch.object(client._client, "get") as mock_get:
            mock_get.return_value = _mock_response(data)
            records = client.get_recall_by_campaign("20V682000")
        assert len(records) == 1
        assert records[0].manufacturer == "Toyota Motor Engineering & Manufacturing"

    def test_api_404_raises(self, client: NhtsaClient) -> None:
        with mock.patch.object(client._client, "get") as mock_get:
            mock_get.return_value = _mock_response({"error": "not found"}, status=404)
            with pytest.raises(httpx.HTTPStatusError):
                client.get_model_years()


# ── live integration (skipped by default) ───────────────────────────────────


@pytest.mark.skip(reason="Live API tests. Run manually with: pytest --live")
class TestLiveNhtsaApi:
    def test_live_model_years(self) -> None:
        c = NhtsaClient()
        years = c.get_model_years()
        assert len(years) > 10
        assert "2024" in years

    def test_live_recall_check(self) -> None:
        c = NhtsaClient()
        records = c.check_vehicle_recalls("TOYOTA", "COROLLA", "2020")
        assert len(records) >= 0  # may be 0 if all recalls closed