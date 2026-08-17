"""Triage — fetch logs, metrics, and deployment history related to an alert.

Real mode (OBSERVABILITY_API_KEY set + client injected): GET the observability
API via the module-level ``_client`` singleton.
Simulated mode (no key/client): deterministic mock evidence derived from the
alert — a recent deploy, an error-log burst, and an error-rate metric spike.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import httpx

from src.models import Alert, Deployment, Evidence, LogEntry, Metric

_client: httpx.Client | None = None


def set_client(client: httpx.Client | None) -> None:
    """Inject (or clear) the HTTP client used for real-mode fetches."""
    global _client
    _client = client


def get_client() -> httpx.Client | None:
    return _client


def _observability_base() -> str:
    return os.environ.get("OBSERVABILITY_BASE_URL", "https://observability.example.com").rstrip("/")


def _observability_enabled() -> bool:
    return bool(os.environ.get("OBSERVABILITY_API_KEY")) and _client is not None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Simulated data (deterministic, anchored to the alert timestamp) ────────


def _simulate_logs(alert: Alert, limit: int = 40) -> list[LogEntry]:
    """Logs: baseline INFO, a deploy line, then a payment-gateway error burst."""
    anchor = alert.timestamp
    logs: list[LogEntry] = []
    for i in range(6):
        logs.append(
            LogEntry(
                timestamp=anchor - timedelta(minutes=32 - i),
                service=alert.service,
                level="INFO",
                message="request processed status=200 path=/health",
            )
        )
    logs.append(
        LogEntry(
            timestamp=anchor - timedelta(minutes=25),
            service=alert.service,
            level="INFO",
            message="deploy v2.3.1 completed (sha 9f3c2a1)",
        )
    )
    for i in range(12):
        ts = anchor - timedelta(minutes=20 - i)
        if i < 6:
            logs.append(
                LogEntry(
                    timestamp=ts,
                    service=alert.service,
                    level="WARNING",
                    message="payment gateway latency 1200ms",
                )
            )
        else:
            logs.append(
                LogEntry(
                    timestamp=ts,
                    service=alert.service,
                    level="ERROR",
                    message="POST /checkout/confirm -> 500: connection reset by peer",
                )
            )
    logs.sort(key=lambda l: l.timestamp)
    return logs[-limit:]


def _simulate_metrics(alert: Alert) -> list[Metric]:
    """Metrics: error_rate spike (~0.3% -> ~12.5%) starting after the deploy, plus latency/CPU."""
    anchor = alert.timestamp
    metrics: list[Metric] = []
    # Minute-by-minute from 30 min ago to now.
    for m in range(30, -1, -1):
        ts = anchor - timedelta(minutes=m)
        if m > 20:  # before the deploy — baseline
            err = 0.3
        elif m > 5:  # spike ramp
            err = 3.0 + (20 - m) * 0.6
        else:  # sustained peak
            err = 12.5
        metrics.append(
            Metric(name="error_rate", service=alert.service, timestamp=ts, value=round(err, 2), unit="%")
        )
        p99 = 180 if m > 20 else 180 + (20 - m) * 45 if m > 5 else 900
        metrics.append(
            Metric(name="p99_latency_ms", service=alert.service, timestamp=ts, value=p99, unit="ms")
        )
        cpu = 42 if m > 20 else min(95, 42 + (20 - m) * 3)
        metrics.append(
            Metric(name="cpu_utilization", service=alert.service, timestamp=ts, value=float(cpu), unit="%")
        )
    return metrics


def _simulate_deployments(alert: Alert) -> list[Deployment]:
    """Deployments: v2.3.1 landed 25 minutes before the alert; previous release a day earlier."""
    anchor = alert.timestamp
    return [
        Deployment(
            sha="9f3c2a1",
            service=alert.service,
            timestamp=anchor - timedelta(minutes=25),
            author="deploy-bot",
            status="deployed",
            version="v2.3.1",
        ),
        Deployment(
            sha="b71e04d",
            service=alert.service,
            timestamp=anchor - timedelta(hours=26),
            author="ci-user",
            status="deployed",
            version="v2.3.0",
        ),
    ]


# ── Public API ─────────────────────────────────────────────────────────────


def fetch_logs(
    service: str,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 50,
) -> list[LogEntry]:
    """Fetch log entries for a service."""
    if _observability_enabled():
        params = {"service": service, "limit": limit}
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()
        resp = _client.get(f"{_observability_base()}/logs", params=params)  # type: ignore[union-attr]
        resp.raise_for_status()
        return [LogEntry.model_validate(item) for item in resp.json()]
    logs = _simulate_logs(Alert(  # anchor simulation on a minimal alert
        id="sim", source="manual", severity="warning", title="", message="", service=service,
        timestamp=until or _utcnow(),
    ))
    return [l for l in logs if (since is None or l.timestamp >= since) and (until is None or l.timestamp <= until)]


def fetch_metrics(
    service: str,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[Metric]:
    """Fetch metric series for a service."""
    if _observability_enabled():
        params = {"service": service}
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()
        resp = _client.get(f"{_observability_base()}/metrics", params=params)  # type: ignore[union-attr]
        resp.raise_for_status()
        return [Metric.model_validate(item) for item in resp.json()]
    metrics = _simulate_metrics(Alert(
        id="sim", source="manual", severity="warning", title="", message="", service=service,
        timestamp=until or _utcnow(),
    ))
    return [m for m in metrics if (since is None or m.timestamp >= since) and (until is None or m.timestamp <= until)]


def fetch_deployments(
    service: str,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[Deployment]:
    """Fetch recent deployments for a service."""
    if _observability_enabled():
        params = {"service": service}
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()
        resp = _client.get(f"{_observability_base()}/deployments", params=params)  # type: ignore[union-attr]
        resp.raise_for_status()
        return [Deployment.model_validate(item) for item in resp.json()]
    deployments = _simulate_deployments(Alert(
        id="sim", source="manual", severity="warning", title="", message="", service=service,
        timestamp=until or _utcnow(),
    ))
    return [d for d in deployments if (since is None or d.timestamp >= since) and (until is None or d.timestamp <= until)]


def gather_evidence(alert: Alert, since: datetime | None = None, until: datetime | None = None) -> Evidence:
    """Collect logs, metrics, and deployments related to the alert."""
    return Evidence(
        alert=alert,
        logs=fetch_logs(alert.service, since=since, until=until),
        metrics=fetch_metrics(alert.service, since=since, until=until),
        deployments=fetch_deployments(alert.service, since=since, until=until),
    )