# 🚀 COSMOS — Space Intelligence Agent

> *Real-time space news, mission tracking, and planetary intelligence — powered by Claude AI + live web search.*

[![CI](https://github.com/your-username/cosmos-space-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/cosmos-space-agent/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

COSMOS is an AI agent that connects you to the latest activities across the entire space industry — from NASA deep-space missions to commercial launches, from Mars rovers to exoplanet discoveries. It uses **Claude claude-opus-4-5** with **real-time web search** to pull current data from all major space agencies.

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Conversational Agent** | Multi-turn chat with full context memory |
| 🌐 **Live Web Search** | Queries NASA, ESA, SpaceX, JAXA, ISRO in real-time |
| 🪐 **Planet Tracker** | Deep-dive reports on any planet with mission data |
| 📰 **Space News Feed** | Latest discoveries, launches, and mission updates |
| 🚀 **Launch Tracker** | Upcoming rocket launches worldwide |
| 🔄 **Follow-up Queries** | Context-aware conversation across multiple questions |

## 📁 Repository Structure

```
cosmos-space-agent/
├── src/
│   ├── __init__.py          # Package exports
│   ├── agent.py             # Main conversational agent (multi-turn)
│   ├── space_news.py        # Space news fetcher module
│   └── launch_tracker.py   # Rocket launch tracker
├── scripts/
│   └── planet_tracker.py   # CLI planet tracking tool
├── tests/
│   └── test_agent.py        # Unit test suite
├── docs/
│   └── examples.md          # Usage examples & sample outputs
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI/CD
├── .env.example             # Environment template
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 🛠 Setup

### Prerequisites

- Python 3.10 or higher
- An [Anthropic API key](https://console.anthropic.com)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/cosmos-space-agent.git
cd cosmos-space-agent

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Environment Configuration

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
```

Or export directly:
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

---

## 🚀 Usage

### 1. Interactive Space Agent (Conversational)

The main agent supports multi-turn conversation with full context memory:

```bash
python src/agent.py
```

**Example session:**
```
🚀  COSMOS — Space Intelligence Agent  🌌
Powered by Claude + Real-Time Web Search

You › What's happening on Mars right now?

COSMOS › 🔴 MARS UPDATE (May 2025)
📡 ACTIVE MISSIONS:
• Perseverance Rover — Currently exploring Jezero Crater...
• Ingenuity Helicopter — Completed 72nd flight...
• Mars Odyssey — 24th year of continuous orbiting...

You › What did Perseverance find recently?

COSMOS › Following up on Perseverance...
🏆 RECENT DISCOVERY: On April 28, 2025, the rover detected...
```

### 2. Planet Tracker CLI

Get a comprehensive tracking report for any planet:

```bash
# Single planet
python scripts/planet_tracker.py mars
python scripts/planet_tracker.py jupiter
python scripts/planet_tracker.py saturn

# With extra historical facts
python scripts/planet_tracker.py neptune --facts

# Full solar system dashboard
python scripts/planet_tracker.py all
```

**Example output for `python scripts/planet_tracker.py mars`:**

```
═══════════════════════════════════════════════════════════
  🪐  COSMOS Planet Tracker
  Target: Mars
═══════════════════════════════════════════════════════════

🔭 Scanning telemetry for Mars...

🌍 BASIC PROFILE
Type: Terrestrial rocky planet
Diameter: 6,779 km (0.532× Earth)
Mass: 6.39 × 10²³ kg
Orbital Period: 686.97 Earth days
Distance from Sun: 1.524 AU (avg), currently 1.38 AU
Moons: 2 (Phobos, Deimos)

📡 ACTIVE MISSIONS
• NASA Perseverance Rover — Jezero Crater, operational since Feb 2021
  Latest: Collected 23rd rock sample, possible biosignature minerals detected
• NASA Ingenuity Helicopter — 72 flights completed, ~17km total distance
• ESA/Roscosmos Trace Gas Orbiter — Methane monitoring, 7th year
• NASA Mars Odyssey — 24 continuous years in orbit (record)
• ISRO Mars Orbiter Mission 2 — Launch NET 2026

🚀 UPCOMING MISSIONS
• NASA Mars Sample Return — Launch window 2027-2030
• SpaceX Starship Mars Demo — Uncrewed, NET 2026
• ESA ExoMars Rosalind Franklin Rover — Launch 2028

🏆 TRACKING MILESTONES
1. Organic compounds detected in 3.5-billion-year-old lakebed (2024)
2. Dust devil imaged at record 20km height by Perseverance (Jan 2025)
...
```

### 3. Fetch Space News

```bash
# General space news
python src/space_news.py

# Topic-specific
python src/space_news.py "black hole discoveries"
python src/space_news.py "moon missions 2025"
python src/space_news.py "james webb telescope"
```

### 4. Launch Tracker

```bash
# Next 10 launches
python src/launch_tracker.py

# Next 20 launches
python src/launch_tracker.py 20
```

---

## 🧪 Testing

```bash
# Run full test suite
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 🔧 Architecture

```
User Input
    │
    ▼
src/agent.py (COSMOS Agent)
    │
    ├─── System Prompt (COSMOS persona)
    │
    ├─── Claude claude-opus-4-5 (model)
    │         │
    │         └─── web_search tool (real-time)
    │                   │
    │                   ├── NASA (nasa.gov, jpl.nasa.gov)
    │                   ├── ESA (esa.int)
    │                   ├── SpaceX (spacex.com)
    │                   ├── JAXA, ISRO, CNSA
    │                   ├── arXiv (arxiv.org)
    │                   └── Space.com, Sky & Telescope
    │
    └─── Conversation History (multi-turn memory)
              │
              └─── Returned to caller for follow-ups
```

### Key Design Decisions

- **Web search over static data**: Space news changes daily. Every response queries live sources.
- **Single model, multiple modes**: The same Claude claude-opus-4-5 model powers all features, with different system prompts tuned for each task.
- **Conversation history array**: Passed as a parameter so callers control persistence (in-memory, database, file — your choice).
- **No external APIs**: No RocketLaunch.Live, no NASA API keys needed. Claude's web search handles sourcing.

---

## 🌐 Data Sources

COSMOS searches across:

| Agency | Website | Coverage |
|--------|---------|----------|
| NASA | nasa.gov, jpl.nasa.gov | All US missions, APOD, research |
| ESA | esa.int | European missions, Hubble, JWST |
| SpaceX | spacex.com | Falcon 9, Starship, Dragon |
| JAXA | jaxa.jp | Hayabusa, H3 rocket |
| ISRO | isro.gov.in | Chandrayaan, Mangalyaan |
| CNSA | cnsa.gov.cn | Tianwen, Chang'e |
| Roscosmos | roscosmos.ru | Soyuz, ISS, Luna |
| arXiv | arxiv.org | Preprint research papers |
| Space.com | space.com | News aggregation |
| The Planetary Society | planetary.org | Advocacy & research |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/asteroid-tracker`
3. Commit your changes: `git commit -m 'Add asteroid close approach tracker'`
4. Push to the branch: `git push origin feature/asteroid-tracker`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🌟 Acknowledgments

Built with [Anthropic Claude](https://anthropic.com) · Inspired by humanity's drive to explore the cosmos.

*"The cosmos is within us. We are made of star-stuff." — Carl Sagan*
