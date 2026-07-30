# Anti-Zapier 🤬

**Managed lightweight automation for solopreneurs who are tired of getting silently screwed by enterprise bloatware.**

> **Automation that tells you when it breaks.** Flat $5/mo. Unlimited workflows. No silent failures. No per-task pricing. No scary enterprise UI that requires a PhD to understand.

---

## The Problem: Zapier Is Holding Your Business Hostage

You know the drill. You build a cute little automation. It works for three weeks. Then one Tuesday at 3 AM, Zapier silently swallows a webhook because "task limit exceeded" or "rate limited" or "Mercury is in retrograde." Your customer doesn't get their welcome email. Your lead doesn't hit the CRM. You find out three weeks later when revenue drops.

**$0/mo for 2,000 tasks.** Then $29.99/mo. Then $73.50/mo. Then "contact sales." Your automation grows; your bill explodes. The workflow that made you $200/month suddenly costs $150/month to run.

And the UI? A flowchart designed by a committee of enterprise architects who've never run a business. You need a flowchart to understand the flowchart.

---

## The Anti-Zapier Promise

| Zapier | Anti-Zapier |
|--------|-------------|
| $0 → $29 → $73 → "Call Sales" | **$5/mo. Flat. Forever.** |
| "2,000 tasks/mo" then 💸 | **Unlimited workflows. Unlimited runs.** |
| Silent failures = lost revenue | **Loud failures = you fix it, you get paid** |
| Flowchart UI from 2012 | **Plain English. "When Stripe webhook hits, create Notion page."** |
| Debugging = prayer | **Logs that tell you exactly what broke and why** |
| "Zap runs" = billing metric | **Runs are free. You pay for the platform, not the traffic.** |

**We don't make money when your automation runs. We make money when you sleep well.**

---

## What This Actually Does

Anti-Zapier is a **thin, opinionated wrapper around n8n's headless API**. You describe what you want in plain English. It generates the n8n workflow JSON, deploys it, monitors it, and screams at you (email, Slack, webhook, carrier pigeon) when something breaks.

```
You: "When a Stripe payment succeeds, create a Notion page in my CRM database,
      tag it 'paid', and send me a Slack DM with the customer email."

Anti-Zapier: *generates n8n JSON → deploys → monitors → "✅ Deployed. 
              Webhook URL: https://anti-zapier.run/webhook/stripe-xyz.
              I'll Slack you if Stripe returns 5xx or Notion returns 401."*
```

**No canvas. No nodes. No "drag the little circle to the other little circle."** You describe the outcome. We handle the plumbing.

---

## Features (The "No BS" Edition)

| Feature | What It Means |
|---------|---------------|
| **Plain English → n8n JSON** | Describe the automation in English. We generate valid n8n workflow JSON. No canvas. No nodes. No tears. |
| **Loud Failure Alerts** | Webhook 5xx? Auth expired? Rate limited? You get a Slack DM / email / webhook / carrier pigeon **immediately**. Silent failures are a bug, not a feature. |
| **Flat $5/mo. Unlimited.** | 10 workflows? 10,000 runs? 500,000 webhook hits? Still $5. We host n8n. You pay for the platform, not the traffic. |
| **Self-hosted n8n, managed** | We run n8n headless on our infra. You get the reliability of managed hosting, the power of n8n's 400+ nodes, zero DevOps. |
| **Plain English → Webhook URL** | Deploy in one message. Get a production HTTPS webhook URL instantly. Test with `curl`. Done. |
| **Audit log that doesn't lie** | Every execution. Every input. Every output. Every error. Searchable. No "task history" pagination hell. |
| **Secret management built-in** | API keys, tokens, webhook secrets — encrypted at rest, injected at runtime. Never in your prompt. Never in logs. |
| **Versioned deployments** | "Revert to v3" is one click. Every deploy is versioned. Rollback is instant. |
| **Webhook replay** | Webhook failed? Replay the payload with one click. Fix the downstream bug. Replay. Move on. |
| **Bring your own n8n (BYON PREMIUM )** | Already self-hosting n8n? Point Anti-Zapier at your instance. Same plain-English deploy. Same alerts. $5/mo still. |

---

## How It Works (The "No Magic" Version)

```mermaid
flowchart LR
    A[You: "When Stripe webhook...\n  create Notion page...\n  Slack me"] --> B[Anti-Zapier API]
    B --> C[LLM → n8n JSON workflow]
    C --> D[Deploy to managed n8n]
    D --> E[HTTPS webhook URL returned]
    E --> F[Stripe hits webhook]
    F --> G[n8n executes workflow]
    G --> H{Success?}
    H -->|Yes| I[✅ Logged. You sleep.]
    H -->|No| J[🚨 ALERT: Slack/Email/Webhook\n     Full payload + error + trace]
    J --> K[You fix. Click "Replay". Done.]
```

**That's it. No canvas. No nodes. No "zaps." Just English → deployed automation → loud alerts when it breaks.**

---

## Tech Stack (No Surprises)

| Layer | Tech | Why |
|-------|------|-----|
| **Orchestration** | **n8n (headless, self-hosted)** | 400+ nodes, battle-tested, open source, no vendor lock-in |
| **API Layer** | **FastAPI (Python)** | Fast, typed, async, easy to extend |
| **LLM → n8n JSON** | **Structured output + JSON Schema validation** | Guaranteed valid n8n workflows. No hallucinated nodes. |
| **Auth / Secrets** | **FastAPI Users + libsodium/sealed-secrets** | Encrypted at rest. Injected at runtime. Never in logs. |
| **Hosting** | **Fly.io / Railway / your VPS** | Cheap, global, trivial to scale. $5/mo covers the infra. |
| **Alerting** | **Pluggable: Slack, Email, Webhook, Discord, PagerDuty** | You pick. We deliver. |
| **Audit Log** | **SQLite → Postgres (when it grows)** | Searchable, exportable, honest. |
| **Frontend (optional)** | **HTMX + Alpine.js** | 0-build. Fast. Works without JS if you're weird. |

**No Kubernetes. No microservices. No Kafka. No Redis (unless you want it).** One container. One DB. One bill.

---

## Getting Started (30 Seconds)

```bash
# 1. Install the CLI
pip install anti-zapier

# 2. Auth (one time)
anti-zapier auth login
# Opens browser → GitHub OAuth → done

# 3. Deploy your first automation
anti-zapier deploy "When Stripe payment succeeds, create Notion page in CRM db, tag 'paid', DM me on Slack"

# Output:
# ✅ Workflow deployed v1
# 🔗 Webhook URL: https://anti-zapier.run/webhook/stripe_abc123
# 📱 Slack alerts enabled for: webhook_5xx, auth_expired, rate_limited
# 💰 This workflow: $0/mo extra. Your plan: $5/mo unlimited.

# 4. Test it
curl -X POST https://anti-zapier.run/webhook/stripe_abc123 \
  -H "Content-Type: application/json" \
  -d '{"type":"payment_intent.succeeded","data":{"object":{"id":"pi_test","customer_email":"customer@example.com"}}}'

# 5. Check Slack. 🎉
```

**That's it. No dashboard required. The CLI is the UI.**

### Prefer a UI? (Weirdo.)

```bash
anti-zapier ui
# Opens http://localhost:8080 — HTMX frontend. Deploys. Logs. Replays. Secrets. Done.
```

---

## Pricing Philosophy: $5/mo. Flat. Forever.

| Plan | Price | Workflows | Runs/Month | Alerts | Support |
|------|-------|-----------|------------|--------|---------|
| **Anti-Zapier** | **$5/mo** | **Unlimited** | **Unlimited** | **Unlimited (Slack, Email, Webhook)** | Discord + Email |

**No tiers. No "tasks." No "zaps." No "operations." No "contact sales."**

$5/mo covers:
- Managed n8n hosting (we run the container, you don't)
- LLM calls for English → n8n JSON (we eat the token cost)
- Alert delivery (Slack, email, webhook — we pay the webhook egress)
- Audit log storage (SQLite → Postgres when you're big)
- Discord support + email support

**We make money when you stay. Not when your automation runs.**

### The "Take That, Zapier" Guarantee

> If your bill ever exceeds $5/mo for any reason other than you explicitly upgrading to a team plan, **we'll refund the difference and apologize personally.**

---

## Why I Built This (The "Origin Story")

I'm a solopreneur. I built a SaaS doing $3k MRR. My "stack" was 12 Zaps.

**Month 1:** Free tier. Happy days.
**Month 3:** Hit 2,000 tasks. $29.99/mo. Okay, cost of doing business.
**Month 6:** 8,000 tasks. $73.50/mo. My automation now costs more than my hosting.
**Month 8:** A Stripe webhook silently fails. "Task limit exceeded." I lose a $500 customer. I find out 3 weeks later.
**Month 9:** I migrate to n8n self-hosted. $5/mo VPS. Zero silent failures. I sleep again.

**But n8n's UI is still a flowchart. And I didn't want to manage a VPS forever.**

So I built Anti-Zapier: the thin layer that lets me *describe* automations in English, deploys them to managed n8n, and screams at me when they break.

**$5/mo. Unlimited. No silent failures. No flowchart PTSD.**

If you're a solopreneur tired of Zapier's pricing ladder and silent failures — this is for you.

If you're an enterprise team needing SOC2, SSO, and a dedicated CSM — **go buy Zapier. Seriously. They're great at that.**

---

## Roadmap (Honest)

| Status | Feature |
|--------|---------|
| ✅ Done | English → n8n JSON (OpenAI structured output + JSON Schema validation) |
| ✅ Done | Deploy to managed n8n, return webhook URL |
| ✅ Done | Slack/Email/Webhook alerts on failure |
| ✅ Done | CLI deploy + test + replay |
| 🚧 In Progress | HTMX dashboard (logs, replay, secrets, versions) |
| 📋 Planned | BYO n8n (point at your self-hosted instance) |
| 📋 Planned | "Explain this failure" — LLM analyzes error + payload + suggests fix |
| 📋 Planned | Workflow templates gallery (community submitted) |
| 📋 Planned | Team plan ($15/mo/seat — still flat, still unlimited) |

---

## Contributing

**PRs welcome. Issues welcome. "This is stupid because X" welcome.**

```bash
git clone https://github.com/yourhandle/anti-zapier
cd anti-zapier
pip install -e ".[dev]"
pre-commit install
pytest
```

**Philosophy:** Small, sharp, no bloat. If a PR adds a dependency that pulls in 50 packages, it better be worth it.

---

## License

**MIT.** Do whatever. Fork it. Sell it. Put it on a VPS and charge your friends $3/mo. I genuinely don't care.

The only request: **if you make money with it, consider not being the next Zapier.**

---

## Links

- **CLI:** `pip install anti-zapier`
- **Dashboard:** `anti-zapier ui` (after auth)
- **Discord:** `discord.gg/anti-zapier` (we're 12 people. 3 are bots. Join us.)
- **Email:** `founder@anti-zapier.dev` (I actually read this)
- **Status:** `status.anti-zapier.dev` (runs on Anti-Zapier. Obviously.)

---

> **Built by a solopreneur who got tired of paying $73/mo for silent failures.**
> 
> **$5/mo. Unlimited. Loud failures. Sleep well.**
> 
> **— @founderhandle**

---

*Anti-Zapier is not affiliated with Zapier, Inc. or n8n.io. "Zapier" is a trademark of Zapier, Inc. n8n is a trademark of n8n.io. This project uses n8n's open-source core under the Sustainable Use License.*