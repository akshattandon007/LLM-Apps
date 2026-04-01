import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Viseme-style mouth shape sequence.
 * Cycles through different mouth openings to simulate speech animation.
 * Shapes: 0=closed, 1=slight, 2=open(ah), 3=wide(ee), 4=round(oh)
 */
const MOUTH_SEQUENCE = [0, 1, 2, 3, 1, 4, 2, 1, 3, 0, 2, 4, 1, 3, 2, 0];
const MOUTH_CYCLE_MS = 110; // milliseconds per shape change

/**
 * Custom hook for browser Text-to-Speech with animated mouth shapes.
 * Uses Web Speech API (speechSynthesis) for audio output.
 *
 * @returns {{
 *   speak: (text: string) => Promise<void>,
 *   stop: () => void,
 *   isSpeaking: boolean,
 *   mouthShape: number
 * }}
 *
 * @example
 * const { speak, stop, isSpeaking, mouthShape } = useTTS();
 * await speak("Hello, I'm Professor Bray-niac!");
 */
export function useTTS() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [mouthShape, setMouthShape] = useState(0);
  const intervalRef = useRef(null);

  // Preload voices on mount
  useEffect(() => {
    window.speechSynthesis?.getVoices();
  }, []);

  const speak = useCallback((text) => {
    return new Promise((resolve) => {
      if (!window.speechSynthesis) {
        console.warn('SpeechSynthesis API not available in this browser.');
        resolve();
        return;
      }

      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      clearInterval(intervalRef.current);

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.92;
      utterance.pitch = 1.1;

      // Voice selection: prefer specific voices, fallback to any English
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(
        (v) =>
          v.name.includes('Daniel') ||
          v.name.includes('Google UK English Male') ||
          v.name.includes('Samantha')
      );
      const english = voices.find((v) => v.lang.startsWith('en'));
      if (preferred) utterance.voice = preferred;
      else if (english) utterance.voice = english;

      utterance.onstart = () => {
        setIsSpeaking(true);
        let frame = 0;
        intervalRef.current = setInterval(() => {
          frame++;
          setMouthShape(MOUTH_SEQUENCE[frame % MOUTH_SEQUENCE.length]);
        }, MOUTH_CYCLE_MS);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        clearInterval(intervalRef.current);
        setMouthShape(0);
        resolve();
      };

      utterance.onerror = () => {
        setIsSpeaking(false);
        clearInterval(intervalRef.current);
        setMouthShape(0);
        resolve();
      };

      window.speechSynthesis.speak(utterance);
    });
  }, []);

  const stop = useCallback(() => {
    window.speechSynthesis?.cancel();
    clearInterval(intervalRef.current);
    setIsSpeaking(false);
    setMouthShape(0);
  }, []);

  return { speak, stop, isSpeaking, mouthShape };
}
