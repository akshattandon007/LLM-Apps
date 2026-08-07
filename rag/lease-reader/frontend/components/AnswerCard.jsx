import React from "react";

export default function AnswerCard({ answer }) {
  if (!answer) return null;

  const { answer: answerText, domain, cited_clauses, caveat } = answer;

  return (
    <div className="answer-card">
      {/* Domain badge */}
      <div className="flex items-center gap-2 mb-3">
        <span className={`domain-badge ${domain}`}>{domain}</span>
        <span className="text-xs text-gray-400">Legal domain</span>
      </div>

      {/* Answer text */}
      <div className="answer-text">
        {answerText.split("\n").map((line, i) => (
          <p key={i} className={line.startsWith("**") ? "font-semibold mt-2" : "mt-1"}>
            {line}
          </p>
        ))}
      </div>

      {/* Cited clauses */}
      {cited_clauses && cited_clauses.length > 0 && (
        <div className="mb-3">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Cited Clauses
          </h4>
          {cited_clauses.map((clause, i) => (
            <div key={i} className="clause-citation">
              <span className="font-medium text-gray-700">
                {clause.clause_ref} — Page {clause.page_number}
              </span>
              <p className="mt-1 text-gray-500">{clause.text}</p>
            </div>
          ))}
        </div>
      )}

      {/* Caveat */}
      {caveat && (
        <div className="caveat-box">
          <span className="font-semibold">⚠️ Caveat: </span>
          {caveat}
        </div>
      )}
    </div>
  );
}