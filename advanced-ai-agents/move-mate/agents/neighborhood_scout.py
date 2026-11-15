"""Neighborhood Scout Agent — researches the new neighborhood via free APIs."""

from models import MoveDetails, NeighborhoodInfo
from utils import nominatim_geocode, osm_nearby_amenities, openmeteo_forecast, wikipedia_summary


def run(details: MoveDetails) -> NeighborhoodInfo:
    """Research the neighborhood using free geocoding and OSM APIs."""
    info = NeighborhoodInfo()

    # Try geocoding the new address/zip
    location_query = details.new_address or details.new_zip
    geo = nominatim_geocode(location_query)

    if geo:
        lat, lon = float(geo["lat"]), float(geo["lon"])

        # Get nearby amenities via Overpass API
        info.nearby_amenities = osm_nearby_amenities(lat, lon)

        # Pull a quick city/area description from Wikipedia
        display = geo.get("display_name", "")
        parts = [p.strip() for p in display.split(",")]
        city_part = parts[0] if parts else ""
        summary = wikipedia_summary(city_part, sentences=2)
        if summary:
            info.notes.append(f"About {city_part}: {summary[:300]}")

        # Get weather
        weather = openmeteo_forecast(lat, lon)
        if weather and "daily" in weather:
            daily = weather["daily"]
            if daily.get("temperature_2m_max"):
                highs = daily["temperature_2m_max"]
                lows = daily["temperature_2m_min"]
                avg_high = sum(highs) / len(highs)
                avg_low = sum(lows) / len(lows)
                info.weather_summary = (
                    f"Week ahead: {avg_high:.0f}°F high / {avg_low:.0f}°F low. "
                    f"Check forecast before moving day."
                )
                info.notes.append(info.weather_summary)
    else:
        # Fallback: generic info
        info.notes.append(
            f"Could not geocode '{location_query}' — try providing a full address "
            f"(street + city + state + zip) for detailed neighborhood data."
        )

    if not info.nearby_amenities:
        info.notes.append(
            "Tip: Visit Google Maps or WalkScore.com to explore the new neighborhood "
            "for restaurants, coffee shops, gyms, and other amenities."
        )

    return info