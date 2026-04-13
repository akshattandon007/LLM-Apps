/* ─── Winnie 🐕 Content Script ─── */
/* Injects the floating chat widget into every page */

(function () {
  "use strict";

  if (document.getElementById("winnie-agent-root")) return; // already injected

  // ─── Create shadow DOM container ───────────────────────────────────────
  const host = document.createElement("div");
  host.id = "winnie-agent-root";
  host.style.cssText = "all:initial; position:fixed; z-index:2147483647; bottom:20px; right:20px; font-family:sans-serif;";
  document.documentElement.appendChild(host);

  const shadow = host.attachShadow({ mode: "closed" });

  // ─── Inject CSS ────────────────────────────────────────────────────────
  const style = document.createElement("style");
  style.textContent = `
    * { margin:0; padding:0; box-sizing:border-box; }

    :host { all: initial; }

    /* ─── Fab Button ─── */
    .winnie-fab {
      width: 54px; height: 54px; border-radius: 50%;
      background: linear-gradient(135deg, #e8a44a, #c2703a);
      border: none; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 20px rgba(0,0,0,0.35), 0 0 0 3px rgba(232,164,74,0.2);
      transition: transform 0.2s, box-shadow 0.2s;
      font-size: 26px; line-height: 1;
      position: relative;
    }
    .winnie-fab:hover { transform: scale(1.08); box-shadow: 0 6px 28px rgba(0,0,0,0.4), 0 0 0 4px rgba(232,164,74,0.3); }
    .winnie-fab.has-panel { display: none; }

    /* ─── Status indicator on fab ─── */
    .fab-status {
      position: absolute; bottom: 2px; right: 2px;
      width: 12px; height: 12px; border-radius: 50%;
      background: #d95050; border: 2px solid #13100e;
    }
    .fab-status.connected { background: #6abf69; }

    /* ─── Panel ─── */
    .winnie-panel {
      width: 380px; height: 520px;
      background: #13100e;
      border-radius: 16px;
      border: 1px solid #3a302a;
      box-shadow: 0 8px 40px rgba(0,0,0,0.5);
      display: none; flex-direction: column;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      color: #f0e8e0;
      font-size: 13px;
      line-height: 1.5;
    }
    .winnie-panel.open { display: flex; }

    /* ─── Header ─── */
    .wn-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 10px 14px;
      border-bottom: 1px solid #3a302a;
      background: #1c1714;
      flex-shrink: 0;
    }
    .wn-header-left { display: flex; align-items: center; gap: 8px; }
    .wn-logo { font-size: 20px; line-height: 1; }
    .wn-title {
      font-size: 16px; font-weight: 800; letter-spacing: -0.3px;
      background: linear-gradient(135deg, #e8a44a, #c2703a);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .wn-header-nav { display: flex; gap: 2px; }
    .wn-tab-btn {
      background: transparent; border: none; color: #6e5f52;
      cursor: pointer; padding: 6px 8px; border-radius: 6px;
      transition: all 0.18s; display: flex; align-items: center; justify-content: center;
    }
    .wn-tab-btn:hover { background: #2e2620; color: #9e8e80; }
    .wn-tab-btn.active { color: #e8a44a; background: rgba(232,164,74,0.15); }
    .wn-close-btn {
      background: transparent; border: none; color: #6e5f52;
      cursor: pointer; padding: 4px 6px; border-radius: 4px;
      font-size: 18px; line-height: 1; transition: color 0.18s;
    }
    .wn-close-btn:hover { color: #d95050; }

    /* ─── Tab Content ─── */
    .wn-tab { display: none; flex-direction: column; flex: 1; overflow: hidden; }
    .wn-tab.active { display: flex; }

    /* ─── Chat Messages ─── */
    .wn-messages {
      flex: 1; overflow-y: auto; padding: 14px;
      display: flex; flex-direction: column; gap: 10px;
      scroll-behavior: smooth;
    }
    .wn-messages::-webkit-scrollbar { width: 4px; }
    .wn-messages::-webkit-scrollbar-track { background: transparent; }
    .wn-messages::-webkit-scrollbar-thumb { background: #3a302a; border-radius: 10px; }

    .wn-msg { display: flex; gap: 8px; animation: wnFadeIn 0.25s ease; }
    .wn-msg.user { flex-direction: row-reverse; }

    @keyframes wnFadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }

    .wn-avatar {
      width: 26px; height: 26px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 14px; flex-shrink: 0; line-height: 1;
    }
    .wn-msg.bot .wn-avatar { background: rgba(232,164,74,0.15); border: 1px solid rgba(232,164,74,0.25); }
    .wn-msg.user .wn-avatar {
      background: #2e2620; border: 1px solid rgba(232,164,74,0.2);
      font-size: 9px; font-weight: 700; color: #e8a44a;
    }

    .wn-bubble {
      max-width: 80%; padding: 9px 13px; border-radius: 10px;
      font-size: 12.5px; line-height: 1.5;
    }
    .wn-msg.bot .wn-bubble {
      background: #1c1714; border: 1px solid #2a221d; border-top-left-radius: 2px;
    }
    .wn-msg.user .wn-bubble {
      background: linear-gradient(135deg, #3a2a18, #2e2010);
      border: 1px solid rgba(232,164,74,0.2); border-top-right-radius: 2px;
    }
    .wn-bubble strong { color: #e8a44a; font-weight: 600; }
    .wn-bubble .hint { color: #6e5f52; font-size: 11px; font-style: italic; margin-top: 4px; }

    /* Steps */
    .wn-steps { margin-top: 6px; display: flex; flex-direction: column; gap: 3px; }
    .wn-step {
      display: flex; align-items: center; gap: 6px; padding: 4px 7px;
      border-radius: 5px; background: #241e19; font-size: 11px;
    }
    .wn-step-icon {
      width: 16px; height: 16px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 9px; font-weight: 700; flex-shrink: 0;
    }
    .wn-step.done .wn-step-icon { background: #6abf69; color: #000; }
    .wn-step.error .wn-step-icon { background: #d95050; color: #fff; }
    .wn-step-text { color: #9e8e80; }
    .wn-step.done .wn-step-text { color: #f0e8e0; }

    /* ─── Input Area ─── */
    .wn-input-area {
      padding: 10px 12px; border-top: 1px solid #3a302a;
      background: #1c1714; flex-shrink: 0;
    }
    .wn-input-row {
      display: flex; align-items: flex-end; gap: 6px;
      background: #241e19; border: 1px solid #3a302a; border-radius: 10px;
      padding: 4px 4px 4px 10px; transition: border-color 0.18s;
    }
    .wn-input-row:focus-within { border-color: #e8a44a; box-shadow: 0 0 0 2px rgba(232,164,74,0.15); }
    .wn-input {
      flex: 1; background: transparent; border: none; color: #f0e8e0;
      font-size: 13px; font-family: inherit; resize: none; outline: none;
      padding: 7px 0; max-height: 72px; line-height: 1.4;
    }
    .wn-input::placeholder { color: #6e5f52; }
    .wn-send {
      width: 32px; height: 32px; border-radius: 7px; border: none;
      background: #e8a44a; color: #13100e; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; transition: all 0.18s;
    }
    .wn-send:hover { background: #f0b860; transform: scale(1.05); }
    .wn-send:disabled { opacity: 0.35; cursor: not-allowed; transform: none; }
    .wn-send svg { width: 16px; height: 16px; }
    .wn-input-footer {
      display: flex; justify-content: space-between; align-items: center;
      margin-top: 5px; padding: 0 2px;
    }
    .wn-text-btn {
      background: none; border: none; color: #6e5f52; font-size: 10px;
      cursor: pointer; transition: color 0.18s;
    }
    .wn-text-btn:hover { color: #d95050; }
    .wn-status {
      width: 7px; height: 7px; border-radius: 50%; background: #d95050; transition: background 0.18s;
    }
    .wn-status.on { background: #6abf69; }

    /* ─── Settings ─── */
    .wn-settings { padding: 16px; overflow-y: auto; flex: 1; }
    .wn-settings h3 { font-size: 14px; font-weight: 600; margin-bottom: 6px; color: #f0e8e0; }
    .wn-settings p { font-size: 11px; color: #9e8e80; margin-bottom: 12px; line-height: 1.5; }
    .wn-settings label {
      display: block; font-size: 10px; font-weight: 600; color: #9e8e80;
      margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .wn-settings input {
      width: 100%; padding: 8px 10px; background: #241e19; border: 1px solid #3a302a;
      border-radius: 6px; color: #f0e8e0; font-size: 12px;
      font-family: 'SF Mono', 'Fira Code', monospace; outline: none; transition: border-color 0.18s;
    }
    .wn-settings input:focus { border-color: #e8a44a; box-shadow: 0 0 0 2px rgba(232,164,74,0.15); }
    .wn-key-row { display: flex; gap: 5px; margin-bottom: 8px; }
    .wn-key-row input { flex: 1; }
    .wn-key-row button {
      width: 34px; background: #241e19; border: 1px solid #3a302a; border-radius: 6px;
      color: #6e5f52; cursor: pointer; display: flex; align-items: center; justify-content: center;
      transition: all 0.18s;
    }
    .wn-key-row button:hover { border-color: #e8a44a; color: #e8a44a; }
    .wn-primary-btn {
      width: 100%; padding: 8px; background: #e8a44a; border: none; border-radius: 6px;
      color: #13100e; font-size: 12px; font-weight: 600; cursor: pointer; transition: background 0.18s;
    }
    .wn-primary-btn:hover { background: #f0b860; }
    .wn-secondary-btn {
      width: 100%; padding: 8px; background: transparent; border: 1px solid #3a302a;
      border-radius: 6px; color: #9e8e80; font-size: 12px; cursor: pointer;
      transition: all 0.18s; margin-top: 6px;
    }
    .wn-secondary-btn:hover { border-color: #e8a44a; color: #e8a44a; }
    .wn-status-msg { margin-top: 6px; font-size: 11px; min-height: 16px; }
    .wn-status-msg.ok { color: #6abf69; }
    .wn-status-msg.err { color: #d95050; }
    .wn-divider { border: none; border-top: 1px solid #3a302a; margin: 14px 0; }

    /* ─── Help ─── */
    .wn-help { padding: 16px; overflow-y: auto; flex: 1; }
    .wn-help h3 {
      font-size: 14px; font-weight: 700; margin-bottom: 12px;
      background: linear-gradient(135deg, #e8a44a, #c2703a);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .wn-help h4 { font-size: 12px; font-weight: 600; color: #e8a44a; margin: 10px 0 6px; }
    .wn-help p, .wn-help li { font-size: 11.5px; color: #9e8e80; line-height: 1.5; }
    .wn-help ol, .wn-help ul { padding-left: 16px; }
    .wn-help li { margin-bottom: 4px; }
    .wn-help code {
      background: #241e19; padding: 1px 5px; border-radius: 3px;
      font-size: 10.5px; font-family: 'SF Mono', monospace; color: #e8a44a;
    }
    .wn-examples { list-style: none; padding: 0; }
    .wn-examples li {
      padding: 5px 8px; background: #241e19; border-radius: 5px;
      border-left: 2px solid #e8a44a; font-size: 11px; color: #f0e8e0;
      margin-bottom: 3px; cursor: pointer; transition: background 0.18s;
    }
    .wn-examples li:hover { background: #2e2620; }

    /* ─── Loading ─── */
    .wn-loading {
      display: flex; align-items: center; gap: 6px; padding: 8px 12px;
      color: #e8a44a; font-size: 12px;
    }
    .wn-spinner {
      width: 14px; height: 14px; border: 2px solid #3a302a;
      border-top-color: #e8a44a; border-radius: 50%;
      animation: wnSpin 0.7s linear infinite;
    }
    @keyframes wnSpin { to { transform: rotate(360deg); } }
  `;
  shadow.appendChild(style);

  // ─── Build DOM ─────────────────────────────────────────────────────────

  const container = document.createElement("div");
  container.innerHTML = `
    <!-- Fab Button -->
    <button class="winnie-fab" id="wn-fab" title="Open Winnie">
      🐕
      <span class="fab-status" id="wn-fab-status"></span>
    </button>

    <!-- Chat Panel -->
    <div class="winnie-panel" id="wn-panel">
      <!-- Header -->
      <div class="wn-header">
        <div class="wn-header-left">
          <span class="wn-logo">🐕</span>
          <span class="wn-title">Winnie</span>
        </div>
        <div class="wn-header-nav">
          <button class="wn-tab-btn active" data-tab="chat" title="Chat">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
          </button>
          <button class="wn-tab-btn" data-tab="settings" title="Settings">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
          </button>
          <button class="wn-tab-btn" data-tab="help" title="How to use">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          </button>
          <button class="wn-close-btn" id="wn-close" title="Close">&times;</button>
        </div>
      </div>

      <!-- Chat Tab -->
      <div class="wn-tab active" id="wn-tab-chat">
        <div class="wn-messages" id="wn-messages">
          <div class="wn-msg bot">
            <div class="wn-avatar">🐕</div>
            <div class="wn-bubble">
              <strong>Woof!</strong> I'm Winnie. Tell me what to fetch and I'll sniff it out!
              <div class="hint">Try: "Go to google.com and search total UK population"</div>
            </div>
          </div>
        </div>
        <div class="wn-input-area">
          <div class="wn-input-row">
            <textarea class="wn-input" id="wn-input" placeholder="Tell Winnie what to fetch…" rows="1"></textarea>
            <button class="wn-send" id="wn-send" title="Send">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
          <div class="wn-input-footer">
            <button class="wn-text-btn" id="wn-clear">Clear history</button>
            <span class="wn-status" id="wn-status"></span>
          </div>
        </div>
      </div>

      <!-- Settings Tab -->
      <div class="wn-tab" id="wn-tab-settings">
        <div class="wn-settings">
          <h3>API Configuration</h3>
          <p>Enter your Anthropic API key so Winnie can think. Stored locally only.</p>
          <label>Claude API Key</label>
          <div class="wn-key-row">
            <input type="password" id="wn-apikey" placeholder="sk-ant-api03-…" spellcheck="false" autocomplete="off"/>
            <button id="wn-eye" title="Show/hide">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
          </div>
          <button class="wn-primary-btn" id="wn-savekey">Save Key</button>
          <div class="wn-status-msg" id="wn-keystatus"></div>
          <hr class="wn-divider"/>
          <h3>Server</h3>
          <label>Server URL</label>
          <input type="text" id="wn-serverurl" value="http://127.0.0.1:8765"/>
          <button class="wn-secondary-btn" id="wn-testconn">Test Connection</button>
          <div class="wn-status-msg" id="wn-connstatus"></div>
        </div>
      </div>

      <!-- Help Tab -->
      <div class="wn-tab" id="wn-tab-help">
        <div class="wn-help">
          <h3>How to Use Winnie</h3>
          <h4>1 — Setup</h4>
          <ol>
            <li>Install: <code>pip install -r requirements.txt</code> then <code>playwright install chromium</code></li>
            <li>Run: <code>python server/agent.py</code></li>
            <li>Add your API key in Settings</li>
          </ol>
          <h4>2 — Commands</h4>
          <p>Type naturally. Click an example to try it:</p>
          <ul class="wn-examples" id="wn-examples">
            <li>Go to google.com and search total UK population</li>
            <li>Open youtube.com and search for lofi music</li>
            <li>Navigate to github.com and click Sign up</li>
            <li>Take a screenshot of the current page</li>
            <li>Open a new tab and go to wikipedia.org</li>
            <li>Switch to tab 1 and scroll down</li>
          </ul>
          <h4>3 — Multi-Tab</h4>
          <p>Winnie can manage multiple browser tabs. Say "open a new tab" or "switch to tab 2". State persists across all your browser tabs — the same chat appears everywhere.</p>
          <h4>4 — Tips</h4>
          <ul>
            <li>Be specific: "click the blue Submit button" beats "submit"</li>
            <li>Winnie opens her own browser window — watch her work!</li>
            <li>The widget syncs across all your browser tabs</li>
            <li>Click the toolbar icon or the × to hide/show the widget</li>
          </ul>
        </div>
      </div>
    </div>
  `;
  shadow.appendChild(container);

  // ─── Refs ──────────────────────────────────────────────────────────────
  const $ = (sel) => shadow.querySelector(sel);
  const fab = $("#wn-fab");
  const panel = $("#wn-panel");
  const closeBtn = $("#wn-close");
  const messagesEl = $("#wn-messages");
  const inputEl = $("#wn-input");
  const sendBtn = $("#wn-send");
  const clearBtn = $("#wn-clear");
  const statusDot = $("#wn-status");
  const fabStatus = $("#wn-fab-status");
  const apiKeyInput = $("#wn-apikey");
  const saveKeyBtn = $("#wn-savekey");
  const keyStatusEl = $("#wn-keystatus");
  const eyeBtn = $("#wn-eye");
  const serverUrlInput = $("#wn-serverurl");
  const testConnBtn = $("#wn-testconn");
  const connStatusEl = $("#wn-connstatus");
  const examplesEl = $("#wn-examples");

  let isExecuting = false;

  // ─── Init ──────────────────────────────────────────────────────────────
  async function init() {
    const state = await sendMsg({ type: "get_state" });
    if (state.apiKey) apiKeyInput.value = state.apiKey;
    if (state.serverUrl) serverUrlInput.value = state.serverUrl;
    if (state.visible) openPanel();
    if (state.activeTab && state.activeTab !== "chat") switchTab(state.activeTab);
    renderHistory(state.chatHistory || []);
    checkConnection();
  }

  // ─── Fab / Panel Toggle ────────────────────────────────────────────────
  fab.addEventListener("click", openPanel);
  closeBtn.addEventListener("click", closePanel);

  function openPanel() {
    panel.classList.add("open");
    fab.classList.add("has-panel");
    messagesEl.scrollTop = messagesEl.scrollHeight;
    inputEl.focus();
  }

  function closePanel() {
    panel.classList.remove("open");
    fab.classList.remove("has-panel");
  }

  // ─── Tabs ──────────────────────────────────────────────────────────────
  shadow.querySelectorAll(".wn-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  function switchTab(tabName) {
    shadow.querySelectorAll(".wn-tab-btn").forEach((b) => b.classList.remove("active"));
    shadow.querySelectorAll(".wn-tab").forEach((t) => t.classList.remove("active"));
    const btn = shadow.querySelector(`.wn-tab-btn[data-tab="${tabName}"]`);
    const tab = shadow.querySelector(`#wn-tab-${tabName}`);
    if (btn) btn.classList.add("active");
    if (tab) tab.classList.add("active");
    sendMsg({ type: "set_tab", tab: tabName });
  }

  // ─── Chat ──────────────────────────────────────────────────────────────
  sendBtn.addEventListener("click", handleSend);
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  });
  inputEl.addEventListener("input", () => {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 72) + "px";
  });
  clearBtn.addEventListener("click", async () => {
    await sendMsg({ type: "clear_history" });
    messagesEl.innerHTML = `
      <div class="wn-msg bot">
        <div class="wn-avatar">🐕</div>
        <div class="wn-bubble">History cleared! What should Winnie fetch next?</div>
      </div>`;
  });

  // Example commands
  examplesEl.addEventListener("click", (e) => {
    if (e.target.tagName === "LI") {
      inputEl.value = e.target.textContent;
      switchTab("chat");
      inputEl.focus();
    }
  });

  async function handleSend() {
    const msg = inputEl.value.trim();
    if (!msg || isExecuting) return;
    isExecuting = true;
    sendBtn.disabled = true;
    inputEl.value = "";
    inputEl.style.height = "auto";

    appendMsg("user", esc(msg));

    // Show loading
    const loadingId = "ld-" + Date.now();
    messagesEl.insertAdjacentHTML("beforeend", `
      <div class="wn-msg bot" id="${loadingId}">
        <div class="wn-avatar">🐕</div>
        <div class="wn-bubble"><div class="wn-loading"><div class="wn-spinner"></div>Winnie is sniffing…</div></div>
      </div>`);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    try {
      const data = await sendMsg({ type: "execute", message: msg });
      if (data.error) throw new Error(data.error);
      // Remove loading
      const ldEl = shadow.getElementById(loadingId);
      if (ldEl) ldEl.remove();
      displayResult(data);
    } catch (err) {
      const ldEl = shadow.getElementById(loadingId);
      if (ldEl) ldEl.remove();
      appendMsg("bot", `<span style="color:#d95050;">Winnie hit a snag: ${esc(err.message)}</span>`);
    }
    isExecuting = false;
    sendBtn.disabled = false;
    inputEl.focus();
  }

  function displayResult(data) {
    let html = `<strong>${esc(data.page_title || "Done!")}</strong>`;
    html += `<div style="font-size:10px;color:#6e5f52;margin:2px 0">${esc(data.current_url || "")}</div>`;
    html += `<div class="wn-steps">`;
    for (const step of (data.steps || [])) {
      const hasErr = step.result.toLowerCase().startsWith("error");
      const cls = hasErr ? "error" : "done";
      const icon = hasErr ? "✕" : "✓";
      html += `<div class="wn-step ${cls}"><span class="wn-step-icon">${icon}</span><span class="wn-step-text">${esc(step.description)}</span></div>`;
    }
    html += `</div>`;
    appendMsg("bot", html);
  }

  function appendMsg(role, html) {
    const avatar = role === "bot" ? "🐕" : "You";
    messagesEl.insertAdjacentHTML("beforeend", `
      <div class="wn-msg ${role}">
        <div class="wn-avatar">${avatar}</div>
        <div class="wn-bubble">${html}</div>
      </div>`);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function renderHistory(history) {
    for (const entry of history) {
      if (entry.role === "user") {
        appendMsg("user", esc(entry.text));
      } else if (entry.steps) {
        displayResult({ page_title: "", current_url: "", steps: entry.steps, summary: entry.text });
      } else {
        appendMsg("bot", esc(entry.text));
      }
    }
  }

  // ─── Settings ──────────────────────────────────────────────────────────
  saveKeyBtn.addEventListener("click", async () => {
    const key = apiKeyInput.value.trim();
    if (!key) { showStatus(keyStatusEl, "Enter an API key", "err"); return; }
    try {
      await sendMsg({ type: "save_settings", apiKey: key });
      showStatus(keyStatusEl, "Saved! Winnie is ready.", "ok");
    } catch (err) { showStatus(keyStatusEl, `Failed: ${err.message}`, "err"); }
  });
  eyeBtn.addEventListener("click", () => {
    apiKeyInput.type = apiKeyInput.type === "password" ? "text" : "password";
  });
  testConnBtn.addEventListener("click", checkConnection);
  serverUrlInput.addEventListener("change", async () => {
    await sendMsg({ type: "save_settings", serverUrl: serverUrlInput.value.replace(/\/+$/, "") });
  });

  async function checkConnection() {
    try {
      const res = await sendMsg({ type: "check_connection" });
      const on = res && res.connected;
      statusDot.classList.toggle("on", on);
      fabStatus.classList.toggle("connected", on);
      showStatus(connStatusEl, on ? "Connected — Winnie is awake!" : "Can't reach server.", on ? "ok" : "err");
    } catch {
      statusDot.classList.remove("on");
      fabStatus.classList.remove("connected");
      showStatus(connStatusEl, "Connection check failed.", "err");
    }
  }

  function showStatus(el, msg, type) {
    el.textContent = msg;
    el.className = "wn-status-msg " + type;
    setTimeout(() => { el.textContent = ""; }, 5000);
  }

  // ─── Listen for broadcasts from background ────────────────────────────
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "toggle_visibility") {
      if (msg.visible) openPanel(); else closePanel();
    } else if (msg.type === "chat_updated") {
      // Re-render chat from background state (keeps all tabs in sync)
      messagesEl.innerHTML = `
        <div class="wn-msg bot">
          <div class="wn-avatar">🐕</div>
          <div class="wn-bubble"><strong>Woof!</strong> I'm Winnie. Tell me what to fetch!</div>
        </div>`;
      renderHistory(msg.history || []);
    }
  });

  // ─── Helpers ───────────────────────────────────────────────────────────
  function sendMsg(msg) {
    return chrome.runtime.sendMessage(msg);
  }
  function esc(str) {
    const d = document.createElement("div");
    d.textContent = str || "";
    return d.innerHTML;
  }

  // ─── Boot ──────────────────────────────────────────────────────────────
  init();
})();
