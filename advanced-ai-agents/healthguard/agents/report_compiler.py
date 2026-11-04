"""Report Compiler Agent — compiles all agent findings into a plain-language health report.

Agent 4 of the HealthGuard multi-agent system.
"""

from datetime import datetime
from models import (
    HealthReport, InteractionResult, SymptomAssessment,
    ConditionInfo, Severity, Urgency
)


def compile_report(
    interactions: list[InteractionResult] | None = None,
    symptoms: list[SymptomAssessment] | None = None,
    conditions: list[ConditionInfo] | None = None,
) -> HealthReport:
    """Collect all agent outputs and compile into a structured health report."""
    interactions = interactions or []
    symptoms = symptoms or []
    conditions = conditions or []

    # Collect key warnings
    key_warnings = []
    for i in interactions:
        if i.severity in (Severity.HIGH, Severity.SEVERE):
            key_warnings.append(
                f"⚠️ SEVERE interaction: {i.drug_a} + {i.drug_b} — {i.description[:120]}"
            )

    for s in symptoms:
        if s.requires_immediate_care:
            key_warnings.append(
                f"🚨 IMMEDIATE CARE NEEDED: {s.symptom} — "
                f"{' '.join(s.recommendations[:2])}"
            )

    # Collect recommendations
    recommendations = []
    for i in interactions:
        if i.interaction_found and i.management:
            recommendations.append(
                f"{i.drug_a} + {i.drug_b}: {i.management}"
            )

    for s in symptoms:
        for r in s.recommendations[:2]:
            if r not in recommendations:
                recommendations.append(f"({s.symptom}) {r}")

    for c in conditions:
        if c.when_to_see_doctor:
            recommendations.append(
                f"({c.name}) {c.when_to_see_doctor}"
            )

    # Generate summary
    summary_parts = []

    if interactions:
        found = [i for i in interactions if i.interaction_found]
        severe = [i for i in found if i.severity in (Severity.HIGH, Severity.SEVERE)]
        if severe:
            summary_parts.append(
                f"⚠️ Found {len(severe)} significant drug interaction(s) requiring attention."
            )
        elif found:
            summary_parts.append(
                f"ℹ️ Found {len(found)} drug interaction(s) — mostly minor. Still worth reviewing."
            )
        else:
            summary_parts.append(
                f"✅ No known interactions found among the {len({i.drug_a for i in interactions})} medications checked."
            )

    if symptoms:
        urgent_count = len([s for s in symptoms if s.urgency in (Urgency.URGENT, Urgency.EMERGENCY)])
        if urgent_count > 0:
            summary_parts.append(
                f"🚨 {urgent_count} symptom(s) flagged as urgent/emergency — seek medical attention."
            )
        else:
            summary_parts.append(
                f"📋 {len(symptoms)} symptom(s) assessed. None flagged as immediately dangerous."
            )

    if conditions:
        summary_parts.append(
            f"📖 Researched {len(conditions)} condition(s). "
            f"See below for treatment and prevention information."
        )

    if not summary_parts:
        summary_parts.append("No health data provided. Run healthguard with medication and/or symptoms.")

    summary = "\n".join(summary_parts)

    return HealthReport(
        drug_interactions=interactions,
        symptom_assessments=symptoms,
        condition_info=conditions,
        summary=summary,
        key_warnings=key_warnings,
        recommendations=recommendations,
        generated_at=datetime.now().isoformat(),
        source="compiled",
    )


def _severity_label(s: Severity) -> str:
    labels = {
        Severity.LOW: "Low — No special action needed",
        Severity.MODERATE: "Moderate — Monitor and consult doctor",
        Severity.HIGH: "High — Requires medical review",
        Severity.SEVERE: "SEVERE — Seek immediate medical attention",
    }
    return labels.get(s, "Unknown")


def _urgency_label(u: Urgency) -> str:
    labels = {
        Urgency.ROUTINE: "Routine — Can wait for regular appointment",
        Urgency.SOON: "Soon — Schedule an appointment this week",
        Urgency.URGENT: "Urgent — Seek care within 24 hours",
        Urgency.EMERGENCY: "EMERGENCY — Call 911 or go to ER now",
    }
    return labels.get(u, "Unknown")


def format_report(report: HealthReport) -> str:
    """Format the health report as a readable string."""
    lines = []
    lines.append("=" * 70)
    lines.append("                 HEALTHGUARD — Health Report")
    lines.append("=" * 70)
    lines.append(f"Generated: {report.generated_at}")
    lines.append("")

    # Warnings
    if report.key_warnings:
        lines.append("⚠️  KEY WARNINGS")
        lines.append("-" * 40)
        for w in report.key_warnings:
            lines.append(f"  {w}")
        lines.append("")

    # Summary
    lines.append("📋  SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  {report.summary}")
    lines.append("")

    # Drug Interactions
    if report.drug_interactions:
        lines.append("💊  DRUG INTERACTIONS")
        lines.append("-" * 40)
        for i in report.drug_interactions:
            label = _severity_label(i.severity)
            lines.append(f"  {i.drug_a} + {i.drug_b}")
            lines.append(f"  Severity: {label}")
            lines.append(f"  {i.description[:200]}")
            if i.management:
                lines.append(f"  Suggestion: {i.management}")
            lines.append(f"  Source: {i.source}")
            lines.append("")
        lines.append("")

    # Symptom Assessments
    if report.symptom_assessments:
        lines.append("🩺  SYMPTOM ASSESSMENTS")
        lines.append("-" * 40)
        for s in report.symptom_assessments:
            label = _urgency_label(s.urgency)
            lines.append(f"  {s.symptom}")
            lines.append(f"  Urgency: {label}")
            if s.possible_conditions:
                lines.append(f"  Possible: {', '.join(s.possible_conditions[:4])}")
            if s.recommendations:
                lines.append(f"  Next steps: {'; '.join(s.recommendations[:3])}")
            lines.append("")
        lines.append("")

    # Condition Info
    if report.condition_info:
        lines.append("📖  CONDITION RESEARCH")
        lines.append("-" * 40)
        for c in report.condition_info:
            lines.append(f"  {c.name}")
            lines.append(f"  {c.description[:200]}")
            if c.treatments:
                lines.append(f"  Treatments: {', '.join(c.treatments[:4])}")
            if c.when_to_see_doctor:
                lines.append(f"  See doctor if: {c.when_to_see_doctor}")
            lines.append("")
        lines.append("")

    # Recommendations
    if report.recommendations:
        lines.append("📌  RECOMMENDATIONS")
        lines.append("-" * 40)
        for r in report.recommendations[:8]:
            lines.append(f"  • {r}")
        if len(report.recommendations) > 8:
            lines.append(f"  ... and {len(report.recommendations) - 8} more")
        lines.append("")

    lines.append("=" * 70)
    lines.append("DISCLAIMER: This report is for informational purposes only.")
    lines.append("It does NOT replace professional medical advice. If in doubt,")
    lines.append("consult a qualified healthcare provider or call emergency services.")
    lines.append("=" * 70)

    return "\n".join(lines)