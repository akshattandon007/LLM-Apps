/**
 * Classroom whiteboard with typewriter text reveal and chalk tray.
 */
export default function Whiteboard({ text = '', visibleChars = 0, title = '' }) {
  const display = text.substring(0, visibleChars);

  return (
    <div
      style={{
        background: 'linear-gradient(145deg, #FAFAF6 0%, #F0ECE0 100%)',
        border: '10px solid #5D4037',
        borderRadius: '10px',
        padding: '24px 28px',
        minHeight: '300px',
        position: 'relative',
        boxShadow: 'inset 0 2px 15px rgba(0,0,0,0.06), 0 8px 32px rgba(0,0,0,0.2)',
        fontFamily: "'Caveat', cursive",
        fontSize: '17px',
        lineHeight: 1.75,
        color: '#263238',
      }}
    >
      {/* Wood grain top edge */}
      <div
        style={{
          position: 'absolute',
          top: -10, left: -10, right: -10,
          height: '10px',
          background: 'linear-gradient(90deg, #5D4037, #6D4C41, #5D4037, #4E342E, #5D4037)',
          borderRadius: '10px 10px 0 0',
        }}
      />

      {/* Title */}
      {title && (
        <div
          style={{
            fontSize: '20px',
            fontWeight: 'bold',
            color: '#1565C0',
            borderBottom: '2px solid #E0E0E0',
            paddingBottom: '10px',
            marginBottom: '12px',
            textAlign: 'center',
          }}
        >
          📘 {title}
        </div>
      )}

      {/* Typed content */}
      <div style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
        {display}
        {visibleChars < text.length && (
          <span
            style={{
              display: 'inline-block',
              width: '2px',
              height: '18px',
              background: '#263238',
              animation: 'cursorBlink 0.6s infinite',
              verticalAlign: 'middle',
              marginLeft: '1px',
            }}
          />
        )}
      </div>

      {/* Chalk tray */}
      <div
        style={{
          position: 'absolute',
          bottom: '-14px', left: '10%', right: '10%',
          height: '10px',
          background: '#4E342E',
          borderRadius: '0 0 4px 4px',
          boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
        }}
      >
        <div style={{ position: 'absolute', left: '12px', top: '-3px', width: '28px', height: '7px', background: '#F5F5F5', borderRadius: '3px', transform: 'rotate(-4deg)' }} />
        <div style={{ position: 'absolute', left: '50px', top: '-2px', width: '22px', height: '7px', background: '#FFCC80', borderRadius: '3px', transform: 'rotate(2deg)' }} />
        <div style={{ position: 'absolute', right: '20px', top: '-3px', width: '25px', height: '7px', background: '#EF9A9A', borderRadius: '3px', transform: 'rotate(-3deg)' }} />
      </div>
    </div>
  );
}
