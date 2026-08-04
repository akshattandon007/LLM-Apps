import { Trace, Skill } from "@/types";

const TRACES_KEY = "traceforge-traces";
const SKILLS_KEY = "traceforge-skills";

function read<T>(key: string): T[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function write<T>(key: string, data: T[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(key, JSON.stringify(data));
}

export function getTraces(): Trace[] {
  return read<Trace>(TRACES_KEY);
}

export function getTrace(id: string): Trace | undefined {
  return read<Trace>(TRACES_KEY).find((t) => t.id === id);
}

export function saveTrace(trace: Trace): void {
  const traces = read<Trace>(TRACES_KEY);
  const idx = traces.findIndex((t) => t.id === trace.id);
  if (idx >= 0) traces[idx] = trace;
  else traces.push(trace);
  write(TRACES_KEY, traces);
}

export function updateTrace(id: string, patch: Partial<Trace>): void {
  const traces = read<Trace>(TRACES_KEY);
  const idx = traces.findIndex((t) => t.id === id);
  if (idx >= 0) {
    traces[idx] = { ...traces[idx], ...patch };
    write(TRACES_KEY, traces);
  }
}

export function getSkills(): Skill[] {
  return read<Skill>(SKILLS_KEY);
}

export function getSkill(id: string): Skill | undefined {
  return read<Skill>(SKILLS_KEY).find((s) => s.id === id);
}

export function saveSkill(skill: Skill): void {
  const skills = read<Skill>(SKILLS_KEY);
  const idx = skills.findIndex((s) => s.id === skill.id);
  if (idx >= 0) skills[idx] = skill;
  else skills.push(skill);
  write(SKILLS_KEY, skills);
}