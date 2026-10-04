"""
ClaimCounsel — Multi-Agent Insurance Claims Assistant
Main orchestrator that runs the full pipeline: Policy → Documents → Timeline → Letter
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from config import CLAIMS_DIR, OUTPUT_DIR, POLICIES_DIR, DOCUMENTS_DIR
from utils.file_utils import ensure_dirs, write_text_file, write_json_file
from agents.policy_parser import PolicyParserAgent
from agents.document_collector import DocumentCollectorAgent
from agents.timeline_tracker import TimelineTrackerAgent
from agents.letter_drafter import LetterDrafterAgent


class ClaimCounselOrchestrator:
    """
    Orchestrates the four-agent pipeline for insurance claim assistance.

    Pipeline:
    1. PolicyParserAgent — Understand coverage
    2. DocumentCollectorAgent — Gather supporting documents
    3. TimelineTrackerAgent — Know deadlines and milestones
    4. LetterDrafterAgent — Draft necessary correspondence
    """

    def __init__(self):
        ensure_dirs()
        self.policy_parser = PolicyParserAgent()
        self.document_collector = DocumentCollectorAgent()
        self.timeline_tracker = TimelineTrackerAgent()
        self.letter_drafter = LetterDrafterAgent()
        self.results = {}

    def run_full_pipeline(
        self,
        claim_type: str,
        state_code: str,
        incident_date: str,
        incident_description: str,
        policy_filepath: Optional[str] = None,
        documents_dir: Optional[str] = None,
        output_name: Optional[str] = None,
    ) -> Dict:
        """
        Run the full ClaimCounsel pipeline.

        Args:
            claim_type: auto | home | health | life | travel
            state_code: Two-letter US state code
            incident_date: YYYY-MM-DD
            incident_description: What happened
            policy_filepath: Path to insurance policy PDF/text
            documents_dir: Directory with supporting documents
            output_name: Custom name for the output files

        Returns:
            Dict with results from all agents.
        """
        print("=" * 60)
        print("  CLAIMCOUNSEL — Multi-Agent Claims Assistant")
        print(f"  Claim Type: {claim_type.upper()}  |  State: {state_code}")
        print(f"  Incident: {incident_date}")
        print("=" * 60)

        # Agent 1: Policy Parser
        print("\n[Agent 1/4] Policy Parser — Analyzing your policy...")
        policy_data = {}
        if policy_filepath and Path(policy_filepath).exists():
            policy_data = self.policy_parser.parse_policy(policy_filepath)
            if "error" not in policy_data:
                policy_data["plain_english"] = self.policy_parser.summarize_in_plain_english(policy_data)
                print(f"  ✓ Policy parsed: {policy_data.get('insurance_company', 'Unknown')}")
            else:
                print(f"  ⚠ Policy parse issue: {policy_data.get('error')}")
        else:
            print("  ℹ No policy file provided — skipping policy analysis")

        # Agent 2: Document Collector
        print("\n[Agent 2/4] Document Collector — Checking your documents...")
        doc_dir = documents_dir or str(DOCUMENTS_DIR)
        readiness = self.document_collector.assess_readiness(
            claim_type=claim_type,
            documents_dir=doc_dir,
            claim_description=incident_description,
        )
        print(f"  ✓ Readiness: {readiness.get('readiness_score', 'N/A')}")
        if readiness.get("documents_missing"):
            print(f"  ⚠ Missing: {', '.join(readiness['documents_missing'][:3])}")
        checklist = self.document_collector.generate_checklist(claim_type)

        # Agent 3: Timeline Tracker
        print("\n[Agent 3/4] Timeline Tracker — Calculating your deadlines...")
        timeline = self.timeline_tracker.calculate_timeline(
            claim_type=claim_type,
            state_code=state_code,
            incident_date_str=incident_date,
        )
        next_steps = self.timeline_tracker.get_next_steps(timeline)
        print(f"  ✓ Filing deadline: {timeline.get('filing_deadline', 'N/A')}")
        print(f"  ✓ Days remaining: {timeline.get('days_remaining', 'N/A')}")
        if timeline.get("is_overdue"):
            print("  ❗ OVERDUE — seek legal help immediately")
        elif timeline.get("days_remaining", 0) < 30:
            print("  ⚠ URGENT — file within 2 weeks")

        # Agent 4: Letter Drafter
        print("\n[Agent 4/4] Letter Drafter — Drafting your claim letter...")
        letter = self.letter_drafter.draft_initial_claim(
            policy_number=policy_data.get("policy_number", "TBD"),
            insurance_company=policy_data.get("insurance_company", "TBD"),
            claim_type=claim_type,
            incident_date=incident_date,
            incident_description=incident_description,
            estimated_damages="Attached estimate",
        )
        print(f"  ✓ Claim letter drafted ({len(letter)} chars)")

        # Compile results
        self.results = {
            "claim_type": claim_type,
            "state": state_code,
            "incident_date": incident_date,
            "incident_description": incident_description,
            "run_timestamp": datetime.now().isoformat(),
            "policy_analysis": policy_data,
            "document_readiness": readiness,
            "timeline": timeline,
            "next_steps": next_steps,
            "draft_letter": letter,
            "checklist": checklist,
        }

        # Save output
        name = output_name or f"claim_{claim_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_path = Path(OUTPUT_DIR) / name
        output_path.mkdir(parents=True, exist_ok=True)

        # Save structured data
        json_path = output_path / "claim_counsel_report.json"
        write_json_file(str(json_path), self.results)

        # Save plain-text report
        report = self._format_report()
        report_path = output_path / "claim_counsel_report.txt"
        write_text_file(str(report_path), report)

        print(f"\n{'=' * 60}")
        print(f"  ✅ Done! Report saved to: {output_path}")
        print(f"  📄 JSON: {json_path.name}")
        print(f"  📝 Text: {report_path.name}")
        print(f"{'=' * 60}")

        return self.results

    def _format_report(self) -> str:
        """Format the full results as a readable text report."""
        lines = []
        lines.append("=" * 65)
        lines.append("  CLAIMCOUNSEL — CLAIM ASSISTANCE REPORT")
        lines.append("=" * 65)
        lines.append("")

        r = self.results

        lines.append(f"Claim Type:    {r.get('claim_type', 'N/A').upper()}")
        lines.append(f"State:         {r.get('state', 'N/A')}")
        lines.append(f"Incident Date: {r.get('incident_date', 'N/A')}")
        lines.append(f"Description:   {r.get('incident_description', 'N/A')}")
        lines.append(f"Generated:     {r.get('run_timestamp', 'N/A')}")
        lines.append("")

        # Timeline section
        timeline = r.get("timeline", {})
        lines.append("── TIMELINE & DEADLINES ──")
        if "error" not in timeline:
            lines.append(f"  Filing Deadline:  {timeline.get('filing_deadline', 'N/A')}")
            lines.append(f"  Days Remaining:   {timeline.get('days_remaining', 'N/A')}")
            lines.append(f"  Status:           {timeline.get('status', 'N/A')}")
        else:
            lines.append(f"  {timeline.get('error')}")
        lines.append("")

        # Next steps
        lines.append("── NEXT STEPS ──")
        for step in r.get("next_steps", []):
            lines.append(f"  • {step}")
        lines.append("")

        # Readiness
        dr = r.get("document_readiness", {})
        lines.append("── DOCUMENT READINESS ──")
        lines.append(f"  Score: {dr.get('readiness_score', 'N/A')}")
        if dr.get("documents_missing"):
            lines.append("  Missing:")
            for d in dr["documents_missing"][:5]:
                lines.append(f"    ✗ {d}")
        lines.append("")

        # Policy summary
        pa = r.get("policy_analysis", {})
        if pa and "error" not in pa:
            lines.append("── POLICY COVERAGE ──")
            lines.append(f"  Company:    {pa.get('insurance_company', 'N/A')}")
            lines.append(f"  Policy #:   {pa.get('policy_number', 'N/A')}")
            lines.append(f"  Deductible: {pa.get('deductible', 'N/A')}")
            lines.append(f"  Type:       {pa.get('policy_type', 'N/A')}")
            if pa.get("exclusions"):
                lines.append("  Key Exclusions:")
                for ex in pa["exclusions"][:4]:
                    lines.append(f"    • {ex}")
            lines.append("")

        # Draft letter preview
        letter = r.get("draft_letter", "")
        if letter:
            lines.append("── DRAFT CLAIM LETTER (Preview) ──")
            # Show first 10 lines
            letter_lines = letter.split("\n")[:10]
            for l in letter_lines:
                lines.append(f"  {l}")
            lines.append("  ... (full letter in JSON report)")
            lines.append("")

        lines.append("=" * 65)
        lines.append("  Report generated by ClaimCounsel")
        lines.append("=" * 65)

        return "\n".join(lines)


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(
        description="ClaimCounsel — Multi-Agent Insurance Claims Assistant"
    )
    parser.add_argument("--claim-type", default="auto",
                        choices=["auto", "home", "health", "life", "travel"],
                        help="Type of insurance claim")
    parser.add_argument("--state", default="CA",
                        help="Two-letter US state code")
    parser.add_argument("--incident-date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="Incident date (YYYY-MM-DD)")
    parser.add_argument("--description", default="No description provided",
                        help="Description of the incident")
    parser.add_argument("--policy", default=None,
                        help="Path to insurance policy PDF/text file")
    parser.add_argument("--documents", default=None,
                        help="Directory containing supporting documents")
    parser.add_argument("--output", default=None,
                        help="Custom output name")

    args = parser.parse_args()

    orchestrator = ClaimCounselOrchestrator()
    orchestrator.run_full_pipeline(
        claim_type=args.claim_type,
        state_code=args.state,
        incident_date=args.incident_date,
        incident_description=args.description,
        policy_filepath=args.policy,
        documents_dir=args.documents,
        output_name=args.output,
    )


if __name__ == "__main__":
    main()