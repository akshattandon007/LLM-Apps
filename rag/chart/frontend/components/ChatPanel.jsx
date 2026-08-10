import { useState } from 'react';
import AnswerCard from './AnswerCard';

export default function ChatPanel() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const askQuestion = async (e) => {
    e?.preventDefault();
    if (!question.trim()) return;

    const q = question.trim();
    setMessages(prev => [...prev, { role: 'user', text: q }]);
    setQuestion('');
    setLoading(true);

    try {
      const resp = await fetch('/api/proxy/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, top_k: 5 }),
      });
      const data = await resp.json();
      setMessages(prev => [...prev, { role: 'assistant', data }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', data: { answer: `Error: ${err.message}`, confidence: 'LOW' } }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-3">Ask about your health records</h2>
      <div className="mb-4 max-h-96 overflow-y-auto space-y-3">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400 italic">
            Try asking: "What was my HbA1c in March 2023?" or "How has my LDL changed?"
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === 'user' ? (
              <div className="bg-blue-50 rounded-lg p-3 text-sm text-gray-800">
                <span className="font-medium text-blue-600">You:</span> {msg.text}
              </div>
            ) : (
              <AnswerCard answer={msg.data} />
            )}
          </div>
        ))}
        {loading && (
          <div className="text-sm text-gray-400 italic">Thinking...</div>
        )}
      </div>
      <form onSubmit={askQuestion} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about your medical records..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()} className="btn-primary">
          Ask
        </button>
      </form>
    </div>
  );
}