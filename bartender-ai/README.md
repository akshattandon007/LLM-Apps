# 🍸 BartenderAI

An AI-powered bartender agent that delivers **real-time, personalised cocktail recommendations** by searching TikTok, YouTube, Instagram, X/Twitter, Reddit, and bar-industry sources — then tailoring results to your exact location, live weather, and season.

Built with **Claude claude-opus-4-5** (Anthropic) and the built-in **web search tool**, so every recommendation is researched fresh from the live web, not from a static database.

---

## ✨ Features

| Feature | Detail |
|---|---|
| 📍 **Location-aware** | Auto-detects your city & country via IP geolocation |
| 🌤 **Weather-matched** | Fetches live conditions from Open-Meteo (free, no key) |
| 🔥 **Social intelligence** | Searches TikTok, YouTube, Instagram, X/Twitter, Reddit |
| 📰 **Industry sources** | Difford's Guide, Imbibe Magazine, Punch Drink, bar menus |
| 🍹 **Make My Cocktail** | Enter your ingredients → get a web-researched recipe |
| 🖥 **Two interfaces** | Interactive CLI **and** Flask web UI |
| ✅ **Tested** | Pytest unit tests with mocks for all core functions |

---

## 🏗 Project Structure

```
bartender-ai/
├── agent.py              # Core AI agent — all Claude calls live here
├── app.py                # Flask web server (wraps agent.py)
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template
├── .gitignore
├── templates/
│   └── index.html        # Full web UI (vanilla JS, no framework)
└── tests/
    └── test_agent.py     # Pytest unit tests
```

---

## 🤖 Architecture

```
User Request
     │
     ▼
┌────────────────────────────────────────┐
│              agent.py                  │
│                                        │
│  get_location()  ──► ip-api.com        │
│  get_weather()   ──► Open-Meteo API    │
│  get_season()    ──► datetime          │
│                                        │
│  get_trending_cocktails()              │
│  make_my_cocktail()                    │
│         │                              │
│         ▼                              │
│  anthropic.messages.create(            │
│    model="claude-opus-4-5",            │
│    tools=[web_search_20250305]         │  ──► Live Web Search
│  )                                     │      TikTok · YouTube
│                                        │      Instagram · Reddit
│  extract_text()  ──► parse_json()      │      X/Twitter · Blogs
└────────────────────────────────────────┘
     │
     ├──► CLI (agent.py __main__)
     └──► Web UI (app.py + templates/index.html)
```

### How Claude searches the web

Claude's `web_search_20250305` tool is passed as part of every API call. Claude autonomously decides when and what to search based on the prompt. For trending cocktails, the prompt instructs it to run **six targeted searches** in sequence:

1. `"tiktok viral cocktail 2025"` + `"trending cocktails tiktok drinkTok"`
2. `"trending cocktail recipes youtube 2025"`
3. `"trending cocktails reddit 2025"` (r/cocktails, r/bartenders)
4. `"trending cocktail 2025 twitter"`
5. `"trending cocktails instagram reels 2025"`
6. `"cocktail trends 2025 bar industry"` + Difford's Guide + Imbibe Magazine

Results are then combined with location, weather, and season context to produce a personalised JSON response.

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/bartender-ai.git
cd bartender-ai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your Anthropic API key

```bash
cp .env.example .env
```

Edit `.env` and add your key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Get a key at [console.anthropic.com](https://console.anthropic.com).

Then load it into your shell:

```bash
# macOS / Linux
export ANTHROPIC_API_KEY=$(grep ANTHROPIC_API_KEY .env | cut -d= -f2)

# Or use python-dotenv — it's already in requirements.txt
```

---

## 🖥 Usage

### Option A — CLI (no server needed)

```bash
python agent.py
```

You'll see:

```
════════════════════════════════════════════════════════════
  🍸  BARTENDER AI  —  Powered by Claude claude-opus-4-5
════════════════════════════════════════════════════════════

📍 Detecting your location…
   London, United Kingdom
🌤  Fetching live weather…
   14°C  ·  Overcast
🗓  Season: Spring

────────────────────────────────────────────────────────────
  What would you like to do?
  1  →  Show top-5 trending cocktails
  2  →  Make My Cocktail (enter your ingredients)
  q  →  Quit

  >
```

#### Show trending cocktails

Enter `1`. Claude searches the web and returns:

```
════════════════════════════════════════════════════════════
  🍸  TOP 5 TRENDING COCKTAILS
════════════════════════════════════════════════════════════

#1  🔴  HUGO SPRITZ  [VIRAL]
────────────────────────────────────────────────────────────
  Light elderflower fizz — perfect for London's mild spring evenings.
  📣  Exploding on TikTok #DrinkTok with 80M+ views this month
  📡  TikTok  ·  Instagram  ·  Bar Menus

  Ingredients:
    • 150ml Prosecco
    • 60ml elderflower cordial
    • 30ml soda water
    • Fresh mint sprig
    • Lime slice

  Method:
    1. Fill a large wine glass with ice.
    2. Add elderflower cordial and soda water.
    3. Top with chilled Prosecco.
    4. Garnish with mint and lime.

  🎩  Bartender tip: Freeze the mint briefly to bruise it slightly — releases more aroma.
```

#### Make My Cocktail

Enter `2`, then type your ingredients:

```
Enter your ingredients (comma-separated, minimum 2):
  > gin, lime juice, cucumber, tonic water

🔍  Searching cocktail databases for: gin, lime juice, cucumber, tonic water…

════════════════════════════════════════════════════════════
  🍸  CUCUMBER GIN COOLER
  A crisp, herbaceous twist on the classic G&T.
════════════════════════════════════════════════════════════

  A refreshing summer cocktail that pairs the botanical notes of gin
  with cool cucumber and bright citrus. Popular on craft cocktail menus
  across the UK and trending on r/cocktails.

  📣  Featured in Difford's Guide summer picks · 45k upvotes on r/cocktails

  Ingredients:
    • 50ml London Dry gin
    • 25ml fresh lime juice
    • 6 slices cucumber
    • 150ml premium tonic water
    • Ice

  Method:
    1. Muddle cucumber slices in a highball glass.
    2. Add ice and pour over the gin.
    3. Squeeze in lime juice.
    4. Top with tonic and stir gently.
    5. Garnish with a cucumber ribbon.

  🎩  Bartender tip: Use Hendrick's gin for extra cucumber synergy.

  📚  Source: Difford's Guide · r/cocktails community favourite
```

---

### Option B — Web UI (Flask)

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

The web UI provides:
- Three tabs: **Trending**, **Make My Cocktail**, **About**
- Real-time loading steps animation
- Expandable recipe cards with source badges
- Live context bar showing your location, weather, and season

To run in debug mode:

```bash
FLASK_DEBUG=true python app.py
```

---

## 🔌 API Endpoints (Flask)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the web UI |
| `GET` | `/api/context` | Returns detected location, weather, and season |
| `POST` | `/api/trending` | Returns top-5 trending cocktails as JSON |
| `POST` | `/api/make` | Returns a cocktail recipe for given ingredients |

### `POST /api/trending`

**Request body** (optional — if omitted, server auto-detects):

```json
{
  "location": { "city": "Tokyo", "country": "Japan", "lat": 35.68, "lon": 139.69 },
  "weather":  { "temp": 28, "desc": "Clear sky", "unit": "°C" },
  "season":   "Summer"
}
```

**Response:**

```json
{
  "cocktails": [
    {
      "rank": 1,
      "name": "Yuzu Highball",
      "badge": "viral",
      "description": "Crisp Japanese citrus highball — perfect for Tokyo's hot summer.",
      "socialBuzz": "Trending on TikTok Japan with 120M+ views under #HighballSeason",
      "sources": ["tiktok", "youtube", "bar"],
      "ingredients": ["60ml Japanese whisky", "20ml yuzu juice", "soda water"],
      "steps": ["Fill glass with ice.", "Pour whisky.", "Add yuzu.", "Top with soda."],
      "bartenderTip": "Use Suntory Toki for the most authentic result."
    }
  ]
}
```

### `POST /api/make`

**Request body:**

```json
{
  "ingredients": ["rum", "lime juice", "mint", "sugar syrup"]
}
```

**Response:**

```json
{
  "recipe": {
    "name": "Classic Mojito",
    "tagline": "Cuba's most famous cocktail — fresh, minty, irresistible.",
    "description": "...",
    "trendingNote": "IBA official cocktail · perpetually trending on r/cocktails",
    "usedIngredients": ["rum", "lime juice", "mint"],
    "additionalIngredients": ["soda water"],
    "ingredients": ["50ml white rum", "25ml fresh lime juice", "..."],
    "steps": ["...", "..."],
    "bartenderTip": "...",
    "source": "IBA standard recipe"
  }
}
```

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

Example output:

```
tests/test_agent.py::TestGetSeason::test_winter_december PASSED
tests/test_agent.py::TestGetSeason::test_spring_april PASSED
tests/test_agent.py::TestExtractText::test_strips_json_fence PASSED
tests/test_agent.py::TestParseJson::test_valid_list PASSED
tests/test_agent.py::TestGetLocation::test_success PASSED
tests/test_agent.py::TestGetLocation::test_fallback_on_failure PASSED
tests/test_agent.py::TestGetWeather::test_clear_sky PASSED
tests/test_agent.py::TestGetWeather::test_rainy PASSED
tests/test_agent.py::TestGetTrendingCocktails::test_returns_list PASSED
tests/test_agent.py::TestGetTrendingCocktails::test_web_search_tool_is_passed PASSED
tests/test_agent.py::TestMakeMycocktail::test_returns_dict PASSED
tests/test_agent.py::TestMakeMycocktail::test_ingredients_in_prompt PASSED

12 passed in 0.42s
```

---

## ⚙️ Configuration

All configuration is done via environment variables:

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | — | Your Anthropic API key |
| `PORT` | No | `5000` | Flask server port |
| `FLASK_DEBUG` | No | `false` | Enable Flask debug mode |

---

## 🌐 External Services

| Service | Purpose | Key required? | Free tier? |
|---|---|---|---|
| [Anthropic API](https://console.anthropic.com) | Claude AI + web search | ✅ Yes | Pay-per-use |
| [ip-api.com](http://ip-api.com) | IP geolocation | ❌ No | ✅ Free (45 req/min) |
| [Open-Meteo](https://open-meteo.com) | Live weather | ❌ No | ✅ Unlimited free |

**A note on social media**: Claude's web search queries the **public web**. It can read TikTok trending pages, YouTube video titles, Reddit threads, and X/Twitter public posts as they appear in search engine results and aggregator sites. It cannot log into these platforms or access private/authenticated feeds.

---

## 🧠 AI Engineering Notes

### Why structured JSON output?

Claude is prompted to return strict JSON at all times. This keeps the agent layer purely functional — `agent.py` parses the JSON and the UI renders it. No natural-language parsing, no regex, no brittle string matching.

### Why one model call per feature?

Both `get_trending_cocktails()` and `make_my_cocktail()` make a single API call with a rich, multi-step prompt. Claude autonomously decides when to invoke the web search tool (and how many times) within that one call. This is simpler and cheaper than orchestrating multiple calls from Python.

### Web search tool

The `web_search_20250305` tool is passed in the `tools` array and requires no additional configuration — Anthropic handles the search backend. Claude decides when to call it based on the prompt. The tool is billed as part of the standard API usage.

### Prompt design

Key techniques used:
- **Explicit source enumeration**: listing TikTok, YouTube, Reddit etc. by name forces Claude to search those specific domains
- **JSON-only system prompt**: setting the persona as one that "responds ONLY in valid JSON" dramatically reduces formatting drift
- **Context injection**: location, weather, and season are injected into the user turn so they appear fresh for each request

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Run the test suite: `pytest tests/ -v`
5. Submit a pull request

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [Anthropic](https://anthropic.com) — Claude claude-opus-4-5 and the web search tool
- [Open-Meteo](https://open-meteo.com) — Free weather API
- [ip-api.com](http://ip-api.com) — Free IP geolocation
- [Difford's Guide](https://www.diffordsguide.com) — The gold standard cocktail reference
- The global bartending community on Reddit, TikTok, and YouTube
