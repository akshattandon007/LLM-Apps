"""Root Cause Analysis — LangGraph-style reasoning over evidence.

The RCA engine runs an explicit step graph (gather -> correlate -> hypothesize
-> decide), the same shape a LangGraph state machine would take, without the
framework dependency:

    run_rca(alert, evidence)
      -> correlate_events(evidence)          # structural correlations
      -> _rank_hypotheses(...)               # scored candidate causes
      -> _simulate_rca(...)                  # deterministic reasoning output

Real mode (RCA_API_URL set + client injected): POST the evidence to an
LLM-backed RCA service and parse the RootCause response.
Simulated mode: deterministic correlation + ranking, no network.
"""

from __future__ import annotations

import os

import httpx

from src import monitor
from src.models import Alert, Correlation, Evidence, RootCause

_client: httpx.Client | None = None


def set_client(client: httpx.Client | None) -> None:
    """Inject (or clear) the HTTP client used for real-mode RCA calls."""
    global _client
    _client = client


def get_client() -> httpx.Client | None:
    return _client


# The step graph the engine walks (mirrors a LangGraph DAG).
GRAPH_STEPS = ["gather", "correlate", "hypothesize", "decide"]

DEPLOY_WINDOW_MINUTES = 30
ERROR_METRIC_THRESHOLD = 5.0
ERROR_LOG_MIN_COUNT = 3


def _rca_base() -> str:
    return os.environ.get("RCA_API_URL", "").rstrip("/")


def _rca_enabled() -> bool:
    return bool(_rca_base()) and _client is not None


def run_rca(alert: Alert, evidence: Evidence) -> RootCause:
    """Run the RCA pipeline over the evidence and return a RootCause."""
    if _rca_enabled():
        payload = {
            "alert": alert.model_dump(mode="json"),
            "evidence": evidence.model_dump(mode="json"),
        }
        resp = _client.post(f"{_rca_base()}/rca", json=payload)  # type: ignore[union-attr]
        resp.raise_for_status()
        return RootCause.model_validate(resp.json())
    return _simulate_rca(alert, evidence)


# ── Correlation ────────────────────────────────────────────────────────────


def correlate_events(evidence: Evidence) -> list[Correlation]:
    """Find structural correlations between evidence and the alert window."""
    alert = evidence.alert
    correlations: list[Correlation] = []

    # 1. Deployment overlap: a deploy landed shortly before the alert.
    recent = [
        d
        for d in evidence.deployments
        if d.status == "deployed"
        and (alert.timestamp - _minutes(DEPLOY_WINDOW_MINUTES)) <= d.timestamp <= alert.timestamp
    ]
    if recent:
        d = max(recent, key=lambda x: x.timestamp)
        minutes_before = int((alert.timestamp - d.timestamp).total_seconds() // 60)
        label = f"{d.version or d.sha[:7]}"
        correlations.append(
            Correlation(
                kind="deployment_overlap",
                description=(
                    f"Deployment {label} to {d.service} landed {minutes_before}m before "
                    "the alert fired"
                ),
                confidence=0.9,
                evidence_refs=[f"deploy:{d.sha}"],
            )
        )

    # 2. Error-log burst near the alert.
    error_logs = [l for l in evidence.logs if l.level.upper() in ("ERROR", "CRITICAL", "FATAL")]
    if len(error_logs) >= ERROR_LOG_MIN_COUNT:
        correlations.append(
            Correlation(
                kind="log_error_burst",
                description=f"{len(error_logs)} error-level log entries near the alert time",
                confidence=0.8,
                evidence_refs=[f"log:{l.timestamp.isoformat()}" for l in error_logs[:3]],
            )
        )

    # 3. Metric anomaly: an error/saturation metric above threshold.
    anomaly_metric = next(
        (m for m in evidence.metrics if "error" in m.name.lower() or "saturation" in m.name.lower()),
        None,
    )
    if anomaly_metric is not None and anomaly_metric.value > ERROR_METRIC_THRESHOLD:
        correlations.append(
            Correlation(
                kind="metric_anomaly",
                description=(
                    f"{anomaly_metric.name} at {anomaly_metric.value}{anomaly_metric.unit} "
                    "exceeds anomaly threshold"
                ),
                confidence=0.85,
                evidence_refs=[f"metric:{anomaly_metric.name}"],
            )
        )

    return correlations


def _minutes(n: int):
    from datetime import timedelta

    return timedelta(minutes=n)


# ── Hypothesis ranking ─────────────────────────────────────────────────────


def _rank_hypotheses(
    evidence: Evidence, correlations: list[Correlation]
) -> list[tuple[str, float, str]]:
    """Score candidate root-cause hypotheses from the correlations."""
    kinds = {c.kind for c in correlations}
    dependency_signal = any(
        "timeout" in l.message.lower() or "connection reset" in l.message.lower()
        for l in evidence.logs
    )
    hypotheses: list[tuple[str, float, str]] = []

    if "deployment_overlap" in kinds:
        hypotheses.append(
            (
                "Recent deployment introduced a regression",
                0.9,
                "A deployment landed inside the alert window and error symptoms started "
                "shortly after; rollback is the fastest mitigation.",
            )
        )
    if "metric_anomaly" in kinds and "deployment_overlap" not in kinds:
        hypotheses.append(
            (
                "Load/capacity degradation",
                0.8,
                "Error/saturation metrics are elevated with no matching deployment, "
                "suggesting a capacity or traffic issue.",
            )
        )
    if dependency_signal:
        hypotheses.append(
            (
                "Downstream dependency failure",
                0.7,
                "Logs show timeouts / connection resets pointing at an upstream dependency.",
            )
        )
    if "log_error_burst" in kinds:
        hypotheses.append(
            (
                "Application-level defect",
                0.6,
                "A burst of application errors correlates with the alert window.",
            )
        )
    if not correlations:
        hypotheses.append(
            (
                "No clear signal — possibly transient or a monitoring false positive",
                0.4,
                "No deployment, log, or metric correlation was found for this alert.",
            )
        )
    hypotheses.sort(key=lambda h: h[1], reverse=True)
    return hypotheses[:3]


# ── Simulated reasoning ────────────────────────────────────────────────────


def _simulate_rca(alert: Alert, evidence: Evidence) -> RootCause:
    """Deterministic RCA: correlate, rank, decide. No network."""
    correlations = correlate_events(evidence)
    hypotheses = _rank_hypotheses(evidence, correlations)

    top = hypotheses[0] if hypotheses else ("Unknown cause", 0.1, "Insufficient evidence.")
    hypothesis, score, why = top

    related = monitor.find_similar(alert)
    related_ids = [r.get("incident", {}).get("id", "") for r in related if r.get("incident")]

    steps = [
        f"[gather] Collected {len(evidence.logs)} log entries, "
        f"{len(evidence.metrics)} metric samples, {len(evidence.deployments)} deployments",
        f"[correlate] Found {len(correlations)} correlation(s): "
        + (", ".join(c.kind for c in correlations) if correlations else "none"),
        f"[hypothesize] Ranked {len(hypotheses)} candidate(s); top: {hypothesis} ({score:.2f})",
        f"[decide] Confidence {min(score, 0.95):.2f} — {hypothesis}. {why}",
    ]
    if related_ids:
        steps.append(f"[memory] {len(related_ids)} similar past incident(s) matched this service")

    return RootCause(
        incident_id=alert.id,
        summary=f"{hypothesis} on {alert.service}",
        hypothesis=hypothesis,
        confidence=round(min(max(score, 0.1), 0.95), 2),
        correlations=correlations,
        related_incidents=related_ids,
        reasoning_steps=steps,
    )