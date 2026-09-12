# 📺 WhatToWatch — MCP Server for TV & Streaming

> *What's on TV tonight that isn't garbage? Personalized, by genre, right now.*

**WhatToWatch** cuts through the paradox of choice. Tell it your mood, and it tells you exactly what's airing right now or streaming. Powered by TVMaze (60K+ shows, global schedule data).

## MCP Tools

| Tool | Description |
|------|-------------|
| `whats_on_right_now(country)` | Live TV schedule for this exact time slot |
| `whats_on_tonight(genre, country)` | Primetime shows filtered by genre |
| `search_show(query)` | Find any show with network, status, rating, genres, summary |
| `find_similar_shows(show_name)` | Recommendations based on a show you love |
| `daily_schedule(date, country)` | Full day's TV lineup for any date |

## Genre Filtering

Comedy · Drama · Cooking/Food · Reality · Sport · News · Documentary · Sci-Fi · Thriller · Crime · Animation · Romance · Horror · Action · Talk Show

## Countries

US · UK · Canada · Australia (via TVMaze schedule endpoint)

## Usage

```bash
# What's on right now
python main.py right-now --country US

# What's on tonight filtered by genre
python main.py tonight --genre comedy --country UK

# Search for a show
python main.py search "Severance"

# Find shows similar to one you love
python main.py similar "Succession"

# Full day's schedule
python main.py schedule --country US

# Start the MCP server
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

## Quick Start

```bash
pip install -r requirements.txt
python main.py right-now --country US
```

## Testing

```bash
pytest tests/ -v
```

## Project Files

| File | Purpose |
|------|---------|
| `Decisions.md` | Why every architectural choice was made |
| `Flow.md` | Execution trace through files and functions |
| `README.md` | Getting started guide |