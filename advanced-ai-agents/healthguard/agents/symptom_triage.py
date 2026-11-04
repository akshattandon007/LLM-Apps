"""Symptom Triage Agent — classifies symptom urgency and suggests possible causes.

Agent 2 of the HealthGuard multi-agent system.
"""

from models import SymptomAssessment, Urgency

# Common symptoms with known urgency levels
KNOWN_SYMPTOMS: dict[str, dict] = {
    "chest pain": {
        "conditions": ["heart attack", "angina", "costochondritis"],
        "urgency": "emergency",
        "recommendations": ["Call emergency services (911) immediately",
                            "Do NOT drive yourself to hospital",
                            "Chew aspirin if available and not allergic"],
        "immediate": True,
    },
    "shortness of breath": {
        "conditions": ["asthma attack", "pulmonary embolism", "COPD exacerbation",
                       "anxiety attack", "pneumonia"],
        "urgency": "urgent",
        "recommendations": ["Sit upright. Try to breathe slowly.",
                            "Call 911 if breathing does not improve",
                            "Use rescue inhaler if you have asthma"],
        "immediate": False,
    },
    "headache": {
        "conditions": ["tension headache", "migraine", "cluster headache",
                       "sinus infection", "dehydration"],
        "urgency": "routine",
        "recommendations": ["Rest in a dark room",
                            "Stay hydrated",
                            "Over-the-counter pain reliever may help",
                            "See doctor if severe or persistent > 48 hours"],
        "immediate": False,
    },
    "fever": {
        "conditions": ["viral infection", "bacterial infection",
                       "influenza", "COVID-19", "UTI"],
        "urgency": "soon",
        "recommendations": ["Rest and hydrate",
                            "Take acetaminophen/paracetamol for fever",
                            "Monitor temperature every 4 hours",
                            "See doctor if fever > 103°F (39.4°C) or > 3 days"],
        "immediate": False,
    },
    "vomiting": {
        "conditions": ["food poisoning", "stomach virus", "pregnancy",
                       "migraine", "medication side effect"],
        "urgency": "soon",
        "recommendations": ["Sip clear fluids slowly (water, electrolyte drinks)",
                            "Avoid solid food until vomiting stops",
                            "Seek help if unable to keep liquids down > 12 hours",
                            "Call 911 if blood in vomit"],
        "immediate": False,
    },
    "rash": {
        "conditions": ["allergic reaction", "eczema", "contact dermatitis",
                       "poison ivy", "psoriasis", "shingles"],
        "urgency": "routine",
        "recommendations": ["Avoid scratching",
                            "Apply cold compress",
                            "OTC hydrocortisone cream for mild rashes",
                            "See doctor if spreading or blistering"],
        "immediate": False,
    },
    "bleeding": {
        "conditions": ["injury/wound", "hemophilia", "medication side effect"],
        "urgency": "urgent",
        "recommendations": ["Apply direct pressure with clean cloth",
                            "Elevate wound above heart if possible",
                            "Call 911 if bleeding does not stop after 10 min"],
        "immediate": True,
    },
    "dizziness": {
        "conditions": ["dehydration", "low blood pressure",
                       "inner ear infection", "anemia", "medication side effect"],
        "urgency": "soon",
        "recommendations": ["Sit or lie down immediately",
                            "Drink water slowly",
                            "Avoid driving until symptoms resolve",
                            "See doctor if recurring or persistent"],
        "immediate": False,
    },
    "back pain": {
        "conditions": ["muscle strain", "herniated disc", "sciatica",
                       "poor posture", "arthritis"],
        "urgency": "routine",
        "recommendations": ["Rest and apply heat/ice alternately",
                            "Gentle stretching if pain allows",
                            "OTC pain relievers (ibuprofen/naproxen)",
                            "See doctor if severe or after injury"],
        "immediate": False,
    },
    "swelling": {
        "conditions": ["allergic reaction", "injury", "infection",
                       "lymphoedema", "medication side effect"],
        "urgency": "urgent",
        "recommendations": ["If face/lip/throat swelling: call 911 (anaphylaxis)",
                            "Apply cold compress to reduce swelling",
                            "Elevate swollen area",
                            "See doctor promptly if spreading"],
        "immediate": False,
    },
}


def assess_symptom(symptom: str) -> SymptomAssessment:
    """Assess a symptom and produce a triage assessment."""
    symptom_lower = symptom.lower().strip()

    # Exact match first
    if symptom_lower in KNOWN_SYMPTOMS:
        info = KNOWN_SYMPTOMS[symptom_lower]
        return SymptomAssessment(
            symptom=symptom,
            possible_conditions=info["conditions"],
            urgency=Urgency(info["urgency"]),
            recommendations=info["recommendations"],
            requires_immediate_care=info["immediate"],
            source="known-db",
        )

    # Partial match
    possible_conditions = []
    urgency = Urgency.ROUTINE
    recommendations = []
    immediate = False

    for key, info in KNOWN_SYMPTOMS.items():
        if key in symptom_lower or symptom_lower in key:
            possible_conditions.extend(info["conditions"])
            # Use highest urgency found
            urgency_order = ["routine", "soon", "urgent", "emergency"]
            if urgency_order.index(info["urgency"]) > urgency_order.index(urgency.value):
                urgency = Urgency(info["urgency"])
            recommendations.extend(info["recommendations"])
            if info["immediate"]:
                immediate = True

    if not possible_conditions:
        return SymptomAssessment(
            symptom=symptom,
            possible_conditions=["General illness — consult a healthcare provider for accurate diagnosis"],
            urgency=Urgency.ROUTINE,
            recommendations=["Monitor symptoms. If worsening, see a doctor.",
                             "Keep a symptom diary (onset, duration, severity)",
                             "Consider telemedicine consultation"],
            source="known-db",
        )

    return SymptomAssessment(
        symptom=symptom,
        possible_conditions=list(set(possible_conditions)),
        urgency=urgency,
        recommendations=list(set(recommendations)),
        requires_immediate_care=immediate,
        source="known-db",
    )


def assess_multiple_symptoms(symptoms: list[str]) -> list[SymptomAssessment]:
    """Assess a list of symptoms, one by one."""
    return [assess_symptom(s) for s in symptoms]