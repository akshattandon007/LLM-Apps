export default function AnswerCard({ answer }) {
  if (!answer) return null;

  const confidenceClass =
    answer.confidence === 'HIGH' ? 'confidence-high' :
    answer.confidence === 'MEDIUM' ? 'confidence-medium' : 'confidence-low';

  return (
    <div className="card border-l-4 border-l-blue-500">
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
          {answer.intent?.replace(/_/g, ' ')}
        </span>
        <span className={`text-xs font-semibold ${confidenceClass}`}>
          {answer.confidence} confidence
        </span>
      </div>

      <p className="text-gray-800 leading-relaxed whitespace-pre-wrap mb-3">
        {answer.answer}
      </p>

      {answer.citations?.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs font-medium text-gray-500 mb-1">Sources:</p>
          {answer.citations.map((c, i) => (
            <div key={i} className="text-xs text-gray-600 mb-1">
              <span className="font-medium">{c.doc_name}</span>
              {c.section && <span> — {c.section}</span>}
              {c.doc_type && <span> ({c.doc_type})</span>}
            </div>
          ))}
        </div>
      )}

      {answer.date_range && (
        <p className="text-xs text-gray-500 mt-2">
          Date range: {answer.date_range}
        </p>
      )}

      <p className="privacy-warning">{answer.privacy_warning}</p>
    </div>
  );
}