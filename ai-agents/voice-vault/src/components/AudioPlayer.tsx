import { useEffect, useRef, useState } from 'react';

interface AudioPlayerProps {
  src: string;
  mime?: string;
  className?: string;
  onEnded?: () => void;
}

export default function AudioPlayer({ src, mime, className = '', onEnded }: AudioPlayerProps) {
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const bars = useRef<number[]>([]);
  const animRef = useRef<number>(0);

  // ── Decode audio for waveform ────────────────────────────
  useEffect(() => {
    if (!src) return;
    const audio = new Audio(src);
    audioRef.current = audio;

    audio.addEventListener('loadedmetadata', () => {
      setDuration(audio.duration || 0);
    });

    audio.addEventListener('timeupdate', () => {
      setCurrentTime(audio.currentTime);
    });

    audio.addEventListener('ended', () => {
      setPlaying(false);
      setCurrentTime(0);
      onEnded?.();
    });

    // Decode for waveform bars
    const ctx = new AudioContext();
    fetch(src)
      .then((r) => r.arrayBuffer())
      .then((buf) => ctx.decodeAudioData(buf))
      .then((decoded) => {
        const channel = decoded.getChannelData(0);
        // Downsample to 40 bars
        const numBars = 40;
        const step = Math.floor(channel.length / numBars);
        bars.current = Array.from({ length: numBars }, (_, i) => {
          let sum = 0;
          for (let j = 0; j < step && i * step + j < channel.length; j++) {
            sum += Math.abs(channel[i * step + j]);
          }
          return sum / step;
        });
        // Normalize
        const max = Math.max(...bars.current, 0.01);
        bars.current = bars.current.map((v) => v / max);
        drawStaticWaveform(0);
      })
      .catch(() => {
        // Fallback: flat bars
        bars.current = Array(40).fill(0.3);
        drawStaticWaveform(0);
      });

    return () => {
      audio.pause();
      audio.src = '';
      cancelAnimationFrame(animRef.current);
      ctx.close();
    };
  }, [src]);

  // ── Draw waveform ────────────────────────────────────────
  function drawStaticWaveform(progress: number) {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx || bars.current.length === 0) return;

    const W = canvas.width;
    const H = canvas.height;
    const barW = 6;
    const gap = 4;
    ctx.clearRect(0, 0, W, H);

    const activeIdx = Math.floor(progress * bars.current.length);

    bars.current.forEach((amp, i) => {
      const x = i * (barW + gap) + 4;
      const barH = Math.max(2, amp * H * 0.8);
      const y = (H - barH) / 2;
      ctx.fillStyle = i <= activeIdx ? '#c2705a' : '#e8dfd0';
      ctx.beginPath();
      ctx.roundRect(x, y, barW, barH, 3);
      ctx.fill();
    });
  }

  // ── Play/Pause ───────────────────────────────────────────
  function togglePlay() {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
      setPlaying(false);
    } else {
      audioRef.current.play();
      setPlaying(true);
      // Animate waveform while playing
      function animate() {
        if (!audioRef.current) return;
        const p = audioRef.current.duration > 0
          ? audioRef.current.currentTime / audioRef.current.duration
          : 0;
        drawStaticWaveform(p);
        animRef.current = requestAnimationFrame(animate);
      }
      animate();
    }
  }

  // ── Seek via click on waveform ───────────────────────────
  function handleSeek(e: React.MouseEvent<HTMLCanvasElement>) {
    if (!audioRef.current || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const fraction = Math.max(0, Math.min(1, x / rect.width));
    const time = fraction * duration;
    audioRef.current.currentTime = time;
    setCurrentTime(time);
    drawStaticWaveform(fraction);
  }

  // ── Format time ──────────────────────────────────────────
  function fmt(sec: number): string {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${String(s).padStart(2, '0')}`;
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <button className="btn btn-circle btn-sm btn-ghost" onClick={togglePlay}>
        {playing ? (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
          </svg>
        )}
      </button>

      <canvas
        ref={canvasRef}
        width={360}
        height={48}
        className="cursor-pointer flex-1 rounded-md"
        onClick={handleSeek}
      />

      <span className="text-xs font-mono text-base-content/60 min-w-12 text-right">
        {fmt(currentTime)} / {fmt(duration)}
      </span>
    </div>
  );
}