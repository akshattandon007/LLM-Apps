# 🎭 Meme Agent

> **AI-powered meme generator** that turns any news headline into a viral, trending meme — powered by Google Gemma 3 (via Gemini API) and Pillow.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Gemma](https://img.shields.io/badge/Model-Gemma%203%2027B-orange?logo=google)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📖 What is this?

**Meme Agent** is a Python CLI tool that:

1. **Discovers trending meme formats** — pulls live top posts from Reddit r/memes and blends them with a curated bank of ~30 evergreen viral formats (Drake Pointing, Distracted Boyfriend, NPC Streamer, Expanding Brain, and more)
2. **Generates meme text using Gemma 3 27B** — the model picks the best-fitting format for your news, writes punchy internet-native top/bottom text, and outputs a caption + hashtags ready to post
3. **Fetches a relevant background image** — via Unsplash API (optional) or Lorem Picsum (no auth required)
4. **Composites the final meme** — Impact-style bold white text with black outline over a darkened background, saved as a JPEG

Perfect for social media managers, developers building content tools, or anyone who wants to automate dank meme creation.

---

## 🏗️ Architecture

```
News Headline (input)
        │
        ▼
┌───────────────────────────┐
│   Trend Discovery         │
│  • Reddit r/memes API     │
│  • Curated format bank    │
└───────────┬───────────────┘
            │ trending format list
            ▼
┌───────────────────────────┐
│   Gemma 3 27B             │
│   (Gemini API)            │
│  • Picks best format      │
│  • Writes meme text       │
│  • Image search query     │
│  • Caption + hashtags     │
└───────────┬───────────────┘
            │ MemeBlueprint (JSON)
            ▼
┌───────────────────────────┐
│   Background Image        │
│  • Unsplash (if key set)  │
│  • Picsum fallback        │
│  • Solid colour fallback  │
└───────────┬───────────────┘
            │ PIL Image
            ▼
┌───────────────────────────┐
│   Compositing (Pillow)    │
│  • Dark overlay           │
│  • Bold text + outline    │
│  • Watermark              │
└───────────┬───────────────┘
            │
            ▼
   memes_output/meme_*.jpg
```

---

## ⚡ Quickstart

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/meme-agent.git
cd meme-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_key_here   # optional
```

| Key | Required | Where to get it |
|-----|----------|-----------------|
| `GEMINI_API_KEY` | ✅ Yes | [aistudio.google.com](https://aistudio.google.com/app/apikey) — free |
| `UNSPLASH_ACCESS_KEY` | ⬜ Optional | [unsplash.com/developers](https://unsplash.com/developers) — free |

> If `UNSPLASH_ACCESS_KEY` is not set, the agent falls back to [Lorem Picsum](https://picsum.photos/) (random photo, no sign-up needed).

### 4. Run it

```bash
python meme_agent.py "your news headline here"
```

Your meme is saved to `memes_output/`.

---

## 🖥️ Usage

```
python meme_agent.py "<news headline or story>"
```

### Examples

```bash
# Tech news
python meme_agent.py "Apple releases iPhone with no ports and no buttons"

# Finance
python meme_agent.py "Fed cuts interest rates to zero as Wall Street erupts"

# Science
python meme_agent.py "Scientists discover that coffee cures everything"

# Sports
python meme_agent.py "England wins the World Cup"

# Politics
python meme_agent.py "Government announces four-day work week for everyone"

# Multi-word without quotes (most shells handle this fine)
python meme_agent.py AI takes over every job but somehow unemployment hits zero
```

### As a Python module

```python
from meme_agent import run_meme_agent

# Returns Path to the saved image
path = run_meme_agent("Scientists discover coffee cures everything")
print(f"Meme saved at: {path}")
```

---

## 📂 Project Structure

```
meme-agent/
├── meme_agent.py        # Main agent script
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .gitignore           # Ignores .env and output images
├── memes_output/        # Generated memes saved here (gitignored)
├── assets/              # Optional: store custom fonts here
└── README.md            # You are here
```

---

## 🎨 Example Output

```
━━━  MEME AGENT  ━━━
News: Scientists discover that coffee cures everything

[→] Calling gemma-3-27b-it to craft meme blueprint …
[✓] Meme format  : Drake Pointing
[✓] Top text     : drinking tea like a basic person
[✓] Bottom text  : drinking 7 espressos because science said so
[✓] Image query  : coffee science lab experiment
[✓] Caption      : doctors hate this one weird trick ☕🔬
[✓] Hashtags     : #Coffee #Science #Memes #Relatable #DrakePointing

[→] Background image fetched from Unsplash (coffee science lab experiment)
[✓] Meme saved   : /your/path/memes_output/meme_Drake_Pointing.jpg

━━━  READY TO POST  ━━━
Caption  : doctors hate this one weird trick ☕🔬
Hashtags : #Coffee #Science #Memes #Relatable #DrakePointing
━━━━━━━━━━━━━━━━━━━━━━━
```

The saved image is an **800 × 600 JPEG** that looks like:

```
┌──────────────────────────────────────────┐
│  DRINKING TEA LIKE A BASIC PERSON        │  ← top text (white, black outline)
│                                          │
│         [relevant background photo]      │
│                                          │
│  DRINKING 7 ESPRESSOS BECAUSE SCIENCE    │  ← bottom text
│                           made with ●    │  ← watermark
└──────────────────────────────────────────┘
```

---

## ⚙️ Configuration

All tuneable options are at the top of `meme_agent.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMMA_MODEL` | `gemma-3-27b-it` | Any Gemini/Gemma model ID |
| `MEME_WIDTH` | `800` | Output image width (px) |
| `MEME_HEIGHT` | `600` | Output image height (px) |
| `FONT_PATH` | `None` | Path to a custom `.ttf` font file |
| `OUTPUT_DIR` | `memes_output/` | Where generated memes are saved |
| `POPULAR_MEME_FORMATS` | ~30 formats | Extend this list with new viral formats |

### Using a custom font (recommended)

Download [Impact.ttf](https://www.wfonts.com/font/impact) or any bold font and set:

```python
FONT_PATH = "assets/Impact.ttf"
```

### Auto-open the image after generation

Add this at the end of `run_meme_agent()` in `meme_agent.py`:

```python
import subprocess, sys, os
if sys.platform == "darwin":
    subprocess.run(["open", str(output_path)])
elif sys.platform == "linux":
    subprocess.run(["xdg-open", str(output_path)])
else:
    os.startfile(output_path)   # Windows
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `google-generativeai` | Gemini / Gemma API client |
| `pillow` | Image compositing |
| `requests` | Fetching background images |
| `httpx` | Async-ready HTTP (used internally) |
| `python-dotenv` | Loading `.env` variables |

---

## 🗺️ Roadmap

- [ ] Streamlit web UI — paste news, preview meme in browser
- [ ] Auto-post to Instagram / X via their APIs
- [ ] Support image meme templates (Drake, Distracted Boyfriend overlays)
- [ ] Batch mode — process a list of headlines from a CSV
- [ ] Discord bot integration
- [ ] Trending format auto-refresh via KnowYourMeme scraper

---

## 🤝 Contributing

Pull requests are welcome! To add new meme formats, just extend `POPULAR_MEME_FORMATS` in `meme_agent.py` and open a PR.

---

## 📄 License

MIT — do whatever you want with it. Just don't blame us if your memes go too viral.
