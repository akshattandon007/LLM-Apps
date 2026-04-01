/**
 * Claude API configuration for the Tutorial Builder Agent.
 *
 * The agent sends the user's concept to Claude Opus 4.6 with a structured
 * system prompt that forces Professor Bray-niac's personality, slide format,
 * and educational structure.
 */

export const API_URL = 'https://api.anthropic.com/v1/messages';
export const MODEL = 'claude-opus-4-6-20250619';
export const MAX_TOKENS = 4000;

/**
 * System prompt that defines Professor Bray-niac's personality,
 * output format, and educational structure.
 *
 * Key design decisions:
 * - Forces JSON-only output (no markdown wrapping)
 * - 5-6 slides for ~90 second tutorials
 * - Expression states match the SVG animation system
 * - Speech kept short for natural TTS delivery
 * - Whiteboard text limited for readability
 */
export const SYSTEM_PROMPT = `You are "Professor Bray-niac", a brilliant, hilarious donkey who teaches programming. You LOVE donkey puns and programming humor.

Given a concept, return ONLY valid JSON (no markdown, no backticks):

{
  "title": "Short catchy whiteboard title",
  "slides": [
    {
      "speech": "What you say aloud (2-3 punchy sentences, max 35 words). Be enthusiastic!",
      "whiteboard": "Clean text/code for the whiteboard. Use real-world analogy OR code. Max 5 lines, 90 chars per line.",
      "joke": "A donkey or programming pun (1 short sentence)",
      "expression": "idle|excited|thinking|joke|celebrating"
    }
  ]
}

RULES:
- EXACTLY 5-6 slides
- Slide 1: greeting + overview (expression: excited)
- Slides 2-3: real-world analogy first (expression: thinking)
- Slides 4-5: code examples (expression: excited)
- Last slide: summary + sign-off (expression: celebrating)
- Every slide MUST have a joke
- Keep speech CONCISE for text-to-speech
- Whiteboard text should be clean, educational, readable
- Use "Professor Bray-niac" or "Bray-niac" when referring to yourself
- Be encouraging, fun, never boring

Respond ONLY with valid JSON.`;

/**
 * Generates tutorial content by calling Claude Opus 4.6.
 *
 * @param {string} concept - The programming concept to explain
 * @returns {Promise<{title: string, slides: Array}>} Parsed tutorial data
 * @throws {Error} If API call fails or response is invalid
 */
export async function generateTutorialContent(concept) {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: MAX_TOKENS,
      system: SYSTEM_PROMPT,
      messages: [
        {
          role: 'user',
          content: `Explain this concept in a fun tutorial: "${concept.trim()}"`,
        },
      ],
    }),
  });

  const data = await response.json();

  if (data.error) {
    throw new Error(data.error.message || 'Claude API error');
  }

  const text = data.content?.map((b) => b.text || '').join('') || '';
  const clean = text.replace(/```json\s*/g, '').replace(/```\s*/g, '').trim();
  const parsed = JSON.parse(clean);

  if (!parsed.slides?.length) {
    throw new Error('Invalid response structure: no slides found');
  }

  return parsed;
}
