import { useState, useEffect } from 'react';
import { useSpring } from '../hooks/useSpring';

/**
 * Expression presets for Professor Bray-niac.
 * Each expression maps to spring-animated SVG parameters.
 */
const EXPRESSIONS = {
  idle:        { eyeScale: 1,    pupilY: 0,  browY: 0,  bodySquash: 1,    bodyStretch: 1,    earAngle: 0,   blush: 0   },
  excited:     { eyeScale: 1.3,  pupilY: -2, browY: -6, bodySquash: 0.92, bodyStretch: 1.08, earAngle: -15, blush: 0.6 },
  thinking:    { eyeScale: 0.9,  pupilY: -4, browY: 2,  bodySquash: 1.02, bodyStretch: 0.98, earAngle: 5,   blush: 0   },
  joke:        { eyeScale: 1.15, pupilY: 0,  browY: -4, bodySquash: 0.95, bodyStretch: 1.05, earAngle: -8,  blush: 0.4 },
  celebrating: { eyeScale: 1.4,  pupilY: -3, browY: -8, bodySquash: 0.85, bodyStretch: 1.15, earAngle: -20, blush: 0.8 },
};

/**
 * Professor Bray-niac — Duolingo-inspired animated donkey character.
 *
 * Features:
 * - 5 expression states with spring-animated transitions
 * - Auto-blinking at random intervals
 * - 6 viseme mouth shapes for lip sync
 * - Idle breathing, head bob, ear wiggle, tail sway
 * - Celebration bounce + rotation
 * - Thinking chin-touch pose
 * - Graduation cap with physics-driven tassel
 *
 * @param {Object} props
 * @param {'idle'|'excited'|'thinking'|'joke'|'celebrating'} props.expression
 * @param {boolean} props.isTalking - Whether TTS is currently speaking
 * @param {number}  props.mouthShape - Current viseme index (0-5)
 * @param {number}  props.time - Animation clock (seconds)
 */
export default function DonkeyCharacter({
  expression = 'idle',
  isTalking = false,
  mouthShape = 0,
  time = 0,
}) {
  // ─── Auto-blink ────────────────────────────────────
  const [blinkState, setBlinkState] = useState(0);
  useEffect(() => {
    let timeout;
    const blink = () => {
      setBlinkState(1);
      setTimeout(() => setBlinkState(0), 150);
      timeout = setTimeout(blink, 2000 + Math.random() * 4000);
    };
    timeout = setTimeout(blink, 2000 + Math.random() * 2000);
    return () => clearTimeout(timeout);
  }, []);

  // ─── Spring-animated expression values ─────────────
  const cfg = EXPRESSIONS[expression] || EXPRESSIONS.idle;
  const sEyeScale    = useSpring(cfg.eyeScale, 0.12, 0.65);
  const sBrowY       = useSpring(cfg.browY, 0.1, 0.6);
  const sBodySquash  = useSpring(cfg.bodySquash, 0.08, 0.55);
  const sBodyStretch = useSpring(cfg.bodyStretch, 0.08, 0.55);
  const sEarAngle    = useSpring(cfg.earAngle, 0.06, 0.5);
  const sBlush       = useSpring(cfg.blush, 0.08, 0.6);

  // ─── Idle loops ────────────────────────────────────
  const breathe   = Math.sin(time * 2) * 2;
  const headBob   = Math.sin(time * 1.8) * 1.5;
  const earWiggle = Math.sin(time * 2.5) * 3;

  // ─── Mouth shapes (visemes) ────────────────────────
  const mouths = [
    <ellipse key="m0" cx="0" cy="6" rx="8" ry="2.5" fill="#6B4537" />,
    <g key="m1"><ellipse cx="0" cy="6" rx="9" ry="5" fill="#5A2020" /><ellipse cx="0" cy="4" rx="6" ry="2" fill="#FF8A80" /></g>,
    <g key="m2"><ellipse cx="0" cy="7" rx="11" ry="8" fill="#5A2020" /><ellipse cx="0" cy="4" rx="7" ry="2.5" fill="#FF8A80" /><rect x="-4" y="2" width="8" height="4" rx="2" fill="white" /></g>,
    <g key="m3"><ellipse cx="0" cy="6" rx="13" ry="5" fill="#5A2020" /><ellipse cx="0" cy="4.5" rx="8" ry="2" fill="#FF8A80" /></g>,
    <g key="m4"><ellipse cx="0" cy="7" rx="7" ry="9" fill="#5A2020" /><ellipse cx="0" cy="5" rx="5" ry="2" fill="#FF8A80" /></g>,
    <g key="m5"><path d="M-14 4 Q0 18 14 4" fill="#5A2020" /><path d="M-10 4 Q0 6 10 4" fill="white" /></g>,
  ];

  const currentMouth = isTalking
    ? mouths[Math.max(0, Math.min(5, mouthShape))]
    : expression === 'celebrating'
      ? mouths[5]
      : mouths[0];

  // ─── Pupil tracking ────────────────────────────────
  const pupilX = expression === 'thinking'
    ? 5 + Math.sin(time * 1.2) * 3
    : Math.sin(time * 0.5) * 2;
  const pupilY = cfg.pupilY + (expression === 'thinking' ? -3 + Math.sin(time * 0.8) * 2 : 0);

  // ─── Celebration physics ───────────────────────────
  const celebY   = expression === 'celebrating' ? Math.abs(Math.sin(time * 5)) * -20 : 0;
  const celebRot = expression === 'celebrating' ? Math.sin(time * 4) * 8 : 0;

  const eyeOpenness = blinkState === 1 ? 0.08 : 1;

  return (
    <svg viewBox="-100 -30 200 260" width="220" height="286" style={{ overflow: 'visible' }}>
      <defs>
        <radialGradient id="bodyGrad" cx="45%" cy="40%">
          <stop offset="0%" stopColor="#C4A882" />
          <stop offset="100%" stopColor="#A08060" />
        </radialGradient>
        <radialGradient id="bellyGrad" cx="50%" cy="35%">
          <stop offset="0%" stopColor="#E8D8C4" />
          <stop offset="100%" stopColor="#D4C0A8" />
        </radialGradient>
        <radialGradient id="headGrad" cx="45%" cy="38%">
          <stop offset="0%" stopColor="#C9AD8A" />
          <stop offset="100%" stopColor="#A8906E" />
        </radialGradient>
        <radialGradient id="snoutGrad" cx="50%" cy="40%">
          <stop offset="0%" stopColor="#E0CCAF" />
          <stop offset="100%" stopColor="#CDBDA0" />
        </radialGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="3" stdDeviation="4" floodOpacity="0.2" />
        </filter>
      </defs>

      <g transform={`translate(0, ${celebY}) rotate(${celebRot})`} filter="url(#shadow)">
        {/* ── BODY ── */}
        <g transform={`translate(0, ${breathe}) scale(${sBodySquash}, ${sBodyStretch})`}>
          {/* Tail */}
          <path
            d={`M-35 148 Q${-55 + Math.sin(time * 3) * 10} ${130 + Math.sin(time * 2.5) * 8} ${-50 + Math.sin(time * 3.5) * 8} ${110 + Math.sin(time * 2) * 5}`}
            stroke="#7A6545" strokeWidth="5" fill="none" strokeLinecap="round"
          />
          <ellipse cx={-50 + Math.sin(time * 3.5) * 8} cy={107 + Math.sin(time * 2) * 5} rx="7" ry="9" fill="#5A4835" />

          {/* Legs + Hooves */}
          <rect x="-22" y="175" width="20" height="36" rx="10" fill="#9A8266" />
          <rect x="10" y="175" width="20" height="36" rx="10" fill="#9A8266" />
          <rect x="-24" y="205" width="24" height="12" rx="6" fill="#5A4835" />
          <rect x="8" y="205" width="24" height="12" rx="6" fill="#5A4835" />

          {/* Body */}
          <ellipse cx="0" cy="160" rx="45" ry="38" fill="url(#bodyGrad)" />
          <ellipse cx="0" cy="168" rx="30" ry="24" fill="url(#bellyGrad)" />

          {/* Bow tie */}
          <g transform="translate(0, 120)">
            <polygon points="-14,0 -2,6 -14,12" fill="#E53935" />
            <polygon points="14,0 2,6 14,12" fill="#E53935" />
            <circle cx="0" cy="6" r="4.5" fill="#EF5350" />
            <circle cx="0" cy="6" r="2.5" fill="#FFCDD2" opacity="0.4" />
          </g>
        </g>

        {/* ── NECK ── */}
        <path d={`M-8 ${125 + breathe} Q-5 ${100 + breathe} 0 ${80 + headBob}`} stroke="#B89B70" strokeWidth="32" fill="none" strokeLinecap="round" />

        {/* ── HEAD ── */}
        <g transform={`translate(0, ${headBob})`}>
          {/* Ears */}
          <g transform={`rotate(${sEarAngle + earWiggle - 15}, -30, 30)`}>
            <ellipse cx="-42" cy="2" rx="14" ry="32" fill="#A8906E" />
            <ellipse cx="-42" cy="2" rx="9" ry="25" fill="#E8A898" />
          </g>
          <g transform={`rotate(${-sEarAngle - earWiggle + 15}, 30, 30)`}>
            <ellipse cx="42" cy="2" rx="14" ry="32" fill="#A8906E" />
            <ellipse cx="42" cy="2" rx="9" ry="25" fill="#E8A898" />
          </g>

          {/* Graduation cap */}
          <g transform="translate(0, -20)">
            <rect x="-30" y="-8" width="60" height="8" rx="2" fill="#2C2C2C" />
            <polygon points="-32,-8 32,-8 24,-12 -24,-12" fill="#333" />
            <rect x="-24" y="-12" width="48" height="4" rx="1" fill="#444" />
            <line x1="24" y1="-10" x2={30 + Math.sin(time * 3) * 4} y2={2 + Math.sin(time * 2) * 3} stroke="#FFD54F" strokeWidth="2" />
            <circle cx={30 + Math.sin(time * 3) * 4} cy={4 + Math.sin(time * 2) * 3} r="3" fill="#FFD54F" />
          </g>

          {/* Head + Snout */}
          <ellipse cx="0" cy="45" rx="40" ry="36" fill="url(#headGrad)" />
          <ellipse cx="0" cy="65" rx="26" ry="18" fill="url(#snoutGrad)" />

          {/* Eyes */}
          <g transform={`scale(1, ${eyeOpenness})`}>
            {[-16, 16].map((ex, i) => (
              <g key={i} transform={`translate(${ex}, 38) scale(${sEyeScale})`}>
                <ellipse cx="0" cy="0" rx="13" ry="14" fill="white" stroke="#8B7355" strokeWidth="1.5" />
                <circle cx={pupilX} cy={pupilY} r="8" fill="#3E2723" />
                <circle cx={pupilX - 1} cy={pupilY - 1} r="5" fill="#1A1A1A" />
                <circle cx={pupilX + 3} cy={pupilY - 4} r="3" fill="white" opacity="0.9" />
                <circle cx={pupilX - 2} cy={pupilY + 2} r="1.5" fill="white" opacity="0.5" />
              </g>
            ))}
          </g>

          {/* Blink lines */}
          {blinkState === 1 && (
            <>
              <line x1="-28" y1="38" x2="-4" y2="38" stroke="#8B7355" strokeWidth="2.5" strokeLinecap="round" />
              <line x1="4" y1="38" x2="28" y2="38" stroke="#8B7355" strokeWidth="2.5" strokeLinecap="round" />
            </>
          )}

          {/* Eyebrows */}
          <g transform={`translate(0, ${sBrowY})`}>
            <path d={expression === 'thinking' ? 'M-28 26 Q-16 28 -6 24' : 'M-28 28 Q-16 22 -6 26'} stroke="#6B5840" strokeWidth="3" fill="none" strokeLinecap="round" />
            <path d={expression === 'thinking' ? 'M6 24 Q16 28 28 26' : 'M6 26 Q16 22 28 28'} stroke="#6B5840" strokeWidth="3" fill="none" strokeLinecap="round" />
          </g>

          {/* Blush */}
          {sBlush > 0.05 && (
            <>
              <ellipse cx="-28" cy="52" rx="8" ry="5" fill="#FF8A65" opacity={sBlush * 0.5} />
              <ellipse cx="28" cy="52" rx="8" ry="5" fill="#FF8A65" opacity={sBlush * 0.5} />
            </>
          )}

          {/* Nostrils */}
          <ellipse cx="-8" cy="64" rx="4" ry="3" fill="#8B7355" />
          <ellipse cx="8" cy="64" rx="4" ry="3" fill="#8B7355" />

          {/* Mouth */}
          <g transform="translate(0, 68)">{currentMouth}</g>

          {/* Glasses */}
          <circle cx="-16" cy="38" r="16" fill="none" stroke="#4A3728" strokeWidth="2.5" />
          <circle cx="16" cy="38" r="16" fill="none" stroke="#4A3728" strokeWidth="2.5" />
          <path d="M-1 38 Q0 36 1 38" stroke="#4A3728" strokeWidth="2.5" fill="none" />
          <line x1="-32" y1="37" x2="-40" y2="33" stroke="#4A3728" strokeWidth="2" strokeLinecap="round" />
          <line x1="32" y1="37" x2="40" y2="33" stroke="#4A3728" strokeWidth="2" strokeLinecap="round" />
          <path d="M-22 30 Q-18 28 -14 30" stroke="white" strokeWidth="1.5" fill="none" opacity="0.4" strokeLinecap="round" />
          <path d="M10 30 Q14 28 18 30" stroke="white" strokeWidth="1.5" fill="none" opacity="0.4" strokeLinecap="round" />

          {/* Thinking chin-touch */}
          {expression === 'thinking' && (
            <ellipse cx="20" cy="78" rx="8" ry="7" fill="#A8906E" transform={`rotate(${Math.sin(time * 2) * 3}, 20, 78)`} />
          )}
        </g>
      </g>
    </svg>
  );
}
