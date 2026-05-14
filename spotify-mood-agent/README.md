# 🎵 Spotify Mood Agent

An AI-powered agent that analyses your Spotify listening history to predict your current emotional state. It combines Spotify's audio features with Claude AI to deliver nuanced mood insights.

---

## How It Works

```
Spotify Recent Tracks
        ↓
  Audio Features (valence, energy, tempo, danceability, ...)
        ↓
  Track Metadata (genres, artist popularity, release era, ...)
        ↓
  Claude AI Agent (multi-step reasoning)
        ↓
  Mood Report (primary mood, confidence, energy level, emotional arc, recommendations)
```

The agent performs **multi-step reasoning**:
1. **Fetch** recent tracks + audio features from Spotify
2. **Enrich** with artist genres and metadata
3. **Analyse** patterns across valence, energy, tempo, instrumentalness, liveness
4. **Detect** emotional trajectory (are you trending happier or sadder?)
5. **Synthesise** a final mood prediction with confidence score

---

## Features

- 🎧 Pulls last N recently played tracks (default: 50)
- 📊 Analyses 13 Spotify audio feature dimensions per track
- 🧠 Claude AI agent with tool-use reasoning loop
- 📈 Detects mood trajectory (improving / declining / stable)
- 🎨 Genre-aware mood context
- 📝 Rich markdown mood report
- 🔄 Streaming CLI output
- 🧪 Full test suite with mocked Spotify responses

---

## Quickstart

### 1. Clone & Install

```bash
git clone https://github.com/yourname/spotify-mood-agent.git
cd spotify-mood-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create an app — set **Redirect URI** to `http://localhost:8888/callback`
3. Copy your **Client ID** and **Client Secret**

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
ANTHROPIC_API_KEY=your_anthropic_key_here
```

### 4. Authenticate with Spotify

```bash
python scripts/authenticate.py
```

This opens a browser for OAuth. After authorising, your token is cached at `.spotify_token_cache`.

### 5. Run the Agent

```bash
python -m src.main
```

Or with options:

```bash
python -m src.main --tracks 30 --output report.md --verbose
```

---

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--tracks` | `50` | Number of recent tracks to analyse |
| `--output` | stdout | Save report to file |
| `--verbose` | false | Show agent reasoning steps |
| `--format` | `rich` | Output format: `rich`, `json`, `markdown` |

---

## Output Example

```
🎵 SPOTIFY MOOD ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analysed 50 tracks from the last 4.2 hours

PRIMARY MOOD:     Melancholic but Hopeful
CONFIDENCE:       87%
ENERGY LEVEL:     Low-Medium (3.2/10)
EMOTIONAL ARC:    📈 Gradually brightening

AUDIO SIGNATURE
  Valence (happiness):   ████░░░░░░  38%
  Energy:                ███░░░░░░░  31%
  Danceability:          █████░░░░░  52%
  Acousticness:          ███████░░░  71%
  Instrumentalness:      ██████░░░░  63%

TOP GENRES:  indie folk · lo-fi · ambient

INSIGHT
You've been gravitating toward introspective, acoustic music — 
a sign of deep reflection. The gradual uptick in valence over 
the last 15 tracks suggests your mood is lifting. The high 
acousticness points to a desire for authenticity and calm.

RECOMMENDATIONS
  • Keep the current vibe: "Holocene" by Bon Iver
  • Gentle mood lift: "Dog Days Are Over" by Florence
  • If you want energy: "Running Up That Hill" by Kate Bush
```

---

## Architecture

```
spotify-mood-agent/
├── src/
│   ├── main.py                  # CLI entry point
│   ├── agent/
│   │   ├── mood_agent.py        # Core agent loop (Claude tool-use)
│   │   ├── tools.py             # Agent tool definitions
│   │   └── prompts.py           # System & analysis prompts
│   ├── spotify/
│   │   ├── client.py            # Spotify API wrapper
│   │   ├── auth.py              # OAuth2 PKCE flow
│   │   └── models.py            # Pydantic data models
│   ├── analysis/
│   │   ├── audio_features.py    # Feature aggregation & stats
│   │   ├── mood_classifier.py   # Rule-based pre-classifier
│   │   └── trajectory.py        # Temporal mood arc detection
│   └── utils/
│       ├── display.py           # Rich terminal output
│       └── cache.py             # Token & response caching
├── tests/
│   ├── test_agent.py
│   ├── test_spotify.py
│   ├── test_analysis.py
│   └── fixtures/                # Mock Spotify API responses
├── scripts/
│   └── authenticate.py          # One-time OAuth setup
├── docs/
│   └── AUDIO_FEATURES.md        # Spotify feature documentation
├── .env.example
├── requirements.txt
└── pyproject.toml
```

---

## Audio Features Reference

| Feature | Range | Mood Signal |
|---------|-------|-------------|
| `valence` | 0–1 | Higher = happier |
| `energy` | 0–1 | Higher = more intense |
| `danceability` | 0–1 | Higher = more rhythmic |
| `acousticness` | 0–1 | Higher = more acoustic/calm |
| `instrumentalness` | 0–1 | Higher = fewer vocals (introspective) |
| `liveness` | 0–1 | Higher = live/social energy |
| `speechiness` | 0–1 | Higher = spoken word / podcasts |
| `tempo` | BPM | Higher = faster, more energetic |
| `loudness` | dB | Higher = more intense |
| `mode` | 0/1 | 1=Major (bright), 0=Minor (dark) |

See [docs/AUDIO_FEATURES.md](docs/AUDIO_FEATURES.md) for full details.

---

## Development

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Lint
ruff check src/
mypy src/
```

---

## License

MIT
