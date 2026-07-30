"""
app.py  —  Flask web interface for BartenderAI
Run with:  python app.py
Then open:  http://localhost:5000
"""

from __future__ import annotations

import json
import os
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import anthropic

from agent import (
    build_client,
    get_location,
    get_weather,
    get_season,
    get_trending_cocktails,
    make_my_cocktail,
)

app = Flask(__name__)
client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global client
    if client is None:
        client = build_client()
    return client


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/context")
def context():
    """Return detected location, weather, and season."""
    location = get_location()
    weather  = get_weather(location["lat"], location["lon"])
    season   = get_season()
    return jsonify({"location": location, "weather": weather, "season": season})


@app.route("/api/trending", methods=["POST"])
def trending():
    """Return top-5 trending cocktails as JSON."""
    body     = request.get_json(force=True)
    location = body.get("location", get_location())
    weather  = body.get("weather",  get_weather(location["lat"], location["lon"]))
    season   = body.get("season",   get_season())
    try:
        cocktails = get_trending_cocktails(get_client(), location, weather, season)
        return jsonify({"cocktails": cocktails})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/make", methods=["POST"])
def make():
    """Return a custom cocktail recipe for the given ingredients."""
    body        = request.get_json(force=True)
    ingredients = body.get("ingredients", [])
    if len(ingredients) < 2:
        return jsonify({"error": "Provide at least 2 ingredients."}), 400
    try:
        recipe = make_my_cocktail(get_client(), ingredients)
        return jsonify({"recipe": recipe})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
