import { useEffect, useState, useCallback } from "react";
import { Trace, Skill, CurationVerdict } from "@/types";
import { getTraces, saveTrace, getSkills, saveSkill, updateTrace } from "@/lib/storage";
import { v4 as uuidv4 } from "uuid";
import Layout from "@/components/Layout";
import Dashboard from "@/components/Dashboard";
import RunCreator from "@/components/RunCreator";
import TraceViewer from "@/components/TraceViewer";
import SkillsLibrary from "@/components/SkillsLibrary";

export default function Home() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [tab, setTab] = useState<"traces" | "skills">("traces");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setTraces(getTraces().sort((a, b) => b.createdAt - a.createdAt));
    setSkills(getSkills().sort((a, b) => b.createdAt - a.createdAt));
    setMounted(true);
  }, []);

  const handleTraceCreated = useCallback((trace: Trace) => {
    saveTrace(trace);
    setTraces((prev) => {
      const idx = prev.findIndex((t) => t.id === trace.id);
      if (idx >= 0) {
        const copy = [...prev];
        copy[idx] = trace;
        return copy;
      }
      return [trace, ...prev];
    });
    setSelectedTraceId(trace.id);
  }, []);

  const handleCurationChange = useCallback(
    (verdict: CurationVerdict) => {
      setTraces((prev) =>
        prev.map((t) =>
          t.id === selectedTraceId ? { ...t, curation: verdict } : t
        )
      );
    },
    [selectedTraceId]
  );

  const handleAnalyze = useCallback(async () => {
    const trace = traces.find((t) => t.id === selectedTraceId);
    if (!trace || trace.curation !== "good") return;

    setAnalyzing(true);
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          trace: {
            task: trace.task,
            steps: trace.steps.map((s) => ({
              type: s.type,
              content: s.content,
              metadata: s.metadata,
            })),
          },
        }),
      });

      const data = await res.json();

      if (data.skill) {
        const skill: Skill = {
          id: uuidv4(),
          name: data.skill.name,
          description: data.skill.description,
          version: data.skill.version,
          sourceTraceId: trace.id,
          sourceTraceTask: trace.task,
          spec: {
            toolChain: data.skill.toolChain,
            decisionLogic: data.skill.decisionLogic,
            verifierRule: data.skill.verifierRule,
          },
          createdAt: Date.now(),
          verified: true,
        };

        saveSkill(skill);
        setSkills((prev) => [skill, ...prev]);
        updateTrace(trace.id, { analyzed: true });
        setTraces((prev) =>
          prev.map((t) => (t.id === trace.id ? { ...t, analyzed: true } : t))
        );
      } else {
        alert(data.reason || "No pattern found in this trace");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Analysis failed";
      alert("Analysis failed: " + msg);
    } finally {
      setAnalyzing(false);
    }
  }, [traces, selectedTraceId]);

  const selectedTrace = traces.find((t) => t.id === selectedTraceId) || null;

  if (!mounted) return null;

  return (
    <Layout>
      <div className="tabs tabs-box mb-6">
        <button
          className={`tab ${tab === "traces" ? "tab-active" : ""}`}
          onClick={() => setTab("traces")}
        >
          Traces ({traces.length})
        </button>
        <button
          className={`tab ${tab === "skills" ? "tab-active" : ""}`}
          onClick={() => setTab("skills")}
        >
          Skills ({skills.length})
        </button>
      </div>

      {tab === "traces" && (
        <>
          <RunCreator onTraceCreated={handleTraceCreated} />

          {selectedTrace && (
            <div className="mb-6">
              <TraceViewer
                trace={selectedTrace}
                onClose={() => setSelectedTraceId(null)}
                onCurationChange={handleCurationChange}
                onAnalyze={handleAnalyze}
              />
              {analyzing && (
                <div className="flex items-center gap-2 mt-3 text-sm opacity-70">
                  <span className="loading loading-spinner loading-sm"></span>
                  Analyzing trace with LLM judge...
                </div>
              )}
            </div>
          )}

          <Dashboard
            traces={traces}
            onSelect={(t) => setSelectedTraceId(t.id)}
            selectedId={selectedTraceId}
          />
        </>
      )}

      {tab === "skills" && <SkillsLibrary skills={skills} />}
    </Layout>
  );
}