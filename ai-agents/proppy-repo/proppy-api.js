// ── Proppy API — calls Anthropic directly from the extension ─────────────────

const ANTHROPIC_URL = "https://api.anthropic.com/v1/messages";
const MODEL = "claude-sonnet-4-5";  // reliable, fast, supports web search

const PROPPY_SYSTEM = `You are Proppy 🏡 — a hilariously enthusiastic but genuinely brilliant AI property agent.
Your personality: warm, witty, slightly chaotic, fiercely dedicated.

YOUR MAIN JOB:
1. Gather info naturally, one or two questions at a time.
   Collect: location, budget (min/max), property type, ownership (buy/rent/shared ownership),
   bedrooms, must-have features (garden, parking, new build, period etc), commute needs, pets, EPC rating.

2. Once you have at minimum location + budget, search the web for real listings.

3. ALWAYS respond with raw JSON only — no markdown fences, no preamble.

RESPONSE FORMAT — always this exact structure:
{
  "text": "Your witty message here",
  "listings": [
    {
      "title": "3 bed semi in Hackney",
      "price": "£450,000",
      "address": "123 Example St, London E8",
      "details": "3 bed | 1 bath | Garden | EPC C",
      "url": "https://www.rightmove.co.uk/properties/12345",
      "source": "Rightmove"
    }
  ],
  "prefs_update": {},
  "stage": "gathering"
}

stages: gathering → searching → done
listings is [] when just chatting.
prefs_update contains any preferences you extracted from the conversation.

SEARCH: Use web search to find listings on Rightmove, Zoopla, OnTheMarket, PrimeLocation.
Include direct property page URLs. Apply all user filters. Return 3-8 listings.

TONE: Witty, warm, slightly unhinged about property. Never boring. Always useful.`;

const SEARCH_SYSTEM = `You are a property search engine. Search the web for real current listings.
Return ONLY raw JSON, no markdown, no preamble:
{
  "listings": [
    {
      "title": "string",
      "price": "string",
      "address": "string",
      "details": "beds, baths, key features",
      "url": "direct URL to listing page",
      "source": "website name"
    }
  ],
  "summary": "one-line summary"
}
Search Rightmove, Zoopla, OnTheMarket, PrimeLocation. Return 3-8 real results.`;

// ── Sanitise API key ──────────────────────────────────────────────────────────

function cleanKey(key) {
  // Remove invisible chars, BOM, zero-width spaces, newlines that appear in copy-paste
  return (key || "").replace(/[\u200B-\u200D\uFEFF\u00A0\r\n\t]/g, "").trim();
}

function validateKey(key) {
  const k = cleanKey(key);
  if (!k) throw new Error("No API key found — add it in the Config tab ⚙️");
  if (!k.startsWith("sk-")) throw new Error("Key should start with 'sk-' — check Config tab ⚙️");
  return k;
}

// ── Core API call ─────────────────────────────────────────────────────────────

async function callAnthropic({ apiKey, system, messages, useWebSearch = true, maxTokens = 2048 }) {
  const key = validateKey(apiKey);

  const body = {
    model: MODEL,
    max_tokens: maxTokens,
    system,
    messages,
  };

  // Add web search tool when needed
  if (useWebSearch) {
    body.tools = [{ type: "web_search_20250305", name: "web_search" }];
  }

  const headers = {
    "Content-Type": "application/json",
    "x-api-key": key,
    "anthropic-version": "2023-06-01",
    "anthropic-dangerous-direct-browser-access": "true",
  };

  // Only add beta header when using web search
  if (useWebSearch) {
    headers["anthropic-beta"] = "web-search-2025-03-05";
  }

  let res;
  try {
    res = await fetch(ANTHROPIC_URL, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
  } catch (networkErr) {
    throw new Error(`Network error — check your internet connection. (${networkErr.message})`);
  }

  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error(`Bad response from Anthropic (status ${res.status})`);
  }

  if (!res.ok) {
    const errType = data?.error?.type || "";
    const errMsg  = data?.error?.message || `HTTP ${res.status}`;
    if (res.status === 401 || errType === "authentication_error") {
      throw new Error("Invalid API key — double-check it in Config tab ⚙️");
    }
    if (res.status === 429) throw new Error("Rate limit — give Proppy a moment! ☕");
    if (res.status === 400) throw new Error(`API error: ${errMsg}`);
    throw new Error(`Anthropic error ${res.status}: ${errMsg}`);
  }

  // Collect all text blocks (Claude may interleave tool use and text)
  const text = (data.content || [])
    .filter(b => b.type === "text")
    .map(b => b.text)
    .join("");

  return parseProppyResponse(text);
}

// ── Parse Claude's JSON response ──────────────────────────────────────────────

function parseProppyResponse(raw) {
  if (!raw) return { text: "Hmm, I got nothing back. Try again?", listings: [], prefs_update: {}, stage: "gathering" };

  // Strip markdown fences if present
  const cleaned = raw.trim()
    .replace(/^```json\s*/i, "")
    .replace(/^```\s*/i, "")
    .replace(/```\s*$/i, "")
    .trim();

  try {
    return JSON.parse(cleaned);
  } catch (_) {
    // Find first { ... } block
    const match = cleaned.match(/\{[\s\S]*\}/);
    if (match) {
      try { return JSON.parse(match[0]); } catch (_) {}
    }
    // Fallback: treat as plain text
    return { text: raw, listings: [], prefs_update: {}, stage: "gathering" };
  }
}

// ── Preference summary ────────────────────────────────────────────────────────

function prefsToText(prefs) {
  const p = [];
  if (prefs.location)              p.push(`Location: ${prefs.location}`);
  if (prefs.budgetMin || prefs.budgetMax)
    p.push(`Budget: £${prefs.budgetMin || 0}–£${prefs.budgetMax || "any"}`);
  if (prefs.types?.length)         p.push(`Type: ${prefs.types.join(", ")}`);
  if (prefs.ownership?.length)     p.push(`Ownership: ${prefs.ownership.join(", ")}`);
  if (prefs.bedsMin || prefs.bedsMax)
    p.push(`Bedrooms: ${prefs.bedsMin || "any"}–${prefs.bedsMax || "any"}`);
  if (prefs.features?.length)      p.push(`Must have: ${prefs.features.join(", ")}`);
  if (prefs.commute)               p.push(`Max commute: ${prefs.commute} mins`);
  return p.length ? p.join("\n") : "No preferences set yet.";
}

// ── Public: chat ──────────────────────────────────────────────────────────────

async function proppyChat({ apiKey, message, history = [], preferences = {} }) {
  const system = PROPPY_SYSTEM + `\n\nCURRENT USER PREFERENCES:\n${prefsToText(preferences)}`;
  const messages = [
    ...history.slice(-20).filter(h => h.role === "user" || h.role === "assistant"),
    { role: "user", content: message },
  ];
  return callAnthropic({ apiKey, system, messages, useWebSearch: true });
}

// ── Public: background search ─────────────────────────────────────────────────

async function proppySearch({ apiKey, preferences = {} }) {
  const summary = prefsToText(preferences);
  if (summary === "No preferences set yet.") {
    throw new Error("Fill in your wishlist first! 📋");
  }
  const prompt = `Find property listings for:\n${summary}\nSearch Rightmove, Zoopla, OnTheMarket, PrimeLocation. Real listings, direct URLs.`;
  return callAnthropic({
    apiKey,
    system: SEARCH_SYSTEM,
    messages: [{ role: "user", content: prompt }],
    useWebSearch: true,
  });
}

// ── Public: lightweight key test (no web search, cheapest model) ──────────────

async function testApiKey(apiKey) {
  const key = validateKey(apiKey);
  const res = await fetch(ANTHROPIC_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": key,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true",
    },
    body: JSON.stringify({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 5,
      messages: [{ role: "user", content: "hi" }],
    }),
  });

  const data = await res.json().catch(() => ({}));

  if (res.status === 401 || data?.error?.type === "authentication_error") {
    throw new Error("Invalid API key");
  }
  // Any other response (200, 400, 529) means key is valid
  return true;
}

// ── Storage helpers ───────────────────────────────────────────────────────────

async function getStoredPrefs() {
  const d = await chrome.storage.local.get("prefs");
  return d.prefs || {};
}

async function getStoredConfig() {
  const d = await chrome.storage.local.get("config");
  return d.config || {};
}
