"""
Orchestrator — Ties all three agents together and compiles the final report.
"""

import json
from datetime import datetime


class Orchestrator:
    """Orchestrates the three Clarity agents and produces the final report."""

    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    def compile_report(self, clauses: list, translations: list, risks: list) -> dict:
        """
        Combine outputs from all three agents into a structured report.

        Args:
            clauses: List of extracted clause dicts
            translations: List of translated clause dicts
            risks: List of risk assessment dicts

        Returns:
            dict with full report
        """
        report = {
            "report_title": "Clarity — Document Analysis Report",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "summary": self._generate_summary(clauses, translations, risks),
            "clauses": self._merge_results(clauses, translations, risks),
            "risk_summary": self._risk_summary(risks),
            "questions_to_ask": self._compile_questions(risks),
            "recommendation": self._recommendation(risks),
        }
        return report

    def _merge_results(self, clauses, translations, risks):
        """Merge clause, translation, and risk data into one record per clause."""
        merged = []
        n = max(len(clauses), len(translations), len(risks))
        for i in range(n):
            clause = clauses[i] if i < len(clauses) else {"text": "—", "type": "unknown"}
            trans = translations[i] if i < len(translations) else {"plain_text": "—", "confidence": 0}
            risk = risks[i] if i < len(risks) else {"score": 0, "flags": [], "explanation": ""}
            merged.append({
                "clause_number": i + 1,
                "clause_type": clause.get("type", "unknown"),
                "original_text": clause.get("text", "")[:500],
                "plain_language": trans.get("plain_text", ""),
                "confidence": trans.get("confidence", 0),
                "risk_score": risk.get("score", 0),
                "risk_flags": risk.get("flags", []),
                "risk_explanation": risk.get("explanation", ""),
            })
        return merged

    def _generate_summary(self, clauses, translations, risks):
        """Generate an executive summary."""
        total = len(clauses)
        high_risk = sum(1 for r in risks if r.get("score", 0) >= 0.7)
        medium_risk = sum(1 for r in risks if 0.4 <= r.get("score", 0) < 0.7)

        lines = [
            f"📋 Document contains {total} clause(s) analyzed.",
            f"⚠️  {high_risk} high-risk clause(s) — requires your attention.",
            f"🔶 {medium_risk} medium-risk clause(s) — review recommended.",
            f"✅ {total - high_risk - medium_risk} low-risk clause(s).",
        ]
        return "\n".join(lines)

    def _risk_summary(self, risks):
        """Return a categorized summary of risk types found."""
        categories = {}
        for r in risks:
            for flag in r.get("flags", []):
                categories[flag] = categories.get(flag, 0) + 1
        return dict(sorted(categories.items(), key=lambda x: -x[1]))

    def _compile_questions(self, risks):
        """Generate questions the user should ask before signing."""
        questions = []
        all_flags = set()
        for r in risks:
            all_flags.update(r.get("flags", []))

        flag_questions = {
            "auto_renewal": "Does this contract auto-renew? When and how can I cancel?",
            "binding_arbitration": "Am I giving up my right to sue in court?",
            "unilateral_amendment": "Can the other party change terms without my consent?",
            "hidden_fee": "What are ALL fees including late fees, service charges, and penalties?",
            "non_compete": "Does this restrict what I can do after the agreement ends?",
            "liability_waiver": "Am I waiving liability for negligence or damages?",
            "early_termination_fee": "What is the cost to end this agreement early?",
            "automatic_data_sharing": "Is my personal data being shared with third parties?",
            "indemnification": "Am I required to cover the other party's legal costs?",
            "jurisdiction": "Where would any legal dispute be settled?",
        }

        for flag in sorted(all_flags, key=lambda f: -risks.count(f)):
            if flag in flag_questions:
                questions.append(flag_questions[flag])

        if not questions:
            questions.append("Are there any clauses that change after signing?")

        return questions[:5]  # max 5

    def _recommendation(self, risks):
        """Generate an overall recommendation."""
        high_count = sum(1 for r in risks if r.get("score", 0) >= 0.7)
        if high_count >= 2:
            return "🚩 STRONG CAUTION — Multiple high-risk clauses detected. Consider legal review before signing."
        elif high_count == 1:
            return "⚠️ CAUTION — One high-risk clause detected. Review carefully before signing."
        elif sum(1 for r in risks if 0.4 <= r.get("score", 0) < 0.7) >= 2:
            return "🔶 REVIEW — Several medium-risk clauses. Read the flagged sections carefully."
        else:
            return "✅ LOW RISK — No significant red flags detected. Document appears standard."

    def to_markdown(self, report: dict) -> str:
        """Convert the structured report to a readable Markdown string."""
        lines = [
            f"# {report['report_title']}",
            f"_Generated: {report['generated_at']}_\n",
            "## 📊 Executive Summary",
            report["summary"],
            "",
            "## 🔍 Clause-by-Clause Analysis",
            "",
        ]

        for c in report["clauses"]:
            risk_icon = "🟢"
            if c["risk_score"] >= 0.7:
                risk_icon = "🔴"
            elif c["risk_score"] >= 0.4:
                risk_icon = "🟡"

            lines.extend([
                f"### Clause {c['clause_number']}: {c['clause_type'].replace('_', ' ').title()}",
                f"**Risk:** {risk_icon} {c['risk_score']:.0%} risk",
                "",
                "**Original:**",
                f"> {c['original_text'][:400]}",
                "",
                "**Plain Language:**",
                f"{c['plain_language']}",
                "",
                f"**Flags:** {', '.join(c['risk_flags']) if c['risk_flags'] else 'None'}",
                "",
                f"**Explanation:** {c['risk_explanation']}",
                "",
                "---",
                "",
            ])

        lines.extend([
            "## ⚠️ Risk Flags Found",
        ])
        for flag, count in report.get("risk_summary", {}).items():
            lines.append(f"- **{flag.replace('_', ' ').title()}**: appears in {count} clause(s)")

        lines.extend([
            "",
            "## ❓ Questions to Ask Before Signing",
        ])
        for i, q in enumerate(report.get("questions_to_ask", []), 1):
            lines.append(f"{i}. {q}")

        lines.extend([
            "",
            "## 🏁 Overall Recommendation",
            report.get("recommendation", ""),
        ])

        return "\n".join(lines)
