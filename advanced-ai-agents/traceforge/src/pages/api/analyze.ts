import type { NextApiRequest, NextApiResponse } from "next";

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { trace } = req.body as { trace: Record<string, unknown> };
  if (!trace) {
    return res.status(400).json({ error: "Trace data is required" });
  }

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: "OPENROUTER_API_KEY not configured" });
  }

  const traceSummary = JSON.stringify(trace, null, 2);

  const systemPrompt = `You are a skill extraction judge. Analyze the provided execution trace from a successful AI agent run and extract a reusable skill.

Respond with a JSON object containing:
{
  "name": "short-kebab-case-name",
  "description": "One-line description of what this skill does",
  "toolChain": ["tool1", "tool2", "tool3"],
  "decisionLogic": "When to apply this pattern and what conditions must hold",
  "verifierRule": "A safety check or assertion that must pass before using this skill",
  "version": 1
}

Rules:
- name: lowercase, kebab-case, max 40 chars, descriptive
- description: one sentence, clear and actionable
- toolChain: ordered list of tool names used in the proven pattern
- decisionLogic: explain when to use this skill and what inputs/conditions trigger it
- verifierRule: a concrete safety check (e.g., "verify X exists before Y", "assert Z is non-empty")
- version: always start at 1

Only extract skills from traces that show a clear, repeatable pattern. If the trace is too simple or doesn't show a reusable pattern, return {"error": "no pattern found"}.`;

  try {
    const response = await fetch(OPENROUTER_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "TraceForge",
      },
      body: JSON.stringify({
        model: "openai/gpt-4o-mini",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: `Analyze this trace and extract a reusable skill:\n\n${traceSummary}` },
        ],
        response_format: { type: "json_object" },
        temperature: 0.3,
        max_tokens: 1024,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || "{}";

    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(content);
    } catch {
      return res.status(500).json({ error: "Failed to parse skill extraction", raw: content });
    }

    if (parsed.error) {
      return res.status(200).json({ skill: null, reason: parsed.error });
    }

    return res.status(200).json({
      skill: {
        name: parsed.name || "unnamed-skill",
        description: parsed.description || "",
        toolChain: parsed.toolChain || [],
        decisionLogic: parsed.decisionLogic || "",
        verifierRule: parsed.verifierRule || "",
        version: parsed.version || 1,
      },
      model: data.model,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return res.status(500).json({ error: message });
  }
}