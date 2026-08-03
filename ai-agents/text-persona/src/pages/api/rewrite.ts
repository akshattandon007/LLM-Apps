import type { NextApiRequest, NextApiResponse } from "next";

type Data = {
  rewritten?: string;
  error?: string;
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<Data>,
) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { message, systemPrompt } = req.body as {
    message?: string;
    systemPrompt?: string;
  };

  if (!message || !message.trim()) {
    return res.status(400).json({ error: "Message is required." });
  }
  if (!systemPrompt || !systemPrompt.trim()) {
    return res.status(400).json({ error: "Persona is required." });
  }

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: "OPENROUTER_API_KEY is not configured." });
  }

  try {
    const response = await fetch(
      "https://openrouter.ai/api/v1/chat/completions",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
          "HTTP-Referer": "https://textpersona.local",
          "X-Title": "TextPersona",
        },
        body: JSON.stringify({
          model: "openai/gpt-4o-mini",
          messages: [
            {
              role: "system",
              content: systemPrompt,
            },
            {
              role: "user",
              content: message,
            },
          ],
          max_tokens: 300,
          temperature: 0.9,
        }),
      },
    );

    if (!response.ok) {
      const errBody = await response.text();
      let errMsg = `OpenRouter returned ${response.status}`;
      try {
        const parsed = JSON.parse(errBody);
        if (parsed.error?.message) errMsg = parsed.error.message;
      } catch {}
      return res.status(502).json({ error: errMsg });
    }

    const data = await response.json();
    const rewritten =
      data.choices?.[0]?.message?.content?.trim() ?? "";

    if (!rewritten) {
      return res.status(502).json({ error: "No response from AI model." });
    }

    return res.status(200).json({ rewritten });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Unknown error calling OpenRouter";
    return res.status(502).json({ error: message });
  }
}
