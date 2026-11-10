# BreatheSmart 🌬️ — Air Quality & Pollen MCP Agent

**Know before you go.** BreatheSmart gives you real-time air quality, pollen forecasts, and UV index data right in your AI assistant — so you know if it's safe to go outside.

## What It Does

BreatheSmart is an MCP (Model Context Protocol) server that connects to the free [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) (zero-auth, no API key needed). It exposes tools your AI assistant can call to:

- ✅ **Check air quality** — US AQI, European AQI, PM2.5, PM10, Ozone, NO₂, SO₂, CO
- 🌿 **Get pollen forecasts** — Grass, Birch, Alder, Olive, Ragweed, Mugwort levels with trends
- ☀️ **Check UV index** — Current UV with clear-sky estimates and sun protection recommendations
- 🫁 **Get an all-in-one health summary** — Air + pollen + UV with an outdoor activity verdict

## How It Works

Your AI assistant (Claude, ChatGPT, or any MCP-compatible client) connects to BreatheSmart via the MCP protocol. When you ask "Is it safe to run outside today?", the assistant calls BreatheSmart's tools, which fetch live data from Open-Meteo and return human-friendly answers.

## Installation

```bash
# Clone and navigate
cd mcp-agents/breathesmart

# Install dependencies
pip install -r requirements.txt
```

## Usage

### MCP Tools

The server exposes these tools:

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_current_air_quality` | Current AQI + pollutant levels | latitude, longitude |
| `get_pollen_forecast` | Pollen forecast for next N days | latitude, longitude, days (1-7) |
| `get_uv_index` | UV index + sun protection | latitude, longitude |
| `get_health_summary` | All-in-one outdoor activity verdict | latitude, longitude, location_name |

### CLI Testing

```bash
# Current air quality
python3 client.py air-quality 40.7128 -74.0060

# Pollen forecast (3 days)
python3 client.py pollen 51.5074 -0.1278 3

# UV index
python3 client.py uv 48.8566 2.3522

# Full health summary
python3 client.py summary 40.7128 -74.0060 "New York City"
```

### MCP Client Configuration

Add to your MCP client config:

```json
{
  "mcpServers": {
    "breathesmart": {
      "command": "python3",
      "args": ["/path/to/breathesmart/server.py"],
      "env": {}
    }
  }
}
```

## Example Queries

- *"Is it safe to go for a run in Central Park today?"*
- *"How bad are allergies in London right now?"*
- *"Do I need sunscreen if I'm going to the beach in Sydney?"*
- *"What's the air quality like in Tokyo?"*
- *"Should I wear a mask outdoors today?"*

## API Reference

All data comes from [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api):
- **Free & open-source** — no API key required
- **Zero auth** — just pass latitude/longitude
- **Global coverage** — works anywhere on Earth
- **Pollen data** — available primarily in Europe and North America

## Tests

```bash
# Run tests
pytest tests/ -v
```

## License

MIT — built for the LLM-Apps project.
