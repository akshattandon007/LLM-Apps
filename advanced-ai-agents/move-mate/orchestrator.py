"""Orchestrator — coordinates all 5 agents to produce the relocation playbook."""

from models import MoveDetails, Playbook
from agents import (
    utility_scheduler,
    address_changer,
    cost_estimator,
    neighborhood_scout,
    timeline_architect,
)


def run(details: MoveDetails) -> Playbook:
    """
    Run all 5 agents and compile results into a Playbook.

    This is the central coordination function. Each agent runs independently
    and contributes its section to the final playbook.
    """
    playbook = Playbook(move_details=details)

    # Agent 1: Utility Scheduler
    playbook.utilities = utility_scheduler.run(details)

    # Agent 2: Address Changer
    playbook.address_changes = address_changer.run(details)

    # Agent 3: Cost Estimator
    playbook.costs = cost_estimator.run(details)

    # Agent 4: Neighborhood Scout
    playbook.neighborhood = neighborhood_scout.run(details)

    # Agent 5: Timeline Architect
    playbook.timeline = timeline_architect.run(details)

    return playbook