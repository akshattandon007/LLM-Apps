import { useSpring } from '../hooks/useSpring';

/**
 * Animated speech bubble with spring pop-in effect.
 * Used for both regular speech and joke bubbles.
 */
export default function SpeechBubble({ text, isJoke = false, visible = false }) {
  const sScale = useSpring(visible ? 1 : 0, 0.14, 0.6);

  if (sScale < 0.02 || !text) return null;

  const bg    = isJoke ? 'linear-gradient(135deg, #FFF9C4, #FFF59D)' : '#fff';
  const border = isJoke ? '3px solid #FFB300' : '3px solid #90A4AE';
  const tailFill = isJoke ? '#FFF59D' : '#fff';
  const tailStroke = isJoke ? '#FFB300' : '#90A4AE';

  return (
    <div
      style={{
        transform: `scale(${sScale})`,
        transformOrigin: 'bottom left',
        background: bg,
        border,
        borderRadius: '22px',
        padding: '14px 18px',
        maxWidth: '300px',
        fontSize: '14.5px',
        fontFamily: "'Nunito', sans-serif",
        fontWeight: 600,
        color: '#37474F',
        boxShadow: '0 6px 24px rgba(0,0,0,0.12)',
        lineHeight: 1.55,
        position: 'relative',
      }}
    >
      {isJoke && <span style={{ fontSize: '18px', marginRight: '4px' }}>🤣</span>}
      {text}
      {/* Tail pointer */}
      <svg
        style={{ position: 'absolute', bottom: '-14px', left: '24px' }}
        width="24"
        height="16"
        viewBox="0 0 24 16"
      >
        <path d="M0 0 L12 14 L24 0" fill={tailFill} stroke={tailStroke} strokeWidth="3" />
        <path d="M2 0 L12 12 L22 0" fill={tailFill} stroke={tailFill} strokeWidth="2" />
      </svg>
    </div>
  );
}
