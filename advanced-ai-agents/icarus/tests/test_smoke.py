"""Smoke tests for Icarus — Incident Remediation Agent.

Uses FakeAlertIngest, FakeTriage, FakeRCA — no real network. Tests use
setup() pattern with _client injection.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Add project root to path (mirrors the sibling pr-auto-pilot pattern)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.alert_ingest import (
    fetch_alert,
    parse_alert,
    parse_cloudwatch_alert,
    parse_pagerduty_alert,
    parse_prometheus_alert,
    set_client as alert_set_client,
    simulate_alert,
    simulate_alert_payload,
)
from src.models import (
    Alert,
    AlertSeverity,
    AlertSource,
    Evidence,
    Incident,
    LogEntry,
    RemediationActionStatus,
    RemediationActionType,
    RootCause,
)
from src.monitor import find_similar, load_incidents, record_incident
from src.postmortem import draft_postmortem, render_markdown
from src.rca import correlate_events, run_rca, set_client as rca_set_client
from src.remediate import (
    approve_action,
    execute_action,
    propose_remediation,
    set_executor,
)
from src.triage import (
    fetch_deployments,
    fetch_logs,
    fetch_metrics,
    gather_evidence,
    set_client as triage_set_client,
)

from tests.conftest import (
    FakeAlertIngest,
    FakeRCA,
    FakeTriage,
    make_mock_alert,
    make_mock_deployments,
    make_mock_evidence,
    make_mock_logs,
    make_mock_metrics,
    MOCK_ALERT_ID,
    MOCK_ANCHOR,
    MOCK_SERVICE,
)


# ═══════════════════════════════════════════════════════════════════════════
# Alert Ingest
# ═══════════════════════════════════════════════════════════════════════════


class TestAlertIngest:
    def test_parse_pagerduty_alert(self):
        payload = {
            "event": {
                "id": "evt-001",
                "event_type": "incident.triggered",
                "occurred_at": "2026-08-17T14:30:00+00:00",
                "incident": {
                    "id": "PD-ABC123",
                    "title": "High error rate on checkout-service",
                    "description": "5xx rate above threshold",
                    "urgency": "high",
                    "service": {"name": "checkout-service", "summary": "checkout-service"},
                    "created_at": "2026-08-17T14:30:00+00:00",
                },
            }
        }
        alert = parse_pagerduty_alert(payload)
        assert alert.id == "PD-ABC123"
        assert alert.source == AlertSource.pagerduty
        assert alert.severity == AlertSeverity.critical
        assert alert.service == "checkout-service"
        assert "High error rate" in alert.title

    def test_parse_pagerduty_low_urgency(self):
        payload = {
            "event": {
                "incident": {
                    "id": "PD-LOW",
                    "title": "Minor warning",
                    "urgency": "low",
                    "service": {"name": "test"},
                }
            }
        }
        alert = parse_pagerduty_alert(payload)
        assert alert.severity == AlertSeverity.warning

    def test_parse_prometheus_alert(self):
        payload = {
            "status": "firing",
            "alerts": [
                {
                    "labels": {
                        "alertname": "HighErrorRate",
                        "service": "checkout-service",
                        "severity": "critical",
                    },
                    "annotations": {
                        "summary": "High error rate",
                        "description": "Error rate > 5% for 10min",
                    },
                    "startsAt": "2026-08-17T14:30:00+00:00",
                }
            ],
        }
        alert = parse_prometheus_alert(payload)
        assert alert.source == AlertSource.prometheus
        assert alert.service == "checkout-service"
        assert alert.severity == AlertSeverity.critical
        assert alert.title == "HighErrorRate"
        assert alert.metadata.get("alert_count") == 1

    def test_parse_cloudwatch_alert(self):
        payload = {
            "AlarmName": "checkout-5xx-rate",
            "AlarmDescription": "High 5xx rate",
            "NewStateValue": "ALARM",
            "NewStateReason": "Error rate exceeded threshold",
            "Trigger": {
                "MetricName": "HTTPCode_Target_5XX_Count",
                "Namespace": "AWS/ApplicationELB",
                "Dimensions": [{"name": "ServiceName", "value": "checkout-service"}],
            },
        }
        alert = parse_cloudwatch_alert(payload)
        assert alert.source == AlertSource.cloudwatch
        assert alert.service == "checkout-service"
        assert alert.severity == AlertSeverity.critical
        assert "checkout-5xx-rate" in alert.id

    def test_parse_alert_dispatch_unknown(self):
        with pytest.raises((ValueError, KeyError)):
            parse_alert("unknown_source", {})

    def test_parse_alert_manual(self):
        payload = {
            "id": "MAN-001",
            "severity": "critical",
            "title": "Manual alert",
            "message": "Something broke",
            "service": "api",
        }
        alert = parse_alert("manual", payload)
        assert alert.source == AlertSource.manual
        assert alert.service == "api"
        assert alert.severity == AlertSeverity.critical

    def test_simulate_alert_payload_and_parse(self):
        alert = simulate_alert(source="pagerduty", service="payments", severity="warning")
        assert alert.source == AlertSource.pagerduty
        assert alert.service == "payments"
        assert alert.severity == AlertSeverity.warning
        assert "error rate" in alert.title.lower()

    def test_fetch_alert_simulated(self):
        """No client set -> fetch_alert returns a simulated alert."""
        alert = fetch_alert("payments", "manual")
        assert alert.service == "payments"
        assert alert.source == AlertSource.manual

    def test_fetch_alert_real_mode(self, fake_alert_ingest, monkeypatch):
        """Client injected + OBSERVABILITY_API_KEY set -> real HTTP through FakeAlertIngest."""
        monkeypatch.setenv("OBSERVABILITY_API_KEY", "test-key")
        alert = fetch_alert(MOCK_ALERT_ID, "pagerduty")
        assert alert.service == MOCK_SERVICE
        assert len(fake_alert_ingest.requests_made) >= 1


# ═══════════════════════════════════════════════════════════════════════════
# Triage
# ═══════════════════════════════════════════════════════════════════════════


class TestTriage:
    def test_fetch_logs_simulated(self):
        logs = fetch_logs(MOCK_SERVICE)
        assert len(logs) > 0
        # Should include error-level entries
        errors = [l for l in logs if l.level.upper() == "ERROR"]
        assert len(errors) >= 1

    def test_fetch_metrics_simulated(self):
        metrics = fetch_metrics(MOCK_SERVICE)
        assert len(metrics) > 0
        # Should have error_rate above threshold
        errs = [m for m in metrics if m.name == "error_rate"]
        assert len(errs) > 0
        assert max(m.value for m in errs) > 5.0

    def test_fetch_deployments_simulated(self):
        deps = fetch_deployments(MOCK_SERVICE)
        assert len(deps) > 0
        # Should have a recent deploy
        assert any(d.version == "v2.3.1" for d in deps)

    def test_gather_evidence_simulated(self):
        alert = make_mock_alert()
        evidence = gather_evidence(alert)
        assert isinstance(evidence, Evidence)
        assert len(evidence.logs) > 0
        assert len(evidence.metrics) > 0
        assert len(evidence.deployments) > 0
        assert evidence.alert.id == alert.id

    def test_fetch_logs_real_mode(self, fake_triage, monkeypatch):
        monkeypatch.setenv("OBSERVABILITY_API_KEY", "test-key")
        logs = fetch_logs(MOCK_SERVICE)
        assert len(logs) > 0
        assert len(fake_triage.requests_made) >= 1
        assert all(isinstance(l, LogEntry) for l in logs)

    def test_fetch_metrics_real_mode(self, fake_triage, monkeypatch):
        monkeypatch.setenv("OBSERVABILITY_API_KEY", "test-key")
        metrics = fetch_metrics(MOCK_SERVICE)
        assert len(metrics) > 0
        assert len(fake_triage.requests_made) >= 1

    def test_fetch_deployments_real_mode(self, fake_triage, monkeypatch):
        monkeypatch.setenv("OBSERVABILITY_API_KEY", "test-key")
        deps = fetch_deployments(MOCK_SERVICE)
        assert len(deps) > 0
        assert len(fake_triage.requests_made) >= 1


# ═══════════════════════════════════════════════════════════════════════════
# RCA
# ═══════════════════════════════════════════════════════════════════════════


class TestRCA:
    def test_correlate_finds_deployment_overlap(self):
        evidence = make_mock_evidence()
        correlations = correlate_events(evidence)
        kinds = {c.kind for c in correlations}
        assert "deployment_overlap" in kinds

    def test_correlate_finds_log_burst_and_metric(self):
        evidence = make_mock_evidence()
        correlations = correlate_events(evidence)
        kinds = {c.kind for c in correlations}
        assert "log_error_burst" in kinds
        assert "metric_anomaly" in kinds

    def test_correlate_empty_evidence(self):
        alert = make_mock_alert()
        evidence = Evidence(alert=alert)
        correlations = correlate_events(evidence)
        assert len(correlations) == 0

    def test_run_rca_simulated(self):
        alert = make_mock_alert()
        evidence = make_mock_evidence(alert)
        rc = run_rca(alert, evidence)
        assert isinstance(rc, RootCause)
        assert "deployment" in rc.summary.lower() or "regression" in rc.summary.lower()
        assert 0.0 < rc.confidence <= 1.0
        assert len(rc.reasoning_steps) > 0
        assert rc.incident_id == alert.id

    def test_run_rca_simulated_no_correlations_low_confidence(self):
        alert = make_mock_alert()
        evidence = Evidence(alert=alert)  # empty evidence
        rc = run_rca(alert, evidence)
        assert rc.confidence <= 0.5
        assert "clear signal" in rc.hypothesis.lower()

    def test_run_rca_real_mode(self, fake_rca, monkeypatch):
        monkeypatch.setenv("RCA_API_URL", "https://rca.example.com")
        alert = make_mock_alert()
        evidence = make_mock_evidence(alert)
        rc = run_rca(alert, evidence)
        assert rc.incident_id == MOCK_ALERT_ID
        assert len(fake_rca.requests_made) >= 1
        assert rc.confidence == 0.88


# ═══════════════════════════════════════════════════════════════════════════
# Remediation
# ═══════════════════════════════════════════════════════════════════════════


class TestRemediation:
    def test_propose_plan_for_deploy_regression(self):
        alert = make_mock_alert()
        evidence = make_mock_evidence(alert)
        rc = run_rca(alert, evidence)
        plan = propose_remediation(rc, evidence)
        assert len(plan.actions) > 0
        ids = [a.id for a in plan.actions]
        assert "act-rollback" in ids
        assert "act-flag" in ids

    def test_destructive_flags(self):
        alert = make_mock_alert()
        evidence = make_mock_evidence(alert)
        rc = run_rca(alert, evidence)
        plan = propose_remediation(rc, evidence)
        actions = {a.id: a for a in plan.actions}
        assert actions["act-rollback"].destructive is True
        assert actions["act-flag"].destructive is True

    def test_execute_requires_approval(self):
        alert = make_mock_alert()
        evidence = make_mock_evidence(alert)
        rc = run_rca(alert, evidence)
        plan = propose_remediation(rc, evidence)
        with pytest.raises(RuntimeError, match="not approved"):
            execute_action(plan, "act-rollback")

    def test_approve_then_execute(self):
        alert = make_mock_alert()
        evidence = make_mock_evidence(alert)
        rc = run_rca(alert, evidence)
        plan = propose_remediation(rc, evidence)
        approve_action(plan, "act-rollback")
        action = execute_action(plan, "act-rollback")
        assert action.status == RemediationActionStatus.executed
        assert action.executed_at is not None

    def test_approve_updates_plan(self):
        alert = make_mock_alert()
        evidence = make_mock_evidence(alert)
        rc = run_rca(alert, evidence)
        plan = propose_remediation(rc, evidence)
        assert plan.approved is False
        approve_action(plan, "act-rollback")
        assert plan.approved is True

    def test_approve_already_executed_raises(self):
        alert = make_mock_alert()
        evidence = make_mock_evidence(alert)
        rc = run_rca(alert, evidence)
        plan = propose_remediation(rc, evidence)
        approve_action(plan, "act-rollback")
        execute_action(plan, "act-rollback")
        with pytest.raises(ValueError, match="already"):
            approve_action(plan, "act-rollback")


# ═══════════════════════════════════════════════════════════════════════════
# Post-Mortem
# ═══════════════════════════════════════════════════════════════════════════


class TestPostMortem:
    def test_draft_postmortem_fields(self):
        alert = make_mock_alert()
        incident = Incident(id="inc-test", alert=alert, severity=alert.severity)
        evidence = make_mock_evidence(alert)
        rc = run_rca(alert, evidence)
        plan = propose_remediation(rc, evidence)
        pm = draft_postmortem(incident, rc, plan, evidence)
        assert pm.incident_id == "inc-test"
        assert pm.severity == AlertSeverity.critical
        assert len(pm.timeline) > 0
        assert len(pm.action_items) > 0
        assert pm.root_cause is not None

    def test_render_markdown_sections(self):
        alert = make_mock_alert()
        incident = Incident(id="inc-test", alert=alert, severity=alert.severity)
        evidence = make_mock_evidence(alert)
        rc = run_rca(alert, evidence)
        plan = propose_remediation(rc, evidence)
        pm = draft_postmortem(incident, rc, plan, evidence)
        md = render_markdown(pm)
        assert "# Post-Mortem:" in md
        assert "## Summary" in md
        assert "## Timeline" in md
        assert "## Impact" in md
        assert "## Root Cause" in md
        assert "## Action Items" in md

    def test_render_markdown_contains_remediation(self):
        alert = make_mock_alert()
        incident = Incident(id="inc-test", alert=alert, severity=alert.severity)
        evidence = make_mock_evidence(alert)
        rc = run_rca(alert, evidence)
        plan = propose_remediation(rc, evidence)
        pm = draft_postmortem(incident, rc, plan, evidence)
        md = render_markdown(pm)
        assert "act-rollback" in md
        assert "rollback" in md.lower()


# ═══════════════════════════════════════════════════════════════════════════
# Monitor (memory / learning)
# ═══════════════════════════════════════════════════════════════════════════


class TestMonitor:
    def test_record_and_load_roundtrip(self, tmp_path):
        db = tmp_path / "test-incidents.jsonl"
        alert = make_mock_alert()
        incident = Incident(id="inc-roundtrip", alert=alert, severity=alert.severity)
        rc = run_rca(alert, make_mock_evidence(alert))
        pm = draft_postmortem(
            incident, rc, propose_remediation(rc, make_mock_evidence(alert)), make_mock_evidence(alert)
        )
        record_incident(incident, rc, pm, db_path=db)
        records = load_incidents(db_path=db)
        assert len(records) == 1
        assert records[0]["incident"]["id"] == "inc-roundtrip"

    def test_find_similar_by_service(self, tmp_path):
        db = tmp_path / "test-incidents.jsonl"
        # Store an incident with the SAME service but a DIFFERENT severity, so
        # only the service signal can produce a match (would fail if the matcher
        # only looked at severity).
        alert = make_mock_alert(severity="warning")
        incident = Incident(id="inc-sim", alert=alert, severity=alert.severity)
        rc = run_rca(alert, make_mock_evidence(alert))
        pm = draft_postmortem(
            incident, rc, propose_remediation(rc, make_mock_evidence(alert)), make_mock_evidence(alert)
        )
        record_incident(incident, rc, pm, db_path=db)

        query = make_mock_alert(alert_id="NEW", service=MOCK_SERVICE, severity="info")
        similar = find_similar(query, db_path=db)
        assert len(similar) >= 1
        assert similar[0]["incident"]["id"] == "inc-sim"

    def test_find_similar_no_match(self, tmp_path):
        db = tmp_path / "test-incidents.jsonl"
        alert = make_mock_alert()
        incident = Incident(id="inc-other", alert=alert, severity=alert.severity)
        rc = run_rca(alert, make_mock_evidence(alert))
        pm = draft_postmortem(
            incident, rc, propose_remediation(rc, make_mock_evidence(alert)), make_mock_evidence(alert)
        )
        record_incident(incident, rc, pm, db_path=db)

        query = make_mock_alert(alert_id="DIFF", service="unrelated-service", severity="info")
        similar = find_similar(query, db_path=db)
        assert similar == []

    def test_load_incidents_missing_file(self, tmp_path):
        db = tmp_path / "nonexistent.jsonl"
        records = load_incidents(db_path=db)
        assert records == []


# ═══════════════════════════════════════════════════════════════════════════
# End-to-end pipeline
# ═══════════════════════════════════════════════════════════════════════════


class TestPipeline:
    def test_simulate_full_pipeline(self):
        """End-to-end: simulate alert -> triage -> rca -> remediate -> post-mortem.
        No network, no failure."""
        alert = simulate_alert("pagerduty", "api-service", "critical")
        incident = Incident(id=f"inc-{alert.id}", alert=alert, severity=alert.severity)

        evidence = gather_evidence(alert)
        assert len(evidence.logs) > 0

        rc = run_rca(alert, evidence)
        assert isinstance(rc, RootCause)

        plan = propose_remediation(rc, evidence)
        assert len(plan.actions) > 0

        approve_action(plan, plan.actions[0].id)
        execute_action(plan, plan.actions[0].id)
        assert plan.actions[0].status == RemediationActionStatus.executed

        pm = draft_postmortem(incident, rc, plan, evidence)
        md = render_markdown(pm)
        assert len(md) > 200
        assert "api-service" in md

    def test_execute_blocked_without_approval(self):
        """Destructive actions remain unexecuted when skipped."""
        alert = simulate_alert("pagerduty", "api-service", "critical")
        incident = Incident(id=f"inc-{alert.id}", alert=alert, severity=alert.severity)
        evidence = gather_evidence(alert)
        rc = run_rca(alert, evidence)
        plan = propose_remediation(rc, evidence)

        # Skip all actions
        for action in plan.actions:
            if action.destructive:
                action.status = RemediationActionStatus.skipped

        # Trying to execute an unapproved action should raise
        for action in plan.actions:
            if action.status == RemediationActionStatus.skipped:
                with pytest.raises((RuntimeError, ValueError)):
                    execute_action(plan, action.id)

    def test_no_network_in_simulate_mode(self):
        """No fake client set -> no HTTP requests made."""
        from src.alert_ingest import get_client as alert_get
        from src.rca import get_client as rca_get
        from src.triage import get_client as triage_get

        assert alert_get() is None
        assert triage_get() is None
        assert rca_get() is None

    def test_model_roundtrip(self):
        """All core models serialize/deserialize cleanly."""
        alert = make_mock_alert()
        data = alert.model_dump(mode="json")
        restored = Alert.model_validate(data)
        assert restored.id == alert.id
        assert restored.service == alert.service

        evidence = make_mock_evidence()
        data = evidence.model_dump(mode="json")
        restored = Evidence.model_validate(data)
        assert len(restored.logs) == len(evidence.logs)

        rc = RootCause(
            incident_id="test", summary="test", hypothesis="test", confidence=0.5
        )
        data = rc.model_dump(mode="json")
        restored = RootCause.model_validate(data)
        assert restored.incident_id == "test"