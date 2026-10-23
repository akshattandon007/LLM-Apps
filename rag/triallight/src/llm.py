"""
LLM augmentation — builds prompts from study data and calls OpenAI-compatible API.
Supports OpenAI, OpenRouter, or any compatible endpoint via env vars.
"""
from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI

from .models import PubMedArticle, SearchResult, StudyProtocol

DEFAULT_MODEL = "gpt-4o-mini"


def build_client() -> OpenAI:
    """Build an OpenAI client from environment variables.

    Uses OPENAI_API_KEY (or OPENROUTER_API_KEY as fallback).
    Uses OPENAI_BASE_URL if set (for OpenRouter etc), defaults to OpenAI.
    """
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY") or ""
    base_url = os.environ.get("OPENAI_BASE_URL", None)
    return OpenAI(api_key=api_key, base_url=base_url or None)


def build_trial_prompt(study: StudyProtocol, articles: list[PubMedArticle]) -> str:
    """Build the prompt for a single study's plain-language digest."""
    criteria_text = "\n".join(
        f"[{c.category}] {c.text}" for c in study.eligibility_criteria
    )
    if not criteria_text:
        criteria_text = "No criteria text available."

    articles_text = ""
    if articles:
        parts = []
        for a in articles:
            parts.append(f"• {a.title} ({a.year}) — {a.authors}")
            if a.abstract:
                parts.append(f"  Abstract: {a.abstract[:500]}")
        articles_text = "\n".join(parts)

    prompt = f"""You are a patient-friendly clinical trial explainer. Your job is to read a clinical trial's official record and explain it in plain, compassionate language that someone WITHOUT a medical background can understand.

## Study Record
**NCT ID:** {study.nct_id}
**Title:** {study.brief_title}
**Status:** {study.status.value}
**Phase:** {study.phase or "Not specified"}
**Lead Sponsor:** {study.lead_sponsor or "Not specified"}
**Enrollment:** {study.enrollment_count or "Not specified"}
**Start:** {study.start_date or "Not specified"}  **Completion:** {study.completion_date or "Not specified"}

**Conditions Studied:** {', '.join(study.conditions) if study.conditions else 'Not specified'}

**Brief Summary:**
{study.brief_summary or "No summary provided."}

**Eligibility Criteria (Official):**
{criteria_text}

**Recent Research Context:**
{articles_text if articles_text else "No recent articles found."}

**Full Details:** {study.url}

---

Write a patient-friendly digest covering these 3 sections. Use **markdown** formatting. Be warm but factual. Always include a disclaimer.

## PATIENT-FRIENDLY DIGEST

### 1. What This Study Is About
(2-3 sentences explaining the study's purpose in plain language — what condition, what intervention, what they're trying to find out.)

### 2. Who Can Participate (Plain Language)
Rewrite the key eligibility criteria in plain English. Start with "This study may be a fit if you..." then "You may NOT qualify if you...". Be specific about what the criteria actually mean.

### 3. What Participation Involves
(1-2 sentences on what participants would do — visits, procedures, duration.)

### 4. Key Details at a Glance
- **Locations:** {', '.join(f"{l.city}, {l.state}" for l in study.locations) if study.locations else "Nationwide / Remote"}
- **Sponsor:** {study.lead_sponsor or "Not specified"}
- **Phase:** {study.phase or "Not specified"}

**🔗 Official Listing:** [{study.nct_id}]({study.url})

---
**⚠️ Disclaimer:** This is an AI-generated plain-language summary of the official clinical trial record. Always verify eligibility and details with the trial coordinator. This is not medical advice.
"""
    return prompt


def generate_study_digest(
    study: StudyProtocol,
    articles: list[PubMedArticle],
    model: str = DEFAULT_MODEL,
) -> str:
    """Generate a plain-language digest for one study using the LLM."""
    client = build_client()
    prompt = build_trial_prompt(study, articles)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a compassionate patient-advocate assistant. "
                    "Explain clinical trial information in plain, welcoming language. "
                    "Use markdown for structure. Never give medical advice. "
                    "Always include the standard disclaimer."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1500,
    )
    return response.choices[0].message.content or ""


def generate_search_summary(result: SearchResult, model: str = DEFAULT_MODEL) -> str:
    """Generate a summary of all search results."""
    if not result.studies:
        return f"No active clinical trials found for '{result.query}'."

    client = build_client()
    study_list = "\n\n".join(
        f"- **{s.brief_title}** ({s.nct_id}) — {s.lead_sponsor or 'Sponsor N/A'} · "
        f"{', '.join(c for c in s.conditions[:3]) if s.conditions else 'N/A'}"
        for s in result.studies[:5]
    )

    prompt = f"""A user searched for clinical trials about "{result.query}"{" near " + result.location if result.location else ""}.

{len(result.studies)} active studies were found. Here are the first {min(len(result.studies), 5)}:

{study_list}

Write a brief, encouraging overview (2-3 sentences) that tells them what they found and invites them to explore individual studies for more detail."""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful patient advocate. Be warm and clear."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=300,
    )
    return response.choices[0].message.content or ""