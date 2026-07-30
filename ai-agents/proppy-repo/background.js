importScripts("proppy-api.js");

const DEFAULT_INTERVAL = 720;

chrome.runtime.onInstalled.addListener(async () => { await setupAlarm(); });
chrome.runtime.onStartup.addListener(async () => { await setupAlarm(); await runSearch("startup"); });
chrome.alarms.onAlarm.addListener(async alarm => { if (alarm.name === "proppy-search") await runSearch("alarm"); });

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {

  if (msg.type === "UPDATE_ALARM") {
    setupAlarm(msg.interval);
    sendResponse({ ok: true });
    return false;
  }

  if (msg.type === "PAGE_LOADED") {
    return false;
  }

  if (msg.type === "TEST_KEY") {
    testApiKey(msg.apiKey)
      .then(() => sendResponse({ ok: true }))
      .catch(err => sendResponse({ ok: false, error: err.message }));
    return true;
  }

  if (msg.type === "CHAT") {
    proppyChat({
      apiKey: msg.apiKey,
      message: msg.message,
      history: msg.history || [],
      preferences: msg.preferences || {},
    })
      .then(reply => sendResponse(reply))
      .catch(err => sendResponse({ error: err.message, text: "Sorry, something went wrong: " + err.message, listings: [], prefs_update: {}, stage: "gathering" }));
    return true;
  }

  if (msg.type === "SEARCH") {
    proppySearch({ apiKey: msg.apiKey, preferences: msg.preferences || {} })
      .then(result => sendResponse(result))
      .catch(err => sendResponse({ error: err.message, listings: [] }));
    return true;
  }

  return false;
});

async function setupAlarm(interval) {
  const cfg = await getStoredConfig();
  const mins = Number(interval) || Number(cfg.interval) || DEFAULT_INTERVAL;
  chrome.alarms.clear("proppy-search");
  chrome.alarms.create("proppy-search", { delayInMinutes: 1, periodInMinutes: mins });
}

async function runSearch(trigger) {
  const config = await getStoredConfig();
  const prefs  = await getStoredPrefs();
  if (!config.anthropicKey || !config.anthropicKey.startsWith("sk-")) return;
  if (!prefs.location && !prefs.budgetMax) return;
  if (config.notify === false) return;
  console.log(`[Proppy] Background search — ${trigger}`);
  try {
    const result = await proppySearch({ apiKey: config.anthropicKey, preferences: prefs });
    const listings = result.listings || [];
    if (listings.length > 0) {
      await chrome.storage.local.set({ lastSearchResults: listings, lastSearchTime: Date.now() });
      chrome.notifications.create("proppy-results", {
        type: "basic", iconUrl: "icons/icon48.png",
        title: `Proppy found ${listings.length} new home${listings.length > 1 ? "s" : ""}!`,
        message: listings[0] ? `${listings[0].title || "Property"} — ${listings[0].price || "POA"}` : "Click to see results",
        priority: 1,
      });
      chrome.runtime.sendMessage({ type: "NEW_LISTINGS", count: listings.length, listings }).catch(() => {});
    }
  } catch (err) {
    console.error("[Proppy] Background search error:", err.message);
  }
}

chrome.notifications.onClicked.addListener(() => {
  chrome.action.openPopup?.().catch(() => {});
});
