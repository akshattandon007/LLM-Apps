(async () => {
  const el = document.getElementById("status");
  try {
    const r = await fetch("http://127.0.0.1:5174/health");
    if (!r.ok) throw new Error("bad status");
    const data = await r.json();
    if (data.api_key_configured) {
      el.className = "status ok";
      el.innerHTML = `<span class="dot"></span> Backend ready · ${data.model}`;
    } else {
      el.className = "status err";
      el.innerHTML = `<span class="dot"></span> Backend running, but ANTHROPIC_API_KEY not set`;
    }
  } catch (e) {
    el.className = "status err";
    el.innerHTML = `<span class="dot"></span> Backend not reachable — start server.py`;
  }
})();
