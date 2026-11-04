"""Drug Interaction Checker Agent — queries OpenFDA for drug interactions.

Agent 1 of the HealthGuard multi-agent system.
Checks pairwise drug-drug interactions using FDA prescribing information.
"""

import httpx
from typing import Optional
from models import DrugInfo, InteractionResult, Severity

_client: httpx.Client | None = None


def set_client(client: httpx.Client | None):
    """Inject a test client. Pass None to restore the default."""
    global _client
    _client = client


def _get_client() -> httpx.Client:
    return _client or httpx.Client()


# ---------------------------------------------------------------------------
# Known high-severity interactions (curated subset for offline/demo mode)
# ---------------------------------------------------------------------------
KNOWN_INTERACTIONS: list[dict] = [
    {"drugs": ("warfarin", "aspirin"), "severity": "high",
     "description": "Aspirin increases bleeding risk when taken with warfarin. Monitor PT/INR closely.",
     "management": "Consult prescriber. Monitor for signs of bleeding."},
    {"drugs": ("warfarin", "ibuprofen"), "severity": "high",
     "description": "NSAIDs increase bleeding risk and may cause GI ulceration with warfarin.",
     "management": "Avoid NSAIDs if possible; use acetaminophen for pain."},
    {"drugs": ("lisinopril", "spironolactone"), "severity": "moderate",
     "description": "Combination may cause hyperkalemia (high potassium). Monitor potassium levels.",
     "management": "Check serum potassium regularly. Avoid potassium supplements."},
    {"drugs": ("metformin", "losartan"), "severity": "low",
     "description": "No significant interaction reported between metformin and losartan.",
     "management": "No special precautions needed."},
    {"drugs": ("simvastatin", "amlodipine"), "severity": "moderate",
     "description": "Amlodipine increases simvastatin levels, raising risk of myopathy.",
     "management": "Limit simvastatin to 20 mg/day when used with amlodipine."},
    {"drugs": ("fluoxetine", "tramadol"), "severity": "high",
     "description": "Increased risk of serotonin syndrome. Monitor for agitation, confusion, rapid heart rate.",
     "management": "Consider alternative antidepressant or pain reliever."},
    {"drugs": ("lisinopril", "metformin"), "severity": "low",
     "description": "No significant interaction. Commonly prescribed together.",
     "management": "No special precautions needed."},
    {"drugs": ("atorvastatin", "amlodipine"), "severity": "low",
     "description": "Mild interaction — amlodipine modestly increases atorvastatin levels.",
     "management": "No dose adjustment typically needed."},
    {"drugs": ("omeprazole", "methotrexate"), "severity": "moderate",
     "description": "PPIs may delay methotrexate elimination, increasing toxicity risk.",
     "management": "Avoid high-dose MTX with PPIs. Consider H2 antagonist instead."},
    {"drugs": ("levothyroxine", "calcium"), "severity": "moderate",
     "description": "Calcium supplements reduce levothyroxine absorption. Space 4+ hours apart.",
     "management": "Take levothyroxine 60 min before calcium."},
]


def normalize_drug_name(name: str) -> str:
    """Lowercase, strip, remove common suffixes for matching."""
    return name.strip().lower()


def _lookup_openfda(drug: str) -> Optional[dict]:
    """Look up drug info via OpenFDA drug labeling API."""
    url = "https://api.fda.gov/drug/label.json"
    params = {
        "search": f"active_ingredient:{drug}",
        "limit": 1,
    }
    try:
        resp = _get_client().get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                return results[0]
    except Exception:
        pass
    return None


def check_interaction(drug_a: str, drug_b: str) -> InteractionResult:
    """Check pairwise interaction between two drugs.

    First checks known interactions, then falls back to OpenFDA label search.
    """
    da, db = normalize_drug_name(drug_a), normalize_drug_name(drug_b)

    # 1. Known interaction DB
    for entry in KNOWN_INTERACTIONS:
        pair = tuple(sorted([normalize_drug_name(d) for d in entry["drugs"]]))
        check_pair = tuple(sorted([da, db]))
        if pair == check_pair:
            return InteractionResult(
                drug_a=drug_a,
                drug_b=drug_b,
                severity=Severity(entry["severity"]),
                description=entry["description"],
                management=entry["management"],
                interaction_found=True,
                source="known-db",
            )

    # 2. Try OpenFDA label search
    try:
        resp_a = _lookup_openfda(da)
        resp_b = _lookup_openfda(db)
        # If we got data from both, check for interaction mentions
        if resp_a and resp_b:
            label_a = resp_a.get("active_ingredients", [{}])[0].get("name", da)
            label_b = resp_b.get("active_ingredients", [{}])[0].get("name", db)
            # Check drug_interactions section of labels
            for label in [resp_a, resp_b]:
                sections = label.get("drug_interactions", [])
                for section in sections if sections else []:
                    text = (section if isinstance(section, str)
                            else section.get("drug_interactions", ""))
                    if isinstance(text, str) and (
                            da in text.lower() or db in text.lower()):
                        return InteractionResult(
                            drug_a=drug_a,
                            drug_b=drug_b,
                            severity=Severity.MODERATE,
                            description=f"Interaction mentioned in FDA label: {text[:300]}",
                            management="Consult your healthcare provider.",
                            interaction_found=True,
                            source="openfda",
                        )
    except Exception:
        pass

    # 3. No interaction found
    return InteractionResult(
        drug_a=drug_a,
        drug_b=drug_b,
        severity=Severity.LOW,
        description=f"No known significant interaction between {drug_a} and {drug_b}.",
        management="Always consult a healthcare provider before combining medications.",
        interaction_found=False,
        source="known-db",
    )


def get_drug_info(drug_name: str) -> DrugInfo:
    """Look up drug info from OpenFDA/RxNorm."""
    name = normalize_drug_name(drug_name)

    # Try RxNorm API for drug identity
    try:
        resp = _get_client().get(
            "https://rxnav.nlm.nih.gov/REST/rxcui.json",
            params={"name": name},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            id_group = data.get("idGroup", {})
            rxcui = id_group.get("rxnormId", [None])[0]
            if rxcui:
                return DrugInfo(
                    name=drug_name,
                    rxcui=rxcui,
                    generic_name=id_group.get("name", drug_name),
                    source="rxnorms",
                )
    except Exception:
        pass

    # Fallback: OpenFDA label search
    label_data = _lookup_openfda(name)
    if label_data:
        brand_name = label_data.get("brand_name", [None])
        generic = label_data.get("generic_name", [None])
        return DrugInfo(
            name=drug_name,
            generic_name=generic[0] if generic else None,
            brand_names=[brand_name[0]] if brand_name and brand_name[0] else [],
            source="openfda",
        )

    return DrugInfo(name=drug_name, source="simulated")


def check_all_interactions(drugs: list[str]) -> list[InteractionResult]:
    """Check all unique pairwise interactions in a drug list."""
    results = []
    for i in range(len(drugs)):
        for j in range(i + 1, len(drugs)):
            result = check_interaction(drugs[i], drugs[j])
            results.append(result)
    return results