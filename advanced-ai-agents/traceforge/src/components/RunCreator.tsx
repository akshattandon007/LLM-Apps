import { useState } from "react";
import { Trace, TraceStep } from "@/types";
import { v4 as uuidv4 } from "uuid";

export default function RunCreator({
  onTraceCreated,
}: {
  onTraceCreated: (trace: Trace) => void;
}) {
  const [task, setTask] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const handleRun = async () => {
    if (!task.trim()) return;
    setRunning(true);
    setError("");

    const traceId = uuidv4();
    const startTime = Date.now();

    const trace: Trace = {
      id: traceId,
      agentName: "TraceForge Agent",
      task: task.trim(),
      status: "running",
      duration: 0,
      createdAt: startTime,
      steps: [
        {
          id: `step-${Date.now()}-prompt`,
          timestamp: startTime,
          type: "prompt",
          content: task.trim(),
        },
      ],
      curation: null,
    };

    onTraceCreated(trace);

    try {
      const res = await fetch("/api/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: task.trim() }),
      });

      const data = await res.json();
      const endTime = Date.now();

      const steps: TraceStep[] = [
        {
          id: `step-${startTime}-prompt`,
          timestamp: startTime,
          type: "prompt",
          content: task.trim(),
        },
      ];

      if (data.steps?.length) {
        data.steps.forEach((s: TraceStep) => steps.push(s));
      } else if (data.answer) {
        steps.push({
          id: `step-${endTime}-answer`,
          timestamp: endTime,
          type: "answer",
          content: data.answer,
        });
      }

      if (data.error) {
        steps.push({
          id: `step-${endTime}-error`,
          timestamp: endTime,
          type: "error",
          content: data.error,
        });
      }

      const updated: Trace = {
        ...trace,
        status: data.error ? "error" : "success",
        duration: endTime - startTime,
        steps,
      };

      onTraceCreated(updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Request failed";
      const endTime = Date.now();
      const updated: Trace = {
        ...trace,
        status: "error",
        duration: endTime - startTime,
        steps: [
          ...trace.steps,
          {
            id: `step-${endTime}-error`,
            timestamp: endTime,
            type: "error",
            content: msg,
          },
        ],
      };
      onTraceCreated(updated);
    } finally {
      setRunning(false);
      setTask("");
    }
  };

  return (
    <div className="card bg-base-200 shadow-sm mb-6">
      <div className="card-body p-4">
        <h2 className="text-lg font-semibold mb-2">Run Agent</h2>
        <textarea
          className="textarea textarea-bordered w-full"
          rows={3}
          placeholder="Type a task for the agent... (e.g., 'Search for the latest AI research papers on arxiv')"
          value={task}
          onChange={(e) => setTask(e.target.value)}
          disabled={running}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleRun();
            }
          }}
        />
        {error && <p className="text-error text-sm mt-2">{error}</p>}
        <div className="card-actions mt-3">
          <button
            className="btn btn-primary"
            onClick={handleRun}
            disabled={running || !task.trim()}
          >
            {running ? (
              <>
                <span className="loading loading-spinner loading-sm"></span>
                Running...
              </>
            ) : (
              "Run"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}