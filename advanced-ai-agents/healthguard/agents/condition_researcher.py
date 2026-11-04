"""Condition Researcher Agent — researches medical conditions via NIH/MedlinePlus.

Agent 3 of the HealthGuard multi-agent system.
Fetches condition info from MedlinePlus (free, zero-auth) with offline fallback.
"""

import re
import httpx
from typing import Optional
from models import ConditionInfo

_client: httpx.Client | None = None


def set_client(client: httpx.Client | None):
    global _client
    _client = client


def _get_client() -> httpx.Client:
    return _client or httpx.Client()


# ---------------------------------------------------------------------------
# Curated condition data for offline/demo mode
# ---------------------------------------------------------------------------
CONDITION_DB: dict[str, dict] = {
    "common cold": {
        "description": "A viral infection of the upper respiratory tract causing mild illness. Usually resolves in 7-10 days.",
        "symptoms": ["Runny or stuffy nose", "Sore throat", "Cough", "Sneezing",
                     "Mild headache", "Low-grade fever", "Fatigue"],
        "treatments": ["Rest and hydration", "OTC decongestants and pain relievers",
                       "Warm saltwater gargles", "Honey and lemon in warm tea",
                       "Zinc lozenges may shorten duration"],
        "when_to_see_doctor": "If fever persists > 3 days, symptoms worsen instead of improving, or breathing difficulty develops.",
        "prevention_tips": ["Hand washing", "Avoid touching face",
                            "Vitamin C and zinc supplementation",
                            "Adequate sleep and stress management"],
    },
    "influenza": {
        "description": "A contagious respiratory illness caused by influenza viruses. More severe than the common cold and can lead to serious complications.",
        "symptoms": ["Sudden fever (100-104°F)", "Body aches and muscle pain",
                     "Fatigue and weakness", "Dry cough", "Sore throat",
                     "Headache", "Chills", "Runny or stuffy nose"],
        "treatments": ["Antiviral medications (oseltamivir) if caught early",
                       "Acetaminophen or ibuprofen for fever and aches",
                       "Rest and hydration", "Cough suppressants if needed"],
        "when_to_see_doctor": "If you have difficulty breathing, chest pain, confusion, or symptoms improve then return with fever.",
        "prevention_tips": ["Annual flu vaccine", "Hand hygiene",
                            "Avoid close contact with sick people",
                            "Cover mouth when coughing/sneezing"],
    },
    "hypertension": {
        "description": "High blood pressure — a common condition where the force of blood against artery walls is too high. Often silent with no symptoms until complications arise.",
        "symptoms": ["Often no symptoms (silent condition)",
                     "Occasional headaches", "Shortness of breath",
                     "Nosebleeds (in severe cases)", "Blurred vision"],
        "treatments": ["ACE inhibitors (lisinopril)", "Diuretics",
                       "Beta-blockers", "Calcium channel blockers",
                       "DASH diet (low sodium, high fruits/vegetables)"],
        "when_to_see_doctor": "If BP consistently > 140/90, if you experience chest pain or vision changes, or if prescribed medication isn't controlling BP.",
        "prevention_tips": ["Reduce sodium intake (< 2300 mg/day)",
                            "Regular exercise (150 min/week moderate)",
                            "Limit alcohol", "Manage stress",
                            "Maintain healthy weight"],
    },
    "diabetes type 2": {
        "description": "A chronic condition where the body becomes resistant to insulin or doesn't produce enough, causing high blood sugar.",
        "symptoms": ["Increased thirst and urination", "Fatigue",
                     "Blurred vision", "Slow-healing cuts", "Numbness in hands/feet",
                     "Frequent infections", "Weight loss despite increased appetite"],
        "treatments": ["Metformin (first-line medication)", "Sulfonylureas",
                       "DPP-4 inhibitors", "GLP-1 agonists",
                       "Insulin therapy (for advanced cases)"],
        "when_to_see_doctor": "If blood sugar > 300 mg/dL, unexplained weight loss, vision changes, or foot sores that won't heal.",
        "prevention_tips": ["Healthy diet (low sugar, high fiber)",
                            "Regular exercise", "Weight management",
                            "Regular blood sugar monitoring",
                            "Limit processed carbohydrates"],
    },
    "asthma": {
        "description": "A chronic lung condition where airways narrow and swell, producing extra mucus. Triggers vary widely.",
        "symptoms": ["Wheezing", "Shortness of breath", "Chest tightness",
                     "Coughing (especially at night)", "Rapid breathing"],
        "treatments": ["Rescue inhalers (albuterol)", "Controller inhalers (corticosteroids)",
                       "Leukotriene modifiers", "Biologic medications",
                       "Avoid triggers and allergens"],
        "when_to_see_doctor": "If rescue inhaler isn't controlling symptoms, peak flow drops > 20%, or ER visits for asthma occur.",
        "prevention_tips": ["Identify and avoid triggers (pollen, dust, mold, pet dander)",
                            "Use air purifiers", "Get annual flu vaccine",
                            "Follow written asthma action plan"],
    },
    "gastroesophageal reflux disease (gerd)": {
        "description": "A chronic condition where stomach acid frequently flows back into the esophagus, causing irritation.",
        "symptoms": ["Heartburn (burning chest pain)", "Regurgitation",
                     "Bitter taste in mouth", "Coughing", "Hoarseness",
                     "Disrupted sleep (waking up coughing/choking)"],
        "treatments": ["PPIs (omeprazole, pantoprazole)", "H2 blockers (famotidine)",
                       "Antacids for mild symptoms", "Lifestyle and diet changes",
                       "Elevated head when sleeping"],
        "when_to_see_doctor": "If PPIs don't help after 8 weeks, severe pain, weight loss, or blood in vomit/stool.",
        "prevention_tips": ["Eat smaller meals", "Avoid lying down after eating (wait 3 hours)",
                            "Limit trigger foods (spicy, fatty, citrus, caffeine)",
                            "Maintain healthy weight", "Elevate bed head 6-8 inches"],
    },
    "migraine": {
        "description": "A neurological condition causing intense recurring headaches with sensory disturbances. More than just a bad headache.",
        "symptoms": ["Throbbing pain (often one-sided)", "Light sensitivity (photophobia)",
                     "Sound sensitivity", "Aura (visual disturbances before onset)",
                     "Nausea", "Tingling or numbness"],
        "treatments": ["Triptans (sumatriptan, rizatriptan)", "NSAIDs",
                       "CGRP inhibitors (newer class)", "Magnesium supplements",
                       "Cold packs and dark room"],
        "when_to_see_doctor": "If migraines last > 72 hours, frequency increases, or OTC medications are ineffective.",
        "prevention_tips": ["Identify triggers (certain foods, bright lights, stress)",
                            "Maintain consistent sleep schedule",
                            "Stay hydrated", "Limit caffeine and alcohol",
                            "Consider magnesium or riboflavin (B2) supplements"],
    },
}


def _search_medlineplus(condition: str) -> Optional[dict]:
    """Search MedlinePlus for condition information."""
    url = "https://wsearch.nlm.nih.gov/ws/query"
    params = {
        "db": "healthTopics",
        "term": condition,
        "retmax": 1,
    }
    try:
        resp = _get_client().get(url, params=params, timeout=15)
        if resp.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.text)
            ns = {"m": "http://webservices.nlm.nih.gov/"}
            results = root.findall(".//m:result", ns)
            if results:
                result = results[0]
                content = result.find("m:content", ns)
                snippet = result.find("m:snippet", ns)
                return {
                    "title": (result.find("m:title", ns).text
                              if result.find("m:title", ns) is not None else condition),
                    "content": content.text[:1000] if content is not None and content.text else "",
                    "snippet": snippet.text[:500] if snippet is not None and snippet.text else "",
                    "url": (result.find("m:url", ns).text
                            if result.find("m:url", ns) is not None else ""),
                }
    except Exception:
        pass
    return None


def search_condition(condition_name: str) -> ConditionInfo:
    """Research a medical condition from MedlinePlus + local DB."""
    key = condition_name.lower().strip()

    # Try local DB first
    if key in CONDITION_DB:
        info = CONDITION_DB[key]
        return ConditionInfo(
            name=condition_name,
            description=info["description"],
            symptoms=info["symptoms"],
            treatments=info["treatments"],
            when_to_see_doctor=info["when_to_see_doctor"],
            prevention_tips=info["prevention_tips"],
            source="known-db",
        )

    # Try MedlinePlus
    medline = _search_medlineplus(condition_name)
    if medline:
        return ConditionInfo(
            name=condition_name,
            description=medline.get("content", ""),
            source="medlineplus",
        )

    # Partial match in local DB
    for db_key, info in CONDITION_DB.items():
        if key in db_key or db_key in key:
            return ConditionInfo(
                name=condition_name,
                description=info["description"],
                symptoms=info["symptoms"],
                treatments=info["treatments"],
                when_to_see_doctor=info["when_to_see_doctor"],
                prevention_tips=info["prevention_tips"],
                source="known-db",
            )

    return ConditionInfo(
        name=condition_name,
        description=f"No detailed information found for '{condition_name}'. Please consult a healthcare professional.",
        source="simulated",
    )


def search_multiple_conditions(conditions: list[str]) -> list[ConditionInfo]:
    """Research multiple conditions."""
    return [search_condition(c) for c in conditions]