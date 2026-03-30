// templates.js — Default templates + user saved templates via localStorage

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

function loadTemplates() {
  try {
    const saved = JSON.parse(localStorage.getItem("ps-templates") || "[]");
    const deletedIds = JSON.parse(localStorage.getItem("ps-deleted") || "[]");
    const builtins = DEFAULT_TEMPLATES.filter(t => !deletedIds.includes(t.id));
    return [...builtins, ...saved];
  } catch { return [...DEFAULT_TEMPLATES]; }
}

function saveTemplate(t) {
  try {
    const saved = JSON.parse(localStorage.getItem("ps-templates") || "[]");
    if (saved.find(x => x.id === t.id)) return;
    saved.push(t);
    localStorage.setItem("ps-templates", JSON.stringify(saved));
  } catch {}
}

function deleteTemplate(id) {
  try {
    // If builtin, add to deleted list
    if (DEFAULT_TEMPLATES.find(t => t.id === id)) {
      const del = JSON.parse(localStorage.getItem("ps-deleted") || "[]");
      if (!del.includes(id)) { del.push(id); localStorage.setItem("ps-deleted", JSON.stringify(del)); }
    }
    // If saved/user, remove from saved
    const saved = JSON.parse(localStorage.getItem("ps-templates") || "[]");
    localStorage.setItem("ps-templates", JSON.stringify(saved.filter(t => t.id !== id)));
  } catch {}
}

// Global mutable list
let PROMPT_TEMPLATES = loadTemplates();
