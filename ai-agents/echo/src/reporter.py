"""Playful mirror report generator — non-preachy conversation insights."""

from __future__ import annotations

from .models import AnalysisResult


def generate_report(result: AnalysisResult) -> str:
    """Generate a playful markdown mirror report from analysis results."""
    lines = []
    lines.append("# 🪞 Echo Mirror Report")
    lines.append("")
    lines.append(
        "*A playful look at how this conversation unfolded — no judgment,"
        " just reflections.*"
    )
    lines.append("")

    # --- Overview ---
    lines.append("## 📊 The Numbers")
    lines.append("")
    top_speaker = result.speakers[0] if result.speakers else None
    lines.append(
        f"- **{result.total_words:,}** words spoken across **{result.total_turns}** turns."
    )
    if top_speaker:
        lines.append(
            f"- **{top_speaker.speaker}** carried the conversation "
            f"({top_speaker.talk_percentage}% of all words)."
        )
    lines.append(
        f"- **{result.filler_words_total}** filler words detected "
        f"({'actually', 'like', 'um', 'you know'}) — we all do it."
    )
    lines.append("")

    # --- Speaker Breakdown ---
    lines.append("## 🎭 Who Said What")
    lines.append("")
    lines.append("| Speaker | Words | Turns | Talk % | Fillers | Avg Sentence |")
    lines.append("|---------|-------|-------|--------|---------|-------------|")
    for s in result.speakers:
        lines.append(
            f"| {s.speaker} | {s.word_count:,} | {s.turn_count} | "
            f"{s.talk_percentage}% | {s.filler_word_count} | "
            f"{s.avg_sentence_length}w |"
        )
    lines.append("")
    lines.append(
        "*Pro tip: If one person dominates, try the 'one breath rule'"
        " — say one idea, then invite someone in.*"
    )
    lines.append("")

    # --- Filler Words ---
    if result.filler_word_summary:
        lines.append("## 🗣️ Filler Word Breakdown")
        lines.append("")
        for word, count in result.filler_word_summary.items():
            bar = "█" * min(count, 20)
            lines.append(f"  **{word}** — {count}x  {bar}")
        lines.append("")
        lines.append(
            "*Fillers are like verbal footprints — we all leave them. "
            "Noticing is the first step.*"
        )
        lines.append("")

    # --- Energy Peaks ---
    if result.energy_peaks:
        lines.append("## ⚡ Energy Peaks")
        lines.append("")
        lines.append("The conversation lit up at these moments:")
        lines.append("")
        for i, peak in enumerate(result.energy_peaks, 1):
            emoji = "🔥" if peak.energy_score >= 5 else "✨" if peak.energy_score >= 3 else "💡"
            lines.append(
                f"  {emoji} **{peak.speaker}**: \"{peak.text}\" "
                f"(score: {peak.energy_score} — {peak.reason})"
            )
        lines.append("")

    # --- Repeated Phrases ---
    if result.repeated_phrases:
        lines.append("## 🔄 Repeated Phrases")
        lines.append("")
        lines.append("Phrases that echoed through the conversation:")
        lines.append("")
        for rp in result.repeated_phrases:
            who = ", ".join(rp.speakers)
            lines.append(f"  » **\"{rp.phrase}\"** — said {rp.count}x by {who}")
        lines.append("")
        lines.append(
            "*Repeated phrases are like musical motifs — they tell you "
            "what the conversation was really about.*"
        )
        lines.append("")

    # --- Longest / Shortest Turns ---
    if result.longest_turns:
        lines.append("## 📏 Turn Length Highlights")
        lines.append("")
        lt = result.longest_turns[0]
        lines.append(
            f"  📖 **Longest turn**: {lt['speaker']} spoke {lt['word_count']} words"
            f" — \"{lt['text']}...\""
        )
        if result.shortest_turns and result.shortest_turns[0]["word_count"] > 0:
            st = result.shortest_turns[0]
            lines.append(
                f"  📍 **Shortest turn**: {st['speaker']} — \"{st['text']}\" "
                f"({st['word_count']} word{'s' if st['word_count'] != 1 else ''})"
            )
        lines.append("")

    # --- Final Takeaway ---
    lines.append("## 💭 One Thing To Take Away")
    lines.append("")
    if top_speaker and top_speaker.talk_percentage > 60:
        # Dominant speaker
        others = [s.speaker for s in result.speakers[1:]]
        if others:
            lines.append(
                f"**{top_speaker.speaker}**, you were the engine of this conversation "
                f"({top_speaker.talk_percentage}% of words). Consider leaving more space for "
                f"{' and '.join(others)} to jump in — sometimes the best insights live in the pauses."
            )
        else:
            lines.append(
                f"You were the main voice here — that's fine! Conversations need drivers. "
                f"Just keep an eye on whether the others are along for the ride."
            )
    elif result.filler_words_total > 10:
        lines.append(
            f"Fillers were present ({result.filler_words_total} total), but "
            f"that's normal. Replace one 'actually' a day with a pause — "
            f"it's amazing what silence can do."
        )
    else:
        lines.append(
            "This was a well-balanced conversation. Everyone got room to speak, "
            "the energy flowed naturally. Keep it up!"
        )
    lines.append("")
    lines.append("---")
    lines.append(
        "*Echo v0.1.0 — Conversation Mindfulness. Try it on your next "
        "team meeting or dinner party.*"
    )
    lines.append("")

    return "\n".join(lines)