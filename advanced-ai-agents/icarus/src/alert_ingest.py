"""Alert ingestion — accept and parse alerts from PagerDuty, Prometheus, CloudWatch, or manual.

Module-level ``_client`` singleton (httpx.Client) is injected for tests via ``set_client``.
When no client is configured, ``fetch_alert`` falls back to a simulated alert.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

import httpx

from src.models import Alert, AlertSeverity, AlertSource

_client: httpx.Client | None = None


def set_client(client: httpx.Client | None) -> None:
    """Inject (or clear) the HTTP client used for real-mode fetches."""
    global _client
    _client = client


def get_client() -> httpx.Client | None:
    return _client


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: Any) -> datetime:
    if not value:
        return _utcnow()
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return _utcnow()


def _coerce_severity(value: Any) -> AlertSeverity:
    raw = str(value or "warning").lower()
    for sev in AlertSeverity:
        if sev.value == raw:
            return sev
    return AlertSeverity.warning


# ── Source parsers ─────────────────────────────────────────────────────────


def parse_pagerduty_alert(payload: dict) -> Alert:
    """Parse a PagerDuty v2 webhook payload (or a bare incident dict)."""
    event = payload.get("event", payload)
    incident = event.get("incident", event)
    service = incident.get("service", {}) if isinstance(incident.get("service"), dict) else {}
    svc_name = (
        service.get("name")
        or service.get("summary")
        or incident.get("service_name")
        or "unknown-service"
    )
    sev = incident.get("severity") or (
        "critical" if str(incident.get("urgency", "")).lower() == "high" else "warning"
    )
    return Alert(
        id=str(incident.get("id") or event.get("id") or f"pd-{uuid.uuid4().hex[:8]}"),
        source=AlertSource.pagerduty,
        severity=_coerce_severity(sev),
        title=str(incident.get("title") or event.get("event_type") or "PagerDuty incident"),
        message=str(incident.get("description") or incident.get("title") or ""),
        service=str(svc_name),
        timestamp=_parse_ts(incident.get("created_at") or event.get("occurred_at")),
        metadata=incident,
    )


def parse_prometheus_alert(payload: dict) -> Alert:
    """Parse a Prometheus Alertmanager webhook payload (or a single alert dict)."""
    alerts = payload.get("alerts") or [payload]
    first = alerts[0]
    labels = first.get("labels", {})
    annotations = first.get("annotations", {})
    svc = labels.get("service") or labels.get("namespace") or labels.get("job") or "unknown-service"
    alertname = labels.get("alertname") or "Prometheus alert"
    return Alert(
        id=f"prom-{alertname}-{uuid.uuid4().hex[:6]}",
        source=AlertSource.prometheus,
        severity=_coerce_severity(labels.get("severity", "warning")),
        title=str(alertname),
        message=str(
            annotations.get("description") or annotations.get("summary") or ""
        ),
        service=str(svc),
        timestamp=_parse_ts(first.get("startsAt")),
        metadata={"status": payload.get("status", ""), "alert_count": len(alerts), **labels},
    )


def parse_cloudwatch_alert(payload: dict) -> Alert:
    """Parse an AWS CloudWatch alarm SNS payload."""
    trigger = payload.get("Trigger", {})
    dims = {
        str(d.get("name")): str(d.get("value"))
        for d in trigger.get("Dimensions", [])
        if isinstance(d, dict)
    }
    svc = dims.get("ServiceName") or str(payload.get("AlarmName", "unknown-service"))
    state = str(payload.get("NewStateValue", "ALARM")).upper()
    sev = "critical" if state == "ALARM" else "warning"
    return Alert(
        id=f"cw-{payload.get('AlarmName') or uuid.uuid4().hex[:8]}",
        source=AlertSource.cloudwatch,
        severity=_coerce_severity(sev),
        title=str(payload.get("AlarmName") or "CloudWatch alarm"),
        message=str(payload.get("NewStateReason") or ""),
        service=str(svc),
        timestamp=_utcnow(),
        metadata={
            "state": state,
            "metric": trigger.get("MetricName", ""),
            "namespace": trigger.get("Namespace", ""),
        },
    )


def parse_manual_alert(payload: dict) -> Alert:
    """Parse a plain manual alert dict: {id, severity, title, message, service, timestamp}."""
    return Alert(
        id=str(payload.get("id") or f"man-{uuid.uuid4().hex[:8]}"),
        source=AlertSource.manual,
        severity=_coerce_severity(payload.get("severity", "warning")),
        title=str(payload.get("title") or "Manual alert"),
        message=str(payload.get("message") or ""),
        service=str(payload.get("service") or "unknown-service"),
        timestamp=_parse_ts(payload.get("timestamp")),
        metadata=payload,
    )


PARSERS: dict[AlertSource, Callable[[dict], Alert]] = {
    AlertSource.pagerduty: parse_pagerduty_alert,
    AlertSource.prometheus: parse_prometheus_alert,
    AlertSource.cloudwatch: parse_cloudwatch_alert,
    AlertSource.manual: parse_manual_alert,
}


def parse_alert(source: str | AlertSource, payload: dict) -> Alert:
    """Dispatch a raw payload to the parser for the given source."""
    key = AlertSource(source) if isinstance(source, str) else source
    parser = PARSERS.get(key)
    if parser is None:
        raise ValueError(f"Unsupported alert source: {source}")
    return parser(payload)


# ── Fetching ───────────────────────────────────────────────────────────────


def _observability_base() -> str:
    return os.environ.get("OBSERVABILITY_BASE_URL", "https://observability.example.com").rstrip("/")


def fetch_alert(alert_id: str, source: str | AlertSource = AlertSource.manual) -> Alert:
    """Fetch a historical alert by id.

    Real mode: GET {OBSERVABILITY_BASE_URL}/alerts/{id}?source=... using the
    injected client. Simulated mode (no client): returns a simulated alert so
    the pipeline still works end-to-end without credentials.
    """
    key = AlertSource(source) if isinstance(source, str) else source
    if _client is not None:
        resp = _client.get(f"{_observability_base()}/alerts/{alert_id}", params={"source": key.value})
        resp.raise_for_status()
        return parse_alert(key, resp.json())
    return simulate_alert(service=alert_id, source=key)


# ── Simulated mode ─────────────────────────────────────────────────────────


def simulate_alert_payload(
    source: str | AlertSource = AlertSource.pagerduty,
    service: str = "checkout-service",
    severity: str = "critical",
) -> dict:
    """Build a realistic simulated alert payload in the given source format.

    Story: checkout-service error rate spiked ~25 minutes after deploy v2.3.1.
    """
    key = AlertSource(source) if isinstance(source, str) else source
    title = f"High error rate on {service}"
    message = (
        f"HTTP 5xx rate for {service} exceeded threshold (12.5% vs 1.0% SLO) "
        "for 10 minutes. Payment gateway timeouts observed."
    )
    if key == AlertSource.pagerduty:
        return {
            "event": {
                "id": f"evt-{uuid.uuid4().hex[:8]}",
                "event_type": "incident.triggered",
                "occurred_at": _utcnow().isoformat(),
                "incident": {
                    "id": f"PD-{uuid.uuid4().hex[:8].upper()}",
                    "title": title,
                    "description": message,
                    "urgency": "high",
                    "severity": severity,
                    "service": {"name": service, "summary": service},
                    "created_at": _utcnow().isoformat(),
                },
            }
        }
    if key == AlertSource.prometheus:
        return {
            "status": "firing",
            "alerts": [
                {
                    "labels": {"alertname": "HighErrorRate", "service": service, "severity": severity},
                    "annotations": {"summary": title, "description": message},
                    "startsAt": _utcnow().isoformat(),
                }
            ],
        }
    if key == AlertSource.cloudwatch:
        return {
            "AlarmName": f"{service}-5xx-rate",
            "AlarmDescription": title,
            "NewStateValue": "ALARM",
            "NewStateReason": message,
            "Trigger": {
                "MetricName": "HTTPCode_Target_5XX_Count",
                "Namespace": "AWS/ApplicationELB",
                "Dimensions": [{"name": "ServiceName", "value": service}],
            },
        }
    # manual
    return {
        "id": f"MAN-{uuid.uuid4().hex[:8].upper()}",
        "severity": severity,
        "title": title,
        "message": message,
        "service": service,
        "timestamp": _utcnow().isoformat(),
    }


def simulate_alert(
    source: str | AlertSource = AlertSource.pagerduty,
    service: str = "checkout-service",
    severity: str = "critical",
) -> Alert:
    """Create a simulated Alert (round-trips through the source parser)."""
    return parse_alert(source, simulate_alert_payload(source, service, severity))