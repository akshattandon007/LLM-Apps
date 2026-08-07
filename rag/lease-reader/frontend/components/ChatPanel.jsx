import React, { useState, useRef, useEffect } from "react";
import AnswerCard from "./AnswerCard";

export default function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput("");
    setError(null);

    // Add user message
    setMessages((prev) => [...prev, { role: "user", content: question }]);

    setLoading(true);
    try {
      const res = await fetch("/api/proxy/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: 5 }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || `Server error: ${res.status}`);
      }

      setMessages((prev) => [...prev, { role: "assistant", content: data }]);
    } catch (err) {
      setError(err.message);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: {
            answer: `**Error:** ${err.message}`,
            domain: "GENERAL",
            cited_clauses: [],
            caveat: null,
          },
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 py-16">
            <svg className="h-16 w-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <p className="text-lg font-medium text-gray-500">Ask about your lease</p>
            <p className="text-sm mt-1">
              Upload a lease, then ask questions like:
            </p>
            <div className="mt-4 space-y-1 text-sm text-gray-400">
              <p>"Can my landlord enter without notice?"</p>
              <p>"What happens if I break the lease early?"</p>
              <p>"Will I get my security deposit back?"</p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === "user" ? (
              <div className="flex justify-end">
                <div className="bg-brand-600 text-white rounded-2xl rounded-br-sm px-4 py-2.5 max-w-[80%] shadow-sm">
                  {msg.content}
                </div>
              </div>
            ) : (
              <AnswerCard answer={msg.content} />
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-gray-400 text-sm pl-2">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
            <span>Analyzing lease...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <form onSubmit={sendMessage} className="relative">
        <textarea
          className="message-input"
          rows={1}
          placeholder="Ask a question about your lease..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
          disabled={loading}
        />
        <button
          type="submit"
          className="send-button"
          disabled={!input.trim() || loading}
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" />
          </svg>
        </button>
      </form>
    </div>
  );
}