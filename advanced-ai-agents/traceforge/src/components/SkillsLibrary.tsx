import { useState } from "react";
import { Skill } from "@/types";

export default function SkillsLibrary({ skills }: { skills: Skill[] }) {
  const [selected, setSelected] = useState<Skill | null>(null);

  if (skills.length === 0) {
    return (
      <div className="text-center py-8 opacity-50">
        <p className="text-lg">No skills yet</p>
        <p className="text-sm mt-1">
          Mark traces as Good and analyze them to extract skills
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">
        Skills Library ({skills.length})
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {skills.map((s) => (
          <div
            key={s.id}
            onClick={() => setSelected(s)}
            className="card bg-base-200 shadow-sm cursor-pointer hover:shadow-md transition-all"
          >
            <div className="card-body p-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm">{s.name}</h3>
                <span className="badge badge-sm">v{s.version}</span>
              </div>
              <p className="text-xs opacity-70 mt-1 line-clamp-2">
                {s.description}
              </p>
              <div className="flex items-center gap-1 mt-2">
                {s.spec.toolChain.map((t) => (
                  <span key={t} className="badge badge-sm badge-outline">
                    {t}
                  </span>
                ))}
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs opacity-40">
                  from: {s.sourceTraceTask.slice(0, 30)}...
                </span>
                {s.verified && (
                  <span className="badge badge-sm badge-success gap-1">
                    ✓ Verified
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Skill Detail Modal */}
      {selected && (
        <div className="modal modal-open" onClick={() => setSelected(null)}>
          <div
            className="modal-box max-w-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-bold">{selected.name}</h3>
            <span className="badge badge-sm ml-2">v{selected.version}</span>

            <p className="text-sm mt-3 opacity-70">{selected.description}</p>

            <div className="mt-4 space-y-3">
              <div>
                <h4 className="text-xs font-semibold uppercase opacity-50">
                  Tool Chain
                </h4>
                <div className="flex flex-wrap gap-1 mt-1">
                  {selected.spec.toolChain.map((t) => (
                    <span key={t} className="badge badge-sm badge-primary">
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase opacity-50">
                  Decision Logic
                </h4>
                <p className="text-sm mt-1 bg-base-300 p-2 rounded">
                  {selected.spec.decisionLogic}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase opacity-50">
                  Verifier Rule
                </h4>
                <p className="text-sm mt-1 bg-base-300 p-2 rounded font-mono">
                  {selected.spec.verifierRule}
                </p>
              </div>

              <div className="text-xs opacity-40">
                Source: {selected.sourceTraceTask}
              </div>
            </div>

            <div className="modal-action">
              <button
                className="btn btn-sm"
                onClick={() => setSelected(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}