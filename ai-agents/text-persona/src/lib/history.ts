export interface HistoryItem {
  id: string;
  personaId: string;
  personaName: string;
  personaEmoji: string;
  original: string;
  rewritten: string;
  timestamp: number;
}

const HISTORY_KEY = "textpersona-history";
const MAX_ITEMS = 50;

export function loadHistory(): HistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as HistoryItem[];
  } catch {
    return [];
  }
}

export function saveHistory(items: HistoryItem[]): void {
  if (typeof window === "undefined") return;
  try {
    const trimmed = items.slice(0, MAX_ITEMS);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmed));
  } catch {
    // localStorage full or unavailable — silently drop
  }
}

export function addHistoryItem(item: HistoryItem): HistoryItem[] {
  const history = loadHistory();
  const updated = [item, ...history];
  saveHistory(updated);
  return updated;
}

export function clearHistory(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(HISTORY_KEY);
}

export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}
