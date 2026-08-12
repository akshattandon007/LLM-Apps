import { NextApiRequest, NextApiResponse } from 'next';
import { createVoice, getFallbackVoiceId } from '@/lib/api';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { name, samples } = req.body;

  if (!name || !samples || !Array.isArray(samples) || samples.length === 0) {
    return res.status(400).json({ error: 'name and samples[] are required' });
  }

  if (!process.env.ELEVENLABS_API_KEY) {
    // Return the fallback voice ID so the app still works
    return res.status(200).json({
      voiceId: getFallbackVoiceId(),
      warning: 'ELEVENLABS_API_KEY not set — using fallback premade voice',
    });
  }

  try {
    const voiceId = await createVoice(name, samples);
    return res.status(200).json({ voiceId });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Unknown error';
    console.error('Voice creation error:', msg);
    // Fallback to premade voice
    return res.status(200).json({
      voiceId: getFallbackVoiceId(),
      warning: `Voice cloning failed (${msg}) — using fallback premade voice`,
    });
  }
}