"""Orchestrator — runs the FairWheel crew.

Planner step: each specialist agent runs independently, then the Deal Reviewer
critic aggregates. Agents that hit API failures fall back to simulated data
(flagging source="simulated") so the pipeline always produces a report.
"""

from __future__ import annotations

from .agents import cost_analyst, deal_reviewer, grievance_scout, recall_auditor, safety_scorer
from .models import ComplaintReport, CostReport, FairWheelReport, RecallReport, SafetyReport, VehicleQuery


def run_pipeline(query: VehicleQuery, demo: bool = False) -> FairWheelReport:
    """Run the full advisory crew and return the assembled report."""
    if demo:
        # Force simulated data so every agent reports source="simulated".
        safety = safety_scorer._simulate(query, "demo mode")
        complaints = grievance_scout._simulate(query, "demo mode")
        recalls = recall_auditor._simulate(query, "demo mode")
        cost = cost_analyst._simulate(query, "demo mode")
    else:
        safety = safety_scorer.run(query)
        complaints = grievance_scout.run(query)
        recalls = recall_auditor.run(query)
        cost = cost_analyst.run(query)

    verdict = deal_reviewer.run(query, safety, complaints, recalls, cost)
    return FairWheelReport(
        query=query,
        safety=safety,
        recalls=recalls,
        complaints=complaints,
        cost=cost,
        verdict=verdict,
    )