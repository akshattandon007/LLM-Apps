// templates.js — Shared storage via chrome.storage.local (synced across all sites)

const DEFAULT_TEMPLATES = [
  { id: "prd", icon: "doc", title: "PRD / Feature Spec", tags: ["product", "spec", "engineering"], builtin: true,
    prompt: "You are a senior PM at [company type]. Write a one-page feature spec for [feature name].\nInclude: Problem Statement, Target Users, Success Metrics, Proposed Solution, Out of Scope.\nAudience: engineering team. Tone: clear and direct." },
  { id: "user-research", icon: "people", title: "User Research Synthesis", tags: ["ux", "research", "interviews"], builtin: true,
    prompt: "You are a UX researcher. Below are customer interview excerpts.\nIdentify the top 3 themes, frequency of each, and a representative quote for each theme.\nFormat as a table.\n\n[Paste excerpts here]" },
  { id: "competitive", icon: "chart", title: "Competitive Analysis", tags: ["strategy", "competition", "market"], builtin: true,
    prompt: "You are a product strategist. Compare [Product A] and [Product B] across:\nTarget customer, core value prop, pricing model, key differentiators, known weaknesses.\nFormat as a comparison table. Base your answer only on the information I provide below.\n\n[Paste research here]" },
  { id: "stakeholder", icon: "envelope", title: "Stakeholder Communication", tags: ["email", "leadership", "persuasion"], builtin: true,
    prompt: "Draft an email to a skeptical VP of Engineering explaining why we're prioritizing [feature]\nover [alternative] this quarter. Lead with impact, acknowledge the trade-off, and end with\na clear ask. Keep it under 200 words." },
  { id: "rca", icon: "magnifier", title: "Root Cause Analysis", tags: ["data", "debugging", "metrics"], builtin: true,
    prompt: "Think step by step. We saw a 15% drop in [metric] between [date range].\nHere is the relevant data: [paste data].\nFirst, list possible hypotheses. Then evaluate each against the data.\nFinally, recommend the most likely root cause and next diagnostic step." }
];

// ── Sync cache — loaded once on init, written through on every change ──
const _cache = {
  "ps-templates": [],
  "ps-deleted": [],
  "ps-api-key": "",
  "ps-theme": "dark",
  "ps-pos": null,
  "ps-size": null,
  _ready: false,
  _readyCallbacks: []
};

// Load everything from chrome.storage.local into cache
function _initStorage(cb) {
  if (_cache._ready) { if (cb) cb(); return; }
  _cache._readyCallbacks.push(cb);
  if (_cache._readyCallbacks.length > 1) return; // already loading

  const keys = ["ps-templates", "ps-deleted", "ps-api-key", "ps-theme", "ps-pos", "ps-size"];
  try {
    chrome.storage.local.get(keys, (result) => {
      if (result["ps-templates"]) _cache["ps-templates"] = result["ps-templates"];
      if (result["ps-deleted"]) _cache["ps-deleted"] = result["ps-deleted"];
      if (result["ps-api-key"]) _cache["ps-api-key"] = result["ps-api-key"];
      if (result["ps-theme"]) _cache["ps-theme"] = result["ps-theme"];
      if (result["ps-pos"]) _cache["ps-pos"] = result["ps-pos"];
      if (result["ps-size"]) _cache["ps-size"] = result["ps-size"];
      _cache._ready = true;
      _cache._readyCallbacks.forEach(fn => { if (fn) fn(); });
      _cache._readyCallbacks = [];
    });
  } catch {
    // Fallback if chrome.storage not available (e.g. in preview HTML)
    _cache._ready = true;
    _cache._readyCallbacks.forEach(fn => { if (fn) fn(); });
    _cache._readyCallbacks = [];
  }
}

// Write a key to both cache and chrome.storage.local
function _store(key, value) {
  _cache[key] = value;
  try { chrome.storage.local.set({ [key]: value }); } catch {}
}

// Read from cache (sync)
function _get(key) { return _cache[key]; }

// ── Public API used by content.js ──

function loadTemplates() {
  const saved = _get("ps-templates") || [];
  const deletedIds = _get("ps-deleted") || [];
  const builtins = DEFAULT_TEMPLATES.filter(t => !deletedIds.includes(t.id));
  return [...builtins, ...saved];
}

function saveTemplate(t) {
  const saved = [...(_get("ps-templates") || [])];
  if (saved.find(x => x.id === t.id)) return;
  saved.push(t);
  _store("ps-templates", saved);
}

function deleteTemplate(id) {
  if (DEFAULT_TEMPLATES.find(t => t.id === id)) {
    const del = [...(_get("ps-deleted") || [])];
    if (!del.includes(id)) { del.push(id); _store("ps-deleted", del); }
  }
  const saved = (_get("ps-templates") || []).filter(t => t.id !== id);
  _store("ps-templates", saved);
}

function updateTemplate(id, updates) {
  const saved = [...(_get("ps-templates") || [])];
  const idx = saved.findIndex(t => t.id === id);
  if (idx >= 0) {
    saved[idx] = { ...saved[idx], ...updates };
    _store("ps-templates", saved);
  }
}

// Settings helpers
function psGet(key) { return _get(key); }
function psSet(key, value) { _store(key, value); }

// Listen for changes from other tabs/sites
try {
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local") return;
    for (const [key, { newValue }] of Object.entries(changes)) {
      if (key in _cache) _cache[key] = newValue;
    }
  });
} catch {}

// Global mutable list — will be populated after init
let PROMPT_TEMPLATES = [...DEFAULT_TEMPLATES];
