export type TraceStatus = "running" | "success" | "error";

export type CurationVerdict = "good" | "bad" | null;

export interface TraceStep {
  id: string;
  timestamp: number;
  type: "prompt" | "tool_call" | "tool_output" | "reasoning" | "answer" | "error";
  content: string;
  metadata?: Record<string, unknown>;
}

export interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
}

export interface Trace {
  id: string;
  agentName: string;
  task: string;
  status: TraceStatus;
  duration: number;
  createdAt: number;
  steps: TraceStep[];
  curation: CurationVerdict;
  analyzed?: boolean;
}

export interface SkillSpec {
  toolChain: string[];
  decisionLogic: string;
  verifierRule: string;
}

export interface Skill {
  id: string;
  name: string;
  description: string;
  version: number;
  sourceTraceId: string;
  sourceTraceTask: string;
  spec: SkillSpec;
  createdAt: number;
  verified: boolean;
}