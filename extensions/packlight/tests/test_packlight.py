"""Tests for Pack Light."""
from pathlib import Path

import yaml
import pytest

from packlight.weather import DayWeather, WeatherClient, WMO_CODES
from packlight.packer import PackingEngine, PackItem


@pytest.fixture
def sample_days():
    """Return a sample 3-day trip: Tokyo, mix of hot and rainy."""
    from datetime import date
    return [
        DayWeather(
            date=date(2026, 10, 15),
            temp_max_c=28.0, temp_min_c=20.0,
            precipitation_mm=0.0, weather_code=0,
            uv_index_max=6.0, wind_speed_max_kmh=15.0,
            daylight_hours=11.0,
        ),
        DayWeather(
            date=date(2026, 10, 16),
            temp_max_c=29.0, temp_min_c=21.0,
            precipitation_mm=5.0, weather_code=61,
            uv_index_max=5.5, wind_speed_max_kmh=20.0,
            daylight_hours=10.5,
        ),
        DayWeather(
            date=date(2026, 10, 17),
            temp_max_c=26.0, temp_min_c=19.0,
            precipitation_mm=2.0, weather_code=80,
            uv_index_max=4.0, wind_speed_max_kmh=35.0,
            daylight_hours=10.0,
        ),
    ]


@pytest.fixture
def cold_days():
    """Return a cold winter trip."""
    from datetime import date
    return [
        DayWeather(
            date=date(2026, 12, 20),
            temp_max_c=-2.0, temp_min_c=-8.0,
            precipitation_mm=3.0, weather_code=73,
            uv_index_max=1.0, wind_speed_max_kmh=25.0,
            daylight_hours=6.0,
        ),
    ]


class TestWeatherClient:
    def test_wmo_code_labels(self):
        """Verify key WMO codes have readable labels."""
        assert WMO_CODES[0] == "Clear"
        assert WMO_CODES[61] == "Slight rain"
        assert WMO_CODES[95] == "Thunderstorm"

    def test_dayweather_weather_label(self):
        """weather_label returns correct string for known codes."""
        d = DayWeather(
            date=None, temp_max_c=0, temp_min_c=0,
            precipitation_mm=0, weather_code=0,
            uv_index_max=0, wind_speed_max_kmh=0, daylight_hours=0,
        )
        assert d.weather_label == "Clear"

    def test_dayweather_unknown_code(self):
        """weather_label falls back to code number for unknown codes."""
        d = DayWeather(
            date=None, temp_max_c=0, temp_min_c=0,
            precipitation_mm=0, weather_code=999,
            uv_index_max=0, wind_speed_max_kmh=0, daylight_hours=0,
        )
        assert "999" in d.weather_label


class TestPackingEngine:
    def test_hot_trip_recommendations(self, sample_days):
        """Hot trip should recommend T-shirts, shorts, sunscreen, hat, sunglasses."""
        engine = PackingEngine()
        items = engine.generate(sample_days)
        item_names = [i.item for i in items]

        assert "T-shirts / short sleeves" in item_names
        assert "Sunscreen (SPF 30+)" in item_names
        assert "Sun hat" in item_names
        assert "Sunglasses" in item_names

    def test_cold_trip_recommendations(self, cold_days):
        """Cold trip should recommend warm coat, gloves, beanie, etc."""
        engine = PackingEngine()
        items = engine.generate(cold_days)
        item_names = [i.item for i in items]

        assert "Warm coat / parka" in item_names
        assert "Gloves" in item_names
        assert "Beanie / warm hat" in item_names
        assert "Snow boots" in item_names

    def test_rain_recommendations(self, sample_days):
        """Trip with rain should recommend umbrella and raincoat."""
        engine = PackingEngine()
        items = engine.generate(sample_days)
        item_names = [i.item for i in items]

        assert "Umbrella" in item_names
        assert "Waterproof jacket / raincoat" in item_names

    def test_wind_recommendations(self, sample_days):
        """Windy trip should recommend windbreaker."""
        engine = PackingEngine()
        items = engine.generate(sample_days)
        item_names = [i.item for i in items]

        # max_wind=35 >= 30 → windbreaker
        assert "Windbreaker" in item_names

    def test_basics_always_included(self, sample_days):
        """Basic items should appear for any trip >= 1 day."""
        engine = PackingEngine()
        items = engine.generate(sample_days)
        item_names = [i.item for i in items]

        assert "Phone charger & cable" in item_names
        assert "Passport / ID" in item_names
        assert "Basic toiletries kit" in item_names

    def test_empty_days_returns_empty(self):
        """Generating for no days returns empty list."""
        engine = PackingEngine()
        assert engine.generate([]) == []

    def test_items_have_categories(self, sample_days):
        """Every recommended item should have a category."""
        engine = PackingEngine()
        items = engine.generate(sample_days)
        for item in items:
            assert item.category, f"Item '{item.item}' missing category"

    def test_default_rules_file_exists(self):
        """The bundled rules.yaml should be readable and valid YAML."""
        path = Path(__file__).parent.parent / "rules.yaml"
        assert path.exists(), "rules.yaml not found"
        with open(path) as f:
            data = yaml.safe_load(f)
        assert "rules" in data, "rules.yaml missing 'rules' key"
        assert len(data["rules"]) > 0, "rules.yaml has no rules"

    def test_engine_loads_custom_rules(self, tmp_path):
        """Engine should load rules from a custom file."""
        from datetime import date
        custom = tmp_path / "my_rules.yaml"
        custom.write_text(yaml.dump({
            "rules": [{
                "item": "Custom item",
                "category": "Test",
                "conditions": {"trip_days": 1},
                "reason": "always pack",
            }],
        }))
        engine = PackingEngine(str(custom))
        day = DayWeather(
            date=date(2026, 10, 15), temp_max_c=20, temp_min_c=15,
            precipitation_mm=0, weather_code=0, uv_index_max=0,
            wind_speed_max_kmh=0, daylight_hours=12,
        )
        items = engine.generate([day])
        item_names = [i.item for i in items]
        assert "Custom item" in item_names