"""
Winnie — The Dachshund Browser Agent 🐕
========================================
A FastAPI server that receives natural-language commands from the browser
extension, uses Claude to plan actions, and executes them via Playwright.

Named after the most determined breed — just like a dachshund following a
scent, Winnie sniffs out what you want and fetches it from the web.
"""

import asyncio
import json
import logging
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  🐕 %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("winnie")

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Winnie — Browser Agent",
    description="A dachshund that fetches web pages. Give commands, watch her work.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch-all: every unhandled error returns JSON, never plain text."""
    log.error("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "Internal server error"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": f"Invalid request: {exc}"},
    )

# ─── Persistent State ────────────────────────────────────────────────────────

DATA_DIR = Path.home() / ".winnie"
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "chat_history.json"
CONFIG_FILE = DATA_DIR / "config.json"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)


def load_json(path: Path, default):
    """Load JSON from disk, returning *default* if missing or corrupt."""
    try:
        if path.exists():
            return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Could not read %s: %s", path, exc)
    return default


def save_json(path: Path, data):
    """Atomically write JSON to disk."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(path)


# ─── Request / Response Models ────────────────────────────────────────────────

class CommandRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ConfigUpdate(BaseModel):
    api_key: str


# ─── Browser Manager (multi-tab) ─────────────────────────────────────────────

class BrowserManager:
    """Manages a Playwright Chromium instance with multiple named tabs."""

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._pages: dict[str, Page] = {}       # name → Page
        self._active_tab: str = "tab-1"
        self._tab_counter: int = 1
        self._lock = asyncio.Lock()

    async def _ensure_browser(self):
        if self._browser is None or not self._browser.is_connected():
            log.info("Launching Chromium…")
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=False,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            self._context = await self._browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            self._pages = {}
            self._tab_counter = 1
            self._active_tab = "tab-1"
            page = await self._context.new_page()
            self._pages["tab-1"] = page
            log.info("Browser ready 🐕 (tab-1)")

    async def get_page(self) -> Page:
        async with self._lock:
            await self._ensure_browser()
            page = self._pages.get(self._active_tab)
            if page is None or page.is_closed():
                page = await self._context.new_page()
                self._pages[self._active_tab] = page
            return page

    async def new_tab(self, name: Optional[str] = None) -> str:
        async with self._lock:
            await self._ensure_browser()
            self._tab_counter += 1
            tab_name = name or f"tab-{self._tab_counter}"
            page = await self._context.new_page()
            self._pages[tab_name] = page
            self._active_tab = tab_name
            log.info("New tab: %s (total: %d)", tab_name, len(self._pages))
            return tab_name

    async def switch_tab(self, tab_name: str) -> str:
        async with self._lock:
            await self._ensure_browser()
            # Allow numeric references like "tab 2" → "tab-2"
            normalized = tab_name.replace(" ", "-").lower()
            if normalized not in self._pages:
                # Try fuzzy match
                for key in self._pages:
                    if tab_name in key or key in tab_name:
                        normalized = key
                        break
            if normalized in self._pages and not self._pages[normalized].is_closed():
                self._active_tab = normalized
                await self._pages[normalized].bring_to_front()
                log.info("Switched to %s", normalized)
                return normalized
            return f"Tab '{tab_name}' not found. Open tabs: {list(self._pages.keys())}"

    async def close_tab(self, tab_name: Optional[str] = None) -> str:
        async with self._lock:
            name = tab_name or self._active_tab
            if name in self._pages:
                if not self._pages[name].is_closed():
                    await self._pages[name].close()
                del self._pages[name]
                # Switch to another tab
                if self._pages:
                    self._active_tab = list(self._pages.keys())[-1]
                else:
                    self._active_tab = "tab-1"
                log.info("Closed tab: %s, active: %s", name, self._active_tab)
                return f"Closed {name}. Active: {self._active_tab}"
            return f"Tab '{name}' not found."

    async def list_tabs(self) -> list[dict]:
        result = []
        for name, page in self._pages.items():
            if not page.is_closed():
                try:
                    title = await page.title()
                    url = page.url
                except:
                    title, url = "(loading)", ""
                result.append({
                    "name": name,
                    "title": title,
                    "url": url,
                    "active": name == self._active_tab,
                })
        return result

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None
        self._pages = {}
        log.info("Browser closed.")


browser_mgr = BrowserManager()


# ─── Action Executor ──────────────────────────────────────────────────────────

async def execute_action(page: Page, step: dict) -> str:
    """Execute a single browser action and return a status message."""
    action = step.get("action", "").lower()
    selector = step.get("selector")
    value = step.get("value", "")
    url = step.get("url", "")
    wait_ms = step.get("wait_ms", 1000)

    try:
        if action == "goto":
            target = url or value
            if target and not target.startswith("http"):
                target = "https://" + target
            await page.goto(target, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(1500)
            return f"Navigated to {target}"

        elif action == "click":
            if selector:
                await page.wait_for_selector(selector, timeout=8000)
                await page.click(selector)
            else:
                await page.get_by_text(value, exact=False).first.click()
            await page.wait_for_timeout(800)
            return f"Clicked: {selector or value}"

        elif action == "type":
            if selector:
                await page.wait_for_selector(selector, timeout=8000)
                await page.fill(selector, "")
                await page.type(selector, value, delay=40)
            else:
                await page.keyboard.type(value, delay=40)
            await page.wait_for_timeout(500)
            return f"Typed: {value}"

        elif action == "press":
            key = value or "Enter"
            await page.keyboard.press(key)
            await page.wait_for_timeout(800)
            return f"Pressed key: {key}"

        elif action == "scroll":
            direction = step.get("direction", "down")
            distance = 600 if direction == "down" else -600
            await page.evaluate(f"window.scrollBy(0, {distance})")
            await page.wait_for_timeout(500)
            return f"Scrolled {direction}"

        elif action == "screenshot":
            ts = int(time.time())
            path = str(SCREENSHOTS_DIR / f"screenshot_{ts}.png")
            await page.screenshot(path=path, full_page=False)
            return f"Screenshot saved: {path}"

        elif action == "wait":
            await page.wait_for_timeout(wait_ms)
            return f"Waited {wait_ms}ms"

        elif action == "extract":
            if selector:
                el = await page.query_selector(selector)
                text = await el.inner_text() if el else ""
            else:
                text = await page.inner_text("body")
            return f"Extracted text:\n{text[:3000]}"

        elif action == "back":
            await page.go_back()
            await page.wait_for_timeout(1000)
            return "Navigated back"

        elif action == "forward":
            await page.go_forward()
            await page.wait_for_timeout(1000)
            return "Navigated forward"

        elif action == "refresh":
            await page.reload()
            await page.wait_for_timeout(1500)
            return "Page refreshed"

        elif action == "select":
            if selector and value:
                await page.select_option(selector, value)
                return f"Selected option: {value}"
            return "Select requires selector and value"

        elif action == "hover":
            if selector:
                await page.hover(selector)
                return f"Hovered over: {selector}"
            return "Hover requires a selector"

        elif action == "new_tab":
            name = await browser_mgr.new_tab(value or None)
            return f"Opened new tab: {name}"

        elif action == "switch_tab":
            result = await browser_mgr.switch_tab(value)
            return result

        elif action == "close_tab":
            result = await browser_mgr.close_tab(value or None)
            return result

        elif action == "list_tabs":
            tabs = await browser_mgr.list_tabs()
            lines = [f"  {'→ ' if t['active'] else '  '}{t['name']}: {t['title']} ({t['url']})" for t in tabs]
            return "Open tabs:\n" + "\n".join(lines)

        else:
            return f"Unknown action: {action}"

    except Exception as exc:
        log.error("Action '%s' failed: %s", action, exc)
        return f"Error executing '{action}': {exc}"


# ─── Claude Planner ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are Winnie 🐕, a cheerful dachshund browser-automation agent.
You receive a user's natural-language command and produce a JSON array of
action steps to fulfill it in a real Chromium browser controlled by Playwright.

Available actions:
  goto       — navigate to a URL          (provide "url")
  click      — click an element           (provide "selector" CSS, OR "value" for text match)
  type       — type text into a field     (provide "selector" + "value")
  press      — press a keyboard key       (provide "value", e.g. "Enter", "Tab")
  scroll     — scroll the page            (provide "direction": "up" | "down")
  wait       — pause                      (provide "wait_ms")
  extract    — get page text              (provide "selector" or omit for full body)
  screenshot — take a screenshot
  back       — browser back button
  forward    — browser forward button
  refresh    — reload page
  select     — choose a dropdown option   (provide "selector" + "value")
  hover      — hover over an element      (provide "selector")
  new_tab    — open a new browser tab     (optional "value" for tab name)
  switch_tab — switch to a tab            (provide "value", e.g. "tab-2")
  close_tab  — close a tab               (optional "value"; defaults to active tab)
  list_tabs  — show all open tabs

Tab management:
- The browser starts with "tab-1". Each new_tab creates "tab-2", "tab-3", etc.
- You can give tabs custom names: new_tab with value "research" creates a tab called "research".
- switch_tab accepts tab names like "tab-1", "tab-2", or custom names.
- Actions always execute on the ACTIVE tab. switch_tab first if you need a different one.
- If user says "open X in a new tab": new_tab → goto URL.
- If user says "go back to the first tab": switch_tab "tab-1".

Rules:
1. Return ONLY a valid JSON array of step objects. No markdown fences, no prose.
2. Every step MUST have "action" and "description" keys.
3. Prefer CSS selectors. For search bars try:
   textarea[name="q"], input[name="q"], input[type="search"],
   [aria-label*="search" i], #search-input, [role="searchbox"].
4. After typing in a search box, always add a press Enter step.
5. Keep plans short: 2–8 steps.
6. For "search X on Google": goto google.com → type in search box → press Enter.
7. After reaching a results page, add an extract step so the user sees content.
8. For ambiguous commands, make reasonable assumptions and note them in descriptions.

Example — multi-tab workflow:
[
  {"action":"goto","url":"https://www.google.com","description":"Open Google in current tab"},
  {"action":"type","selector":"textarea[name='q']","value":"UK population","description":"Search"},
  {"action":"press","value":"Enter","description":"Submit"},
  {"action":"new_tab","description":"Open a new tab for Wikipedia"},
  {"action":"goto","url":"https://en.wikipedia.org","description":"Go to Wikipedia in tab-2"},
  {"action":"switch_tab","value":"tab-1","description":"Switch back to Google results"},
  {"action":"extract","selector":"#search","description":"Extract Google results"}
]
"""


async def plan_actions(user_message: str, api_key: str, history: list) -> list[dict]:
    """Send the user command to Claude and parse the returned action plan."""
    client = anthropic.AsyncAnthropic(api_key=api_key)

    # Build conversation context (last 10 exchanges)
    messages = []
    for entry in history[-10:]:
        messages.append({"role": "user", "content": entry["user"]})
        if entry.get("assistant"):
            messages.append({"role": "assistant", "content": entry["assistant"]})
    messages.append({"role": "user", "content": user_message})

    log.info("Asking Claude to plan: %s", user_message[:80])

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
    except anthropic.AuthenticationError:
        raise ValueError("Invalid API key. Check your key in Settings.")
    except anthropic.RateLimitError:
        raise ValueError("Rate limited by Anthropic. Wait a moment and try again.")
    except anthropic.APIConnectionError:
        raise ValueError("Could not connect to Anthropic API. Check your internet.")
    except anthropic.APIError as exc:
        raise ValueError(f"Anthropic API error: {exc.message}")

    if not response.content:
        raise ValueError("Claude returned an empty response.")

    raw = response.content[0].text.strip()
    log.info("Claude raw response: %s", raw[:200])

    # Extract JSON array from response
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        raise ValueError(f"Claude did not return a valid action plan. Response: {raw[:300]}")

    try:
        plan = json.loads(match.group())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse action plan as JSON: {exc}")

    if not isinstance(plan, list) or len(plan) == 0:
        raise ValueError("Claude returned an empty action plan.")

    log.info("Plan: %d steps", len(plan))
    return plan


# ─── Chat History ─────────────────────────────────────────────────────────────

def get_history(session_id: str) -> list:
    return load_json(HISTORY_FILE, {}).get(session_id, [])


def save_entry(session_id: str, user_msg: str, assistant_msg: str, steps: list):
    all_hist = load_json(HISTORY_FILE, {})
    all_hist.setdefault(session_id, []).append({
        "timestamp": datetime.now().isoformat(),
        "user": user_msg,
        "assistant": assistant_msg,
        "steps": steps,
    })
    # Keep per-session cap at 200 entries
    if len(all_hist[session_id]) > 200:
        all_hist[session_id] = all_hist[session_id][-200:]
    save_json(HISTORY_FILE, all_hist)


# ─── REST Endpoints ──────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "name": "Winnie 🐕"}


@app.post("/config")
async def update_config(cfg: ConfigUpdate):
    """Save the API key to local config."""
    config = load_json(CONFIG_FILE, {})
    config["api_key"] = cfg.api_key
    save_json(CONFIG_FILE, config)
    log.info("API key saved.")
    return {"status": "saved"}


@app.get("/config")
async def get_config():
    config = load_json(CONFIG_FILE, {})
    return {"has_key": bool(config.get("api_key"))}


@app.get("/history/{session_id}")
async def fetch_history(session_id: str):
    return {"history": get_history(session_id)}


@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    all_hist = load_json(HISTORY_FILE, {})
    all_hist.pop(session_id, None)
    save_json(HISTORY_FILE, all_hist)
    return {"status": "cleared"}


@app.get("/tabs")
async def get_tabs():
    """List all open Playwright tabs."""
    tabs = await browser_mgr.list_tabs()
    return {"tabs": tabs}


@app.post("/execute")
async def execute_command(req: CommandRequest):
    """Main endpoint: plan via Claude, execute via Playwright."""
    config = load_json(CONFIG_FILE, {})
    api_key = config.get("api_key")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="API key not configured. Add your Claude API key in Settings.",
        )

    session_id = req.session_id or str(uuid.uuid4())
    history = get_history(session_id)

    # 1 — Plan
    try:
        steps = await plan_actions(req.message, api_key, history)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Planning failed: {exc}")

    # 2 — Execute (get fresh page ref each step — tab actions change active page)
    TAB_ACTIONS = {"new_tab", "switch_tab", "close_tab", "list_tabs"}
    results = []
    for i, step in enumerate(steps):
        action_name = step.get("action", "").lower()
        if action_name not in TAB_ACTIONS:
            page = await browser_mgr.get_page()
        else:
            page = None  # tab actions don't need a page ref
        desc = step.get("description", step.get("action", ""))
        result = await execute_action(page, step)
        results.append({"step": i + 1, "description": desc, "result": result})

    # 3 — Gather final state from whichever page is now active
    page = await browser_mgr.get_page()
    current_url = page.url
    title = await page.title()

    summary_lines = [
        f"  Step {r['step']}: {r['description']} → {r['result'][:200]}"
        for r in results
    ]
    assistant_msg = (
        f"Completed {len(steps)} actions.\n"
        f"Current page: {title} ({current_url})\n\n"
        + "\n".join(summary_lines)
    )

    # 4 — Persist
    save_entry(session_id, req.message, assistant_msg, steps)

    return {
        "session_id": session_id,
        "steps": results,
        "current_url": current_url,
        "page_title": title,
        "summary": assistant_msg,
    }


# ─── WebSocket (streaming execution) ─────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """Stream step-by-step execution results over WebSocket."""
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            message = data.get("message", "")
            session_id = data.get("session_id", str(uuid.uuid4()))

            config = load_json(CONFIG_FILE, {})
            api_key = config.get("api_key")
            if not api_key:
                await ws.send_json({"type": "error", "message": "API key not configured."})
                continue

            history = get_history(session_id)

            # Plan
            await ws.send_json({"type": "status", "message": "Winnie is sniffing out a plan… 🐕"})
            try:
                steps = await plan_actions(message, api_key, history)
            except Exception as exc:
                await ws.send_json({"type": "error", "message": f"Planning failed: {exc}"})
                continue

            await ws.send_json({"type": "plan", "steps": steps})

            # Execute
            TAB_ACTIONS = {"new_tab", "switch_tab", "close_tab", "list_tabs"}
            results = []
            for i, step in enumerate(steps):
                action_name = step.get("action", "").lower()
                if action_name not in TAB_ACTIONS:
                    page = await browser_mgr.get_page()
                else:
                    page = None
                desc = step.get("description", step.get("action"))
                await ws.send_json({
                    "type": "step_start",
                    "step": i + 1,
                    "total": len(steps),
                    "description": desc,
                })
                result = await execute_action(page, step)
                results.append({"step": i + 1, "description": desc, "result": result})
                await ws.send_json({
                    "type": "step_done",
                    "step": i + 1,
                    "total": len(steps),
                    "description": desc,
                    "result": result[:500],
                })

            page = await browser_mgr.get_page()
            current_url = page.url
            title = await page.title()
            summary = f"Done! {len(steps)} actions. Page: {title}"
            save_entry(session_id, message, summary, steps)

            await ws.send_json({
                "type": "complete",
                "session_id": session_id,
                "current_url": current_url,
                "page_title": title,
                "summary": summary,
            })

    except WebSocketDisconnect:
        log.info("WebSocket client disconnected.")


# ─── Lifecycle ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    log.info("🐕 Winnie is awake and ready to fetch!")


@app.on_event("shutdown")
async def shutdown():
    await browser_mgr.close()


# ─── Entrypoint ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║     🐕 Winnie — Browser Agent        ║")
    print("  ║     http://127.0.0.1:8765            ║")
    print("  ╚══════════════════════════════════════╝")
    print()
    uvicorn.run(app, host="127.0.0.1", port=8765)
