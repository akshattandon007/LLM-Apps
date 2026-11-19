"""
VibeCheck — Core analyzer module.

Handles text analysis using LLM API calls. Supports multiple providers
with a clean abstraction layer so the analysis logic doesn't depend on
which backend is running.
"""

import json
import os
import re
from dataclasses import dataclass, field, asdict
from typing import Optional

import requests


# ── Data models ──────────────────────────────────────────────────────────

@dataclass
class ToneAnalysis:
    """Structured output from a single tone analysis pass."""
    overall_tone: str = ""
    emotional_subtext: list[str] = field(default_factory=list)
    clarity_score: int = 0          # 1-10
    confidence_level: str = ""      # low / moderate / high / assertive
    formality: str = ""             # casual / neutral / formal
    detected_mood: str = ""
    potential_misinterpretations: list[str] = field(default_factory=list)
    rewrite_suggestions: list[str] = field(default_factory=list)
    key_strengths: list[str] = field(default_factory=list)
    raw_llm_response: str = ""


@dataclass
class ComparisonResult:
    """Side-by-side comparison of two texts."""
    original: ToneAnalysis = field(default_factory=ToneAnalysis)
    rewritten: ToneAnalysis = field(default_factory=ToneAnalysis)
    differences: list[str] = field(default_factory=list)
    improvement_areas: list[str] = field(default_factory=list)


# ── Prompt templates ────────────────────────────────────────────────────

ANALYSIS_PROMPT = """You are VibeCheck, an expert communication analyst. Analyze the following text and provide a structured assessment.

TEXT TO ANALYZE:
```
{text}
```

Return a JSON object with these exact keys (no markdown, no code fences):
{{
  "overall_tone": "Brief one-sentence summary of the overall tone",
  "emotional_subtext": ["List of 1-3 emotional undercurrents detected"],
  "clarity_score": <integer 1-10>,
  "confidence_level": "low | moderate | high | assertive | passive",
  "formality": "casual | neutral | formal | very_formal",
  "detected_mood": "Primary mood detected (e.g. frustrated, excited, neutral, anxious, warm)",
  "potential_misinterpretations": ["List 1-3 ways this could be misunderstood"],
  "rewrite_suggestions": ["1-3 specific rewrites or adjustments"],
  "key_strengths": ["1-2 things the text does well communicatively"]
}}

Only return valid JSON. No explanation outside the JSON."""

COMPARE_PROMPT = """You are VibeCheck, an expert communication analyst. Compare the ORIGINAL and REWRITTEN versions of a text and describe what changed.

ORIGINAL:
```
{original}
```

REWRITTEN:
```
{rewritten}
```

Return a JSON object with these exact keys (no markdown, no code fences):
{{
  "original_tone": "One-sentence summary of original tone",
  "rewritten_tone": "One-sentence summary of rewritten tone",
  "differences": ["List 2-4 key differences in tone, clarity, formality"],
  "improvement_areas": ["1-2 things the rewrite improved or could improve further"]
}}

Only return valid JSON. No explanation outside the JSON."""


# ── LLM Provider abstraction ─────────────────────────────────────────────

class LLMProvider:
    """Abstract base for LLM API providers."""

    def query(self, prompt: str) -> str:
        raise NotImplementedError


class OpenRouterProvider(LLMProvider):
    """Uses OpenRouter API (free-tier models available)."""

    def __init__(self, api_key: str, model: str = "gryphe/mythomax-l2-13b:free"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def query(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/akshattandon007/vibecheck",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1024,
        }
        resp = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


class OpenAICompatibleProvider(LLMProvider):
    """Generic OpenAI-compatible provider (local LLM, Ollama, etc.)."""

    def __init__(self, api_key: str, base_url: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/") + "/chat/completions"

    def query(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1024,
        }
        resp = requests.post(self.base_url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _try_parse_json(text: str) -> Optional[dict]:
    """Attempt to parse JSON from LLM response, handling markdown fences."""
    # Strip markdown fences if present
    cleaned = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def _build_provider() -> LLMProvider:
    """Factory: read env vars and return the right provider."""
    provider_type = os.environ.get("VIBECHECK_PROVIDER", "openrouter").lower()

    if provider_type == "openai":
        return OpenAICompatibleProvider(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model=os.environ.get("VIBECHECK_MODEL", "gpt-3.5-turbo"),
        )
    elif provider_type == "ollama":
        return OpenAICompatibleProvider(
            api_key="ollama",
            base_url=os.environ.get("OLLAMA_URL", "http://localhost:11434/v1"),
            model=os.environ.get("VIBECHECK_MODEL", "llama3"),
        )
    elif provider_type == "local":
        return OpenAICompatibleProvider(
            api_key=os.environ.get("LOCAL_API_KEY", "no-key"),
            base_url=os.environ.get("LOCAL_BASE_URL", "http://localhost:8000/v1"),
            model=os.environ.get("VIBECHECK_MODEL", "local-model"),
        )
    else:
        # Default: OpenRouter
        key = os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            # Try reading from config file
            config_path = os.path.expanduser("~/.vibecheck/config.json")
            if os.path.exists(config_path):
                with open(config_path) as f:
                    cfg = json.load(f)
                key = cfg.get("api_key", "")
        return OpenRouterProvider(
            api_key=key,
            model=os.environ.get("VIBECHECK_MODEL", "gryphe/mythomax-l2-13b:free"),
        )


# ── Public API ───────────────────────────────────────────────────────────

def analyze_text(text: str, provider: Optional[LLMProvider] = None) -> ToneAnalysis:
    """Analyze a piece of text for tone, subtext, and communication style.

    Args:
        text: The text to analyze (1-2000 words recommended).
        provider: Optional LLM provider. Auto-detected from env if None.

    Returns:
        ToneAnalysis dataclass with all analysis fields.
    """
    if not text or not text.strip():
        return ToneAnalysis(overall_tone="No text provided to analyze.")

    provider = provider or _build_provider()
    prompt = ANALYSIS_PROMPT.format(text=text[:4000])
    raw = provider.query(prompt)

    result = ToneAnalysis(raw_llm_response=raw)
    parsed = _try_parse_json(raw)

    if parsed:
        result.overall_tone = parsed.get("overall_tone", "")
        result.emotional_subtext = parsed.get("emotional_subtext", [])
        result.clarity_score = parsed.get("clarity_score", 0)
        result.confidence_level = parsed.get("confidence_level", "")
        result.formality = parsed.get("formality", "")
        result.detected_mood = parsed.get("detected_mood", "")
        result.potential_misinterpretations = parsed.get("potential_misinterpretations", [])
        result.rewrite_suggestions = parsed.get("rewrite_suggestions", [])
        result.key_strengths = parsed.get("key_strengths", [])

    return result


def compare_texts(original: str, rewritten: str,
                  provider: Optional[LLMProvider] = None) -> ComparisonResult:
    """Compare original and rewritten versions of a text.

    Args:
        original: The original text.
        rewritten: The rewritten/modified version.
        provider: Optional LLM provider.

    Returns:
        ComparisonResult with both analyses and difference summary.
    """
    provider = provider or _build_provider()

    # Analyze both independently
    orig_result = analyze_text(original, provider)
    rew_result = analyze_text(rewritten, provider)

    # Compare
    prompt = COMPARE_PROMPT.format(original=original[:2000], rewritten=rewritten[:2000])
    raw = provider.query(prompt)
    parsed = _try_parse_json(raw)

    diff = ComparisonResult(
        original=orig_result,
        rewritten=rew_result,
        differences=parsed.get("differences", []) if parsed else [],
        improvement_areas=parsed.get("improvement_areas", []) if parsed else [],
    )
    return diff


def setup_config(api_key: str) -> str:
    """Save the OpenRouter API key to ~/.vibecheck/config.json.

    Args:
        api_key: OpenRouter API key.

    Returns:
        Path to config file.
    """
    config_dir = os.path.expanduser("~/.vibecheck")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "config.json")
    with open(config_path, "w") as f:
        json.dump({"api_key": api_key}, f)
    os.chmod(config_path, 0o600)
    return config_path