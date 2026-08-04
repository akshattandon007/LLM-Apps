import type { NextApiRequest, NextApiResponse } from "next";

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { task, model } = req.body as { task: string; model?: string };
  if (!task?.trim()) {
    return res.status(400).json({ error: "Task is required" });
  }

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: "OPENROUTER_API_KEY not configured" });
  }

  const systemPrompt = `You are a capable AI agent. You have access to the following tools:

1. web_search(query: string) — Search the web for information.
2. read_file(path: string) — Read a file from the local filesystem.
3. write_file(path: string, content: string) — Write content to a file.
4. execute_bash(command: string) — Run a bash command.

When the user gives you a task, break it down into steps. Use tools as needed. After each tool call, reason about the result and decide the next step. When done, provide a clear final answer.`;

  const messages = [
    { role: "system", content: systemPrompt },
    { role: "user", content: task },
  ];

  const tools = [
    {
      type: "function",
      function: {
        name: "web_search",
        description: "Search the web for information",
        parameters: {
          type: "object",
          properties: {
            query: { type: "string", description: "Search query" },
          },
          required: ["query"],
        },
      },
    },
    {
      type: "function",
      function: {
        name: "read_file",
        description: "Read a file from the local filesystem",
        parameters: {
          type: "object",
          properties: {
            path: { type: "string", description: "File path" },
          },
          required: ["path"],
        },
      },
    },
    {
      type: "function",
      function: {
        name: "write_file",
        description: "Write content to a file",
        parameters: {
          type: "object",
          properties: {
            path: { type: "string", description: "File path" },
            content: { type: "string", description: "File content" },
          },
          required: ["path", "content"],
        },
      },
    },
    {
      type: "function",
      function: {
        name: "execute_bash",
        description: "Run a bash command",
        parameters: {
          type: "object",
          properties: {
            command: { type: "string", description: "Bash command" },
          },
          required: ["command"],
        },
      },
    },
  ];

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
        model: model || "openai/gpt-4o-mini",
        messages,
        tools,
        tool_choice: "auto",
        temperature: 0.7,
        max_tokens: 2048,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }

    const data = await response.json();
    const choice = data.choices?.[0];
    const msg = choice?.message;
    const usage = data.usage;

    // Build steps from the response
    const steps = [];
    const now = Date.now();

    if (msg?.content) {
      steps.push({
        id: `step-${now}-0`,
        timestamp: now,
        type: "answer",
        content: msg.content,
      });
    }

    if (msg?.tool_calls?.length) {
      msg.tool_calls.forEach((tc: Record<string, unknown>, i: number) => {
        const fn = (tc.function as Record<string, string>) || {};
        steps.push({
          id: `step-${now}-tc-${i}`,
          timestamp: now,
          type: "tool_call",
          content: `${fn.name}`,
          metadata: {
            name: fn.name,
            arguments: safeParse(fn.arguments),
          },
        });
      });
    }

    return res.status(200).json({
      success: true,
      answer: msg?.content || "",
      toolCalls: msg?.tool_calls || [],
      tokens: usage ? { input: usage.prompt_tokens, output: usage.completion_tokens } : null,
      steps,
      model: data.model,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return res.status(500).json({ error: message });
  }
}

function safeParse(raw: string): Record<string, unknown> {
  try {
    return JSON.parse(raw);
  } catch {
    return { raw };
  }
}