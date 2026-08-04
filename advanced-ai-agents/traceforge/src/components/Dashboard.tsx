import { Trace } from "@/types";

const statusColors: Record<string, string> = {
  success: "badge-success",
  error: "badge-error",
  running: "badge-warning",
};

const statusLabels: Record<string, string> = {
  success: "Success",
  error: "Failed",
  running: "Running",
};

export default function Dashboard({
  traces,
  onSelect,
  selectedId,
}: {
  traces: Trace[];
  onSelect: (t: Trace) => void;
  selectedId: string | null;
}) {
  if (traces.length === 0) {
    return (
      <div className="text-center py-12 opacity-50">
        <p className="text-lg">No traces yet</p>
        <p className="text-sm mt-1">Create a run to get started</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Recent Traces</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {traces.map((t) => (
          <div
            key={t.id}
            onClick={() => onSelect(t)}
            className={`card bg-base-200 shadow-sm cursor-pointer hover:shadow-md transition-all border-2 ${
              selectedId === t.id ? "border-primary" : "border-transparent"
            }`}
          >
            <div className="card-body p-4">
              <div className="flex items-center justify-between">
                <span className={`badge badge-sm ${statusColors[t.status]}`}>
                  {statusLabels[t.status]}
                </span>
                {t.curation === "good" && (
                  <span className="badge badge-sm badge-success">Good</span>
                )}
                {t.curation === "bad" && (
                  <span className="badge badge-sm badge-error">Bad</span>
                )}
              </div>
              <p className="text-sm mt-2 line-clamp-2">{t.task}</p>
              <div className="flex items-center justify-between mt-2 text-xs opacity-50">
                <span>{t.agentName}</span>
                <span>{formatDuration(t.duration)}</span>
              </div>
              <div className="text-xs opacity-40 mt-1">
                {new Date(t.createdAt).toLocaleString()}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}