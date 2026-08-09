export default function AnswerCard({ source }) {
  const speakerColors = {
    'Sarah': 'bg-pink-100 text-pink-700',
    'Mike': 'bg-blue-100 text-blue-700',
    'Alex': 'bg-green-100 text-green-700',
    'Priya': 'bg-purple-100 text-purple-700',
  };

  const badgeClass = speakerColors[source.speaker] || 'bg-gray-100 text-gray-700';

  return (
    <div className="flex items-start gap-2 p-2 bg-gray-50 rounded-lg text-xs">
      {/* Speaker badge */}
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full font-medium shrink-0 ${badgeClass}`}>
        {source.speaker}
      </span>
      
      <div className="min-w-0">
        <p className="text-gray-700">{source.text}</p>
        <div className="flex items-center gap-2 mt-1 text-gray-400">
          {source.timestamp && (
            <span>⏱ {source.timestamp}</span>
          )}
          {source.meeting && (
            <span>📋 {source.meeting}</span>
          )}
          {source.score !== undefined && (
            <span className="text-gray-300">score: {source.score.toFixed(2)}</span>
          )}
        </div>
      </div>
    </div>
  );
}