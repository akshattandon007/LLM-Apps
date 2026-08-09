import { useState, useRef, useEffect } from 'react';
import AnswerCard from './AnswerCard';

export default function ChatPanel({ meetings }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Show welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          role: 'assistant',
          text: meetings.length > 0
            ? `👋 I've ingested ${meetings.length} meeting${meetings.length !== 1 ? 's' : ''}. Ask me anything about them!`
            : '👋 Upload a meeting transcript to get started.',
        },
      ]);
    }
  }, [meetings]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput('');
    setError(null);

    // Add user message
    setMessages(prev => [...prev, { role: 'user', text: question }]);
    setLoading(true);

    try {
      const res = await fetch('/api/proxy?endpoint=query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: 5 }),
      });
      const data = await res.json();

      if (res.ok) {
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            text: data.answer,
            intent: data.intent,
            sources: data.sources || [],
          },
        ]);
      } else {
        setError(data.detail || 'Query failed');
      }
    } catch (e) {
      setError(`Connection error: ${e.message}. Is the backend running?`);
    }
    setLoading(false);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === 'user' ? (
              <div className="flex justify-end">
                <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-md px-4 py-2.5 max-w-[80%] shadow-sm">
                  <p className="text-sm">{msg.text}</p>
                </div>
              </div>
            ) : (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-md px-4 py-3 max-w-[90%] shadow-sm">
                  <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                  
                  {/* Intent badge */}
                  {msg.intent && (
                    <div className="mt-2">
                      <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full ${
                        msg.intent === 'DECISION' ? 'bg-green-100 text-green-700' :
                        msg.intent === 'ACTION_ITEM' ? 'bg-blue-100 text-blue-700' :
                        msg.intent === 'OPINION' ? 'bg-purple-100 text-purple-700' :
                        msg.intent === 'FOLLOW_UP' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {msg.intent}
                      </span>
                    </div>
                  )}

                  {/* Source cards */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 space-y-2 pt-3 border-t border-gray-100">
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                        Sources
                      </p>
                      {msg.sources.map((source, j) => (
                        <AnswerCard key={j} source={source} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your meetings..."
          disabled={loading || meetings.length === 0}
          className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        />
        <button
          type="submit"
          disabled={loading || !input.trim() || meetings.length === 0}
          className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm transition-colors"
        >
          Ask
        </button>
      </form>
    </div>
  );
}