import { useState, useRef, useEffect } from 'react';

export default function Home() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Upload a codebase directory to get started. I\'ll help you search through it using natural language.' }
  ]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [hasIndex, setHasIndex] = useState(false);
  const [status, setStatus] = useState({ indexedFiles: 0, indexedChunks: 0 });
  const chatEnd = useRef(null);

  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function fetchStatus() {
    try {
      const res = await fetch('/api/proxy?endpoint=status');
      const data = await res.json();
      setHasIndex(data.has_index);
      setStatus({ indexedFiles: data.indexed_files, indexedChunks: data.indexed_chunks });
    } catch (e) {
      console.error('Status fetch failed', e);
    }
  }

  async function handleIngest(e) {
    e.preventDefault();
    const dir = prompt('Enter the absolute path to the codebase directory:');
    if (!dir) return;

    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', content: `Ingest codebase from: ${dir}` }]);

    try {
      const res = await fetch('/api/proxy?endpoint=ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ directory_path: dir })
      });
      const data = await res.json();
      if (res.ok) {
        setMessages(prev => [...prev, { role: 'assistant', content: `✅ ${data.message}\nFiles: ${data.files_ingested} | Chunks: ${data.chunks_created} | Total indexed: ${data.index_size}` }]);
        setHasIndex(true);
        setStatus({ indexedFiles: data.files_ingested, indexedChunks: data.index_size });
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: `❌ Error: ${data.detail || 'Unknown error'}` }]);
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `❌ Connection error: ${e.message}` }]);
    }
    setLoading(false);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!query.trim() || loading) return;

    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setLoading(true);

    try {
      const res = await fetch('/api/proxy?endpoint=query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim(), top_k: 5 })
      });
      const data = await res.json();
      if (res.ok) {
        const sourceText = data.sources.map((s, i) =>
          `  ${i + 1}. \`${s.file_path}:${s.start_line}-${s.end_line}\` (score: ${s.relevance_score.toFixed(3)})`
        ).join('\n');
        setMessages(prev => [...prev, { role: 'assistant', content: `${data.answer}\n\n**Sources:**\n${sourceText}` }]);
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: `❌ Error: ${data.detail || 'Unknown error'}` }]);
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `❌ Connection error: ${e.message}` }]);
    }
    setLoading(false);
    setQuery('');
  }

  async function handleClear() {
    if (!confirm('Clear the index and start over?')) return;
    try {
      const res = await fetch('/api/proxy?endpoint=clear', { method: 'POST' });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: `🗑️ ${data.message}` }]);
      setHasIndex(false);
      setStatus({ indexedFiles: 0, indexedChunks: 0 });
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `❌ Error: ${e.message}` }]);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">🧭 Code Compass</h1>
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <span>{status.indexedFiles} files</span>
            <span>{status.indexedChunks} chunks</span>
            <span className={`px-2 py-0.5 rounded text-xs ${hasIndex ? 'bg-emerald-900/50 text-emerald-400' : 'bg-gray-800 text-gray-500'}`}>
              {hasIndex ? 'INDEXED' : 'EMPTY'}
            </span>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-2xl rounded-xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-100'
              }`}>
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">{msg.content}</pre>
              </div>
            </div>
          ))}
          <div ref={chatEnd} />
        </div>
      </div>

      <div className="border-t border-gray-800 px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-2 mb-3">
            <button
              onClick={handleIngest}
              disabled={loading}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              📂 Ingest Codebase
            </button>
            {hasIndex && (
              <button
                onClick={handleClear}
                disabled={loading}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-medium text-red-400 transition-colors disabled:opacity-50"
              >
                🗑️ Clear Index
              </button>
            )}
          </div>

          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder={hasIndex ? 'Ask about your codebase...' : 'Ingest a codebase first...'}
              disabled={loading || !hasIndex}
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !hasIndex || !query.trim()}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? '...' : '→'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
