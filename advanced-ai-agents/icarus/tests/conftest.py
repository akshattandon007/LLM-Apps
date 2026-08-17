"""Test fixtures and mock data for Icarus — no real network."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import pytest

from src.alert_ingest import set_client as alert_set_client
from src.models import (
    Alert,
    AlertSeverity,
    AlertSource,
    Deployment,
    Evidence,
    LogEntry,
    Metric,
    RootCause,
)
from src.rca import set_client as rca_set_client
from src.triage import set_client as triage_set_client

# ── Shared constants ────────────────────────────────────────────────────────

MOCK_ALERT_ID = "PD-ABC123"
MOCK_SERVICE = "checkout-service"
MOCK_ANCHOR = datetime(2026, 8, 17, 14, 30, 0, tzinfo=timezone.utc)


# ── Mock data builders ─────────────────────────────────────────────────────


def make_mock_alert(
    alert_id: str = MOCK_ALERT_ID,
    service: str = MOCK_SERVICE,
    severity: str = "critical",
    anchor: datetime = MOCK_ANCHOR,
) -> Alert:
    return Alert(
        id=alert_id,
        source=AlertSource.pagerduty,
        severity=AlertSeverity(severity),
        title=f"High error rate on {service}",
        message="HTTP 5xx rate exceeded threshold",
        service=service,
        timestamp=anchor,
        metadata={"urgency": "high"},
    )


def make_mock_logs(anchor: datetime = MOCK_ANCHOR) -> list[LogEntry]:
    return [
        LogEntry(
            timestamp=anchor - timedelta(minutes=20),
            service=MOCK_SERVICE,
            level="ERROR",
            message="POST /checkout/confirm -> 500: connection reset by peer",
        ),
        LogEntry(
            timestamp=anchor - timedelta(minutes=15),
            service=MOCK_SERVICE,
            level="ERROR",
            message="POST /checkout/confirm -> 500: payment gateway timeout",
        ),
        LogEntry(
            timestamp=anchor - timedelta(minutes=10),
            service=MOCK_SERVICE,
            level="ERROR",
            message="POST /checkout/confirm -> 500: connection reset by peer",
        ),
        LogEntry(
            timestamp=anchor - timedelta(minutes=5),
            service=MOCK_SERVICE,
            level="WARNING",
            message="payment gateway latency 1200ms",
        ),
        LogEntry(
            timestamp=anchor - timedelta(minutes=30),
            service=MOCK_SERVICE,
            level="INFO",
            message="request processed status=200 path=/health",
        ),
    ]


def make_mock_metrics(anchor: datetime = MOCK_ANCHOR) -> list[Metric]:
    return [
        Metric(name="error_rate", service=MOCK_SERVICE, timestamp=anchor, value=12.5, unit="%"),
        Metric(name="error_rate", service=MOCK_SERVICE, timestamp=anchor - timedelta(minutes=15), value=8.0, unit="%"),
        Metric(name="error_rate", service=MOCK_SERVICE, timestamp=anchor - timedelta(minutes=30), value=0.4, unit="%"),
        Metric(name="p99_latency_ms", service=MOCK_SERVICE, timestamp=anchor, value=900.0, unit="ms"),
        Metric(name="cpu_utilization", service=MOCK_SERVICE, timestamp=anchor, value=72.0, unit="%"),
    ]


def make_mock_deployments(anchor: datetime = MOCK_ANCHOR) -> list[Deployment]:
    return [
        Deployment(
            sha="9f3c2a1",
            service=MOCK_SERVICE,
            timestamp=anchor - timedelta(minutes=25),
            author="deploy-bot",
            status="deployed",
            version="v2.3.1",
        ),
        Deployment(
            sha="b71e04d",
            service=MOCK_SERVICE,
            timestamp=anchor - timedelta(hours=26),
            author="ci-user",
            status="deployed",
            version="v2.3.0",
        ),
    ]


def make_mock_evidence(alert: Alert | None = None, anchor: datetime = MOCK_ANCHOR) -> Evidence:
    if alert is None:
        alert = make_mock_alert(anchor=anchor)
    return Evidence(
        alert=alert,
        logs=make_mock_logs(anchor),
        metrics=make_mock_metrics(anchor),
        deployments=make_mock_deployments(anchor),
    )


# ── Fake HTTPX clients (route on URL, no real network) ─────────────────────


class FakeAlertIngest(httpx.Client):
    """Fake client for alert ingestion endpoints."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.requests_made: list[dict] = []

    def send(self, request: httpx.Request, **kwargs: Any) -> httpx.Response:
        self.requests_made.append({"method": request.method, "url": str(request.url)})
        url = str(request.url)
        if "/alerts/" in url:
            # Return a PagerDuty-shaped payload (what parse_pagerduty_alert expects)
            return httpx.Response(
                200,
                json={
                    "event": {
                        "id": MOCK_ALERT_ID,
                        "event_type": "incident.triggered",
                        "occurred_at": MOCK_ANCHOR.isoformat(),
                        "incident": {
                            "id": MOCK_ALERT_ID,
                            "title": f"High error rate on {MOCK_SERVICE}",
                            "description": "HTTP 5xx rate exceeded threshold",
                            "urgency": "high",
                            "severity": "critical",
                            "service": {"name": MOCK_SERVICE, "summary": MOCK_SERVICE},
                            "created_at": MOCK_ANCHOR.isoformat(),
                        },
                    }
                },
                request=request,
            )
        return httpx.Response(404, text="Not found", request=request)


class FakeTriage(httpx.Client):
    """Fake client for observability endpoints (logs/metrics/deployments)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.requests_made: list[dict] = []

    def send(self, request: httpx.Request, **kwargs: Any) -> httpx.Response:
        self.requests_made.append({"method": request.method, "url": str(request.url)})
        url = str(request.url)
        if "/logs" in url:
            data = [l.model_dump(mode="json") for l in make_mock_logs()]
        elif "/metrics" in url:
            data = [m.model_dump(mode="json") for m in make_mock_metrics()]
        elif "/deployments" in url:
            data = [d.model_dump(mode="json") for d in make_mock_deployments()]
        else:
            return httpx.Response(404, text="Not found", request=request)
        return httpx.Response(200, json=data, request=request)


class FakeRCA(httpx.Client):
    """Fake client for an LLM-backed RCA service."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.requests_made: list[dict] = []

    def send(self, request: httpx.Request, **kwargs: Any) -> httpx.Response:
        self.requests_made.append({"method": request.method, "url": str(request.url)})
        url = str(request.url)
        if url.endswith("/rca") or "/rca" in url:
            return httpx.Response(
                200,
                json=RootCause(
                    incident_id=MOCK_ALERT_ID,
                    summary="Recent deployment introduced a regression on checkout-service",
                    hypothesis="Recent deployment introduced a regression",
                    confidence=0.88,
                    correlations=[
                        {"kind": "deployment_overlap", "description": "deploy in window", "confidence": 0.9}
                    ],
                    reasoning_steps=["[gather] mock evidence", "[decide] fake RCA service"],
                ).model_dump(mode="json"),
                request=request,
            )
        return httpx.Response(404, text="Not found", request=request)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_clients(monkeypatch, tmp_path):
    """Reset all module-level singletons and isolate env per test."""
    alert_set_client(None)
    triage_set_client(None)
    rca_set_client(None)
    # Force simulated mode unless a test opts into real mode explicitly.
    monkeypatch.delenv("OBSERVABILITY_API_KEY", raising=False)
    monkeypatch.delenv("RCA_API_URL", raising=False)
    # Isolate the incident database so tests never touch the project data dir.
    monkeypatch.setenv("INCIDENT_DB_PATH", str(tmp_path / "incidents.jsonl"))
    yield
    alert_set_client(None)
    triage_set_client(None)
    rca_set_client(None)


@pytest.fixture
def mock_alert() -> Alert:
    return make_mock_alert()


@pytest.fixture
def mock_evidence() -> Evidence:
    return make_mock_evidence()


@pytest.fixture
def fake_alert_ingest() -> FakeAlertIngest:
    client = FakeAlertIngest()
    alert_set_client(client)
    return client


@pytest.fixture
def fake_triage() -> FakeTriage:
    client = FakeTriage()
    triage_set_client(client)
    return client


@pytest.fixture
def fake_rca() -> FakeRCA:
    client = FakeRCA()
    rca_set_client(client)
    return client