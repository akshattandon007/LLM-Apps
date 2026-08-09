#!/usr/bin/env python3
"""Generate a sample meeting transcript for testing Recall.

Produces a 15-utterance meeting transcript about SaaS Q3 pricing decisions
with 4 speakers (Sarah, Mike, Alex, Priya).
"""

from __future__ import annotations

from pathlib import Path

TRANSCRIPT = """[00:00] Sarah: Hello everyone, let's discuss Q3 pricing for our SaaS product. We need to finalize the model by next Friday.
[00:15] Mike: Thanks Sarah. I've been analyzing the competitors and most are moving to usage-based pricing. I think we should follow suit.
[00:30] Alex: I disagree with usage-based. Our customers prefer predictable flat-rate pricing. Usage-based could scare off our enterprise clients.
[00:45] Sarah: Good points both. Priya, what does the data say about customer segments?
[01:00] Priya: We surveyed 200 customers last month. Sixty percent prefer flat-rate, but the high-usage segment strongly favors consumption-based. There's a clear split.
[01:20] Mike: That supports my point — we could offer tiered usage plans and capture both segments.
[01:35] Alex: I'm still concerned about churn risk. If enterprise customers see unpredictable bills, they might leave.
[01:50] Sarah: Let me propose a decision. We go with a hybrid model: flat base tier plus usage-based overage. Alex, can you model the pricing tiers by next Tuesday?
[02:10] Alex: Yes, I can have a draft by Tuesday. I'll look at three tiers: basic, professional, and enterprise.
[02:25] Mike: I'll work on the usage metering requirements. We need to track API calls, storage, and compute.
[02:40] Priya: I'll prepare the customer communication plan and pricing page copy by Thursday.
[02:55] Sarah: Great. Action items: Alex — pricing tiers by Tuesday. Mike — usage metering specs by Wednesday. Priya — customer comms by Thursday.
[03:15] Mike: One more thing — should we grandfather existing customers into the new model?
[03:30] Sarah: Yes, existing customers stay on their current plan for 12 months. That should address Alex's churn concern.
[03:45] Priya: Agreed. I'll include grandfathering in the comms plan. Meeting adjourned."""


def main():
    output_path = Path(__file__).resolve().parent / "data" / "q3_pricing_meeting.txt"
    output_path.write_text(TRANSCRIPT.strip() + "\n")
    print(f"Sample transcript written to {output_path}")


if __name__ == "__main__":
    main()