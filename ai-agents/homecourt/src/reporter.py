"""Verdict formatting for HomeCourt — produces a shareable 'court order'."""

from src.models import Verdict

_SEPARATOR = "─" * 46


def format_verdict(verdict: Verdict) -> str:
    """Format a Verdict as a shareable, terminal-friendly court order.

    The output is designed to be screenshot-and-share worthy: clean
    formatting, emoji header, clear sections, and no line-wrapping
    disasters on a standard 80-col terminal.
    """
    lines: list[str] = []

    # ── Header ──────────────────────────────────────────────────────────
    lines.append(verdict.formatted_header)
    lines.append("")
    lines.append(f"  Case:        {verdict.case_name}")
    lines.append(f"  Presiding:   {verdict.judge_emoji} {verdict.presiding_judge}")
    lines.append(f"  Date:        {verdict.date_issued.isoformat()}")
    lines.append("")

    # ── Reasoning ────────────────────────────────────────────────────────
    lines.append(_SEPARATOR)
    lines.append("  REASONING")
    lines.append(_SEPARATOR)
    lines.append("")

    for paragraph in verdict.reasoning.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            lines.append("")
            continue
        lines.append(_wrap_text(paragraph, prefix="  "))

    lines.append("")

    # ── Ruling ───────────────────────────────────────────────────────────
    lines.append(verdict.formatted_ruling)
    lines.append("")

    # ── Dissenting opinion ───────────────────────────────────────────────
    if verdict.dissenting_opinion:
        lines.append(_SEPARATOR)
        lines.append("  DISSENTING OPINION")
        lines.append(_SEPARATOR)
        lines.append(f"  💬 {verdict.dissenting_opinion}")
        lines.append("")

    # ── Footer ───────────────────────────────────────────────────────────
    lines.append(
        "  — This verdict is binding in the court of friendship.     —"
    )
    lines.append("  — Share freely. Appeal fees: one snack per party.  —")
    lines.append("")

    return "\n".join(lines)


def _wrap_text(text: str, prefix: str = "  ", width: int = 76) -> str:
    """Simple word-wrap for terminal display.

    Falls back to the original text if no better wrapping is needed.
    """
    available = width - len(prefix)
    if available <= 20:
        return prefix + text

    words = text.split()
    if not words:
        return prefix + text

    result: list[str] = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if len(test_line) > available and current_line:
            result.append(f"{prefix}{current_line}")
            current_line = word
        else:
            current_line = test_line
    if current_line:
        result.append(f"{prefix}{current_line}")

    return "\n".join(result) if len(result) > 1 else prefix + text