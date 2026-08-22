"""Echo — Conversation Mindfulness CLI.

Usage:
  python main.py --transcript <file>
  python main.py --simulate

Paste a conversation transcript (or use a mock one) to get a playful
"mirror report" on conversation dynamics.
"""

from __future__ import annotations

import argparse
import sys

from src.analyzer import analyze
from src.models import Transcript, TranscriptLine
from src.patterns import detect_energy_peaks, detect_interruptions, detect_repeated_phrases
from src.reporter import generate_report

# ── Mock transcripts for demo/──

MOCK_TRANSCRIPT = [
    ("Alice", "Hey everyone! Sorry I'm late — traffic was insane today."),
    ("Bob", "No worries, we just started. So I was telling Carol about the camping trip."),
    ("Carol", "Oh my gosh YES the camping trip! That was honestly the most amazing weekend ever."),
    (
        "Bob",
        "So basically we drove up to Big Sur on Friday night. The traffic was actually fine — "
        "like, we hit zero traffic which is unheard of.",
    ),
    ("Alice", "Wow, that's lucky. I love Big Sur. The views are incredible."),
    (
        "Bob",
        "Right? So we set up camp around midnight. And then like an hour later, "
        "we hear this rustling. And I'm like 'what is that?' and Carol's like 'it's probably nothing.'",
    ),
    (
        "Carol",
        "And then the tent starts SHAKING. Like, full-on earthquake shaking. "
        "I literally thought we were going to die! But it was just a deer.",
    ),
    ("Alice", "A DEER? A deer shook your tent? That is hilarious."),
    (
        "Bob",
        "Yeah, turns out there was a salt lick nearby and this deer was just scratching "
        "its antlers on our tent pole. Amazing. We laughed about it for the rest of the trip.",
    ),
    ("Alice", "You know, I've never been camping. I mean, I've done glamping — does that count?"),
    ("Carol", "Honestly? No. Glamping does not count. But we should totally take you sometime."),
    ("Carol", "Actually, we're planning another trip next month. You should come!"),
    ("Alice", "I'd love to! Okay wait — do I need to buy a tent? I don't own a tent."),
    ("Bob", "We have spare gear. We've got you covered."),
    ("Alice", "You guys are the best. Okay, so speaking of travel — did anyone see Sarah's post about Japan?"),
    ("Bob", "Oh yeah! Her photos were beautiful. She said the food was incredible."),
    (
        "Carol",
        "I saw that! The ramen looked so good. I've been wanting to go to Japan forever. "
        "Like, it's literally at the top of my bucket list.",
    ),
    ("Alice", "Same! Let's plan a group trip. Echo trip, anyone?"),
    ("Bob", "I'm in. Let me check my calendar... Actually, March might work."),
    ("Carol", "March is perfect! This is happening! I'm so excited!"),
]

MOCK_TRANSCRIPT_2 = [
    ("Priya", "Let's talk about the dashboard redesign. What's working?"),
    ("Raj", "The new chart library is great. Load times are, like, 60%% faster actually."),
    ("Priya", "Nice. But users are complaining about the color contrast."),
    ("Raj", "Yeah, I saw those tickets. The contrast ratio on the status badges is below WCAG AA."),
    ("Priya", "So fix it. What's the ETA?"),
    ("Raj", "Well, it's going to take about three days. I need to audit all 47 badge variants."),
    ("Priya", "Three days is too long. Can you scope it to the critical ones first?"),
    ("Raj", "Actually, the critical ones are only 12. I can have those done by Friday."),
    ("Priya", "Okay. Ship the critical ones Friday, then circle back for the rest next sprint."),
]


def parse_transcript_file(path: str) -> Transcript:
    """Read a transcript file and convert to Transcript model.

    Format: each line should be 'Speaker: Their text here'
    Blank lines and lines without ':' are skipped.
    """
    lines: list[TranscriptLine] = []
    with open(path) as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            if ":" in raw_line:
                speaker, _, text = raw_line.partition(":")
                speaker = speaker.strip()
                text = text.strip()
                if speaker and text:
                    lines.append(TranscriptLine(speaker=speaker, text=text))
    if not lines:
        print("Warning: No valid lines found. Expected format: 'Speaker: Their text'")
    return Transcript(lines=lines)


def build_mock_transcript(lines_data: list[tuple[str, str]]) -> Transcript:
    """Build a Transcript from a list of (speaker, text) tuples."""
    return Transcript(
        lines=[TranscriptLine(speaker=s, text=t) for s, t in lines_data]
    )


def run_analysis(transcript: Transcript) -> str:
    """Run full analysis pipeline and return the report."""
    result = analyze(transcript)
    result.energy_peaks = detect_energy_peaks(transcript)
    result.repeated_phrases = detect_repeated_phrases(transcript)

    report = generate_report(result)
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Echo — Conversation Mindfulness CLI",
        epilog="Example: python main.py --simulate",
    )
    parser.add_argument(
        "--transcript",
        "-t",
        type=str,
        help="Path to a transcript file (format: 'Speaker: Their text')",
    )
    parser.add_argument(
        "--simulate",
        "-s",
        action="store_true",
        help="Run with a mock conversation for demo",
    )
    args = parser.parse_args()

    if args.transcript:
        transcript = parse_transcript_file(args.transcript)
    elif args.simulate:
        print("🎭 Using mock conversation (camping trip chat)\n")
        transcript = build_mock_transcript(MOCK_TRANSCRIPT)
    else:
        print("📄 Paste a transcript or paste text below (Ctrl+D to end):")
        transcript = parse_transcript_file("/dev/stdin")

    report = run_analysis(transcript)
    print(report)


if __name__ == "__main__":
    main()