/* ─── Winnie 🐕 Background Service Worker ─── */
/* Central brain: persists state, proxies server calls, syncs all tabs */

const DEFAULT_SERVER = "http://127.0.0.1:8765";

// ─── State Init ─────────────────────────────────────────────────────────────

async function getState() {
  const data = await chrome.storage.local.get([
    "winnie_server_url",
    "winnie_api_key",
    "winnie_session_id",
    "winnie_chat_history",
    "winnie_visible",
    "winnie_tab",
  ]);
  return {
    serverUrl: data.winnie_server_url || DEFAULT_SERVER,
    apiKey: data.winnie_api_key || "",
    sessionId: data.winnie_session_id || generateSessionId(),
    chatHistory: data.winnie_chat_history || [],
    visible: data.winnie_visible !== false,
    activeTab: data.winnie_tab || "chat",
  };
}

function generateSessionId() {
  const id = "wn-" + Date.now() + "-" + Math.random().toString(36).slice(2, 8);
  chrome.storage.local.set({ winnie_session_id: id });
  return id;
}

// ─── Toolbar icon click toggles widget ──────────────────────────────────────

chrome.action.onClicked.addListener(async (tab) => {
  const { visible } = await getState();
  const newVisible = !visible;
  await chrome.storage.local.set({ winnie_visible: newVisible });
  // Notify ALL content scripts
  const tabs = await chrome.tabs.query({});
  for (const t of tabs) {
    try {
      await chrome.tabs.sendMessage(t.id, { type: "toggle_visibility", visible: newVisible });
    } catch {}
  }
});

// ─── Message Router ─────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  handleMessage(msg, sender).then(sendResponse).catch((err) => {
    sendResponse({ error: err.message || String(err) });
  });
  return true; // keep channel open for async
});

async function handleMessage(msg) {
  switch (msg.type) {
    case "get_state":
      return await getState();

    case "save_settings": {
      const updates = {};
      if (msg.serverUrl !== undefined) updates.winnie_server_url = msg.serverUrl;
      if (msg.apiKey !== undefined) updates.winnie_api_key = msg.apiKey;
      await chrome.storage.local.set(updates);
      // Also push API key to the server
      if (msg.apiKey) {
        const state = await getState();
        try {
          await fetch(`${state.serverUrl}/config`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: msg.apiKey }),
          });
        } catch {}
      }
      return { ok: true };
    }

    case "execute": {
      const state = await getState();
      const response = await fetch(`${state.serverUrl}/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: msg.message,
          session_id: state.sessionId,
        }),
      });

      if (!response.ok) {
        let detail = `Server ${response.status}`;
        try { const j = await response.json(); detail = j.detail || detail; } catch {
          try { detail = (await response.text()).slice(0, 200) || detail; } catch {}
        }
        throw new Error(detail);
      }

      const data = await response.json();

      // Update session
      if (data.session_id) {
        await chrome.storage.local.set({ winnie_session_id: data.session_id });
      }

      // Append to chat history
      const history = state.chatHistory.slice(-99);
      history.push({ role: "user", text: msg.message, ts: Date.now() });
      history.push({ role: "bot", text: data.summary || "Done!", steps: data.steps, ts: Date.now() });
      await chrome.storage.local.set({ winnie_chat_history: history });

      // Broadcast update to all tabs
      broadcastToAllTabs({ type: "chat_updated", history });

      return data;
    }

    case "check_connection": {
      const state = await getState();
      try {
        const res = await fetch(`${state.serverUrl}/health`, {
          signal: AbortSignal.timeout(3000),
        });
        return { connected: res.ok };
      } catch {
        return { connected: false };
      }
    }

    case "clear_history": {
      await chrome.storage.local.set({ winnie_chat_history: [] });
      const state = await getState();
      // Clear server-side too
      try {
        await fetch(`${state.serverUrl}/history/${state.sessionId}`, { method: "DELETE" });
      } catch {}
      // New session
      const newId = generateSessionId();
      broadcastToAllTabs({ type: "chat_updated", history: [] });
      return { ok: true };
    }

    case "set_tab": {
      await chrome.storage.local.set({ winnie_tab: msg.tab });
      return { ok: true };
    }

    default:
      return { error: "Unknown message type" };
  }
}

async function broadcastToAllTabs(msg) {
  const tabs = await chrome.tabs.query({});
  for (const t of tabs) {
    try { await chrome.tabs.sendMessage(t.id, msg); } catch {}
  }
}
