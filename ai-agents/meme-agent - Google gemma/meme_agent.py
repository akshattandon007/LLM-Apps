"""
Meme Agent — Generates trending memes from news using Google Gemini + Gemma
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pipeline:
  1. Scrape trending meme formats from Google Trends + Reddit
  2. Use Gemini (gemma-3-27b-it) to craft meme text aligned to the news
  3. Fetch a relevant background image via Unsplash (free, no auth needed)
  4. Composite the meme with Pillow and save it

Requirements:
  pip install google-generativeai pillow requests httpx python-dotenv

Environment variables (put in a .env file or export them):
  GEMINI_API_KEY=your_key_here
  UNSPLASH_ACCESS_KEY=your_key_here   # optional — falls back to a solid colour bg
"""

from __future__ import annotations

import io
import json
import os
import random
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai

load_dotenv()

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "")
UNSPLASH_KEY     = os.getenv("UNSPLASH_ACCESS_KEY", "")   # optional
OUTPUT_DIR       = Path("memes_output")
MEME_WIDTH       = 800
MEME_HEIGHT      = 600
FONT_PATH        = None   # set to a .ttf path if you want a custom font

# Gemma model via Gemini API
GEMMA_MODEL = "gemma-3-27b-it"


# ─────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────

@dataclass
class MemeBlueprint:
    format_name: str          # e.g. "Drake Pointing", "This is Fine", "Distracted Boyfriend"
    top_text: str
    bottom_text: str
    image_search_query: str   # used to fetch a background image
    caption: str              # social-media caption for the post
    hashtags: list[str]


# ─────────────────────────────────────────────
# Step 1 — Discover trending meme formats
# ─────────────────────────────────────────────

POPULAR_MEME_FORMATS = [
    "Drake Pointing",
    "Distracted Boyfriend",
    "This is Fine (dog in fire)",
    "Gru's Plan",
    "Two Buttons",
    "Left Exit 12 Off Ramp",
    "Bernie Sanders Sitting",
    "Surprised Pikachu",
    "Change My Mind",
    "Woman Yelling at Cat",
    "Doge",
    "One Does Not Simply",
    "Is This a Pigeon",
    "Ancient Aliens Guy",
    "Crying Jordan",
    "Galaxy Brain",
    "Expanding Brain",
    "Always Has Been (Astronaut)",
    "Nobody: / Literally Nobody:",
    "Math Lady / Confused",
    "POV: meme format",
    "NPC Streamer reaction",
    "Me vs. the guy she told me not to worry about",
    "Ratio + L + bozo (Twitter/X reply culture)",
    "Hawk Tuah",
    "Demure / Very mindful, very demure",
    "AI Slop vs Real Art",
    "Brain Worms (2025 trend)",
    "Roman Empire thought",
    "Delulu",
]


def get_trending_formats(top_n: int = 8) -> list[str]:
    """
    In production you would hit a real-time API (KnowYourMeme, Imgflip, etc.).
    Here we simulate a 'trending' subset by shuffling the curated list and
    optionally pulling a few extras from Reddit r/memes via the public JSON API.
    """
    trending = random.sample(POPULAR_MEME_FORMATS, min(top_n, len(POPULAR_MEME_FORMATS)))

    # Try to grab a couple of real top posts from r/memes (no auth needed)
    try:
        resp = requests.get(
            "https://www.reddit.com/r/memes/top.json?limit=10&t=day",
            headers={"User-Agent": "MemeAgent/1.0"},
            timeout=6,
        )
        if resp.status_code == 200:
            posts = resp.json().get("data", {}).get("children", [])
            reddit_titles = [p["data"]["title"] for p in posts[:4]]
            trending = reddit_titles + trending[: max(0, top_n - len(reddit_titles))]
    except Exception:
        pass  # silently fall back to curated list

    return trending[:top_n]


# ─────────────────────────────────────────────
# Step 2 — Gemma generates the meme blueprint
# ─────────────────────────────────────────────

def build_meme_prompt(news: str, trending_formats: list[str]) -> str:
    formats_str = "\n".join(f"  - {f}" for f in trending_formats)
    return f"""
You are a viral meme creator who deeply understands internet culture, Gen-Z humour,
and what makes content trend on Instagram and X (formerly Twitter).

## Input News
{news}

## Currently Trending Meme Formats (choose the BEST fitting one)
{formats_str}

## Your Task
1. Pick the single most fitting meme format from the list above.
2. Write punchy, shareable meme text (top and bottom text, or just one if the format needs it).
   - Keep it short, funny, and culturally resonant.
   - Use internet slang, irony, absurdism, or relatable humour where appropriate.
3. Suggest a vivid image search query to fetch a relevant background image.
4. Write a 1-sentence social media caption (with emojis) and 5 trending hashtags.

## Output — respond ONLY with valid JSON, no markdown fences, no extra text:
{{
  "format_name": "<chosen format>",
  "top_text": "<top text — can be empty string>",
  "bottom_text": "<bottom text>",
  "image_search_query": "<3-5 word image search query>",
  "caption": "<social media caption with emojis>",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
}}
""".strip()


def generate_meme_blueprint(news: str) -> MemeBlueprint:
    if not GEMINI_API_KEY:
        raise EnvironmentError("GEMINI_API_KEY is not set. Add it to your .env file.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMMA_MODEL)

    trending = get_trending_formats()
    prompt   = build_meme_prompt(news, trending)

    print(f"[→] Calling {GEMMA_MODEL} to craft meme blueprint …")
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.95,
            max_output_tokens=512,
        ),
    )

    raw = response.text.strip()
    # Strip accidental markdown fences
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemma returned invalid JSON:\n{raw}") from exc

    return MemeBlueprint(
        format_name        = data.get("format_name", "Custom Meme"),
        top_text           = data.get("top_text", ""),
        bottom_text        = data.get("bottom_text", ""),
        image_search_query = data.get("image_search_query", "funny meme background"),
        caption            = data.get("caption", ""),
        hashtags           = data.get("hashtags", []),
    )


# ─────────────────────────────────────────────
# Step 3 — Fetch a background image
# ─────────────────────────────────────────────

FALLBACK_BG_COLOURS = [
    (30, 30, 30),
    (15, 52, 96),
    (83, 16, 47),
    (22, 78, 49),
    (60, 9, 108),
]


def fetch_background_image(query: str) -> Image.Image:
    """
    Try Unsplash (if key provided) → Picsum fallback (random photo).
    Returns a PIL Image sized to MEME_WIDTH × MEME_HEIGHT.
    """
    img_data: Optional[bytes] = None

    # 1. Unsplash
    if UNSPLASH_KEY:
        try:
            url = (
                f"https://api.unsplash.com/photos/random"
                f"?query={requests.utils.quote(query)}"
                f"&orientation=landscape&w={MEME_WIDTH}&h={MEME_HEIGHT}"
                f"&client_id={UNSPLASH_KEY}"
            )
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                download_url = r.json()["urls"]["regular"]
                img_data = requests.get(download_url, timeout=15).content
                print(f"[→] Background image fetched from Unsplash ({query})")
        except Exception as exc:
            print(f"[!] Unsplash failed: {exc}")

    # 2. Picsum (no auth, random photo)
    if not img_data:
        try:
            url = f"https://picsum.photos/{MEME_WIDTH}/{MEME_HEIGHT}"
            img_data = requests.get(url, timeout=15).content
            print("[→] Background image fetched from Lorem Picsum (random)")
        except Exception as exc:
            print(f"[!] Picsum failed: {exc}")

    # 3. Solid colour fallback
    if not img_data:
        print("[→] Using solid colour background (no internet image available)")
        colour = random.choice(FALLBACK_BG_COLOURS)
        return Image.new("RGB", (MEME_WIDTH, MEME_HEIGHT), colour)

    img = Image.open(io.BytesIO(img_data)).convert("RGB")
    img = img.resize((MEME_WIDTH, MEME_HEIGHT), Image.LANCZOS)
    return img


# ─────────────────────────────────────────────
# Step 4 — Composite the meme
# ─────────────────────────────────────────────

def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font, falling back to PIL default if custom path not set."""
    if FONT_PATH and Path(FONT_PATH).exists():
        return ImageFont.truetype(FONT_PATH, size)
    # Try common system fonts
    for candidate in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "C:/Windows/Fonts/impact.ttf",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    # PIL built-in (tiny but always available)
    return ImageFont.load_default()


def draw_meme_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    position: str,  # "top" | "bottom"
    width: int,
    height: int,
    font_size: int = 52,
) -> None:
    """Draw bold Impact-style text with a thick black outline."""
    if not text:
        return

    font    = _get_font(font_size)
    margin  = 20
    padding = 10
    max_chars_per_line = max(10, width // (font_size // 2))

    lines = []
    for para in text.upper().split("\n"):
        lines.extend(textwrap.wrap(para, width=max_chars_per_line) or [""])

    # Measure block height
    line_h = font_size + 6
    block_h = line_h * len(lines)

    if position == "top":
        y_start = margin
    else:
        y_start = height - block_h - margin

    for i, line in enumerate(lines):
        # Estimate text width for centering
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
        except AttributeError:
            text_w = len(line) * (font_size // 2)

        x = (width - text_w) // 2
        y = y_start + i * line_h

        # Outline (stroke)
        stroke = max(2, font_size // 14)
        for dx in range(-stroke, stroke + 1):
            for dy in range(-stroke, stroke + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0))
        # Main text
        draw.text((x, y), line, font=font, fill=(255, 255, 255))


def add_watermark(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    font = _get_font(18)
    text = "made with MemeAgent"
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
    except AttributeError:
        tw = len(text) * 10
    draw.text((width - tw - 10, height - 28), text, font=font, fill=(200, 200, 200, 120))


def add_dark_overlay(img: Image.Image, opacity: int = 90) -> Image.Image:
    """Add a translucent dark overlay to improve text legibility."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, opacity))
    base    = img.convert("RGBA")
    merged  = Image.alpha_composite(base, overlay)
    return merged.convert("RGB")


def composite_meme(blueprint: MemeBlueprint, bg: Image.Image) -> Image.Image:
    bg = add_dark_overlay(bg, opacity=100)
    draw = ImageDraw.Draw(bg)

    draw_meme_text(draw, blueprint.top_text,    "top",    MEME_WIDTH, MEME_HEIGHT)
    draw_meme_text(draw, blueprint.bottom_text, "bottom", MEME_WIDTH, MEME_HEIGHT)
    add_watermark(draw, MEME_WIDTH, MEME_HEIGHT)

    return bg


# ─────────────────────────────────────────────
# Main agent entrypoint
# ─────────────────────────────────────────────

def run_meme_agent(news: str, output_path: Optional[Path] = None) -> Path:
    """
    Full pipeline: news → meme image saved to disk.
    Returns the path to the saved meme.
    """
    print("\n━━━  MEME AGENT  ━━━")
    print(f"News: {news[:120]}{'…' if len(news) > 120 else ''}\n")

    # 1. Generate blueprint via Gemma
    blueprint = generate_meme_blueprint(news)
    print(f"[✓] Meme format  : {blueprint.format_name}")
    print(f"[✓] Top text     : {blueprint.top_text or '(none)'}")
    print(f"[✓] Bottom text  : {blueprint.bottom_text}")
    print(f"[✓] Image query  : {blueprint.image_search_query}")
    print(f"[✓] Caption      : {blueprint.caption}")
    print(f"[✓] Hashtags     : {' '.join(blueprint.hashtags)}\n")

    # 2. Fetch background
    bg = fetch_background_image(blueprint.image_search_query)

    # 3. Composite
    meme = composite_meme(blueprint, bg)

    # 4. Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        safe_name = "".join(c if c.isalnum() else "_" for c in blueprint.format_name[:40])
        output_path = OUTPUT_DIR / f"meme_{safe_name}.jpg"

    meme.save(output_path, "JPEG", quality=92)
    print(f"[✓] Meme saved   : {output_path.resolve()}\n")

    # 5. Print post-ready output
    print("━━━  READY TO POST  ━━━")
    print(f"Caption  : {blueprint.caption}")
    print(f"Hashtags : {' '.join(blueprint.hashtags)}")
    print("━━━━━━━━━━━━━━━━━━━━━━━\n")

    return output_path


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:  python meme_agent.py \"<news headline or story>\"")
        print("Example: python meme_agent.py \"Scientists discover that coffee cures everything\"")
        sys.exit(1)

    news_input = " ".join(sys.argv[1:])
    run_meme_agent(news_input)
