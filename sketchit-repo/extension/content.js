/* ============================================================
 * SketchIt — content script
 * Injects a floating chat widget in the lower-right corner of
 * every page. Sends user prompts + current page HTML to the
 * local Python backend and applies the returned design
 * operations directly to the live DOM.
 * ============================================================ */

(function () {
  if (window.__sketchit_loaded__) return;
  window.__sketchit_loaded__ = true;

  const BACKEND_URL = "http://127.0.0.1:5174";
  const STORAGE_KEY = "sketchit_api_key";

  // --- State ---------------------------------------------------
  const state = {
    open: false,
    busy: false,
    apiKey: "",          // loaded from chrome.storage on init
    history: [],         // [{role, content}]
    appliedOps: [],      // flat log of every op applied this session
  };

  // --- Storage helpers -----------------------------------------
  function loadApiKey() {
    return new Promise((resolve) => {
      try {
        chrome.storage.local.get([STORAGE_KEY], (result) => {
          resolve((result && result[STORAGE_KEY]) || "");
        });
      } catch (e) {
        resolve("");
      }
    });
  }

  function saveApiKey(key) {
    return new Promise((resolve) => {
      try {
        chrome.storage.local.set({ [STORAGE_KEY]: key }, () => resolve(true));
      } catch (e) {
        resolve(false);
      }
    });
  }

  function clearApiKey() {
    return new Promise((resolve) => {
      try {
        chrome.storage.local.remove([STORAGE_KEY], () => resolve(true));
      } catch (e) {
        resolve(false);
      }
    });
  }

  function maskKey(key) {
    if (!key) return "";
    if (key.length <= 12) return "•".repeat(key.length);
    return key.slice(0, 8) + "••••••••" + key.slice(-4);
  }

  // --- Widget DOM ----------------------------------------------
  const root = document.createElement("div");
  root.id = "sketchit-root";
  root.setAttribute("data-sketchit", "true");
  root.innerHTML = `
    <button id="sketchit-fab" title="Open SketchIt" aria-label="Open SketchIt">
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 20 L4 16 L16 4 L20 8 L8 20 Z"></path>
        <path d="M14 6 L18 10"></path>
        <path d="M4 20 L8 20"></path>
      </svg>
    </button>

    <div id="sketchit-panel" role="dialog" aria-label="SketchIt chat" aria-hidden="true">
      <header id="sketchit-header">
        <div class="sketchit-brand">
          <div class="sketchit-logo">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 20 L4 16 L16 4 L20 8 L8 20 Z"></path>
              <path d="M14 6 L18 10"></path>
              <path d="M4 20 L8 20"></path>
            </svg>
          </div>
          <div class="sketchit-title">
            <div class="sketchit-title-main">SketchIt</div>
            <div class="sketchit-title-sub">Prototyping agent</div>
          </div>
        </div>
        <div class="sketchit-actions">
          <button class="sketchit-icon-btn" id="sketchit-settings" title="Settings (API key)">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          </button>
          <button class="sketchit-icon-btn" id="sketchit-save" title="Save modified page as HTML">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
          </button>
          <button class="sketchit-icon-btn" id="sketchit-reset" title="Undo all changes">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
          </button>
          <button class="sketchit-icon-btn" id="sketchit-close" title="Close">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </header>

      <!-- Settings panel: shown when the user clicks the gear, or automatically
           on first launch when no key has been saved yet. -->
      <section id="sketchit-settings-panel" aria-hidden="true">
        <div class="sketchit-settings-inner">
          <div class="sketchit-settings-title">Anthropic API key</div>
          <div class="sketchit-settings-desc">
            Your key is stored locally in this browser and sent only to your SketchIt backend at <code>127.0.0.1:5174</code>. Get a key at <a href="https://console.anthropic.com/" target="_blank" rel="noopener">console.anthropic.com</a>.
          </div>

          <div class="sketchit-key-row">
            <input type="password" id="sketchit-key-input" placeholder="sk-ant-..." autocomplete="off" spellcheck="false" />
            <button class="sketchit-icon-btn" id="sketchit-key-toggle" title="Show/hide key" type="button">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
          </div>

          <div class="sketchit-key-status" id="sketchit-key-status"></div>

          <div class="sketchit-settings-actions">
            <button class="sketchit-btn sketchit-btn-ghost" id="sketchit-key-clear" type="button">Clear</button>
            <button class="sketchit-btn sketchit-btn-primary" id="sketchit-key-save" type="button">Save &amp; verify</button>
          </div>
        </div>
      </section>

      <div id="sketchit-messages" aria-live="polite">
        <div class="sketchit-welcome">
          <div class="sketchit-welcome-title">Hi, I'm SketchIt.</div>
          <div class="sketchit-welcome-body">
            Describe a change and I'll redesign this page live. Try:
            <ul>
              <li>"Restructure the form and use a blue color scheme"</li>
              <li>"Make the typography more editorial"</li>
              <li>"Add a hero section with a call to action"</li>
            </ul>
          </div>
        </div>
      </div>

      <footer id="sketchit-footer">
        <textarea id="sketchit-input" rows="2" placeholder="Describe a design change..." aria-label="Design instruction"></textarea>
        <button id="sketchit-send" title="Send (Enter)" aria-label="Send">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </footer>
    </div>
  `;

  // Append to <html> rather than <body> so it survives aggressive body rewrites
  document.documentElement.appendChild(root);

  // --- Element refs --------------------------------------------
  const fab = root.querySelector("#sketchit-fab");
  const panel = root.querySelector("#sketchit-panel");
  const messagesEl = root.querySelector("#sketchit-messages");
  const inputEl = root.querySelector("#sketchit-input");
  const sendBtn = root.querySelector("#sketchit-send");
  const closeBtn = root.querySelector("#sketchit-close");
  const resetBtn = root.querySelector("#sketchit-reset");
  const saveBtn = root.querySelector("#sketchit-save");
  const settingsBtn = root.querySelector("#sketchit-settings");

  // Settings panel refs
  const settingsPanel = root.querySelector("#sketchit-settings-panel");
  const keyInput = root.querySelector("#sketchit-key-input");
  const keyToggleBtn = root.querySelector("#sketchit-key-toggle");
  const keyStatus = root.querySelector("#sketchit-key-status");
  const keySaveBtn = root.querySelector("#sketchit-key-save");
  const keyClearBtn = root.querySelector("#sketchit-key-clear");

  // --- UI helpers ----------------------------------------------
  function togglePanel(force) {
    state.open = typeof force === "boolean" ? force : !state.open;
    panel.classList.toggle("open", state.open);
    panel.setAttribute("aria-hidden", String(!state.open));
    fab.classList.toggle("hidden", state.open);
    if (state.open) {
      // If no key is configured, show the settings panel immediately so the
      // user isn't left wondering why sending doesn't work.
      if (!state.apiKey) {
        toggleSettings(true);
      } else {
        setTimeout(() => inputEl.focus(), 150);
      }
    }
  }

  function toggleSettings(force) {
    const show = typeof force === "boolean"
      ? force
      : !settingsPanel.classList.contains("open");
    settingsPanel.classList.toggle("open", show);
    settingsPanel.setAttribute("aria-hidden", String(!show));
    settingsBtn.classList.toggle("active", show);
    if (show) {
      // Populate with the currently saved key (always password-masked at first)
      keyInput.value = state.apiKey || "";
      keyInput.type = "password";
      setKeyStatus(
        state.apiKey ? `Saved · ${maskKey(state.apiKey)}` : "No key saved",
        state.apiKey ? "ok" : "neutral"
      );
      setTimeout(() => keyInput.focus(), 100);
    }
  }

  function setKeyStatus(msg, kind) {
    keyStatus.textContent = msg;
    keyStatus.className = "sketchit-key-status";
    if (kind) keyStatus.classList.add("sketchit-key-status-" + kind);
  }

  function addMessage(role, content, opts = {}) {
    const welcome = messagesEl.querySelector(".sketchit-welcome");
    if (welcome) welcome.remove();

    const el = document.createElement("div");
    el.className = `sketchit-msg sketchit-msg-${role}`;
    if (opts.pending) el.classList.add("pending");
    el.textContent = content;
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return el;
  }

  function addSystemNote(text) {
    const el = document.createElement("div");
    el.className = "sketchit-sysnote";
    el.textContent = text;
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  // --- DOM operation executor ----------------------------------
  function safeQuerySelectorAll(selector) {
    try {
      return Array.from(document.querySelectorAll(selector)).filter(
        (el) => !el.closest('[data-sketchit="true"]')
      );
    } catch (e) {
      console.warn("[SketchIt] Invalid selector:", selector, e);
      return [];
    }
  }

  function applyOperation(op) {
    const type = op.type;
    try {
      switch (type) {
        case "inject_css": {
          const style = document.createElement("style");
          style.setAttribute("data-sketchit-injected", "css");
          style.textContent = op.css || "";
          document.head.appendChild(style);
          return { ok: true, note: "CSS injected" };
        }
        case "load_font": {
          if (!op.href) return { ok: false, note: "load_font missing href" };
          const link = document.createElement("link");
          link.setAttribute("data-sketchit-injected", "font");
          link.rel = "stylesheet";
          link.href = op.href;
          document.head.appendChild(link);
          return { ok: true, note: `Loaded font: ${op.href}` };
        }
        case "set_attribute": {
          const els = safeQuerySelectorAll(op.selector);
          els.forEach((el) => el.setAttribute(op.attribute, op.value));
          return { ok: true, note: `Set ${op.attribute} on ${els.length} el(s)` };
        }
        case "set_text": {
          const els = safeQuerySelectorAll(op.selector);
          els.forEach((el) => (el.textContent = op.text ?? ""));
          return { ok: true, note: `Set text on ${els.length} el(s)` };
        }
        case "set_html": {
          const els = safeQuerySelectorAll(op.selector);
          els.forEach((el) => (el.innerHTML = op.html ?? ""));
          return { ok: true, note: `Set HTML on ${els.length} el(s)` };
        }
        case "add_class": {
          const els = safeQuerySelectorAll(op.selector);
          els.forEach((el) => el.classList.add(op.class));
          return { ok: true, note: `Added class on ${els.length} el(s)` };
        }
        case "remove_class": {
          const els = safeQuerySelectorAll(op.selector);
          els.forEach((el) => el.classList.remove(op.class));
          return { ok: true, note: `Removed class on ${els.length} el(s)` };
        }
        case "replace_element": {
          const els = safeQuerySelectorAll(op.selector);
          els.forEach((el) => {
            const tmp = document.createElement("div");
            tmp.innerHTML = op.html || "";
            const replacement = tmp.firstElementChild;
            if (replacement) el.replaceWith(replacement);
          });
          return { ok: true, note: `Replaced ${els.length} el(s)` };
        }
        case "append_to": {
          const els = safeQuerySelectorAll(op.selector);
          els.forEach((el) => {
            const tmp = document.createElement("div");
            tmp.innerHTML = op.html || "";
            Array.from(tmp.childNodes).forEach((node) => el.appendChild(node));
          });
          return { ok: true, note: `Appended to ${els.length} el(s)` };
        }
        case "remove_element": {
          const els = safeQuerySelectorAll(op.selector);
          els.forEach((el) => el.remove());
          return { ok: true, note: `Removed ${els.length} el(s)` };
        }
        default:
          return { ok: false, note: `Unknown op: ${type}` };
      }
    } catch (err) {
      console.error("[SketchIt] Op failed:", op, err);
      return { ok: false, note: `Error: ${err.message}` };
    }
  }

  // --- Capture page HTML for the model -------------------------
  function capturePageHtml() {
    const clone = document.documentElement.cloneNode(true);
    clone.querySelectorAll('[data-sketchit="true"]').forEach((n) => n.remove());
    return "<!DOCTYPE html>\n<html>" + clone.innerHTML + "</html>";
  }

  // --- Send to backend -----------------------------------------
  async function sendPrompt(prompt) {
    if (state.busy) return;
    if (!prompt.trim()) return;

    // Guardrail: no key means no send. Open settings instead.
    if (!state.apiKey) {
      addSystemNote("Please add your Anthropic API key in settings first.");
      toggleSettings(true);
      return;
    }

    state.busy = true;
    sendBtn.disabled = true;
    inputEl.disabled = true;

    addMessage("user", prompt);
    const pending = addMessage("assistant", "Thinking like a designer…", { pending: true });

    const pageHtml = capturePageHtml();

    try {
      const resp = await fetch(BACKEND_URL + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          page_html: pageHtml,
          page_url: location.href,
          history: state.history,
          api_key: state.apiKey,
        }),
      });

      const data = await resp.json().catch(() => ({ error: "Non-JSON response from backend." }));

      if (!resp.ok || data.error) {
        pending.classList.remove("pending");
        const msg = data.error || `Backend error (${resp.status}).`;
        pending.textContent = "⚠︎ " + msg;

        // If the key is bad or missing, open the settings panel for the user.
        if (data.error_code === "missing_api_key" || data.error_code === "invalid_api_key") {
          toggleSettings(true);
          setKeyStatus(data.error || "Key problem", "err");
        }
        return;
      }

      // Apply operations
      const ops = data.operations || [];
      const results = ops.map((op) => {
        const res = applyOperation(op);
        if (res.ok) state.appliedOps.push(op);
        return res;
      });

      pending.classList.remove("pending");
      pending.textContent = data.explanation || "Done.";

      const okCount = results.filter((r) => r.ok).length;
      addSystemNote(`Applied ${okCount} / ${ops.length} operation(s).`);

      state.history.push({ role: "user", content: prompt });
      state.history.push({
        role: "assistant",
        content: JSON.stringify({ explanation: data.explanation, operations_count: ops.length }),
      });
    } catch (err) {
      pending.classList.remove("pending");
      pending.textContent = `⚠︎ Couldn't reach backend. Start the Python server:\n\n    python backend/server.py\n\nDetails: ${err.message}`;
    } finally {
      state.busy = false;
      sendBtn.disabled = false;
      inputEl.disabled = false;
      inputEl.focus();
    }
  }

  // --- Save modified page --------------------------------------
  function saveModifiedPage() {
    const html = capturePageHtml();
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const base = (location.hostname || "sketchit") + "-sketchit.html";
    a.download = base.replace(/[^a-z0-9.-]/gi, "_");
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    addSystemNote(`Saved: ${a.download}`);
  }

  function resetPage() {
    document.querySelectorAll('[data-sketchit-injected]').forEach((el) => el.remove());
    state.appliedOps = [];
    state.history = [];
    addSystemNote("Reverted injected styles & fonts. (Structural edits require page reload.)");
  }

  // --- Settings handlers ---------------------------------------
  async function handleSaveKey() {
    const raw = (keyInput.value || "").trim();
    if (!raw) {
      setKeyStatus("Paste a key first.", "err");
      return;
    }
    // Minimal shape check — Anthropic keys start with "sk-ant-"
    if (!raw.startsWith("sk-ant-")) {
      setKeyStatus('Expected a key starting with "sk-ant-".', "err");
      return;
    }

    keySaveBtn.disabled = true;
    setKeyStatus("Verifying…", "neutral");

    try {
      const resp = await fetch(BACKEND_URL + "/validate_key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: raw }),
      });
      const data = await resp.json().catch(() => ({}));

      if (resp.ok && data.valid) {
        await saveApiKey(raw);
        state.apiKey = raw;
        setKeyStatus(`Verified · ${maskKey(raw)}`, "ok");
        setTimeout(() => {
          toggleSettings(false);
          setTimeout(() => inputEl.focus(), 100);
        }, 700);
      } else {
        setKeyStatus(data.error || "Key rejected by Anthropic.", "err");
      }
    } catch (err) {
      setKeyStatus(`Couldn't reach backend to verify (${err.message}). Is it running?`, "err");
    } finally {
      keySaveBtn.disabled = false;
    }
  }

  async function handleClearKey() {
    await clearApiKey();
    state.apiKey = "";
    keyInput.value = "";
    setKeyStatus("Cleared.", "neutral");
  }

  function toggleKeyVisibility() {
    keyInput.type = keyInput.type === "password" ? "text" : "password";
  }

  // --- Event wiring --------------------------------------------
  fab.addEventListener("click", () => togglePanel(true));
  closeBtn.addEventListener("click", () => togglePanel(false));
  saveBtn.addEventListener("click", saveModifiedPage);
  resetBtn.addEventListener("click", resetPage);
  settingsBtn.addEventListener("click", () => toggleSettings());

  keySaveBtn.addEventListener("click", handleSaveKey);
  keyClearBtn.addEventListener("click", handleClearKey);
  keyToggleBtn.addEventListener("click", toggleKeyVisibility);
  keyInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSaveKey();
    }
  });

  sendBtn.addEventListener("click", () => {
    const v = inputEl.value;
    inputEl.value = "";
    sendPrompt(v);
  });

  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const v = inputEl.value;
      inputEl.value = "";
      sendPrompt(v);
    }
  });

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg && msg.type === "SKETCHIT_TOGGLE") togglePanel();
  });

  // --- Init: load the saved key ---------------------------------
  loadApiKey().then((key) => {
    state.apiKey = key || "";
  });
})();
