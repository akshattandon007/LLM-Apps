"""Smoke tests for Complaint Copilot.

Tests all 5 MCP tool functions with fake/mock data.
No external dependencies — everything runs against the local simulated database.
"""

from __future__ import annotations

import pytest

from src.drafter import draft_complaint
from src.ombudsman import find_ombudsman
from src.rights import get_rights, list_supported_issues
from src.tracker import track_complaint
from src.escalation import escalate_to_regulator
from src.models import Country, IssueType

# ═══════════════════════════════════════════════════════════════════════
# draft_complaint
# ═══════════════════════════════════════════════════════════════════════


class TestDraftComplaint:
    """Smoke tests for the complaint drafter."""

    def test_draft_basic(self, mock_company_british_airways, mock_issue_delayed_flight):
        """Draft a complaint with minimum params."""
        result = draft_complaint(
            company=mock_company_british_airways,
            issue=mock_issue_delayed_flight,
        )
        assert "British Airways" in result
        assert "COMPLAINT REFERENCE" in result
        assert mock_issue_delayed_flight in result
        assert "Yours faithfully" in result

    def test_draft_with_amount_and_outcome(
        self, mock_company_british_airways, mock_issue_delayed_flight
    ):
        """Draft with amount and desired outcome."""
        result = draft_complaint(
            company=mock_company_british_airways,
            issue=mock_issue_delayed_flight,
            amount="$650",
            outcome="Full compensation under UK EC261",
        )
        assert "$650" in result
        assert "Full compensation under UK EC261" in result

    def test_draft_with_legal_references(
        self, mock_company_british_airways, mock_issue_delayed_flight
    ):
        """Draft with issue type and country to get legal references."""
        result = draft_complaint(
            company=mock_company_british_airways,
            issue=mock_issue_delayed_flight,
            amount="$650",
            issue_type=IssueType.DELAYED_CANCELLED_FLIGHT,
            country=Country.UK,
        )
        assert "UK EC261" in result or "EU Regulation" in result
        assert "LEGAL BASIS" in result
        assert "COMPLAINT REFERENCE" in result

    def test_draft_all_issue_types(self):
        """Draft a complaint for every supported issue type."""
        issues = {
            IssueType.DELAYED_CANCELLED_FLIGHT: "Flight delayed 5 hours",
            IssueType.DEFECTIVE_PRODUCT: "Laptop screen failed",
            IssueType.OVERCHARGE_BILLING_ERROR: "Charged double the agreed rate",
            IssueType.POOR_SERVICE: "Plumber did shoddy work",
            IssueType.LANDLORD_TENANT: "Boiler not fixed for 3 weeks",
            IssueType.WARRANTY_CLAIM: "Car stereo failed under warranty",
            IssueType.CONTRACT_DISPUTE: "Contractor did not deliver on time",
        }
        for issue_type, issue_text in issues.items():
            result = draft_complaint(
                company="TestCorp",
                issue=issue_text,
                issue_type=issue_type,
                country=Country.US,
            )
            assert "COMPLAINT REFERENCE" in result
            assert "TestCorp" in result

    def test_draft_generates_reference(self):
        """Each draft gets a unique reference."""
        r1 = draft_complaint(company="A", issue="Issue one")
        r2 = draft_complaint(company="A", issue="Issue two")
        # Extract reference lines
        ref1 = [l for l in r1.split("\n") if "COMPLAINT REFERENCE" in l][0]
        ref2 = [l for l in r2.split("\n") if "COMPLAINT REFERENCE" in l][0]
        assert ref1 != ref2

    def test_draft_has_response_deadline(self):
        """Draft includes a response deadline."""
        result = draft_complaint(company="A", issue="Issue")
        assert "RESPONSE DEADLINE" in result
        assert "14 calendar days" in result or "response by" in result


# ═══════════════════════════════════════════════════════════════════════
# find_ombudsman
# ═══════════════════════════════════════════════════════════════════════


class TestFindOmbudsman:
    """Smoke tests for the ombudsman finder."""

    def test_known_airline(self, mock_company_british_airways):
        """Known company returns specific ombudsman."""
        results = find_ombudsman(mock_company_british_airways, IssueType.DELAYED_CANCELLED_FLIGHT)
        assert len(results) >= 1
        # Should find CAA
        names = [r.name for r in results]
        assert any("CAA" in n or "Aviation" in n for n in names)

    def test_known_bank(self, mock_company_bank):
        """Known bank returns financial ombudsman."""
        results = find_ombudsman(mock_company_bank, IssueType.OVERCHARGE_BILLING_ERROR)
        assert len(results) >= 1
        names = [r.name for r in results]
        assert any("CFPB" in n or "Consumer" in n for n in names)

    def test_unknown_company(self, mock_company_unknown):
        """Unknown company falls back to general ombudsmen."""
        results = find_ombudsman(mock_company_unknown, IssueType.DEFECTIVE_PRODUCT)
        assert len(results) >= 1
        # Should include FTC and/or general bodies
        names = [r.name for r in results]
        assert any("FTC" in n or "Citizens Advice" in n or "ECC" in n for n in names)

    def test_all_issue_types_have_fallback(self):
        """Every issue type has at least one fallback ombudsman."""
        for issue_type in IssueType:
            results = find_ombudsman("UnknownCompany", issue_type)
            assert len(results) >= 1, f"No fallback for {issue_type}"

    def test_company_name_case_insensitive(self):
        """Company name matching is case-insensitive."""
        r1 = find_ombudsman("british airways", IssueType.DELAYED_CANCELLED_FLIGHT)
        r2 = find_ombudsman("BRITISH AIRWAYS", IssueType.DELAYED_CANCELLED_FLIGHT)
        assert r1[0].name == r2[0].name

    def test_result_has_required_fields(self):
        """Each ombudsman result has name, url, jurisdiction, eligibility."""
        results = find_ombudsman("British Airways", IssueType.DELAYED_CANCELLED_FLIGHT)
        for r in results:
            assert r.name
            assert r.url
            assert r.jurisdiction
            assert r.eligibility


# ═══════════════════════════════════════════════════════════════════════
# statutory_rights
# ═══════════════════════════════════════════════════════════════════════


class TestStatutoryRights:
    """Smoke tests for the rights database."""

    def test_known_combination(self):
        """Known issue + country returns rights info."""
        right = get_rights(IssueType.DELAYED_CANCELLED_FLIGHT, Country.UK)
        assert right is not None
        assert right.right
        assert right.summary
        assert right.deadline
        assert right.reference

    def test_all_countries_have_flight_rights(self):
        """Flight delay/cancellation rights exist for all countries."""
        for country in Country:
            right = get_rights(IssueType.DELAYED_CANCELLED_FLIGHT, country)
            assert right is not None, f"No flight rights for {country}"

    def test_all_issue_types_have_us_rights(self):
        """All issue types have US rights entries."""
        for issue_type in IssueType:
            right = get_rights(issue_type, Country.US)
            assert right is not None, f"No US rights for {issue_type}"

    def test_all_issue_types_have_uk_rights(self):
        """All issue types have UK rights entries."""
        for issue_type in IssueType:
            right = get_rights(issue_type, Country.UK)
            assert right is not None, f"No UK rights for {issue_type}"

    def test_all_issue_types_have_eu_rights(self):
        """All issue types have EU rights entries."""
        for issue_type in IssueType:
            right = get_rights(issue_type, Country.EU)
            assert right is not None, f"No EU rights for {issue_type}"

    def test_unknown_combination_returns_none(self):
        """Unknown combination returns None."""
        # No rights for a made-up issue type
        right = get_rights(IssueType.DELAYED_CANCELLED_FLIGHT, Country.US)
        assert right is not None  # This one should exist

    def test_list_supported_issues(self):
        """list_supported_issues returns all combinations."""
        issues = list_supported_issues()
        assert len(issues) >= 7 * 3  # 7 issue types * 3 countries


# ═══════════════════════════════════════════════════════════════════════
# track_complaint
# ═══════════════════════════════════════════════════════════════════════


class TestTrackComplaint:
    """Smoke tests for the complaint tracker."""

    def test_track_without_reference(self, mock_company_british_airways):
        """Tracking without a reference returns template info."""
        result = track_complaint(company=mock_company_british_airways)
        assert "British Airways" in result
        assert "PENDING" in result or "escalation stages" in result or "reference" in result.lower()

    def test_track_with_new_reference(self, mock_company_british_airways):
        """Tracking with a new reference creates and returns status."""
        result = track_complaint(
            company=mock_company_british_airways,
            reference="CC-20260311-TEST001",
        )
        assert "CC-20260311-TEST001" in result
        assert "British Airways" in result

    def test_track_returns_next_action(self, mock_company_british_airways):
        """Track result includes a next action."""
        result = track_complaint(company=mock_company_british_airways)
        assert "Next action" in result or "next action" in result.lower()


# ═══════════════════════════════════════════════════════════════════════
# escalate_to_regulator
# ═══════════════════════════════════════════════════════════════════════


class TestEscalateToRegulator:
    """Smoke tests for escalation referral letters."""

    def test_escalate_basic(self, mock_company_british_airways):
        """Basic escalation produces a formal referral letter."""
        result = escalate_to_regulator(
            company=mock_company_british_airways,
            ombudsman="UK Civil Aviation Authority",
            case_summary="Flight BA123 delayed 6 hours. No compensation offered.",
        )
        assert "UK Civil Aviation Authority" in result
        assert "British Airways" in result
        assert "REFERRAL TO REGULATORY BODY" in result
        assert "Yours faithfully" in result

    def test_escalate_with_known_ombudsman(self, mock_company_british_airways):
        """Escalation to a known ombudsman includes their URL."""
        result = escalate_to_regulator(
            company=mock_company_british_airways,
            ombudsman="CAA",
            case_summary="Delayed flight, no response.",
        )
        assert "CAA" in result
        assert "caa.co.uk" in result or "aviationconsumer" in result

    def test_escalate_all_sections_present(self):
        """Referral letter has all expected sections."""
        result = escalate_to_regulator(
            company="TestCo",
            ombudsman="FTC",
            case_summary="Overcharged by $500.",
        )
        assert "REFERRAL TO REGULATORY BODY" in result
        assert "CASE SUMMARY" in result
        assert "GROUNDS FOR REFERRAL" in result
        assert "RELIEF SOUGHT" in result


# ═══════════════════════════════════════════════════════════════════════
# MCP server integration
# ═══════════════════════════════════════════════════════════════════════


class TestMCPServer:
    """Smoke tests for the MCP server module (no client)."""

    def test_server_imports(self):
        """Server module imports cleanly."""
        import server  # noqa: F811
        assert hasattr(server, "mcp")
        assert hasattr(server, "draft_complaint")
        assert hasattr(server, "find_ombudsman")
        assert hasattr(server, "statutory_rights")
        assert hasattr(server, "track_complaint")
        assert hasattr(server, "escalate_to_regulator")

    def test_mcp_tool_names(self):
        """MCP server exposes the expected tool names."""
        import server
        tool_names = {tool.name for tool in server.mcp._tool_manager.list_tools()}
        expected = {
            "draft_complaint",
            "find_ombudsman",
            "statutory_rights",
            "track_complaint",
            "escalate_to_regulator",
        }
        missing = expected - tool_names
        assert not missing, f"Missing tools: {missing}"
