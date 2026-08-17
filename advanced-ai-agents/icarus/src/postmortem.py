"""Post-mortem — draft structured incident reports and render them as markdown."""

from __future__ import annotations

from datetime import datetime, timezone

from src.models import (
    ActionItem,
    AlertSeverity,
    Evidence,
    Incident,
    PostMortem,
    RemediationActionStatus,
    RemediationPlan,
    RootCause,
    TimelineEntry,
)


def draft_postmortem(
    incident: Incident,
    root_cause: RootCause,
    remediation: RemediationPlan,
    evidence: Evidence,
) -> PostMortem:
    """Draft a structured post-mortem report from the incident lifecycle data."""
    timeline = _build_timeline(incident, evidence, remediation)
    impact = _build_impact(evidence)
    action_items = _build_action_items(root_cause, evidence)

    return PostMortem(
        incident_id=incident.id,
        title=incident.alert.title,
        summary=root_cause.summary,
        severity=incident.severity,
        timeline=timeline,
        impact=impact,
        root_cause=root_cause,
        action_items=action_items,
        remediation=remediation,
    )


def render_markdown(pm: PostMortem) -> str:
    """Render the post-mortem as structured markdown."""
    lines = [
        f"# Post-Mortem: {pm.title}",
        "",
        "**Incident ID:** " + pm.incident_id,
        "**Severity:** " + pm.severity.value,
        "**Generated:** " + pm.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "",
        "---",
        "",
        "## Summary",
        "",
        pm.summary or "_No summary provided._",
        "",
        "---",
        "",
        "## Timeline",
        "",
        "| Timestamp (UTC) | Event | Detail |",
        "|---|---|---|",
    ]
    for entry in pm.timeline:
        ts = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        detail = entry.detail.replace("\n", " ") if entry.detail else ""
        lines.append(f"| {ts} | {entry.event} | {detail} |")

    lines += [
        "",
        "---",
        "",
        "## Impact",
        "",
        pm.impact or "_No impact assessment recorded._",
        "",
        "---",
        "",
        "## Root Cause",
        "",
    ]

    if pm.root_cause:
        rc = pm.root_cause
        lines += [
            "### Hypothesis",
            "",
            rc.hypothesis,
            "",
            f"**Confidence:** {rc.confidence:.0%}",
            "",
            "### Reasoning Steps",
            "",
        ]
        for i, step in enumerate(rc.reasoning_steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")
        if rc.related_incidents:
            lines += ["**Related Incidents:** " + ", ".join(rc.related_incidents), ""]
        if rc.correlations:
            lines += ["### Correlations", "", "| Type | Description | Confidence |", "|---|---|---|"]
            for c in rc.correlations:
                lines.append(
                    f"| {c.kind} | {c.description} | {c.confidence:.0%} |"
                )
            lines.append("")
    else:
        lines.append("_No root cause analysis recorded._\n")

    lines += ["---", "", "## Remediation", ""]
    if pm.remediation and pm.remediation.actions:
        lines += [
            "| Action | Type | Destructive | Status | Rationale |",
            "|---|---|---|---|---|",
        ]
        for a in pm.remediation.actions:
            lines.append(
                f"| {a.id} | {a.type.value} | {'Yes' if a.destructive else 'No'} | "
                f"{a.status.value} | {a.rationale} |"
            )
        lines.append("")
    else:
        lines.append("_No remediation actions proposed._\n")

    lines += ["---", "", "## Action Items", ""]
    if pm.action_items:
        for item in pm.action_items:
            checkbox = "[ ]" if item.status == "open" else "[x]"
            lines.append(f"- {checkbox} **{item.title}** _(Owner: {item.owner}, Priority: {item.priority})_")
    else:
        lines.append("_No action items recorded._")
    lines.append("")

    return "\n".join(lines)


# ── Internal helpers ───────────────────────────────────────────────────────


def _build_timeline(
    incident: Incident, evidence: Evidence, remediation: RemediationPlan
) -> list[TimelineEntry]:
    entries: list[TimelineEntry] = []
    alert = incident.alert

    entries.append(
        TimelineEntry(timestamp=incident.opened_at, event="Incident opened", detail=f"Alert: {alert.title}")
    )
    for dep in evidence.deployments:
        entries.append(
            TimelineEntry(
                timestamp=dep.timestamp,
                event="Deployment",
                detail=f"{dep.version or dep.sha[:7]} by {dep.author} (status: {dep.status})",
            )
        )
    error_logs = [l for l in evidence.logs if l.level.upper() in ("ERROR", "CRITICAL", "FATAL")]
    if error_logs:
        first_err = error_logs[0]
        entries.append(
            TimelineEntry(
                timestamp=first_err.timestamp,
                event="Error burst begins",
                detail=f"{first_err.level} {first_err.message}",
            )
        )
    entries.append(
        TimelineEntry(
            timestamp=alert.timestamp,
            event="Alert fired",
            detail=f"Alert source: {alert.source.value}, severity: {alert.severity.value}",
        )
    )
    for action in remediation.actions:
        if action.approved_at:
            entries.append(
                TimelineEntry(
                    timestamp=action.approved_at,
                    event="Remediation approved",
                    detail=f"Action: {action.type.value} ({action.id})",
                )
            )
        if action.executed_at:
            entries.append(
                TimelineEntry(
                    timestamp=action.executed_at,
                    event="Remediation executed",
                    detail=f"Action: {action.type.value} ({action.id})",
                )
            )
    entries.sort(key=lambda e: e.timestamp)
    return entries


def _build_impact(evidence: Evidence) -> str:
    err_metrics = [m for m in evidence.metrics if "error" in m.name.lower()]
    peak = max((m.value for m in err_metrics), default=0.0)
    error_logs = [l for l in evidence.logs if l.level.upper() in ("ERROR", "CRITICAL", "FATAL")]
    duration = ""
    if error_logs:
        first = error_logs[0].timestamp
        last = error_logs[-1].timestamp
        mins = int((last - first).total_seconds() // 60)
        duration = f"Service degraded for approximately {mins} minutes; "
    return (
        f"Service **{evidence.alert.service}** {duration}"
        f"Peak error rate reached **{peak:.1f}%**. "
        f"{len(error_logs)} error-level log entries were recorded."
    ).strip()


def _build_action_items(root_cause: RootCause, evidence: Evidence) -> list[ActionItem]:
    items: list[ActionItem] = []
    kinds = {c.kind for c in root_cause.correlations}
    has_dependency_signal = any(
        "timeout" in l.message.lower() or "connection reset" in l.message.lower()
        for l in evidence.logs
    )

    if "deployment_overlap" in kinds:
        items.append(
            ActionItem(
                title="Add integration test covering the checkout payment flow",
                owner="backend",
                priority="high",
            )
        )
        items.append(
            ActionItem(
                title="Require canary deployment before full rollout to production",
                owner="platform",
                priority="high",
            )
        )
        items.append(
            ActionItem(
                title="Attach automated rollback to the deploy pipeline",
                owner="platform",
                priority="medium",
            )
        )
    if has_dependency_signal:
        items.append(
            ActionItem(
                title="Add timeout/retry budget to downstream payment gateway calls",
                owner="backend",
                priority="high",
            )
        )
        items.append(
            ActionItem(
                title="Set up dependency health alerts for payment gateway",
                owner="observability",
                priority="medium",
            )
        )
    if "metric_anomaly" in kinds and "deployment_overlap" not in kinds:
        items.append(
            ActionItem(
                title="Review auto-scaling thresholds for the affected service",
                owner="platform",
                priority="medium",
            )
        )
    items.append(
        ActionItem(
            title="Review alert thresholds to reduce noise on lower-severity signals",
            owner="observability",
            priority="low",
        )
    )
    items.append(
        ActionItem(
            title="Update runbook with incident learnings",
            owner="platform",
            priority="low",
        )
    )
    return items