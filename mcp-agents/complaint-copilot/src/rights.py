"""Consumer rights database — what users are owed by issue type and country."""

from __future__ import annotations

from src.models import Country, IssueType, StatutoryRight

# ---------------------------------------------------------------------------
# Rights database
# Each issue type + country combination returns what the user is owed and
# the deadline to claim. Simulated in v0.1; could be pulled from live APIs
# in a future version.
# ---------------------------------------------------------------------------

_RIGHTS: dict[tuple[IssueType, Country], StatutoryRight] = {
    # ── Delayed / Cancelled Flight ──────────────────────────────────────
    (IssueType.DELAYED_CANCELLED_FLIGHT, Country.US): StatutoryRight(
        right="Right to compensation for flight delays and cancellations",
        summary=(
            "Under DOT rules, you are entitled to a refund if your flight is "
            "cancelled or significantly changed and you choose not to travel. "
            "For delays over 3 hours on domestic flights, airlines must provide "
            "compensation. There is no fixed cash compensation amount under US "
            "law (unlike EU261), but you are owed a prompt refund to your "
            "original form of payment."
        ),
        deadline="Claim within 2 years of the incident (varies by airline contract).",
        reference="14 CFR Part 259 — DOT Enhanced Protections for Airline Passengers",
        details=(
            "The US Department of Transportation requires airlines to refund "
            "tickets for cancelled or significantly changed flights if the "
            "passenger does not accept alternative arrangements. File a complaint "
            "with the airline first, then escalate to DOT via aviationconsumer.dot.gov."
        ),
    ),
    (IssueType.DELAYED_CANCELLED_FLIGHT, Country.UK): StatutoryRight(
        right="Right to compensation under UK EC261 retention",
        summary=(
            "Under retained EU law (UK EC261), you are entitled to compensation "
            "of £220–£520 per passenger depending on flight distance for delays "
            "over 3 hours, cancellations without 14 days' notice, and denied "
            "boarding. You are also owed care (meals, accommodation, transport)."
        ),
        deadline="Claim within 6 years of the incident.",
        reference="Retained EU Regulation 261/2004 (UK EC261) — CAA guidance",
        details=(
            "File directly with the airline first. If rejected, escalate to the "
            "Civil Aviation Authority (CAA) or use an ADR scheme. The CAA can "
            "enforce but does not award compensation directly for individual claims."
        ),
    ),
    (IssueType.DELAYED_CANCELLED_FLIGHT, Country.EU): StatutoryRight(
        right="Right to compensation under EU Regulation 261/2004",
        summary=(
            "You are entitled to compensation of €250–€600 per passenger depending "
            "on flight distance for delays over 3 hours, cancellations without "
            "14 days' notice, or denied boarding. Airlines must also provide care "
            "(meals, hotel, transport) during delays."
        ),
        deadline="Claim within 2–3 years depending on member state (check local law).",
        reference="EU Regulation 261/2004 — ECC-Net guidance",
        details=(
            "File with the airline. If rejected, contact the National Enforcement "
            "Body (NEB) of the country where the incident occurred, or use ECC-Net "
            "for cross-border assistance."
        ),
    ),
    # ── Defective Product ───────────────────────────────────────────────
    (IssueType.DEFECTIVE_PRODUCT, Country.US): StatutoryRight(
        right="Right to refund, repair, or replacement for defective products",
        summary=(
            "Under the Magnuson-Moss Warranty Act and state consumer protection "
            "laws, you are entitled to repair, replacement, or refund for "
            "defective products covered by an express or implied warranty. "
            "If the product fails after a reasonable number of repair attempts, "
            "you may be entitled to a refund or replacement."
        ),
        deadline="State laws vary (typically 2–6 years from discovery of defect).",
        reference="15 U.S.C. §§ 2301–2312 — Magnuson-Moss Warranty Act",
        details=(
            "Contact the manufacturer or seller first. If they refuse, file a "
            "complaint with the FTC (reportfraud.ftc.gov) or your state Attorney "
            "General's consumer protection office. For safety defects, also report "
            "to the CPSC (saferproducts.gov)."
        ),
    ),
    (IssueType.DEFECTIVE_PRODUCT, Country.UK): StatutoryRight(
        right="Right to reject, repair, or replacement under Consumer Rights Act 2015",
        summary=(
            "Under the Consumer Rights Act 2015, goods must be of satisfactory "
            "quality, fit for purpose, and as described. You have 30 days to "
            "reject and get a full refund. After 30 days but within 6 months, "
            "the seller must repair or replace. If that fails, you can claim a "
            "partial or full refund (up to 6 years)."
        ),
        deadline="Short-term right to reject: 30 days. Full claim: 6 years from purchase.",
        reference="Consumer Rights Act 2015, Parts 1 & 2 — Citizens Advice",
        details=(
            "You must give the seller one opportunity to repair or replace before "
            "claiming a refund (after the 30-day window). Digital content and "
            "services are also covered. Escalate to Citizens Advice consumer "
            "service or Trading Standards."
        ),
    ),
    (IssueType.DEFECTIVE_PRODUCT, Country.EU): StatutoryRight(
        right="Right to remedy for defective goods under EU Consumer Sales Directive",
        summary=(
            "Under EU law, you have 2 years from delivery to claim a free repair "
            "or replacement for defective goods. During the first year (or 2 "
            "years in some member states), the defect is presumed to have existed "
            "at delivery. If repair/replacement fails, you can claim a price "
            "reduction or rescind the contract."
        ),
        deadline="2 years from delivery (presumption reverses after 1 year in some states).",
        reference="EU Directive 2019/771 (Consumer Sales and Guarantees Directive)",
        details=(
            "Contact the seller first. If unresolved, contact the European Consumer "
            "Centre (ECC-Net) in your country for free cross-border assistance. "
            "Each member state has a national enforcement body."
        ),
    ),
    # ── Overcharge / Billing Error ──────────────────────────────────────
    (IssueType.OVERCHARGE_BILLING_ERROR, Country.US): StatutoryRight(
        right="Right to dispute billing errors and unauthorised charges",
        summary=(
            "Under the Fair Credit Billing Act (FCBA) for credit cards and the "
            "Electronic Fund Transfer Act (EFTA) for debit cards, you can dispute "
            "billing errors, unauthorised charges, and charges for goods not "
            "received. The provider must investigate within 30 days and credit "
            "the amount during the investigation."
        ),
        deadline="Dispute must be submitted within 60 days of the statement date.",
        reference="Fair Credit Billing Act (15 U.S.C. § 1666) / EFTA (15 U.S.C. § 1693)",
        details=(
            "Send a written dispute to the billing address for billing inquiries. "
            "For unauthorised card charges, contact the card issuer immediately. "
            "Escalate to the CFPB (cfpb.gov/complaint) if unresolved."
        ),
    ),
    (IssueType.OVERCHARGE_BILLING_ERROR, Country.UK): StatutoryRight(
        right="Right to refund for incorrect charges and unfair billing",
        summary=(
            "Under the Consumer Rights Act 2015 (for services) and Payment "
            "Services Regulations 2017, you are entitled to a refund for "
            "incorrect charges, unauthorised transactions, or services not "
            "provided with reasonable care and skill. Chargeback rights apply "
            "to card payments under the Visa/Mastercard schemes."
        ),
        deadline="Chargeback: 120 days from transaction. Other claims: 6 years.",
        reference="Consumer Rights Act 2015 — Payment Services Regulations 2017",
        details=(
            "Contact the provider first. If they refuse, contact your bank for "
            "a chargeback, or escalate to the Financial Ombudsman Service (for "
            "financial products) or Citizens Advice consumer service."
        ),
    ),
    (IssueType.OVERCHARGE_BILLING_ERROR, Country.EU): StatutoryRight(
        right="Right to refund for unauthorised payments under PSD2",
        summary=(
            "Under the EU Payment Services Directive 2 (PSD2), you are entitled "
            "to an immediate refund for unauthorised payment transactions. The "
            "payment service provider must refund the full amount by the end of "
            "the next business day after you report it."
        ),
        deadline="Report immediately. Refund claims generally within 13 months.",
        reference="EU Directive 2015/2366 (PSD2) — ECC-Net",
        details=(
            "Contact your payment provider immediately. If the transaction was "
            "authorised but the amount was not specified in advance (e.g. card "
            "not present), you also have refund rights. Escalate via ECC-Net."
        ),
    ),
    # ── Poor Service ────────────────────────────────────────────────────
    (IssueType.POOR_SERVICE, Country.US): StatutoryRight(
        right="Right to service provided with reasonable care and skill",
        summary=(
            "Under state consumer protection laws and the FTC Act (Section 5), "
            "services must be provided as advertised and with reasonable care. "
            "If a service is not delivered as promised, you may be entitled to a "
            "refund or damages. Each state has its own unfair trade practices act."
        ),
        deadline="Varies by state (typically 2–4 years from the service date).",
        reference="FTC Act Section 5 (15 U.S.C. § 45) — state UDAP statutes",
        details=(
            "Document what was promised vs delivered. Send a formal demand letter. "
            "Escalate to your state Attorney General's consumer protection office "
            "or the FTC (reportfraud.ftc.gov)."
        ),
    ),
    (IssueType.POOR_SERVICE, Country.UK): StatutoryRight(
        right="Right to reasonable care and skill for services",
        summary=(
            "Under the Consumer Rights Act 2015, services must be performed with "
            "reasonable care and skill, within a reasonable time, and for a "
            "reasonable price (if not agreed in advance). If not, you are entitled "
            "to require repeat performance or a price reduction (up to 100%)."
        ),
        deadline="6 years from the date of service (5 years in Scotland).",
        reference="Consumer Rights Act 2015, Part 1, Chapter 4 — Citizens Advice",
        details=(
            "Give the trader one opportunity to re-perform the service. If they "
            "fail or cannot, claim a price reduction. Escalate to Trading "
            "Standards via Citizens Advice consumer service."
        ),
    ),
    (IssueType.POOR_SERVICE, Country.EU): StatutoryRight(
        right="Right to service conformity under EU law",
        summary=(
            "Under the EU Services Directive and national implementations, "
            "services must be provided in conformity with the contract. You have "
            "the right to have the service brought into conformity, a price "
            "reduction, or contract termination. Remedies depend on member state "
            "implementation."
        ),
        deadline="Varies by member state (typically 2–3 years from service date).",
        reference="EU Directive 2006/123/EC (Services Directive) — ECC-Net",
        details=(
            "Contact the service provider. If unresolved, contact the European "
            "Consumer Centre (ECC-Net) in your country or the national consumer "
            "protection authority."
        ),
    ),
    # ── Landlord / Tenant ───────────────────────────────────────────────
    (IssueType.LANDLORD_TENANT, Country.US): StatutoryRight(
        right="Right to habitable premises and repairs under implied warranty of habitability",
        summary=(
            "Every residential lease in the US includes an implied warranty of "
            "habitability. Your landlord must maintain the property in a safe and "
            "livable condition (heat, water, electricity, structural integrity). "
            "If they fail, you may withhold rent, repair-and-deduct, or sue. "
            "Some states have 'repair and deduct' statutes allowing up to 1 "
            "month's rent or $500."
        ),
        deadline="Varies by state (typically 1–6 years for breach of lease claims).",
        reference="State landlord-tenant laws — HUD guidance on habitability",
        details=(
            "Notify the landlord in writing and give a reasonable time to repair "
            "(typically 14–30 days depending on severity). Check your state's "
            "specific laws. For unsafe conditions, contact local code enforcement "
            "or the health department. Escalate to your state Attorney General or "
            "legal aid."
        ),
    ),
    (IssueType.LANDLORD_TENANT, Country.UK): StatutoryRight(
        right="Right to repairs and decent housing standards",
        summary=(
            "Under the Landlord and Tenant Act 1985, the Housing Act 2004, and "
            "the Homes (Fitness for Human Habitation) Act 2018, your landlord "
            "must keep the property in repair and fit for human habitation. "
            "This covers structural issues, damp, heating, electrical, and "
            "sanitary facilities. If they fail, you can apply for a court order "
            "or claim damages."
        ),
        deadline="6 years from the date the disrepair began (5 years in Scotland).",
        reference="Landlord and Tenant Act 1985 — Homes (Fitness for Human Habitation) Act 2018",
        details=(
            "Report the issue in writing. If no action within a reasonable time, "
            "contact the local council's environmental health department. For "
            "serious hazards, the council can issue an improvement notice. "
            "Escalate to the Property Ombudsman or First-tier Tribunal (Property "
            "Chamber). Shelter provides free advice."
        ),
    ),
    (IssueType.LANDLORD_TENANT, Country.EU): StatutoryRight(
        right="Right to minimum housing standards under national/EU law",
        summary=(
            "EU member states have national housing standards that require "
            "landlords to provide habitable accommodation. Minimum requirements "
            "cover structural safety, heating, sanitation, and electrical safety. "
            "Tenants have the right to request repairs and may claim rent "
            "reduction or damages for disrepair."
        ),
        deadline="Varies by member state (typically 2–5 years).",
        reference="National housing/tenancy laws — ECC-Net housing guidance",
        details=(
            "Notify the landlord in writing. If no action, contact the local "
            "housing authority or tenant union. For cross-border rentals, "
            "contact ECC-Net."
        ),
    ),
    # ── Warranty Claim ──────────────────────────────────────────────────
    (IssueType.WARRANTY_CLAIM, Country.US): StatutoryRight(
        right="Right to warranty service under Magnuson-Moss and state lemon laws",
        summary=(
            "Under the Magnuson-Moss Warranty Act, written warranties must be "
            "clear and full. The warrantor must repair defects within a "
            "reasonable time. State 'lemon laws' (mostly for vehicles) require "
            "replacement or refund after a reasonable number of repair attempts. "
            "Some states also have lemon laws for consumer electronics."
        ),
        deadline="Varies by warranty terms and state law (typically 1–4 years).",
        reference="Magnuson-Moss Warranty Act (15 U.S.C. § 2301) — state lemon laws",
        details=(
            "Review the warranty terms. Send a written demand for repair. If the "
            "warrantor refuses or takes too long, file a complaint with the FTC "
            "or state Attorney General. For vehicles, contact the state DMV or "
            "consumer affairs office for lemon law arbitration."
        ),
    ),
    (IssueType.WARRANTY_CLAIM, Country.UK): StatutoryRight(
        right="Right to repair or replacement under Consumer Rights Act 2015",
        summary=(
            "Under the Consumer Rights Act 2015, goods must last a reasonable "
            "time. If a fault appears within 6 months of purchase, it is "
            "presumed to have existed at delivery. After 6 months but within "
            "6 years, you must prove the defect existed. The seller can offer "
            "a repair or replacement — if both fail, you can claim a refund."
        ),
        deadline="6 years from purchase (5 in Scotland).",
        reference="Consumer Rights Act 2015, Section 23 — Citizens Advice",
        details=(
            "Contact the seller (not the manufacturer for CRA rights). Give them "
            "one opportunity to repair or replace. If they fail or cause "
            "significant inconvenience, you can claim a final right to reject "
            "and get a refund (may be reduced for use)."
        ),
    ),
    (IssueType.WARRANTY_CLAIM, Country.EU): StatutoryRight(
        right="Right to remedy under EU Consumer Sales Directive",
        summary=(
            "Under EU Directive 2019/771, you have 2 years from delivery to "
            "claim a free repair or replacement for non-conforming goods. The "
            "seller must complete the repair or replacement within a reasonable "
            "time and without significant inconvenience. You can also claim a "
            "price reduction or contract termination."
        ),
        deadline="2 years from delivery (some states extend to 3 years).",
        reference="EU Directive 2019/771 — ECC-Net guidance",
        details=(
            "Contact the seller. If the repair or replacement fails or is "
            "impossible, you can demand a price reduction or rescind the contract. "
            "Use ECC-Net for cross-border claims."
        ),
    ),
    # ── Contract Dispute ────────────────────────────────────────────────
    (IssueType.CONTRACT_DISPUTE, Country.US): StatutoryRight(
        right="Right to enforce contract terms and seek damages for breach",
        summary=(
            "Under state contract law (UCC for goods, common law for services), "
            "you are entitled to the benefit of your bargain. If the other party "
            "breaches, you can claim actual damages (to put you in the position "
            "you would have been in) or, in some cases, specific performance. "
            "Unfair contract terms may be void under state UDAP laws."
        ),
        deadline="Varies by state (typically 4–6 years for written contracts, 3 for oral).",
        reference="Uniform Commercial Code Article 2 (goods) — state common law (services)",
        details=(
            "Review the contract terms. Send a formal letter detailing the breach "
            "and your demand. If unresolved, consider mediation, small claims "
            "court (for amounts under $5k–$10k depending on state), or consult "
            "an attorney. Escalate to the state Attorney General if the contract "
            "violates consumer protection laws."
        ),
    ),
    (IssueType.CONTRACT_DISPUTE, Country.UK): StatutoryRight(
        right="Right to enforce contract terms and challenge unfair terms",
        summary=(
            "Under the Consumer Rights Act 2015, unfair contract terms are not "
            "binding on consumers. If a trader breaches the contract, you are "
            "entitled to damages that put you in the position the contract would "
            "have been performed. Unfair terms include terms that create a "
            "significant imbalance between the parties."
        ),
        deadline="6 years from breach (5 in Scotland).",
        reference="Consumer Rights Act 2015, Part 2 — Unfair contract terms",
        details=(
            "Document the breach and your losses. Send a formal letter before "
            "action. Consider mediation (Small Claims Mediation Service) or "
            "Money Claim Online for claims under £10,000. Escalate to Citizens "
            "Advice or Trading Standards."
        ),
    ),
    (IssueType.CONTRACT_DISPUTE, Country.EU): StatutoryRight(
        right="Right to challenge unfair contract terms under EU Directive 93/13",
        summary=(
            "Under the EU Unfair Contract Terms Directive, contract terms that "
            "cause a significant imbalance in consumer contracts are not binding. "
            "You are entitled to damages for breach of contract. Member states "
            "must provide effective remedies."
        ),
        deadline="Varies by member state (typically 3–5 years from breach).",
        reference="EU Directive 93/13/EEC (Unfair Contract Terms) — ECC-Net",
        details=(
            "Document the breach. Send a formal demand letter. For cross-border "
            "disputes under €5,000, use the European Small Claims Procedure. "
            "Contact ECC-Net for guidance on your member state's specific "
            "procedures."
        ),
    ),
}


def get_rights(issue_type: IssueType, country: Country) -> StatutoryRight | None:
    """Look up statutory rights for a given issue type and country."""
    return _RIGHTS.get((issue_type, country))


def list_supported_issues() -> list[tuple[IssueType, Country]]:
    """List all supported issue type + country combinations."""
    return list(_RIGHTS.keys())
