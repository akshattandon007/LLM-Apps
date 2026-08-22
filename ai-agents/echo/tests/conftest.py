"""Test fixtures — mock transcripts for smoke testing."""

from __future__ import annotations

import pytest

from src.models import Transcript, TranscriptLine


@pytest.fixture
def mock_transcript_camping():
    """A 20-line mock conversation about a camping trip with 3 speakers."""
    lines = [
        ("Alice", "Hey everyone! Sorry I'm late — traffic was insane today."),
        ("Bob", "No worries, we just started. So I was telling Carol about the camping trip."),
        ("Carol", "Oh my gosh YES the camping trip! That was honestly the most amazing weekend ever."),
        (
            "Bob",
            "So basically we drove up to Big Sur on Friday night. The traffic was actually fine "
            "— like, we hit zero traffic which is unheard of.",
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
    return Transcript(lines=[TranscriptLine(speaker=s, text=t) for s, t in lines])


@pytest.fixture
def mock_transcript_meeting():
    """A 10-line mock meeting transcript with 2 speakers."""
    lines = [
        ("Priya", "Let's talk about the dashboard redesign. What's working?"),
        ("Raj", "The new chart library is great. Load times are 60 percent faster."),
        ("Priya", "Nice. But users are complaining about the color contrast."),
        ("Raj", "Yeah, I saw those tickets. The contrast ratio is below WCAG AA."),
        ("Priya", "So fix it. What's the ETA?"),
        ("Raj", "Well, it's going to take about three days."),
        ("Priya", "Three days is too long. Can you scope it to the critical ones first?"),
        ("Raj", "The critical ones are only 12. I can have those done by Friday."),
        ("Priya", "Okay. Ship the critical ones Friday, then circle back for the rest next sprint."),
    ]
    return Transcript(lines=[TranscriptLine(speaker=s, text=t) for s, t in lines])


@pytest.fixture
def mock_single_speaker():
    """A monologue — single speaker, many turns."""
    lines = [
        ("Narrator", "It was the best of times, it was the worst of times."),
        ("Narrator", "Actually, it was mostly just confusing."),
        ("Narrator", "Like, you know, ambiguous at best."),
        ("Narrator", "But honestly, looking back — wow. What a ride."),
    ]
    return Transcript(lines=[TranscriptLine(speaker=s, text=t) for s, t in lines])