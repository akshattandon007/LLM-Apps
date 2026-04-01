import { useState, useEffect, useRef, useCallback } from 'react';
import DonkeyCharacter from './components/DonkeyCharacter';
import SpeechBubble from './components/SpeechBubble';
import Whiteboard from './components/Whiteboard';
import { useTTS } from './hooks/useTTS';
import { generateTutorialContent } from './config/prompt';

const LOADING_MESSAGES = [
  '🎓 Adjusting graduation cap...',
  '✏️ Finding the best chalk...',
  '🐴 Clearing throat... HEE-HAW!',
  '🤔 Thinking of perfect puns...',
  '📚 Opening the textbook...',
  '🎭 Practising expressions...',
];

const EXAMPLE_TOPICS = [
  'What is a class in Python?',
  'Explain recursion',
  'What are decorators?',
  'How do APIs work?',
  'What is a dictionary?',
];

export default function App() {
  // ─── State ─────────────────────────────────────────
  const [concept, setConcept] = useState('');
  const [slides, setSlides] = useState(null);
  const [title, setTitle] = useState('');
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [visibleChars, setVisibleChars] = useState(0);
  const [showSpeech, setShowSpeech] = useState(false);
  const [showJoke, setShowJoke] = useState(false);
  const [expression, setExpression] = useState('idle');
  const [time, setTime] = useState(0);
  const [loadIdx, setLoadIdx] = useState(0);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [wordCount, setWordCount] = useState(0);

  const { speak, stop: stopTTS, isSpeaking, mouthShape } = useTTS();
  const cancelRef = useRef(false);

  // ─── Animation clock ───────────────────────────────
  useEffect(() => {
    let raf;
    const tick = () => {
      setTime((t) => t + 0.016);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  // ─── Word count ────────────────────────────────────
  useEffect(() => {
    setWordCount(concept.trim() ? concept.trim().split(/\s+/).length : 0);
  }, [concept]);

  // ─── Loading cycler ────────────────────────────────
  useEffect(() => {
    if (!isLoading) return;
    const iv = setInterval(() => setLoadIdx((i) => (i + 1) % LOADING_MESSAGES.length), 2200);
    return () => clearInterval(iv);
  }, [isLoading]);

  // ─── Slide playback engine ─────────────────────────
  const playSlide = useCallback(
    async (idx) => {
      if (!slides || idx >= slides.length || cancelRef.current) {
        setIsPlaying(false);
        if (slides && idx >= slides.length) setExpression('celebrating');
        return;
      }

      const slide = slides[idx];
      setCurrentSlide(idx);
      setVisibleChars(0);
      setShowSpeech(true);
      setShowJoke(false);
      setExpression(slide.expression || 'idle');

      // Phase 1: Speech
      if (audioEnabled) {
        await speak(slide.speech);
      } else {
        await new Promise((r) => setTimeout(r, 2500));
      }
      if (cancelRef.current) return;

      // Phase 2: Whiteboard typing
      setExpression('thinking');
      const fullText = slide.whiteboard || '';
      await new Promise((resolve) => {
        let ci = 0;
        const iv = setInterval(() => {
          if (cancelRef.current) { clearInterval(iv); resolve(); return; }
          ci += 1;
          setVisibleChars(ci);
          if (ci >= fullText.length) { clearInterval(iv); resolve(); }
        }, 30);
      });
      if (cancelRef.current) return;

      // Phase 3: Joke
      setShowJoke(true);
      setExpression('joke');
      if (audioEnabled) {
        await speak(slide.joke);
      } else {
        await new Promise((r) => setTimeout(r, 2500));
      }
      if (cancelRef.current) return;

      await new Promise((r) => setTimeout(r, 800));
      if (cancelRef.current) return;

      playSlide(idx + 1);
    },
    [slides, audioEnabled, speak]
  );

  const handlePlay = () => {
    if (!slides) return;
    cancelRef.current = false;
    setIsPlaying(true);
    const startIdx = currentSlide >= slides.length - 1 && !isPlaying ? 0 : currentSlide;
    if (startIdx === 0) setCurrentSlide(0);
    playSlide(startIdx);
  };

  const handlePause = () => {
    cancelRef.current = true;
    setIsPlaying(false);
    stopTTS();
  };

  const handleRestart = () => {
    cancelRef.current = true;
    stopTTS();
    setTimeout(() => {
      cancelRef.current = false;
      setIsPlaying(true);
      setCurrentSlide(0);
      playSlide(0);
    }, 100);
  };

  const handleNewTutorial = () => {
    cancelRef.current = true;
    stopTTS();
    setSlides(null);
    setIsPlaying(false);
    setConcept('');
    setExpression('idle');
  };

  // ─── API call ──────────────────────────────────────
  const generateTutorial = async () => {
    if (!concept.trim() || wordCount > 150) return;
    setIsLoading(true);
    setError('');
    setSlides(null);
    setCurrentSlide(0);
    setIsPlaying(false);
    cancelRef.current = true;
    stopTTS();

    try {
      const parsed = await generateTutorialContent(concept);
      setSlides(parsed.slides);
      setTitle(parsed.title || concept);
      setExpression('excited');
    } catch (err) {
      console.error(err);
      setError(err.message || "Professor Bray-niac tripped over his chalk!");
    } finally {
      setIsLoading(false);
    }
  };

  // ─── Derived ───────────────────────────────────────
  const currentData = slides?.[currentSlide];
  const isOver = wordCount > 150;

  // ─── Shared button styles ──────────────────────────
  const btnCircle = {
    background: 'white', border: '2px solid #E0E0E0', borderRadius: '50%',
    width: '40px', height: '40px', fontSize: '18px', cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  };

  // ═══════════════════════════════════════════════════
  return (
    <div style={{ minHeight: '100vh', fontFamily: "'Nunito', sans-serif", padding: 0 }}>
      {/* ─── HEADER ─── */}
      <div style={{ padding: '24px 24px 16px', textAlign: 'center', borderBottom: '2px solid rgba(67,160,71,0.15)' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          background: '#43A047', color: 'white', borderRadius: '20px',
          padding: '4px 16px', fontSize: '12px', fontWeight: 800,
          letterSpacing: '1.5px', textTransform: 'uppercase', marginBottom: '8px',
        }}>
          🎓 Tutorial Builder Agent
        </div>
        <h1 style={{ fontSize: '38px', fontWeight: 900, color: '#2E7D32', lineHeight: 1.1 }}>
          Professor Bray-niac
        </h1>
        <p style={{ color: '#81C784', fontSize: '14px', fontWeight: 600, marginTop: '2px' }}>
          Your favourite donkey teacher — powered by Claude Opus 4.6
        </p>
      </div>

      {/* ─── INPUT SCREEN ─── */}
      {!slides && !isLoading && (
        <div style={{ maxWidth: '640px', margin: '24px auto', padding: '0 20px', animation: 'fadeSlideUp 0.5s ease-out' }}>
          <div style={{ background: 'white', borderRadius: '24px', padding: '32px', boxShadow: '0 8px 40px rgba(0,0,0,0.08)', border: '2px solid #E8F5E9' }}>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '8px' }}>
              <div style={{ animation: 'float 3s ease-in-out infinite' }}>
                <DonkeyCharacter expression="excited" time={time} />
              </div>
            </div>

            <div style={{
              background: '#F1F8E9', borderRadius: '16px', padding: '14px 20px',
              textAlign: 'center', marginBottom: '20px', fontSize: '15px',
              color: '#558B2F', fontWeight: 600, fontStyle: 'italic', border: '2px dashed #C5E1A5',
            }}>
              "HEE-HAW! Type any concept and I'll teach it with real-world examples, code, and terrible puns!" 🐴
            </div>

            <label style={{
              display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 800,
              color: '#78909C', letterSpacing: '1.5px', textTransform: 'uppercase', marginBottom: '8px',
            }}>
              <span>What do you want to learn?</span>
              <span style={{ color: isOver ? '#E53935' : '#B0BEC5' }}>{wordCount}/150</span>
            </label>
            <textarea
              value={concept}
              onChange={(e) => setConcept(e.target.value)}
              placeholder="e.g. What is a class in Python?"
              rows={3}
              style={{
                width: '100%', background: '#FAFAFA', border: `2px solid ${isOver ? '#FFCDD2' : '#E0E0E0'}`,
                borderRadius: '14px', padding: '14px 16px', color: '#37474F', fontSize: '16px',
                fontFamily: "'Nunito', sans-serif", fontWeight: 600, resize: 'vertical',
              }}
              onFocus={(e) => { if (!isOver) e.target.style.borderColor = '#66BB6A'; }}
              onBlur={(e) => { e.target.style.borderColor = isOver ? '#FFCDD2' : '#E0E0E0'; }}
            />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
              <button
                onClick={() => setAudioEnabled((a) => !a)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '6px',
                  background: audioEnabled ? '#E8F5E9' : '#FAFAFA',
                  border: `2px solid ${audioEnabled ? '#66BB6A' : '#E0E0E0'}`,
                  borderRadius: '12px', padding: '8px 14px',
                  color: audioEnabled ? '#2E7D32' : '#9E9E9E', fontSize: '13px', fontWeight: 700,
                  cursor: 'pointer', fontFamily: "'Nunito', sans-serif",
                }}
              >
                {audioEnabled ? '🔊' : '🔇'} Audio {audioEnabled ? 'ON' : 'OFF'}
              </button>

              <button
                onClick={generateTutorial}
                disabled={!concept.trim() || isOver}
                style={{
                  background: !concept.trim() || isOver ? '#E0E0E0' : 'linear-gradient(135deg, #43A047, #66BB6A)',
                  color: !concept.trim() || isOver ? '#9E9E9E' : 'white',
                  border: 'none', borderRadius: '14px', padding: '14px 32px', fontSize: '16px',
                  fontWeight: 800, cursor: !concept.trim() || isOver ? 'not-allowed' : 'pointer',
                  fontFamily: "'Nunito', sans-serif",
                  boxShadow: concept.trim() && !isOver ? '0 4px 20px rgba(67,160,71,0.35)' : 'none',
                }}
              >
                🎬 Generate Tutorial
              </button>
            </div>

            {error && (
              <div style={{ marginTop: '14px', background: '#FFEBEE', border: '2px solid #FFCDD2', borderRadius: '12px', padding: '12px 16px', color: '#C62828', fontSize: '14px', fontWeight: 600 }}>
                ⚠️ {error}
              </div>
            )}
          </div>

          {/* Example pills */}
          <div style={{ marginTop: '20px', textAlign: 'center' }}>
            <span style={{ fontSize: '11px', color: '#9E9E9E', fontWeight: 800, letterSpacing: '1.5px', textTransform: 'uppercase' }}>Try these</span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center', marginTop: '10px' }}>
              {EXAMPLE_TOPICS.map((ex) => (
                <button
                  key={ex}
                  onClick={() => setConcept(ex)}
                  style={{
                    background: 'white', border: '2px solid #E8F5E9', borderRadius: '20px',
                    padding: '6px 16px', color: '#558B2F', fontSize: '13px', fontWeight: 700,
                    cursor: 'pointer', fontFamily: "'Nunito', sans-serif",
                    boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                  }}
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ─── LOADING ─── */}
      {isLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '48px 24px', animation: 'fadeSlideUp 0.4s ease-out' }}>
          <div style={{ animation: 'pulse 1.5s ease-in-out infinite' }}>
            <DonkeyCharacter expression="thinking" isTalking mouthShape={Math.floor(time * 6) % 5} time={time} />
          </div>
          <div style={{ marginTop: '16px', fontSize: '18px', fontWeight: 700, color: '#558B2F' }}>
            {LOADING_MESSAGES[loadIdx]}
          </div>
          <div style={{ display: 'flex', gap: '6px', marginTop: '16px' }}>
            {[0, 1, 2].map((i) => (
              <div key={i} style={{ width: 10, height: 10, borderRadius: '50%', background: '#66BB6A', animation: `dotBounce 0.6s ease-in-out ${i * 0.15}s infinite` }} />
            ))}
          </div>
        </div>
      )}

      {/* ─── VIDEO PLAYER ─── */}
      {slides && !isLoading && (
        <div style={{ maxWidth: '960px', margin: '20px auto', padding: '0 16px', animation: 'fadeSlideUp 0.5s ease-out' }}>
          <div style={{ background: 'white', borderRadius: '24px', overflow: 'hidden', boxShadow: '0 12px 48px rgba(0,0,0,0.1)', border: '2px solid #E8F5E9' }}>
            {/* Stage */}
            <div style={{ display: 'flex', gap: '20px', padding: '28px 24px', minHeight: '480px', alignItems: 'flex-start', background: 'linear-gradient(180deg, #FAFFFE 0%, #F5FAF5 100%)', flexWrap: 'wrap' }}>
              {/* Donkey column */}
              <div style={{ flex: '0 0 240px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px', minWidth: '220px' }}>
                <SpeechBubble text={currentData?.speech} visible={showSpeech} />
                <DonkeyCharacter expression={expression} isTalking={isSpeaking} mouthShape={mouthShape} time={time} />
                <SpeechBubble text={currentData?.joke} isJoke visible={showJoke} />
              </div>

              {/* Whiteboard column */}
              <div style={{ flex: 1, minWidth: '280px' }}>
                <Whiteboard text={currentData?.whiteboard || ''} visibleChars={visibleChars} title={title} />
                {/* Slide dots */}
                <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '20px' }}>
                  {slides.map((_, i) => (
                    <div
                      key={i}
                      onClick={() => {
                        if (!isPlaying) {
                          setCurrentSlide(i);
                          setVisibleChars(999);
                          setShowSpeech(true);
                          setShowJoke(true);
                          setExpression(slides[i].expression || 'idle');
                        }
                      }}
                      style={{
                        width: i === currentSlide ? '28px' : '10px', height: '10px', borderRadius: '5px',
                        background: i === currentSlide ? '#43A047' : i < currentSlide ? '#A5D6A7' : '#E0E0E0',
                        transition: 'all 0.3s cubic-bezier(0.4,0,0.2,1)',
                        cursor: isPlaying ? 'default' : 'pointer',
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Controls */}
            <div style={{ padding: '16px 28px 20px', background: '#F9FBE7', borderTop: '2px solid #F0F4C3' }}>
              {/* Progress */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '12px', color: '#78909C', fontWeight: 700 }}>{currentSlide + 1}/{slides.length}</span>
                <div style={{ flex: 1, height: '8px', background: '#ECEFF1', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${((currentSlide + 1) / slides.length) * 100}%`, borderRadius: '4px', background: 'linear-gradient(90deg, #66BB6A, #43A047)', transition: 'width 0.4s' }} />
                </div>
              </div>
              {/* Buttons */}
              <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', marginTop: '14px', alignItems: 'center' }}>
                <button onClick={handleRestart} style={btnCircle}>⏮</button>
                <button
                  onClick={isPlaying ? handlePause : handlePlay}
                  style={{
                    background: 'linear-gradient(135deg, #43A047, #66BB6A)', border: 'none',
                    borderRadius: '50%', width: '54px', height: '54px', fontSize: '22px',
                    cursor: 'pointer', color: 'white', display: 'flex', alignItems: 'center',
                    justifyContent: 'center', boxShadow: '0 4px 20px rgba(67,160,71,0.35)',
                  }}
                >
                  {isPlaying ? '⏸' : '▶️'}
                </button>
                <button onClick={() => setAudioEnabled((a) => !a)} style={{ ...btnCircle, fontSize: '16px' }}>
                  {audioEnabled ? '🔊' : '🔇'}
                </button>
                <button onClick={handleNewTutorial} style={btnCircle}>✕</button>
              </div>
            </div>
          </div>

          <div style={{ textAlign: 'center', marginTop: '14px', fontSize: '13px', color: '#9E9E9E', fontWeight: 600 }}>
            Topic: <span style={{ color: '#558B2F' }}>{concept}</span>
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{ textAlign: 'center', padding: '24px', fontSize: '12px', color: '#C5E1A5', fontWeight: 700 }}>
        Professor Bray-niac © HEE-HAW Industries • Built with Claude Opus 4.6
      </div>
    </div>
  );
}
