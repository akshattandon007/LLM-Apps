"""Tests for the NameSage API module."""

from unittest.mock import ANY

import pytest
import httpx

from namesage.api import get_age, get_gender, get_nationality, get_rhymes, fetch_all


@pytest.mark.asyncio
async def test_get_age_success(httpx_mock):
    """Agify returns age prediction."""
    httpx_mock.add_response(
        url="https://api.agify.io/?name=john",
        json={"name": "john", "age": 40, "count": 123456},
    )
    result = await get_age("john")
    assert result["name"] == "john"
    assert result["age"] == 40
    assert result["count"] == 123456


@pytest.mark.asyncio
async def test_get_age_no_data(httpx_mock):
    """Agify returns empty for unknown name."""
    httpx_mock.add_response(
        url="https://api.agify.io/?name=zzzzz",
        json={"name": "zzzzz", "age": None, "count": 0},
    )
    result = await get_age("zzzzz")
    assert result["age"] is None


@pytest.mark.asyncio
async def test_get_age_http_error(httpx_mock):
    """Agify HTTP error returns error dict."""
    httpx_mock.add_response(
        url="https://api.agify.io/?name=john",
        status_code=500,
    )
    result = await get_age("john")
    assert "error" in result


@pytest.mark.asyncio
async def test_get_gender_success(httpx_mock):
    """Genderize returns gender prediction."""
    httpx_mock.add_response(
        url="https://api.genderize.io/?name=alex",
        json={"name": "alex", "gender": "male", "probability": 0.99, "count": 5000},
    )
    result = await get_gender("alex")
    assert result["gender"] == "male"
    assert result["probability"] == 0.99


@pytest.mark.asyncio
async def test_get_nationality_success(httpx_mock):
    """Nationalize returns country probabilities."""
    httpx_mock.add_response(
        url="https://api.nationalize.io/?name=sarah",
        json={
            "name": "sarah",
            "country": [
                {"country_id": "US", "probability": 0.7},
                {"country_id": "GB", "probability": 0.2},
            ],
        },
    )
    result = await get_nationality("sarah")
    assert len(result["country"]) == 2
    assert result["country"][0]["country_id"] == "US"


@pytest.mark.asyncio
async def test_get_rhymes_success(httpx_mock):
    """Datamuse returns rhyming words."""
    httpx_mock.add_response(
        url="https://api.datamuse.com/words?rel_rhy=john",
        json=[
            {"word": "don", "score": 100},
            {"word": "ron", "score": 95},
        ],
    )
    result = await get_rhymes("john")
    assert len(result) == 2
    assert result[0]["word"] == "don"


@pytest.mark.asyncio
async def test_get_rhymes_empty(httpx_mock):
    """Datamuse returns empty list for names with no rhymes."""
    httpx_mock.add_response(
        url="https://api.datamuse.com/words?rel_rhy=xyzzy",
        json=[],
    )
    result = await get_rhymes("xyzzy")
    assert result == []


@pytest.mark.asyncio
async def test_fetch_all_parallel(httpx_mock):
    """fetch_all returns consolidated data from all 4 APIs."""
    # Mock all 4 endpoints
    httpx_mock.add_response(
        url="https://api.agify.io/?name=test",
        json={"name": "test", "age": 25, "count": 100},
    )
    httpx_mock.add_response(
        url="https://api.genderize.io/?name=test",
        json={"name": "test", "gender": "female", "probability": 0.8},
    )
    httpx_mock.add_response(
        url="https://api.nationalize.io/?name=test",
        json={"name": "test", "country": [{"country_id": "US", "probability": 0.9}]},
    )
    httpx_mock.add_response(
        url="https://api.datamuse.com/words?rel_rhy=test",
        json=[{"word": "best", "score": 100}],
    )

    result = await fetch_all("test")
    assert "age" in result
    assert "gender" in result
    assert "nationality" in result
    assert "rhymes" in result
    assert result["age"]["age"] == 25
    assert result["gender"]["gender"] == "female"
    assert result["nationality"]["country"][0]["country_id"] == "US"
    assert result["rhymes"][0]["word"] == "best"


@pytest.mark.asyncio
async def test_get_age_with_client(httpx_mock):
    """get_age works with a provided client."""
    httpx_mock.add_response(
        url="https://api.agify.io/?name=alice",
        json={"name": "alice", "age": 30, "count": 200},
    )
    async with httpx.AsyncClient() as client:
        result = await get_age("alice", client=client)
    assert result["age"] == 30