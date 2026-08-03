import { HistoryItem } from "@/lib/history";

interface HistorySidebarProps {
  open: boolean;
  onClose: () => void;
  history: HistoryItem[];
  onClear: () => void;
  onSelect: (item: HistoryItem) => void;
}

export default function HistorySidebar({
  open,
  onClose,
  history,
  onClear,
  onSelect,
}: HistorySidebarProps) {
  return (
    <>
      {/* Overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 right-0 h-full w-80 max-w-[85vw] bg-base-100 border-l border-base-300
          z-50 transform transition-transform duration-300 ease-in-out overflow-y-auto
          ${open ? "translate-x-0" : "translate-x-full"}
        `}
      >
        <div className="sticky top-0 bg-base-100 z-10 border-b border-base-300 p-4 flex items-center justify-between">
          <h2 className="text-lg font-bold">📜 History</h2>
          <button className="btn btn-ghost btn-sm btn-circle" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="p-4">
          {history.length === 0 ? (
            <div className="text-center text-base-content/50 py-12">
              <p className="text-4xl mb-3">🕰️</p>
              <p className="text-sm">No rewrites yet.</p>
              <p className="text-xs mt-1">Your recent rewrites will appear here.</p>
            </div>
          ) : (
            <>
              {history.map((item) => (
                <div
                  key={item.id}
                  className="card bg-base-200 border border-base-300 mb-3 cursor-pointer hover:border-primary/50 transition-colors"
                  onClick={() => onSelect(item)}
                >
                  <div className="p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <span>{item.personaEmoji}</span>
                      <span className="text-sm font-semibold">
                        {item.personaName}
                      </span>
                      <span className="text-xs text-base-content/40 ml-auto">
                        {new Date(item.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                    <p className="text-xs text-base-content/50 line-clamp-1 mb-1">
                      {item.original}
                    </p>
                    <p className="text-sm line-clamp-2 font-medium">
                      {item.rewritten}
                    </p>
                  </div>
                </div>
              ))}
              <button
                className="btn btn-ghost btn-sm text-error w-full"
                onClick={onClear}
              >
                Clear All History
              </button>
            </>
          )}
        </div>
      </aside>
    </>
  );
}