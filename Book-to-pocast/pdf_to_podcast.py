#!/usr/bin/env python3
"""
PDF → Podcast Script
Reads a PDF, summarises it as a podcast monologue (with selectable speaker tone),
then converts that to an MP3 audio file using gTTS.

Requirements:
    pip install pypdf anthropic gtts

Usage:
    python pdf_to_podcast.py <path_to_pdf> [--tone TONE] [--output OUTPUT]

Tone options:
    casual       - Friendly, conversational, like a tech podcast host
    academic     - Thoughtful, measured, like a university lecturer
    energetic    - High-energy, punchy, like a morning radio host
    storyteller  - Narrative-driven, immersive, like an audiobook narrator
    news         - Crisp, authoritative, like a news anchor

Example:
    python pdf_to_podcast.py report.pdf --tone energetic --output my_podcast.mp3
"""

import argparse
import sys
import os
import anthropic
from pypdf import PdfReader
from gtts import gTTS

# ── Tone definitions ──────────────────────────────────────────────────────────

TONES = {
    "casual": {
        "label": "Casual / Conversational",
        "description": (
            "You are a friendly tech-podcast host. Use a warm, conversational tone. "
            "Keep sentences short and punchy. Use contractions (you're, it's, we've). "
            "Occasionally address the listener directly ('think about it this way…'). "
            "Avoid jargon unless you explain it immediately."
        ),
    },
    "academic": {
        "label": "Academic / Reflective",
        "description": (
            "You are a thoughtful university lecturer with deep expertise. Use a measured, "
            "precise tone. Structure ideas logically with clear signposting ('first… then… "
            "finally…'). It is acceptable to use technical vocabulary, but always define "
            "key terms for a general audience."
        ),
    },
    "energetic": {
        "label": "Energetic / High-energy",
        "description": (
            "You are a high-energy morning-radio host who loves big ideas. Use punchy, "
            "exclamatory language. Short sentences. Build momentum. Use rhetorical questions "
            "to keep the listener hooked. Make it feel exciting — like this content could "
            "change someone's day."
        ),
    },
    "storyteller": {
        "label": "Storyteller / Narrative",
        "description": (
            "You are a skilled audiobook narrator. Paint vivid pictures with words. "
            "Weave the key ideas into a flowing narrative with a clear beginning, middle, "
            "and end. Use metaphors and analogies to make abstract concepts tangible. "
            "Vary sentence rhythm for dramatic effect."
        ),
    },
    "news": {
        "label": "News Anchor / Authoritative",
        "description": (
            "You are a seasoned news anchor. Use a crisp, authoritative tone. Lead with "
            "the most important information. Be concise and factual. Avoid filler words. "
            "Structure each point like a broadcast news segment."
        ),
    },
}

# ── PDF extraction ────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(pdf_path)
    pages_text = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages_text.append(text.strip())

    if not pages_text:
        raise ValueError("No extractable text found in the PDF.")

    full_text = "\n\n".join(pages_text)
    print(f"✅ Extracted text from {len(reader.pages)} page(s) ({len(full_text):,} characters).")
    return full_text

# ── LLM summarisation → podcast script ───────────────────────────────────────

def generate_podcast_script(pdf_text: str, tone_key: str) -> str:
    """Send PDF text to Claude and get back a podcast-style script."""
    tone = TONES[tone_key]
    client = anthropic.Anthropic()

    system_prompt = f"""You convert document content into engaging podcast monologue scripts.

TONE INSTRUCTION:
{tone['description']}

FORMAT RULES:
- Write as a spoken monologue — no headers, no bullet points, no markdown.
- Aim for 400–600 words (roughly 3–5 minutes of speech).
- Open with a hook that draws the listener in immediately.
- Cover the 5–7 most important ideas from the document.
- Close with a memorable takeaway or call to reflection.
- Write ONLY the spoken script — no stage directions, no [PAUSE], no speaker labels.
"""

    user_prompt = f"""Here is the document content to turn into a podcast episode:

---
{pdf_text[:12000]}  
---

Write the podcast monologue script now."""

    print(f"🤖 Generating podcast script with tone: {tone['label']} …")

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    script = message.content[0].text.strip()
    print(f"✅ Script generated ({len(script.split()):,} words).")
    return script

# ── Text-to-speech ────────────────────────────────────────────────────────────

def text_to_audio(script: str, output_path: str, lang: str = "en") -> None:
    """Convert the podcast script to an MP3 audio file using gTTS."""
    print(f"🎙️  Converting script to audio …")
    tts = gTTS(text=script, lang=lang, slow=False)
    tts.save(output_path)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ Audio saved → {output_path}  ({size_kb:.1f} KB)")

# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert a PDF into a spoken podcast episode.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Tone options:
  casual       Friendly, conversational  (tech podcast vibe)
  academic     Measured, precise         (university lecture vibe)
  energetic    High-energy, punchy       (morning radio vibe)
  storyteller  Narrative, immersive      (audiobook narrator vibe)
  news         Crisp, authoritative      (news anchor vibe)

Example:
  python pdf_to_podcast.py report.pdf --tone storyteller --output episode.mp3
        """,
    )
    parser.add_argument("pdf", help="Path to the input PDF file.")
    parser.add_argument(
        "--tone",
        choices=list(TONES.keys()),
        default="casual",
        help="Speaking tone for the podcast (default: casual).",
    )
    parser.add_argument(
        "--output",
        default="podcast_output.mp3",
        help="Output MP3 file path (default: podcast_output.mp3).",
    )
    parser.add_argument(
        "--save-script",
        action="store_true",
        help="Also save the podcast script as a .txt file alongside the audio.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"\n📄 PDF Podcast Generator")
    print(f"   PDF    : {args.pdf}")
    print(f"   Tone   : {TONES[args.tone]['label']}")
    print(f"   Output : {args.output}\n")

    # Step 1: Extract PDF text
    pdf_text = extract_text_from_pdf(args.pdf)

    # Step 2: Generate podcast script via Claude
    script = generate_podcast_script(pdf_text, args.tone)

    # Step 3 (optional): Save the script
    if args.save_script:
        script_path = os.path.splitext(args.output)[0] + "_script.txt"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"📝 Script saved → {script_path}")

    # Step 4: Convert to audio
    text_to_audio(script, args.output)

    print("\n🎧 All done! Enjoy your podcast.\n")


if __name__ == "__main__":
    main()
