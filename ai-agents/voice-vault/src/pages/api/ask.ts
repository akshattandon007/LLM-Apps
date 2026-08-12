import { NextApiRequest, NextApiResponse } from 'next';
import { callLLM, textToSpeech, getFallbackVoiceId } from '@/lib/api';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { question, stories, voiceId } = req.body;

  if (!question || !stories || !Array.isArray(stories) || stories.length === 0) {
    return res.status(400).json({
      error: 'question and stories[] are required',
      answerText: '',
    });
  }

  // ── Build the prompt ─────────────────────────────────────
  const storiesList = stories
    .map(
      (s, i) =>
        `[${i + 1}] Caption: "${s.caption || 'Untitled'}" (${s.duration || '?'}s)`,
    )
    .join('\n');

  const systemPrompt = `You are a warm, conversational assistant for VoiceVault, an app that lets people ask questions about a loved one's life and get answers drawn from their recorded stories.

Your job:
1. Read the user's question and the list of story captions (each caption describes a short audio recording the person made).
2. Pick the ONE story caption that best matches the question.
3. Write a warm, natural, first-person response AS IF you are the person who recorded those stories. The answer should:
   - Reference the matched story naturally
   - Be 2-4 sentences, spoken aloud (no markdown, no lists)
   - Sound like a real person reminiscing, not a robot
   - End with a gentle follow-up or invitation to ask another question

If no story caption clearly matches, pick the closest one and acknowledge it gently ("That's a lovely question... let me share what I remember").

Return ONLY a JSON object with these fields:
- matchedIndex: number (1-based index of the matched story, 0 if none)
- answer: string (the spoken response text)`;

  const userMessage = `Question: "${question}"\n\nStories:\n${storiesList}`;

  // ── Call LLM ─────────────────────────────────────────────
  let answerText = '';
  let matchedIndex = 0;

  try {
    const llmResult = await callLLM(systemPrompt, userMessage);
    const raw = llmResult.content.trim();

    // Parse JSON from the response
    const jsonMatch = raw.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      answerText = parsed.answer || raw;
      matchedIndex = typeof parsed.matchedIndex === 'number' ? parsed.matchedIndex : 0;
    } else {
      answerText = raw;
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Unknown error';
    console.error('LLM error:', msg);
    return res.status(502).json({
      error: `Failed to generate response: ${msg}`,
      answerText: 'I couldn\'t find a story to match your question right now.',
    });
  }

  // ── Get matched caption ──────────────────────────────────
  const matchedStory = matchedIndex > 0 && matchedIndex <= stories.length
    ? stories[matchedIndex - 1]
    : null;
  const matchedCaption = matchedStory?.caption || null;

  // ── Generate speech ──────────────────────────────────────
  let audioDataUrl: string | undefined;
  let audioMime: string | undefined;

  // Only attempt TTS if we have a valid answer
  if (answerText && process.env.ELEVENLABS_API_KEY) {
    const vid = voiceId || getFallbackVoiceId();
    try {
      const tts = await textToSpeech(answerText, vid);
      audioDataUrl = tts.dataUrl;
      audioMime = tts.mime;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      console.error('TTS error:', msg);
      // Return text-only response
    }
  }

  return res.status(200).json({
    answerText,
    matchedCaption,
    audioDataUrl,
    audioMime,
    matchedIndex,
  });
}