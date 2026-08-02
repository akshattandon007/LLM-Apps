import { useState, useEffect, useCallback } from "react";

type Mood = "empty" | "chilling" | "dancing" | "studying" | "working-out";
type Track = { title: string; artist: string; bpm: number; genre: string };

const MOODS: { id: Mood; label: string; emoji: string; color: string }[] = [
  { id: "empty", label: "Empty Room", emoji: "🫗", color: "#71717a" },
  { id: "chilling", label: "Chilling", emoji: "🧘", color: "#22d3ee" },
  { id: "dancing", label: "Dancing", emoji: "🕺", color: "#f43f5e" },
  { id: "studying", label: "Studying", emoji: "📚", color: "#a78bfa" },
  { id: "working-out", label: "Working Out", emoji: "💪", color: "#f97316" },
];

const PLAYLISTS: Record<Mood, Track[]> = {
  empty: [
    { title: "Silence", artist: "—", bpm: 0, genre: "Ambient" },
    { title: "Waiting", artist: "The Void", bpm: 0, genre: "Ambient" },
  ],
  chilling: [
    { title: "Sunset Boulevard", artist: "Kavinsky", bpm: 95, genre: "Synthwave" },
    { title: "Night Owl", artist: "Galimatias", bpm: 85, genre: "Downtempo" },
    { title: "Lost in Thought", artist: "Tycho", bpm: 90, genre: "Ambient House" },
  ],
  dancing: [
    { title: "Neon Pulse", artist: "Justice", bpm: 128, genre: "French House" },
    { title: "Disco Inferno 2.0", artist: "Daft Punk", bpm: 124, genre: "Disco" },
    { title: "Drop Everything", artist: "Skrillex", bpm: 140, genre: "Dubstep" },
  ],
  studying: [
    { title: "Deep Focus", artist: "Lofi Girl", bpm: 75, genre: "Lo-fi" },
    { title: "Ambient Study", artist: "Brian Eno", bpm: 60, genre: "Ambient" },
    { title: "Coffee Shop Rain", artist: "JazzHop", bpm: 80, genre: "Jazz Hop" },
  ],
  "working-out": [
    { title: "Iron Paradise", artist: "NEFFEX", bpm: 135, genre: "Hard Rock" },
    { title: "Push Through", artist: "The Prodigy", bpm: 140, genre: "Big Beat" },
    { title: "Last Rep", artist: "Pendulum", bpm: 174, genre: "Drum & Bass" },
  ],
};

const GESTURES = [
  { gesture: "✋ Palm Up", action: "Volume +", color: "text-green-400" },
  { gesture: "✊ Fist", action: "Pause / Play", color: "text-yellow-400" },
  { gesture: "👉 Point Right", action: "Next Track", color: "text-cyan-400" },
  { gesture: "👈 Point Left", action: "Previous", color: "text-cyan-400" },
  { gesture: "🤘 Rock On", action: "Party Mode", color: "text-pink-400" },
  { gesture: "🤟 Love", action: "Save Track", color: "text-red-400" },
];

type HistoryEntry = { mood: Mood; timestamp: Date; track: Track };

export default function GestureDJ() {
  const [cameraOn, setCameraOn] = useState(false);
  const [currentMood, setCurrentMood] = useState<Mood>("empty");
  const [headcount, setHeadcount] = useState(0);
  const [nowPlaying, setNowPlaying] = useState<Track | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [moodCycle, setMoodCycle] = useState(0);
  const [simSpeed, setSimSpeed] = useState(1);

  const pickTrack = useCallback((mood: Mood) => {
    const tracks = PLAYLISTS[mood];
    return tracks[Math.floor(Math.random() * tracks.length)];
  }, []);

  // Simulated vision detection — cycles through moods
  useEffect(() => {
    if (!cameraOn) return;

    const moods: Mood[] = ["empty", "chilling", "dancing", "studying", "working-out"];
    const counts = { empty: 0, chilling: 2, dancing: 5, studying: 1, "working-out": 2 };

    const interval = setInterval(
      () => {
        setMoodCycle((prev) => {
          const next = (prev + 1) % moods.length;
          const mood = moods[next];
          setCurrentMood(mood);
          setHeadcount(counts[mood]);
          const track = pickTrack(mood);
          setNowPlaying(track);
          setHistory((h) => [{ mood, timestamp: new Date(), track }, ...h].slice(0, 20));
          return next;
        });
      },
      4000 / simSpeed,
    );

    return () => clearInterval(interval);
  }, [cameraOn, simSpeed, pickTrack]);

  const toggleCamera = () => {
    if (cameraOn) {
      setCameraOn(false);
      setCurrentMood("empty");
      setHeadcount(0);
      setNowPlaying(null);
    } else {
      setCameraOn(true);
      setHistory([]);
    }
  };

  const currentMoodData = MOODS.find((m) => m.id === currentMood)!;

  return (
    <div data-theme="dark" className="min-h-screen bg-[#0a0a0f] text-[#e4e4e7] font-sans">
      {/* Hero */}
      <header className="text-center pt-12 pb-6 px-4">
        <h1 className="text-5xl md:text-7xl font-black tracking-tight">
          Gesture{" "}
          <span className="bg-gradient-to-r from-purple-500 via-pink-500 to-orange-400 bg-clip-text text-transparent">
            DJ
          </span>
        </h1>
        <p className="mt-4 text-lg text-zinc-400 max-w-lg mx-auto">
          Your room is the DJ booth. The music adapts to the vibe — automatically.
        </p>
        <div className="mt-6 flex gap-3 justify-center flex-wrap">
          <button onClick={toggleCamera} className="btn btn-lg gap-2 border-0 text-base" style={{
            background: cameraOn
              ? "linear-gradient(135deg, #ef4444, #dc2626)"
              : "linear-gradient(135deg, #a855f7, #7c3aed)",
            boxShadow: cameraOn
              ? "0 0 30px rgba(239,68,68,0.3)"
              : "0 0 30px rgba(168,85,247,0.3)",
          }}>
            {cameraOn ? "⏹ Stop Agent" : "▶ Start Agent"}
          </button>
          {cameraOn && (
            <select
              className="select select-bordered bg-[#12121a] border-zinc-700 text-zinc-300"
              value={simSpeed}
              onChange={(e) => setSimSpeed(Number(e.target.value))}
            >
              <option value={0.5}>0.5× Speed</option>
              <option value={1}>1× Speed</option>
              <option value={2}>2× Speed</option>
              <option value={4}>4× Speed</option>
            </select>
          )}
        </div>
      </header>

      {/* Main Grid */}
      <div className="max-w-7xl mx-auto px-4 pb-16 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Webcam Feed */}
        <div className="lg:col-span-2">
          <div
            className="relative rounded-2xl overflow-hidden border-2 transition-all duration-500"
            style={{
              borderColor: cameraOn ? currentMoodData.color : "#27272a",
              boxShadow: cameraOn
                ? `0 0 40px ${currentMoodData.color}22, inset 0 0 40px ${currentMoodData.color}0a`
                : "none",
              background: "#12121a",
              aspectRatio: "16/9",
            }}
          >
            {cameraOn ? (
              <div className="w-full h-full flex flex-col items-center justify-center relative">
                {/* Simulated webcam grid */}
                <div className="absolute inset-0 opacity-10" style={{
                  backgroundImage: `repeating-linear-gradient(0deg, transparent, transparent 2px, ${currentMoodData.color} 2px, ${currentMoodData.color} 4px), repeating-linear-gradient(90deg, transparent, transparent 2px, ${currentMoodData.color} 2px, ${currentMoodData.color} 4px)`,
                }} />
                {/* Scanning line */}
                <div className="absolute inset-0 overflow-hidden">
                  <div className="w-full h-[2px] absolute animate-scan" style={{
                    background: `linear-gradient(90deg, transparent, ${currentMoodData.color}, transparent)`,
                    animation: "scan 2s ease-in-out infinite",
                    top: `${(moodCycle * 11) % 100}%`,
                  }} />
                </div>
                {/* Simulated people */}
                <div className="text-7xl mb-4 relative z-10 transition-all duration-500" style={{
                  transform: `scale(${cameraOn ? 1 : 0.5})`,
                }}>
                  {headcount === 0 && "🪑"}
                  {headcount === 1 && "🧑‍💻"}
                  {headcount === 2 && "👥"}
                  {headcount >= 5 && "🎉"}
                </div>
                <div className="text-sm text-zinc-500 relative z-10">
                  {headcount} {headcount === 1 ? "person" : "people"} detected
                </div>
                {/* Corner badge */}
                <div className="absolute top-4 left-4 px-3 py-1.5 rounded-full text-xs font-mono flex items-center gap-2 z-10"
                  style={{ background: "#0a0a0fcc", border: `1px solid ${currentMoodData.color}44` }}>
                  <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: currentMoodData.color }} />
                  LIVE • 30 FPS
                </div>
              </div>
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center text-zinc-600">
                <span className="text-6xl mb-3">📹</span>
                <p className="text-sm">Camera offline</p>
                <p className="text-xs mt-1">Click Start Agent to begin</p>
              </div>
            )}
          </div>

          {/* Mood Indicator */}
          {cameraOn && (
            <div className="mt-4 p-4 rounded-xl flex items-center gap-4 transition-all duration-500"
              style={{ background: `#12121a`, border: `1px solid ${currentMoodData.color}33` }}>
              <span className="text-3xl animate-bounce">{currentMoodData.emoji}</span>
              <div>
                <div className="text-sm text-zinc-400">Detected Mood</div>
                <div className="text-xl font-bold" style={{ color: currentMoodData.color }}>
                  {currentMoodData.label}
                </div>
              </div>
              <div className="ml-auto text-right">
                <div className="text-xs text-zinc-500">Headcount</div>
                <div className="text-lg font-mono">{headcount}</div>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel */}
        <div className="space-y-6">
          {/* Now Playing */}
          <div className="rounded-2xl p-5 border border-zinc-800" style={{ background: "#12121a" }}>
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
              🎵 Now Playing
            </h2>
            {nowPlaying ? (
              <div>
                <div className="text-lg font-bold">{nowPlaying.title}</div>
                <div className="text-sm text-zinc-400">{nowPlaying.artist}</div>
                <div className="flex gap-3 mt-3">
                  <span className="badge border-0 text-xs" style={{ background: "#7c3aed22", color: "#a78bfa" }}>
                    {nowPlaying.bpm} BPM
                  </span>
                  <span className="badge border-0 text-xs" style={{ background: "#22d3ee22", color: "#22d3ee" }}>
                    {nowPlaying.genre}
                  </span>
                </div>
                {/* Fake waveform */}
                <div className="mt-4 flex items-end gap-[2px] h-8">
                  {Array.from({ length: 32 }).map((_, i) => (
                    <div
                      key={i}
                      className="flex-1 rounded-sm transition-all duration-300"
                      style={{
                        height: `${12 + Math.sin((i + moodCycle) * 0.5) * 8 + Math.random() * 4}px`,
                        background: currentMoodData.color,
                        opacity: 0.6 + Math.random() * 0.4,
                      }}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-zinc-600 text-sm italic">Waiting for agent to start…</p>
            )}
          </div>

          {/* Gesture Guide */}
          <div className="rounded-2xl p-5 border border-zinc-800" style={{ background: "#12121a" }}>
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
              ✋ Gesture Controls
            </h2>
            <div className="space-y-2">
              {GESTURES.map((g) => (
                <div key={g.gesture} className="flex justify-between items-center text-sm py-1.5 border-b border-zinc-800/50 last:border-0">
                  <span>{g.gesture}</span>
                  <span className={`font-mono text-xs ${g.color}`}>{g.action}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Session History */}
          <div className="rounded-2xl p-5 border border-zinc-800" style={{ background: "#12121a" }}>
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
              📜 Session History
            </h2>
            {history.length > 0 ? (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {history.map((entry, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs py-1.5 border-b border-zinc-800/30 last:border-0">
                    <span>{MOODS.find((m) => m.id === entry.mood)?.emoji}</span>
                    <span className="text-zinc-400">{MOODS.find((m) => m.id === entry.mood)?.label}</span>
                    <span className="text-zinc-600 ml-auto font-mono">
                      {entry.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-zinc-600 text-sm italic">No sessions recorded yet</p>
            )}
          </div>
        </div>
      </div>

      {/* Keyframe for scan animation */}
      <style jsx>{`
        @keyframes scan {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 1; }
        }
      `}</style>
    </div>
  );
}