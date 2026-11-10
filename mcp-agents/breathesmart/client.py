"""
BreatheSmart CLI — test the MCP server by making direct API calls.

Usage:
    python3 client.py air-quality <latitude> <longitude>
    python3 client.py pollen <latitude> <longitude> [days]
    python3 client.py uv <latitude> <longitude>
    python3 client.py summary <latitude> <longitude> [location_name]
"""

import sys
import json
import requests

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def fetch_air_quality(lat, lon, current_params, hourly_params=None, forecast_days=0):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join(current_params),
        "timezone": "auto",
    }
    if hourly_params and forecast_days > 0:
        params["hourly"] = ",".join(hourly_params)
        params["forecast_days"] = min(forecast_days, 7)
    resp = requests.get(AIR_QUALITY_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def cmd_air_quality(lat, lon):
    data = fetch_air_quality(lat, lon, [
        "us_aqi", "european_aqi", "pm2_5", "pm10",
        "ozone", "nitrogen_dioxide", "sulphur_dioxide", "carbon_monoxide",
    ])
    print(json.dumps(data, indent=2))


def cmd_pollen(lat, lon, days=1):
    pollen_params = [
        "alder_pollen", "birch_pollen", "grass_pollen",
        "mugwort_pollen", "olive_pollen", "ragweed_pollen",
    ]
    data = fetch_air_quality(lat, lon, pollen_params, pollen_params, days)
    print(json.dumps(data, indent=2))


def cmd_uv(lat, lon):
    data = fetch_air_quality(lat, lon, ["us_aqi", "uv_index", "uv_index_clear_sky"])
    print(json.dumps(data, indent=2))


def cmd_summary(lat, lon):
    data = fetch_air_quality(lat, lon, [
        "us_aqi", "european_aqi", "pm2_5", "pm10",
        "ozone", "nitrogen_dioxide", "sulphur_dioxide", "carbon_monoxide",
        "uv_index", "uv_index_clear_sky",
        "grass_pollen", "birch_pollen", "alder_pollen",
        "olive_pollen", "ragweed_pollen", "mugwort_pollen",
    ])
    current = data.get("current", {})
    print(f"Location: {lat}, {lon}")
    print(f"US AQI: {current.get('us_aqi', 'N/A')}")
    print(f"UV Index: {current.get('uv_index', 'N/A')}")
    print(f"PM2.5: {current.get('pm2_5', 'N/A')} μg/m³")
    print(f"PM10: {current.get('pm10', 'N/A')} μg/m³")
    print(f"Grass Pollen: {current.get('grass_pollen', 'N/A')} grains/m³")
    print(f"Birch Pollen: {current.get('birch_pollen', 'N/A')} grains/m³")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 client.py <command> <lat> <lon> [days|location_name]")
        sys.exit(1)

    cmd = sys.argv[1]
    lat = float(sys.argv[2])
    lon = float(sys.argv[3])

    if cmd in ("air-quality", "air_quality", "aqi"):
        cmd_air_quality(lat, lon)
    elif cmd == "pollen":
        days = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        cmd_pollen(lat, lon, days)
    elif cmd == "uv":
        cmd_uv(lat, lon)
    elif cmd in ("summary", "health"):
        cmd_summary(lat, lon)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
