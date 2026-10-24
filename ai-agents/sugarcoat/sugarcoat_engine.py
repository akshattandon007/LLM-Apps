"""sugarcoat_engine - LLM-powered message rephrasing engine."""

import json
from typing import Any

import httpx


# Default tone and style definitions
SUPPORTED_TONES = [
    "gentle",
    "empathetic",
    "professional",
    "assertive",
    "warm",
    "neutral",
]
"""Tones affect the emotional register of the output."""

SUPPORTED_STYLES = [
    "diplomatic",
    "direct",
    "apologetic",
    "encouraging",
    "concise",
    "detailed",
]
"""Styles affect the structure and verbosity of the output."""

# System prompt template
SYSTEM_PROMPT_TEMPLATE = """You are a diplomatic communication coach. Your job is to help people
rephrase difficult messages — breaking bad news, declining invitations, giving criticism,
apologizing, or setting boundaries — in a way that is KIND, CLEAR, and EFFECTIVE.

TONE: {tone_description}
STYLE: {style_description}

RULES:
1. Preserve the sender's original intent and core message — do NOT change facts or meaning.
2. Remove harsh, passive-aggressive, or unclear phrasing.
3. Use "I" statements where appropriate.
4. Offer alternatives or next steps when possible.
5. Keep approximately the same length as the original (±30%).
6. Do NOT add text that changes commitments or invents promises.

Respond with a JSON object containing:
- "rephrased": the improved message text
- "explanation": 1-2 sentences on why this version is better (what changed and why it helps)
- "alternatives": 1-2 shorter alternative phrasings (optional)

Return ONLY valid JSON, no markdown fences."""

# Per-tone instructions
TONE_INSTRUCTIONS = {
    "gentle": "Soft, caring tone. Use tender language, hedge when needed, prioritize the recipient's feelings.",
    "empathetic": "Deeply understanding and validating. Acknowledge the other person's perspective explicitly.",
    "professional": "Polished, respectful workplace tone. Clear boundaries, no emotional language.",
    "assertive": "Firm but respectful. Clear about your position while remaining polite and considerate.",
    "warm": "Friendly and personal. Like writing to a close friend — warm, natural, affectionate.",
    "neutral": "Plain, factual, calm. No emotional coloring, just clear communication.",
}

# Per-style instructions
STYLE_INSTRUCTIONS = {
    "diplomatic": "Tactful phrasing with softeners ('unfortunately', 'I'm afraid'), buffers ('I wanted to let you know...'), and graceful bridges.",
    "direct": "Get straight to the point. No padding or hedges, but still kind. Use clear, simple sentences.",
    "apologetic": "Lead with regret and acknowledgment of impact. Offer sincere apology and amends where appropriate.",
    "encouraging": "Focus on the positive and supportive aspects. End with warmth and openness.",
    "concise": "Keep it short — 1-3 sentences max. Every word earns its place. No elaboration.",
    "detailed": "Thorough explanation with rationale, context, and possible next steps.",
}


def _make_system_prompt(tone: str, style: str) -> str:
    """Build the system prompt with tone and style instructions."""
    tone_desc = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["neutral"])
    style_desc = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["diplomatic"])
    return SYSTEM_PROMPT_TEMPLATE.format(
        tone_description=tone_desc,
        style_description=style_desc,
    )


def _make_user_prompt(
    message: str,
    context: str = "",
    history: list[dict] | None = None,
) -> str:
    """Build the user prompt with message, context, and history."""
    parts = []

    if context:
        parts.append(f"CONTEXT: {context}\n")

    if history:
        parts.append("CONVERSATION HISTORY (most recent first):\n")
        for entry in history[-5:]:
            if isinstance(entry, dict):
                sender = entry.get("sender", "Them")
                text = entry.get("text", "")
                parts.append(f"  [{sender}]: {text}")
        parts.append("")

    parts.append("MESSAGE TO REPHRASE:")
    parts.append(message)

    return "\n".join(parts)


def rephrase_message(
    message: str,
    tone: str = "gentle",
    style: str = "diplomatic",
    context: str = "",
    api_key: str = "",
    model: str = "deepseek/deepseek-chat",
    history: list[dict] | None = None,
) -> dict[str, Any]:
    """Send the message to OpenRouter for rephrasing.

    Args:
        message: The original difficult message text.
        tone: Desired tone (see SUPPORTED_TONES).
        style: Desired style (see SUPPORTED_STYLES).
        context: Optional situational context.
        api_key: OpenRouter API key.
        model: OpenRouter model ID.
        history: Optional conversation history.

    Returns:
        Dict with "rephrased", "explanation", and optionally "alternatives".

    Raises:
        ValueError: If the API returns an unexpected format.
        httpx.HTTPError: For network/API errors.
    """
    if not api_key:
        raise ValueError("API key is required")

    system_prompt = _make_system_prompt(tone, style)
    user_prompt = _make_user_prompt(message, context, history)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/akshattandon007/LLM-Apps",
            "X-Title": "sugarcoat",
        },
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    content = data["choices"][0]["message"]["content"].strip()

    # Try to parse as JSON
    # Handle cases where the model wraps in markdown fences
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        if "```" in content:
            content = content.rsplit("```", 1)[0]
    content = content.strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: wrap raw text as rephrased
        result = {"rephrased": content, "explanation": None, "alternatives": None}

    # Validate result shape
    if "rephrased" not in result or not result["rephrased"]:
        result["rephrased"] = content.strip()

    return result


def get_supported_tones() -> list[str]:
    """Return the list of supported tone options."""
    return list(SUPPORTED_TONES)


def get_supported_styles() -> list[str]:
    """Return the list of supported style options."""
    return list(SUPPORTED_STYLES)