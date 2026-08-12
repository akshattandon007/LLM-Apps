// ── LLM call helper ──────────────────────────────────────────

interface LLMResponse {
  content: string;
  provider: 'anthropic' | 'openrouter';
}

/**
 * Call the configured LLM (Anthropic or OpenRouter) with the given system
 * prompt and user message. Returns the generated text.
 */
export async function callLLM(
  systemPrompt: string,
  userMessage: string,
): Promise<LLMResponse> {
  // Try Anthropic first
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  if (anthropicKey) {
    return callAnthropic(anthropicKey, systemPrompt, userMessage);
  }

  // Fallback to OpenRouter
  const openrouterKey = process.env.OPENROUTER_API_KEY;
  if (openrouterKey) {
    return callOpenRouter(openrouterKey, systemPrompt, userMessage);
  }

  throw new Error(
    'No LLM API key configured. Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY in .env',
  );
}

async function callAnthropic(
  key: string,
  system: string,
  user: string,
): Promise<LLMResponse> {
  const model = process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-20250514';

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': key,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model,
      max_tokens: 1024,
      system,
      messages: [{ role: 'user', content: user }],
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Anthropic error (${res.status}): ${err}`);
  }

  const json = await res.json();
  const text = json.content?.[0]?.text || '';
  return { content: text, provider: 'anthropic' };
}

async function callOpenRouter(
  key: string,
  system: string,
  user: string,
): Promise<LLMResponse> {
  const model = process.env.OPENROUTER_MODEL || 'anthropic/claude-sonnet-4-20250514';

  const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${key}`,
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model,
      max_tokens: 1024,
      messages: [
        { role: 'system', content: system },
        { role: 'user', content: user },
      ],
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`OpenRouter error (${res.status}): ${err}`);
  }

  const json = await res.json();
  const text = json.choices?.[0]?.message?.content || '';
  return { content: text, provider: 'openrouter' };
}

// ── ElevenLabs helpers ───────────────────────────────────────

/**
 * Create a cloned voice from audio samples.
 * Returns the ElevenLabs voice_id.
 */
export async function createVoice(
  name: string,
  samples: { dataUrl: string; mime: string }[],
): Promise<string> {
  const key = process.env.ELEVENLABS_API_KEY;
  if (!key) throw new Error('ELEVENLABS_API_KEY not set');

  const form = new FormData();
  form.append('name', name);

  // Derive file extension from MIME type
  const ext = (mime: string): string => {
    if (mime.includes('webm')) return 'webm';
    if (mime.includes('mp4') || mime.includes('m4a')) return 'm4a';
    if (mime.includes('wav')) return 'wav';
    if (mime.includes('mp3')) return 'mp3';
    return 'webm';
  };

  samples.forEach((sample, i) => {
    const base64 = sample.dataUrl.split(',')[1];
    if (!base64) return;
    const buf = Buffer.from(base64, 'base64');
    const blob = new Blob([buf], { type: sample.mime });
    form.append('files', blob, `sample-${i}.${ext(sample.mime)}`);
  });

  const res = await fetch('https://api.elevenlabs.io/v1/voices', {
    method: 'POST',
    headers: { 'xi-api-key': key },
    body: form,
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`ElevenLabs voice creation error (${res.status}): ${err}`);
  }

  const json = await res.json();
  return json.voice_id as string;
}

/**
 * Generate speech from text using ElevenLabs TTS.
 * Returns a base64 data URL string.
 */
export async function textToSpeech(
  text: string,
  voiceId: string,
): Promise<{ dataUrl: string; mime: string }> {
  const key = process.env.ELEVENLABS_API_KEY;
  if (!key) throw new Error('ELEVENLABS_API_KEY not set');

  const res = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
    {
      method: 'POST',
      headers: {
        'xi-api-key': key,
        'content-type': 'application/json',
        accept: 'audio/mpeg',
      },
      body: JSON.stringify({
        text,
        model_id: 'eleven_turbo_v2_5',
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75,
          style: 0.2,
        },
      }),
    },
  );

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`ElevenLabs TTS error (${res.status}): ${err}`);
  }

  const arrayBuffer = await res.arrayBuffer();
  const base64 = Buffer.from(arrayBuffer).toString('base64');
  return {
    dataUrl: `data:audio/mpeg;base64,${base64}`,
    mime: 'audio/mpeg',
  };
}

/**
 * Get the fallback premade voice ID (from env or default Rachel).
 */
export function getFallbackVoiceId(): string {
  return process.env.VOICEFAULT || '21m00Tcm4TlvDq8ikWAM';
}