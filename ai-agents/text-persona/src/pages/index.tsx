import { useState, useCallback, useEffect } from "react";
import Head from "next/head";
import { Persona, personas, getPersonaById } from "@/lib/personas";
import {
  HistoryItem,
  loadHistory,
  addHistoryItem,
  clearHistory,
  generateId,
} from "@/lib/history";
import PersonaGrid from "@/components/PersonaGrid";
import MessageInput from "@/components/MessageInput";
import RewriteOutput from "@/components/RewriteOutput";
import HistorySidebar from "@/components/HistorySidebar";
import DarkModeToggle from "@/components/DarkModeToggle";

export default function Home() {
  const [message, setMessage] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [rewritten, setRewritten] = useState("");
  const [original, setOriginal] = useState("");
  const [personaName, setPersonaName] = useState("");
  const [personaEmoji, setPersonaEmoji] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dark, setDark] = useState(false);

  // Load dark mode preference on mount
  useEffect(() => {
    const saved = localStorage.getItem("textpersona-dark");
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)",
    ).matches;
    const isDark = saved !== null ? saved === "true" : prefersDark;
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
    document.documentElement.setAttribute(
      "data-theme",
      isDark ? "dark" : "light",
    );
  }, []);

  // Load history on mount
  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  const toggleDark = useCallback(() => {
    setDark((prev) => {
      const next = !prev;
      localStorage.setItem("textpersona-dark", String(next));
      document.documentElement.classList.toggle("dark", next);
      document.documentElement.setAttribute(
        "data-theme",
        next ? "dark" : "light",
      );
      return next;
    });
  }, []);

  const handleSelectPersona = useCallback(
    async (persona: Persona) => {
      const trimmed = message.trim();
      if (!trimmed) return;

      setSelectedId(persona.id);
      setLoading(true);
      setError(null);
      setRewritten("");
      setOriginal(trimmed);
      setPersonaName(persona.name);
      setPersonaEmoji(persona.emoji);

      try {
        const res = await fetch("/api/rewrite", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: trimmed,
            systemPrompt: persona.systemPrompt,
          }),
        });

        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.error || `Server error (${res.status})`);
        }

        setRewritten(data.rewritten);

        // Save to history
        const item: HistoryItem = {
          id: generateId(),
          personaId: persona.id,
          personaName: persona.name,
          personaEmoji: persona.emoji,
          original: trimmed,
          rewritten: data.rewritten,
          timestamp: Date.now(),
        };
        const updated = addHistoryItem(item);
        setHistory(updated);
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Something went wrong";
        setError(msg);
      } finally {
        setLoading(false);
      }
    },
    [message],
  );

  const handleHistorySelect = useCallback((item: HistoryItem) => {
    setMessage(item.original);
    setOriginal(item.original);
    setRewritten(item.rewritten);
    setPersonaName(item.personaName);
    setPersonaEmoji(item.personaEmoji);
    setSelectedId(item.personaId);
    setSidebarOpen(false);
  }, []);

  const handleClearHistory = useCallback(() => {
    clearHistory();
    setHistory([]);
  }, []);

  const selectedPersona = selectedId ? getPersonaById(selectedId) : null;

  return (
    <>
      <Head>
        <title>TextPersona — AI Message Rewriter</title>
      </Head>

      <div className="min-h-screen">
        {/* Header */}
        <header className="sticky top-0 z-20 bg-base-100/80 backdrop-blur border-b border-base-300">
          <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl">🎭</span>
              <h1 className="text-xl font-bold">TextPersona</h1>
            </div>
            <div className="flex items-center gap-2">
              <DarkModeToggle dark={dark} onToggle={toggleDark} />
              <button
                className="btn btn-circle btn-ghost"
                onClick={() => setSidebarOpen(true)}
                aria-label="Open history"
              >
                <span className="text-xl">📜</span>
              </button>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="max-w-4xl mx-auto px-4 py-6 space-y-8">
          {/* Input */}
          <MessageInput
            message={message}
            setMessage={setMessage}
            disabled={loading}
          />

          {/* Persona grid */}
          <PersonaGrid
            personas={personas}
            selectedId={selectedId}
            loading={loading}
            onSelect={handleSelectPersona}
          />

          {/* Output */}
          <RewriteOutput
            original={original}
            rewritten={rewritten}
            personaName={personaName}
            personaEmoji={personaEmoji}
            loading={loading}
            error={error}
          />

          {/* Footer */}
          {!rewritten && !loading && !error && (
            <div className="text-center text-base-content/40 py-8">
              <p className="text-4xl mb-3">👆</p>
              <p className="text-sm">
                Type a message above and click a persona to see the magic!
              </p>
            </div>
          )}
        </main>

        {/* History sidebar */}
        <HistorySidebar
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          history={history}
          onClear={handleClearHistory}
          onSelect={handleHistorySelect}
        />
      </div>
    </>
  );
}
