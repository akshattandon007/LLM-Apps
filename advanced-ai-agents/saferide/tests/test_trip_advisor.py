"""Tests for the Trip Advisor agent."""

from saferide.agents.trip_advisor import _overall_weather_rating, _build_verdict, build_report
from saferide.models import RouteWeather, SegmentForecast, TripReport, VehicleCheck, Recall


def _make_forecast(temp=20, precip=0, wind=10, hazard=False, condition="clear") -> SegmentForecast:
    return SegmentForecast(
        location="Test",
        lat=40.0,
        lon=-74.0,
        temp_c=temp,
        feels_like_c=temp - 2,
        precip_mm=precip,
        wind_speed_kmh=wind,
        wind_gust_kmh=wind + 5,
        visibility_km=10,
        condition=condition,
        hazard=hazard,
        hazard_note="Hazard detected" if hazard else "",
    )


def test_overall_weather_rating():
    good_fc = _make_forecast()
    hazard_fc = _make_forecast(hazard=True)
    avoid_fcs = [_make_forecast(hazard=True) for _ in range(3)]

    good_weather = RouteWeather(origin_name="A", origin_forecast=good_fc, destination_name="B", destination_forecast=good_fc)
    assert _overall_weather_rating(good_weather) == "good"

    caution_weather = RouteWeather(origin_name="A", origin_forecast=hazard_fc, destination_name="B", destination_forecast=good_fc)
    assert _overall_weather_rating(caution_weather) == "caution"

    avoid_weather = RouteWeather(
        origin_name="A", origin_forecast=avoid_fcs[0],
        destination_name="B", destination_forecast=avoid_fcs[1],
        waypoint_forecasts=[avoid_fcs[2]],
    )
    assert _overall_weather_rating(avoid_weather) == "avoid"


def test_build_verdict_clear():
    v = VehicleCheck(vin=None, make="Toyota", model="Camry", year=2024, status="clear")
    w = RouteWeather(origin_name="A", origin_forecast=_make_forecast(), destination_name="B", destination_forecast=_make_forecast(),
                     overall_rating="good")
    assert "All clear" in _build_verdict(v, w)


def test_build_verdict_recall():
    v = VehicleCheck(
        vin=None, make="Toyota", model="Camry", year=2024, status="recall_found",
        recalls=[Recall(nhtsa_id="X", component="Brakes", summary="Failure", consequence="Risk",
                        remedy="Fix", safety_risk="critical", report_date="2024-01-01")],
        recall_count=1,
    )
    w = RouteWeather(origin_name="A", origin_forecast=_make_forecast(), destination_name="B", destination_forecast=_make_forecast(),
                     overall_rating="good")
    verdict = _build_verdict(v, w)
    assert "recall" in verdict.lower()


def test_build_report_full():
    v = VehicleCheck(vin=None, make="Toyota", model="Camry", year=2024, status="clear")
    fc = _make_forecast()
    report = build_report(v, fc, fc, [], origin_name="NYC", dest_name="LA")
    assert isinstance(report, TripReport)
    assert report.vehicle.make == "Toyota"
    assert "NYC" in report.summary