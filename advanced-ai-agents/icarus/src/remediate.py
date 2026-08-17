"""Remediation — propose and execute remediation plans, human-gated for destructive actions.

The workflow:
  1. propose_remediation(root_cause, evidence) -> RemediationPlan
  2. approve_action(plan, action_id) — the human gate
  3. execute_action(plan, action_id) — only succeeds after approval

Destructive actions (rollback, feature-flag toggle) are always flagged as
``destructive=True``.  The pipeline never auto-executes without explicit
approval via ``approve_action``.
"""

from __future__ import annotations

from datetime import timezone
from typing import Protocol

from src.models import (
    Alert,
    Deployment,
    Evidence,
    RemediationAction,
    RemediationActionStatus,
    RemediationActionType,
    RemediationPlan,
    RootCause,
)

EXECUTOR: Executor | None = None


class Executor(Protocol):
    """Protocol for real command execution (e.g., kubectl, API calls).

    In v1 this is a no-op — the command string is logged but not executed.
    Override with a real executor for production use.
    """

    def run(self, command: str, destructive: bool, /) -> str:
        """Execute *command* and return stdout / a summary."""
        ...


class DryRunExecutor:
    """Simulated executor — records the command without running it."""

    def run(self, command: str, destructive: bool = False, /) -> str:
        return f"[dry-run] would execute: {command}  (destructive={destructive})"


def set_executor(executor: Executor | None) -> None:
    """Inject a custom executor (for tests or real infra)."""
    global EXECUTOR
    EXECUTOR = executor


def get_executor() -> Executor:
    if EXECUTOR is not None:
        return EXECUTOR
    return DryRunExecutor()


# ── Plan proposals ─────────────────────────────────────────────────────────


def _latest_deployment(evidence: Evidence) -> Deployment | None:
    deployed = [d for d in evidence.deployments if d.status == "deployed"]
    return max(deployed, key=lambda d: d.timestamp) if deployed else None


def propose_remediation(root_cause: RootCause, evidence: Evidence) -> RemediationPlan:
    """Propose a remediation plan rooted in the RCA findings.

    The plan is **always** human-gated — no action is auto-approved.
    """
    plan = RemediationPlan(incident_id=root_cause.incident_id)
    kinds = {c.kind for c in root_cause.correlations}
    alert = evidence.alert

    if "deployment_overlap" in kinds:
        deploy = _latest_deployment(evidence)
        ver = ""
        if deploy and deploy.version:
            ver = deploy.version if deploy.version.startswith("v") else f"v{deploy.version}"
        prev = "the previous stable version"
        plan.actions.append(
            RemediationAction(
                id="act-rollback",
                type=RemediationActionType.rollback,
                destructive=True,
                description=f"Roll back {alert.service} {ver} to {prev}",
                command=f"kubectl rollout undo deployment/{alert.service}",
                rationale=(
                    "Deployment landed inside the alert window; rollback is the fastest "
                    "mitigation to restore SLO."
                ),
            )
        )
        plan.actions.append(
            RemediationAction(
                id="act-flag",
                type=RemediationActionType.feature_flag,
                destructive=True,
                description="Disable the new payment gateway feature flag on checkout-service",
                command="icarus flag off checkout-service new-payment-gateway",
                rationale="Isolates the suspected feature without a full rollback of all changes.",
            )
        )

    if "metric_anomaly" in kinds and "deployment_overlap" not in kinds:
        plan.actions.append(
            RemediationAction(
                id="act-scale",
                type=RemediationActionType.scale_up,
                destructive=False,
                description=f"Scale up {alert.service} replicas to absorb load",
                command=f"kubectl scale deployment/{alert.service} --replicas=5",
                rationale="Metrics indicate capacity stress; scaling up can absorb the spike.",
            )
        )
        plan.actions.append(
            RemediationAction(
                id="act-restart",
                type=RemediationActionType.restart,
                destructive=False,
                description=f"Restart unhealthy pods in {alert.service}",
                command=f"kubectl rollout restart deployment/{alert.service}",
                rationale="Restart clears transient process-level issues.",
            )
        )

    if any("timeout" in l.message.lower() or "connection reset" in l.message.lower() for l in evidence.logs):
        plan.actions.append(
            RemediationAction(
                id="act-dependency",
                type=RemediationActionType.other,
                destructive=False,
                description="Escalate to dependency owner (payment gateway team)",
                command="pagerduty: escalate to payment-gateway team",
                rationale="Logs show downstream timeout / connection reset; the dependency team "
                "should investigate.",
            )
        )

    # Fallback: if no specific actions yet, propose a restart.
    if not plan.actions:
        plan.actions.append(
            RemediationAction(
                id="act-restart",
                type=RemediationActionType.restart,
                destructive=False,
                description=f"Restart {alert.service} pods as a generic mitigation",
                command=f"kubectl rollout restart deployment/{alert.service}",
                rationale="No strong signal; restart is a safe, non-destructive first step.",
            )
        )

    return plan


# ── Human gate ─────────────────────────────────────────────────────────────


def approve_action(plan: RemediationPlan, action_id: str) -> RemediationAction:
    """Approve a single action.  This is the human gate.

    Raises ``ValueError`` if the action doesn't exist or is already
    executed/skipped.
    """
    for action in plan.actions:
        if action.id == action_id:
            if action.status in (RemediationActionStatus.executed, RemediationActionStatus.skipped):
                raise ValueError(
                    f"Cannot approve action {action_id}: already {action.status.value}"
                )
            action.status = RemediationActionStatus.approved
            action.approved_at = _now()
            plan.approved = True
            return action
    raise ValueError(f"Action '{action_id}' not found in the remediation plan")


def execute_action(plan: RemediationPlan, action_id: str) -> RemediationAction:
    """Execute an approved action.

    **Never auto-executes destructive ops.** Raises ``RuntimeError`` if the
    action has not been approved first.
    """
    for action in plan.actions:
        if action.id == action_id:
            if action.status != RemediationActionStatus.approved:
                raise RuntimeError(
                    f"Action {action_id} is not approved — remediation is human-gated. "
                    "Call approve_action() first."
                )
            executor = get_executor()
            executor.run(action.command, action.destructive)
            action.status = RemediationActionStatus.executed
            action.executed_at = _now()
            return action
    raise ValueError(f"Action '{action_id}' not found in the remediation plan")


def _now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)