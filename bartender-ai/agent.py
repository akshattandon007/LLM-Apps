"""
BartenderAI Agent
=================
An AI-powered bartender agent that:
  1. Detects user location & live weather via Open-Meteo
  2. Searches TikTok, YouTube, Instagram, X/Twitter, Reddit, and bar-industry
     sites for genuinely trending cocktails
  3. Personalises recommendations to the user's region, weather, and season
  4. Offers a "Make My Cocktail" mode — give it your ingredients and it
     searches the web for the best matching recipe

Model  : claude-opus-4-5  (Anthropic)
Search : web_search_20250305 tool (built-in to Claude API)
Weather: Open-Meteo (free, no key required)
Geo    : ip-api.com  (free, no key required)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Any

import httpx
import anthropic

# ── constants ────────────────────────────────────────────────────────────────

MODEL = "claude-opus-4-5"
MAX_TOKENS = 4096

WEB_SEARCH_TOOL: dict[str, Any] = {
    "type": "web_search_20250305",
    "name": "web_search",
}

SEASONS = {
    (12, 1, 2): "Winter",
    (3, 4, 5):  "Spring",
    (6, 7, 8):  "Summer",
    (9, 10, 11): "Autumn",
}

WMO_CODES: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle",
    55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Rain showers",
    85: "Snow showers", 95: "Thunderstorm",
}

# ── helpers ───────────────────────────────────────────────────────────────────

def get_season() -> str:
    month = datetime.now().month
    for months, name in SEASONS.items():
        if month in months:
            return name
    return "Winter"


def get_location() -> dict[str, Any]:
    """Detect city/country from public IP via ip-api.com (no key needed)."""
    try:
        r = httpx.get("http://ip-api.com/json/", timeout=5)
        d = r.json()
        if d.get("status") == "success":
            return {
                "city":    d.get("city", "London"),
                "country": d.get("country", "UK"),
                "lat":     d.get("lat", 51.5),
                "lon":     d.get("lon", -0.12),
            }
    except Exception:
        pass
    return {"city": "London", "country": "UK", "lat": 51.5, "lon": -0.12}


def get_weather(lat: float, lon: float) -> dict[str, Any]:
    """Fetch current conditions from Open-Meteo (free, no API key)."""
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current_weather=true&temperature_unit=celsius"
        )
        r = httpx.get(url, timeout=5)
        cw = r.json()["current_weather"]
        code = cw["weathercode"]
        desc = next(
            (v for k, v in sorted(WMO_CODES.items(), reverse=True) if code >= k),
            "Mild",
        )
        return {"temp": round(cw["temperature"]), "desc": desc, "unit": "°C"}
    except Exception:
        return {"temp": 15, "desc": "Mild", "unit": "°C"}


def extract_text(response: anthropic.types.Message) -> str:
    """Pull text blocks from a Claude message, strip JSON fences."""
    raw = "\n".join(
        block.text for block in response.content if block.type == "text"
    )
    return raw.replace("```json", "").replace("```", "").strip()


def parse_json(text: str) -> Any:
    """Best-effort JSON parse with helpful error."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Claude did not return valid JSON.\nRaw output:\n{text[:600]}"
        ) from exc


# ── core agent calls ──────────────────────────────────────────────────────────

def build_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()   # reads ANTHROPIC_API_KEY from env


def get_trending_cocktails(
    client: anthropic.Anthropic,
    location: dict[str, Any],
    weather: dict[str, Any],
    season: str,
) -> list[dict[str, Any]]:
    """
    Ask Claude (with web search) for the top-5 trending cocktails,
    personalised to location + weather + season.

    Sources searched: TikTok, YouTube, Instagram, X/Twitter, Reddit,
    Difford's Guide, Imbibe Magazine, Punch Drink, bar-industry reports.
    """

    system = (
        "You are an expert AI mixologist and trend analyst. "
        "You use web search aggressively across TikTok aggregators, "
        "YouTube trending videos, Reddit communities (r/cocktails, "
        "r/bartenders, r/mixology), X/Twitter public posts, Instagram "
        "highlight sites, Difford's Guide, Punch Drink, Imbibe Magazine, "
        "and bar-industry trend reports. "
        "You respond ONLY in valid JSON — no markdown, no preamble."
    )

    user = f"""
Search the web to find the TOP 5 trending cocktails RIGHT NOW.
Query each of these sources separately:

1. TikTok  – search "tiktok viral cocktail 2025" and "trending cocktails tiktok drinkTok"
2. YouTube – search "trending cocktail recipes youtube 2025" popular bartender channels
3. Reddit  – search "trending cocktails reddit 2025" r/cocktails r/bartenders top posts
4. X/Twitter – search "trending cocktail 2025 twitter"
5. Instagram – search "trending cocktails instagram reels 2025"
6. Industry  – search "cocktail trends 2025 bar industry" "Imbibe cocktail trends 2025"
   and "Difford's Guide trending cocktails"

Personalise the final list for:
- Location : {location['city']}, {location['country']}
- Weather  : {weather['temp']}{weather['unit']}, {weather['desc']}
- Season   : {season}

Return ONLY a JSON array of exactly 5 objects. Each object must have:
  "rank"         : integer 1–5
  "name"         : string  (cocktail name)
  "badge"        : one of  "viral" | "trending" | "seasonal" | "classic" | "rising"
  "description"  : string  ≤120 chars — why it suits the weather/location
  "socialBuzz"   : string  — where it's blowing up (mention platforms + approx views/posts)
  "sources"      : array of strings from: tiktok youtube reddit x instagram bar blog
  "ingredients"  : array of strings with measures (e.g. "60 ml gin")
  "steps"        : array of 4–6 step strings
  "bartenderTip" : string  — one professional tip

JSON array only. Absolutely no other text.
""".strip()

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        tools=[WEB_SEARCH_TOOL],
        messages=[{"role": "user", "content": user}],
    )

    raw = extract_text(response)
    return parse_json(raw)


def make_my_cocktail(
    client: anthropic.Anthropic,
    ingredients: list[str],
) -> dict[str, Any]:
    """
    Given a list of ingredients the user has at home, search the web for
    the best matching cocktail recipe (IBA standards, Difford's, Reddit,
    TikTok/YouTube aggregators, craft bartender blogs).
    """

    system = (
        "You are an expert AI bartender and cocktail researcher. "
        "You search the web across IBA standards, Difford's Guide, "
        "Punch Drink, Reddit r/cocktails, TikTok and YouTube recipe "
        "aggregators, and craft bartender blogs to find the best possible "
        "cocktail recipe for the given ingredients. "
        "Respond ONLY in valid JSON — no markdown, no preamble."
    )

    ing_str = ", ".join(ingredients)
    first_three = ", ".join(ingredients[:3])

    user = f"""
The user has these ingredients: {ing_str}.

Use web search to find the best cocktail recipe. Search:
1. "cocktail recipe with {first_three}"
2. "{ingredients[0]} cocktail recipes 2025"
3. IBA classic cocktails and Difford's Guide database
4. Reddit r/cocktails creative combinations
5. TikTok and YouTube viral recipes with these ingredients

Find the single BEST cocktail that uses as many of these ingredients as
possible. Prioritise well-loved or currently trending recipes.

Return ONLY a JSON object with:
  "name"                 : string (cocktail name)
  "tagline"              : string ≤80 chars (flavour tease)
  "description"          : string (2–3 sentences on origin, flavour, vibe)
  "trendingNote"         : string (where this recipe is popular right now)
  "usedIngredients"      : array of strings (which of the user's ingredients are used)
  "additionalIngredients": array ≤3 strings (extra items needed — keep minimal)
  "ingredients"          : array of strings with full measures
  "steps"                : array of 4–6 step strings
  "bartenderTip"         : string (one professional tip)
  "source"               : string (references found, e.g. "IBA classic · trending on r/cocktails")

JSON object only. No other text.
""".strip()

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        tools=[WEB_SEARCH_TOOL],
        messages=[{"role": "user", "content": user}],
    )

    raw = extract_text(response)
    return parse_json(raw)


# ── display helpers ───────────────────────────────────────────────────────────

BADGE_ICONS = {
    "viral": "🔴", "trending": "🔥", "seasonal": "🍂",
    "classic": "🏆", "rising": "⭐",
}

SOURCE_LABELS = {
    "tiktok": "TikTok", "youtube": "YouTube", "reddit": "Reddit",
    "x": "X/Twitter", "instagram": "Instagram",
    "bar": "Bar Menus", "blog": "Cocktail Blogs",
}


def print_separator(char: str = "─", width: int = 60) -> None:
    print(char * width)


def display_trending(cocktails: list[dict[str, Any]]) -> None:
    print_separator("═")
    print("  🍸  TOP 5 TRENDING COCKTAILS")
    print_separator("═")

    for c in cocktails:
        icon = BADGE_ICONS.get(c.get("badge", ""), "🍹")
        sources = "  ·  ".join(
            SOURCE_LABELS.get(s, s) for s in c.get("sources", [])
        )
        print(f"\n#{c['rank']}  {icon}  {c['name'].upper()}  [{c.get('badge','').upper()}]")
        print_separator()
        print(f"  {c.get('description', '')}")
        print(f"  📣  {c.get('socialBuzz', '')}")
        if sources:
            print(f"  📡  {sources}")

        print("\n  Ingredients:")
        for ing in c.get("ingredients", []):
            print(f"    • {ing}")

        print("\n  Method:")
        for i, step in enumerate(c.get("steps", []), 1):
            print(f"    {i}. {step}")

        if tip := c.get("bartenderTip"):
            print(f"\n  🎩  Bartender tip: {tip}")

    print()
    print_separator("═")


def display_recipe(recipe: dict[str, Any]) -> None:
    print_separator("═")
    print(f"  🍸  {recipe['name'].upper()}")
    print(f"  {recipe.get('tagline', '')}")
    print_separator("═")
    print(f"\n  {recipe.get('description', '')}")

    if note := recipe.get("trendingNote"):
        print(f"\n  📣  {note}")

    if extra := recipe.get("additionalIngredients"):
        print(f"\n  ⚠️   You'll also need: {', '.join(extra)}")

    print("\n  Ingredients:")
    for ing in recipe.get("ingredients", []):
        print(f"    • {ing}")

    print("\n  Method:")
    for i, step in enumerate(recipe.get("steps", []), 1):
        print(f"    {i}. {step}")

    if tip := recipe.get("bartenderTip"):
        print(f"\n  🎩  Bartender tip: {tip}")

    if src := recipe.get("source"):
        print(f"\n  📚  Source: {src}")

    print()
    print_separator("═")


# ── interactive CLI ───────────────────────────────────────────────────────────

def prompt_ingredients() -> list[str]:
    print("\nEnter your ingredients (comma-separated, minimum 2):")
    while True:
        raw = input("  > ").strip()
        items = [i.strip().lower() for i in raw.split(",") if i.strip()]
        if len(items) >= 2:
            return items
        print("  ⚠️  Please enter at least 2 ingredients.")


def main() -> None:
    print("\n" + "═" * 60)
    print("  🍸  BARTENDER AI  —  Powered by Claude claude-opus-4-5")
    print("═" * 60)

    # ── context detection ────────────────────────────────────────
    print("\n📍 Detecting your location…")
    location = get_location()
    print(f"   {location['city']}, {location['country']}")

    print("🌤  Fetching live weather…")
    weather = get_weather(location["lat"], location["lon"])
    print(f"   {weather['temp']}{weather['unit']}  ·  {weather['desc']}")

    season = get_season()
    print(f"🗓  Season: {season}")

    client = build_client()

    # ── main menu loop ────────────────────────────────────────────
    while True:
        print("\n" + "─" * 60)
        print("  What would you like to do?")
        print("  1  →  Show top-5 trending cocktails")
        print("  2  →  Make My Cocktail (enter your ingredients)")
        print("  q  →  Quit")
        choice = input("\n  > ").strip().lower()

        if choice == "1":
            print(
                f"\n🔍  Searching TikTok, YouTube, Instagram, X, Reddit "
                f"and bar industry sites for {location['city']}…\n"
            )
            try:
                cocktails = get_trending_cocktails(client, location, weather, season)
                display_trending(cocktails)
            except Exception as exc:
                print(f"  ❌  Error: {exc}")

        elif choice == "2":
            ingredients = prompt_ingredients()
            print(f"\n🔍  Searching cocktail databases for: {', '.join(ingredients)}…\n")
            try:
                recipe = make_my_cocktail(client, ingredients)
                display_recipe(recipe)
            except Exception as exc:
                print(f"  ❌  Error: {exc}")

        elif choice in ("q", "quit", "exit"):
            print("\n  Cheers! 🥂\n")
            sys.exit(0)

        else:
            print("  Please enter 1, 2, or q.")


if __name__ == "__main__":
    main()
