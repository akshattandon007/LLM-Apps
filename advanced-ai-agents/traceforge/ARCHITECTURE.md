# TraceForge — Architecture

## System Overview

TraceForge is a Next.js 16 (Pages Router) application with two serverless API routes and a client-side dashboard that runs entirely on your machine. There is no backend database — all state lives in the browser's `localStorage`.

```
┌─────────────────────────────────────────────────────┐
│                    Browser (Client)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Dashboard│  │  Trace   │  │  Skills Library  │  │
│  │  (list)  │  │  Viewer  │  │     (grid)       │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │              │                │             │
│  ┌────┴──────────────┴────────────────┴─────────┐   │
│  │              localStorage                     │   │
│  │  traces: TraceRecord[]   skills: SkillSpec[]  │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │  POST /api/agent
                       │  POST /api/analyze
                       ▼
┌─────────────────────────────────────────────────────┐
│              Next.js API Routes (Server)             │
│  ┌─────────────────┐  ┌────────────────────────┐   │
│  │ /api/agent      │  │ /api/analyze           │   │
│  │ Execute task,   │  │ Extract skill from     │   │
│  │ capture trace   │  │ curated good trace     │   │
│  └────────┬────────┘  └───────────┬────────────┘   │
│           │                        │                │
│           ▼                        ▼                │
│  ┌─────────────────────────────────────────────┐    │
│  │        OpenRouter (chat completions)         │    │
│  │  OPENROUTER_API_KEY from env                 │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Data Model

### TraceRecord

```typescript
interface TraceRecord {
  id: string;                    // UUID v4
  agentName: string;             // e.g. "research-agent"
  status: "running" | "success" | "failed";
  task: string;                  // The user's input task
  startedAt: number;             // Unix timestamp ms
  finishedAt: number | null;
  duration: number | null;       // ms
  curated: "good" | "bad" | null;
  steps: TraceStep[];
}

type TraceStep =
  | { type: "prompt"; content: string; timestamp: number }
  | { type: "tool_call"; tool: string; args: Record<string, unknown>; timestamp: number }
  | { type: "tool_output"; tool: string; output: string; timestamp: number }
  | { type: "reasoning"; content: string; timestamp: number }
  | { type: "final_answer"; content: string; timestamp: number }
  | { type: "error"; message: string; timestamp: number };
```

### SkillSpec

```typescript
interface SkillSpec {
  id: string;                    // UUID v4
  sourceTraceId: string;         // The good trace this was extracted from
  name: string;                  // Generated skill name
  description: string;           // One-line summary
  version: number;               // Integer, auto-incremented
  toolChain: string[];           // Ordered list of tool names
  decisionLogic: string;         // Natural language decision rules
  safetyVerifier: string;        // Pre-execution validation rule
  extractedAt: number;           // Unix timestamp ms
}
```

## Trace Capture Pipeline

1. **User submits a task** via the Run Creator (`pages/index.tsx`)
2. **Client POSTs to `/api/agent`** with `{ task, agentName }`
3. **Server calls OpenRouter** with function calling enabled, sending the task and available tool definitions
4. **Streaming capture**: As the LLM responds, each function call, function result, and text chunk is timestamped and appended to the trace
5. **The completed trace** (all steps + final answer + duration) is returned to the client
6. **Client saves** the `TraceRecord` to `localStorage.traces` and the dashboard re-renders

The API route is at `pages/api/agent.ts`. It uses the OpenRouter chat completions endpoint (`https://openrouter.ai/api/v1/chat/completions`) with the key from `process.env.OPENROUTER_API_KEY`.

## Skill Extraction Pipeline (The "Forge")

1. **User marks a trace as "good"** in the Trace Viewer
2. **User clicks "Forge Skill"** on a curated-good trace
3. **Client POSTs to `/api/analyze`** with the full `TraceRecord`
4. **Server formats an extraction prompt** that includes:
   - The task the agent was given
   - The full sequence of tool calls and outputs
   - The reasoning steps
   - Instructions to extract: skill name, description, tool chain, decision logic, safety verifier
5. **OpenRouter returns a structured JSON** with the extracted skill
6. **Client creates a `SkillSpec`**, assigns version 1 (or increments if same name exists), links back to the source trace, and saves to `localStorage.skills`

The API route is at `pages/api/analyze.ts`.

## LLM-as-Judge Prompt Design

The extraction prompt used by `/api/analyze`:

```
You are a skill extraction engine. Analyze this agent execution trace and extract a reusable sub-skill.

Output ONLY valid JSON with these fields:
- name: A short, memorable skill name
- description: One sentence describing what this pattern accomplishes
- toolChain: Ordered list of tool names used in the successful pattern
- decisionLogic: The key decision rules the agent followed (when to call which tool, how to handle ambiguity)
- safetyVerifier: A rule that can be checked before execution to ensure the skill is being applied correctly

The trace shows: [task description]
Steps: [full trace steps]
```

## Component Tree

```
pages/
├── index.tsx              # Dashboard — main entry, tabbed layout
│   ├── <Layout>           # App shell (header, dark mode toggle)
│   ├── <RunCreator>       # Task input + Run button
│   ├── <TraceDashboard>   # Grid of trace cards
│   │   └── <TraceCard>    # Single trace: status badge, duration, actions
│   ├── <TraceViewer>      # Modal/panel: collapsible timeline
│   │   └── <TraceStep>    # Single step with type icon + content
│   ├── <CurationBar>      # Good/Bad toggle + Forge Skill button
│   └── <SkillsLibrary>    # Grid of extracted skill cards
│       └── <SkillCard>    # Skill name, description, version, source link
│
└── api/
    ├── agent.ts           # POST — executes agent task, returns trace
    └── analyze.ts         # POST — extracts skill from trace
```

## Storage Strategy

All data lives in `localStorage` under two keys:

- `traces`: `TraceRecord[]` — persisted array of all execution traces
- `skills`: `SkillSpec[]` — persisted array of all extracted skills

A custom `useLocalStorage<T>(key)` hook handles serialization/deserialization and provides React state that syncs to localStorage on every update. No backend database, no server state — the app is fully portable and works offline after initial load.
