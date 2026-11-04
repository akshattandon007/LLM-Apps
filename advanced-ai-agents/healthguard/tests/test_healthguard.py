"""Tests for HealthGuard multi-agent system."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from agents.drug_checker import (
    check_interaction, check_all_interactions, get_drug_info,
    normalize_drug_name, set_client as set_drug_client,
    KNOWN_INTERACTIONS,
)
from agents.symptom_triage import assess_symptom, assess_multiple_symptoms
from agents.condition_researcher import (
    search_condition, search_multiple_conditions, set_client as set_condition_client,
)
from agents.report_compiler import compile_report, format_report


class TestDrugChecker:
    """Tests for Agent 1 — Drug Interaction Checker."""

    def test_normalize_drug_name(self):
        assert normalize_drug_name("Aspirin") == "aspirin"
        assert normalize_drug_name("  IBUPROFEN  ") == "ibuprofen"

    def test_known_interaction_found(self):
        result = check_interaction("warfarin", "aspirin")
        assert result.interaction_found is True
        assert result.severity.value == "high"
        assert result.drug_a.lower() == "warfarin"
        assert result.drug_b.lower() == "aspirin"

    def test_known_interaction_reversed_order(self):
        result = check_interaction("aspirin", "warfarin")
        assert result.interaction_found is True
        assert result.severity.value == "high"

    def test_no_interaction(self):
        result = check_interaction("aspirin", "vitamin c")
        assert result.interaction_found is False

    def test_check_all_interactions(self):
        results = check_all_interactions(["warfarin", "aspirin", "vitamin c"])
        assert len(results) == 3  # 3 pairs: w+a, w+v, a+v
        # warfarin+aspirin should be found
        w_a = [r for r in results
               if {r.drug_a.lower(), r.drug_b.lower()} == {"warfarin", "aspirin"}]
        assert len(w_a) == 1
        assert w_a[0].interaction_found is True
        assert w_a[0].severity.value == "high"

    def test_get_drug_info_simulated_fallback(self):
        info = get_drug_info("NonexistentDrugXYZ123")
        assert info.name == "NonexistentDrugXYZ123"
        assert info.source in ("simulated", "live")

    def test_known_interaction_count(self):
        """Verify we have at least 8 known interaction pairs."""
        assert len(KNOWN_INTERACTIONS) >= 8


class TestSymptomTriage:
    """Tests for Agent 2 — Symptom Triage."""

    def test_emergency_symptom(self):
        result = assess_symptom("chest pain")
        assert result.requires_immediate_care is True
        assert "emergency" in result.urgency.value
        assert "911" in " ".join(result.recommendations).lower()

    def test_routine_symptom(self):
        result = assess_symptom("headache")
        assert result.requires_immediate_care is False
        assert result.urgency.value == "routine"

    def test_partial_match(self):
        result = assess_symptom("severe headache with nausea")
        assert "headache" in result.symptom.lower()
        assert len(result.possible_conditions) > 0

    def test_unknown_symptom(self):
        result = assess_symptom("fribulonia")
        assert len(result.possible_conditions) > 0  # Falls back to generic advice

    def test_multiple_symptoms(self):
        results = assess_multiple_symptoms(["headache", "chest pain"])
        assert len(results) == 2
        assert results[0].requires_immediate_care is False
        assert results[1].requires_immediate_care is True


class TestConditionResearcher:
    """Tests for Agent 3 — Condition Researcher."""

    def test_known_condition(self):
        result = search_condition("common cold")
        assert result.name == "common cold"
        assert len(result.symptoms) > 0
        assert len(result.treatments) > 0
        assert result.when_to_see_doctor != ""

    def test_partial_match_condition(self):
        result = search_condition("hypertension")
        assert result.description != ""
        assert result.source == "known-db"

    def test_unknown_condition(self):
        result = search_condition("zzzznotacondition")
        assert result.source == "simulated"

    def test_multiple_conditions(self):
        results = search_multiple_conditions(["asthma", "influenza"])
        assert len(results) == 2

    def test_gerd_match(self):
        """GERD should match with partial keys."""
        result = search_condition("gerd")
        assert result.name == "gerd"
        assert "stomach acid" in result.description.lower()


class TestReportCompiler:
    """Tests for Agent 4 — Report Compiler."""

    def test_empty_report(self):
        report = compile_report()
        assert report.summary != ""
        assert report.generated_at != ""
        assert report.source == "compiled"

    def test_report_with_interaction(self):
        from models import InteractionResult, Severity
        interactions = [
            InteractionResult("warfarin", "aspirin", Severity.HIGH,
                              "Risk of bleeding", "Monitor carefully", True)
        ]
        report = compile_report(interactions=interactions)
        assert len(report.drug_interactions) == 1
        assert len(report.key_warnings) >= 1
        assert "warfarin" in report.key_warnings[0]

    def test_report_formatting(self):
        report = compile_report()
        formatted = format_report(report)
        assert "HEALTHGUARD" in formatted
        assert "DISCLAIMER" in formatted

    def test_severity_warning_threshold(self):
        from models import InteractionResult, Severity
        low = InteractionResult("a", "b", Severity.LOW, "none", "", False)
        high = InteractionResult("x", "y", Severity.HIGH, "danger", "call doctor", True)
        report = compile_report(interactions=[low, high])
        assert len(report.key_warnings) == 1  # Only high severity triggers warning
        assert "x + y" in report.key_warnings[0]


class TestEndToEnd:
    """Full pipeline integration tests."""

    def test_drugs_to_report(self):
        """Run the full pipeline: drugs → interactions → report."""
        drugs = ["warfarin", "aspirin"]
        interactions = check_all_interactions(drugs)
        report = compile_report(interactions=interactions)
        assert len(report.drug_interactions) == 1
        assert report.drug_interactions[0].interaction_found is True
        assert report.key_warnings is not None

    def test_symptoms_to_report(self):
        """Run the full pipeline: symptoms → assessment → report."""
        symptom_results = assess_multiple_symptoms(["headache", "chest pain"])
        report = compile_report(symptoms=symptom_results)
        assert len(report.symptom_assessments) == 2
        # chest pain should trigger emergency warning
        has_emergency = any("IMMEDIATE CARE" in w for w in report.key_warnings)
        assert has_emergency, "Chest pain should trigger immediate care warning"

    def test_full_pipeline(self):
        """Run all agents end-to-end."""
        drugs = ["warfarin", "ibuprofen"]
        symptoms = ["headache", "back pain"]

        interactions = check_all_interactions(drugs)
        symptom_results = assess_multiple_symptoms(symptoms)

        # Collect conditions from symptoms
        cond_names = set()
        for s in symptom_results:
            for c in s.possible_conditions:
                cond_names.add(c)
        condition_results = search_multiple_conditions(list(cond_names)[:3])

        report = compile_report(interactions, symptom_results, condition_results)
        assert len(report.drug_interactions) == 1
        assert len(report.symptom_assessments) == 2
        assert len(report.condition_info) > 0
        assert report.generated_at != ""