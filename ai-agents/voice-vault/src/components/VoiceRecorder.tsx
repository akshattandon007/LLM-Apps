import { useEffect, useRef, useState } from 'react';

interface VoiceRecorderProps {
  onSave: (data: { dataUrl: string; mime: string; duration: number }) => void;
  maxDuration?: number; // seconds, default 60
}

type RecorderState = 'idle' | 'recording' | 'stopped';

export default function VoiceRecorder({ onSave, maxDuration = 60 }: VoiceRecorderProps) {
  const [state, setState] = useState<RecorderState>('idle');
  const [duration, setDuration] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const chunks = useRef<Blob[]>([]);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const animFrame = useRef(0);
  const startTime = useRef(0);
  const audioCtx = useRef<AudioContext | null>(null);

  // ── Cleanup ──────────────────────────────────────────────
  useEffect(() => {
    return () => {
      stopTracks();
      cancelAnimationFrame(animFrame.current);
      if (timer.current) clearInterval(timer.current);
      if (audioCtx.current) audioCtx.current.close();
    };
  }, []);

  function stopTracks() {
    stream.current?.getTracks().forEach((t) => t.stop());
    stream.current = null;
  }

  // ── Start recording ──────────────────────────────────────
  async function startRecording() {
    setError(null);
    setAudioUrl(null);
    setDuration(0);
    chunks.current = [];

    try {
      const s = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 48000,
          channelCount: 1,
        },
      });
      stream.current = s;

      // Set up analyser for waveform
      audioCtx.current = new AudioContext();
      const source = audioCtx.current.createMediaStreamSource(s);
      const node = audioCtx.current.createAnalyser();
      node.fftSize = 256;
      source.connect(node);
      analyser.current = node;

      // Determine supported MIME type
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      const recorder = new MediaRecorder(s, {
        mimeType,
        audioBitsPerSecond: 32000,
      });
      mediaRecorder.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks.current, { type: recorder.mimeType });
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        setState('stopped');
        stopTracks();
        if (timer.current) clearInterval(timer.current);
        timer.current = null;
      };

      recorder.start(100); // timeslice 100ms
      startTime.current = Date.now();
      setState('recording');

      // Update duration timer
      const intervalId = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime.current) / 1000);
        setDuration(elapsed);
        if (elapsed >= maxDuration) {
          recorder.stop();
        }
      }, 200);
      timer.current = intervalId;

      drawWaveform();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Microphone access denied';
      setError(msg);
      setState('idle');
    }
  }

  // ── Stop recording ───────────────────────────────────────
  function stopRecording() {
    mediaRecorder.current?.stop();
    cancelAnimationFrame(animFrame.current);
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
  }

  // ── Waveform drawing ─────────────────────────────────────
  function drawWaveform() {
    if (!canvasRef.current || !analyser.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    const bufferLength = analyser.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
      if (!analyser.current || !canvasRef.current) return;
      const c = canvasRef.current.getContext('2d');
      if (!c) return;
      analyser.current.getByteTimeDomainData(dataArray);
      c.clearRect(0, 0, W, H);
      c.fillStyle = '#c2705a';
      c.fillRect(0, 0, W, H);

      const barWidth = Math.max(2, W / bufferLength);
      c.strokeStyle = '#faf6f0';
      c.lineWidth = 2;
      c.beginPath();
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * H) / 2;
        if (i === 0) c.moveTo(i * barWidth, y);
        else c.lineTo(i * barWidth, y);
      }
      c.stroke();
      animFrame.current = requestAnimationFrame(draw);
    }
    draw();
  }

  // ── Confirm recording ────────────────────────────────────
  function confirmRecording() {
    if (!audioUrl || chunks.current.length === 0) return;
    const blob = new Blob(chunks.current, {
      type: mediaRecorder.current?.mimeType || 'audio/webm',
    });
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      onSave({
        dataUrl,
        mime: mediaRecorder.current?.mimeType || 'audio/webm',
        duration,
      });
      // Reset
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
      setState('idle');
      setDuration(0);
      chunks.current = [];
    };
    reader.readAsDataURL(blob);
  }

  // ── Cancel / retry ───────────────────────────────────────
  function cancel() {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(null);
    setState('idle');
    setDuration(0);
    setError(null);
    chunks.current = [];
  }

  // ── Render ───────────────────────────────────────────────
  return (
    <div className="card bg-base-200 rounded-box p-4">
      {/* Waveform canvas */}
      <canvas
        ref={canvasRef}
        width={600}
        height={80}
        className="waveform-canvas mb-3 bg-base-300"
      />

      {/* Error */}
      {error && (
        <p className="text-error text-sm mb-2">{error}</p>
      )}

      {/* Duration */}
      {state !== 'idle' && (
        <p className="text-sm text-base-content/70 mb-3 text-center font-mono">
          {Math.floor(duration / 60)}:{String(duration % 60).padStart(2, '0')}
          {' / '}
          {Math.floor(maxDuration / 60)}:{String(maxDuration % 60).padStart(2, '0')}
        </p>
      )}

      {/* Buttons */}
      <div className="flex justify-center gap-3">
        {state === 'idle' && (
          <button className="btn btn-primary" onClick={startRecording}>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
            Record
          </button>
        )}

        {state === 'recording' && (
          <button className="btn btn-error" onClick={stopRecording}>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
            </svg>
            Stop
          </button>
        )}

        {state === 'stopped' && audioUrl && (
          <>
            <button
              className="btn btn-outline"
              onClick={() => {
                const a = new Audio(audioUrl);
                a.play();
              }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
              </svg>
              Play
            </button>
            <button className="btn btn-ghost" onClick={cancel}>
              Retry
            </button>
            <button className="btn btn-primary" onClick={confirmRecording}>
              Use this
            </button>
          </>
        )}
      </div>
    </div>
  );
}