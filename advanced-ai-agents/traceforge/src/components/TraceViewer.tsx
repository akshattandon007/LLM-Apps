import { useState } from "react";
import { Trace, CurationVerdict } from "@/types";
import { updateTrace } from "@/lib/storage";

const stepIcons: Record<string, string> = {
  prompt: "💬",
  tool_call: "🔧",
  tool_output: "📤",
  reasoning: "🧠",
  answer: "✅",
  error: "❌",
};

const stepLabels: Record<string, string> = {
  prompt: "Prompt",
  tool_call: "Tool Call",
  tool_output: "Tool Output",
  reasoning: "Reasoning",
  answer: "Answer",
  error: "Error",
};

export default function TraceViewer({
  trace,
  onClose,
  onCurationChange,
  onAnalyze,
}: {
  trace: Trace;
  onClose: () => void;
  onCurationChange: (verdict: CurationVerdict) => void;
  onAnalyze: () => void;
}) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const toggle = (id: string) =>
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));

  const handleCuration = (verdict: CurationVerdict) => {
    updateTrace(trace.id, { curation: verdict });
    onCurationChange(verdict);
  };

  return (
    <div className="card bg-base-200 shadow-sm">
      <div className="card-body p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Trace Detail</h2>
          <button className="btn btn-sm btn-ghost" onClick={onClose}>
            ✕ Close
          </button>
        </div>

        <div className="text-sm opacity-70 mt-1">
          <span className="font-medium">Task:</span> {trace.task}
        </div>
        <div className="flex items-center gap-2 text-xs opacity-50 mt-1">
          <span>{trace.agentName}</span>
          <span>·</span>
          <span>{new Date(trace.createdAt).toLocaleString()}</span>
          <span>·</span>
          <span>{trace.steps.length} steps</span>
        </div>

        {/* Curation */}
        <div className="flex items-center gap-2 mt-3">
          <span className="text-sm font-medium">Curation:</span>
          <button
            className={`btn btn-xs ${trace.curation === "good" ? "btn-success" : "btn-outline"}`}
            onClick={() => handleCuration("good")}
          >
            ✓ Good
          </button>
          <button
            className={`btn btn-xs ${trace.curation === "bad" ? "btn-error" : "btn-outline"}`}
            onClick={() => handleCuration("bad")}
          >
            ✗ Bad
          </button>
          {trace.curation === "good" && !trace.analyzed && (
            <button className="btn btn-xs btn-primary ml-2" onClick={onAnalyze}>
              🔬 Analyze
            </button>
          )}
          {trace.analyzed && (
            <span className="badge badge-sm badge-info">Analyzed</span>
          )}
        </div>

        {/* Timeline */}
        <div className="mt-4">
          <h3 className="text-sm font-semibold mb-3">Execution Timeline</h3>
          <div className="space-y-2">
            {trace.steps.map((step, i) => {
              const isError = step.type === "error";
              const isOpen = expanded[step.id] ?? false;

              return (
                <div
                  key={step.id}
                  className={`border rounded-lg overflow-hidden ${
                    isError ? "border-error bg-error/5" : "border-base-300"
                  }`}
                >
                  <button
                    onClick={() => toggle(step.id)}
                    className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-base-300/50 transition-colors"
                  >
                    <span className="text-lg">{stepIcons[step.type] || "•"}</span>
                    <span className="text-sm font-medium flex-1">
                      {stepLabels[step.type] || step.type}
                    </span>
                    <span className="text-xs opacity-40">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="text-xs">{isOpen ? "▲" : "▼"}</span>
                  </button>
                  {isOpen && (
                    <div
                      className={`px-4 pb-3 pt-1 text-sm font-mono whitespace-pre-wrap ${
                        isError ? "text-error" : ""
                      }`}
                    >
                      {step.metadata ? (
                        <div>
                          <div className="opacity-70 mb-1">
                            Tool: {step.metadata.name as string}
                          </div>
                          <div>Arguments:</div>
                          <pre className="bg-base-300 p-2 rounded text-xs mt-1 overflow-x-auto">
                            {JSON.stringify(step.metadata.arguments, null, 2)}
                          </pre>
                        </div>
                      ) : (
                        step.content
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}