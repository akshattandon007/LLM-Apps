/* ════════════════════════════════════════════════════════════════════
   FLIGHTS OVER ME — frontend controller
   Talks to the FastAPI backend, paints planes on a Leaflet radar, and
   wires up the "ask the expert" LLM chat.
   ════════════════════════════════════════════════════════════════════ */

"use strict";

const App = (() => {
  // ---- state -----------------------------------------------------------
  const state = {
    location: null,      // {name, lat, lon}
    accuracy: null,      // GPS accuracy in metres
    watchId: null,       // geolocation watch handle
    radiusKm: 50,
    markers: new Map(),  // icao24 -> Leaflet marker
    anim: new Map(),     // icao24 -> animation state (position/heading tweening)
    animLast: 0,         // timestamp of last animation frame
    flights: new Map(),  // icao24 -> flight object
    selected: null,      // icao24
    ws: null,
    observer: null,      // observer marker
    ring: null,          // radius circle
    llmEnabled: false,
  };

  // ---- DOM -------------------------------------------------------------
  const $ = (id) => document.getElementById(id);
  const el = {
    locationInput: $("locationInput"),
    searchBtn: $("searchBtn"),
    geoBtn: $("geoBtn"),
    radiusSelect: $("radiusSelect"),
    status: $("status"),
    statusText: $("statusText"),
    mapLocation: $("mapLocation"),
    mapCoords: $("mapCoords"),
    mapCount: $("mapCount"),
    overheadBanner: $("overheadBanner"),
    overheadText: $("overheadText"),
    flightList: $("flightList"),
    detail: $("detail"),
    detailTitle: $("detailTitle"),
    detailBody: $("detailBody"),
    closeDetail: $("closeDetail"),
    chatLog: $("chatLog"),
    chatInput: $("chatInput"),
    chatSend: $("chatSend"),
    chatDisabled: $("chatDisabled"),
    chatWrap: $("chatWrap"),
  };

  // ---- map -------------------------------------------------------------
  let map;
  function initMap() {
    map = L.map("map", { zoomControl: true, attributionControl: true }).setView(
      [20, 0],
      3
    );
    // CartoDB dark tiles — fits the cockpit aesthetic and is free to use.
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      {
        maxZoom: 19,
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      }
    ).addTo(map);
  }

  // SVG plane glyph, rotated to the aircraft heading.
  function planeIcon(headingDeg, selected) {
    const rot = headingDeg == null ? 0 : headingDeg;
    return L.divIcon({
      className: "",
      iconSize: [26, 26],
      iconAnchor: [13, 13],
      html: `<div class="plane-icon ${selected ? "selected" : ""}"
                  style="transform: rotate(${rot}deg)">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2c-.5 0-1 .6-1 1.5V9L3 14v2l8-2.5V19l-2 1.2V22l3-1 3 1v-1.8L13 19v-5.5L21 16v-2l-8-5V3.5C13 2.6 12.5 2 12 2z"/>
        </svg>
      </div>`,
    });
  }

  // ---- smooth motion ---------------------------------------------------
  // Aircraft positions arrive only every poll interval (~10s). To avoid the
  // markers teleporting, we dead-reckon each plane forward from its last real
  // fix using its reported velocity + heading, and smoothly reconcile to the
  // authoritative position whenever a fresh snapshot lands.

  const DEG = Math.PI / 180;
  const M_PER_DEG_LAT = 111320; // metres per degree of latitude

  // Advance a position by velocity (m/s) along a heading for dt seconds.
  function deadReckon(lat, lon, velocityMs, headingDeg, dtSec) {
    if (!velocityMs || headingDeg == null) return { lat, lon };
    const north = velocityMs * Math.cos(headingDeg * DEG) * dtSec;
    const east = velocityMs * Math.sin(headingDeg * DEG) * dtSec;
    const cosLat = Math.max(Math.cos(lat * DEG), 1e-6);
    return {
      lat: lat + north / M_PER_DEG_LAT,
      lon: lon + east / (M_PER_DEG_LAT * cosLat),
    };
  }

  // Interpolate an angle along the shortest path (handles the 359°→1° wrap).
  function lerpAngle(from, to, t) {
    const delta = (((to - from) % 360) + 540) % 360 - 180;
    return from + delta * t;
  }

  // The inner .plane-icon element we rotate each frame (cached lazily).
  function innerPlaneEl(marker) {
    const root = marker.getElement();
    return root ? root.querySelector(".plane-icon") : null;
  }

  // ---- status ----------------------------------------------------------
  function setStatus(mode, text) {
    el.status.className = `status status--${mode}`;
    el.statusText.textContent = text;
  }

  // ---- formatting helpers ---------------------------------------------
  const fmt = {
    alt: (f) => {
      const m = f.geo_altitude_m ?? f.baro_altitude_m;
      return m == null ? "—" : `${Math.round(m * 3.28084).toLocaleString()} ft`;
    },
    spd: (f) =>
      f.velocity_ms == null ? "—" : `${Math.round(f.velocity_ms * 1.94384)} kt`,
    vrate: (f) => {
      if (f.vertical_rate_ms == null || Math.abs(f.vertical_rate_ms) < 0.5)
        return "level";
      return f.vertical_rate_ms > 0
        ? `↑ climbing ${Math.round(f.vertical_rate_ms * 196.85)} fpm`
        : `↓ descending ${Math.round(-f.vertical_rate_ms * 196.85)} fpm`;
    },
    compass: (deg) => {
      if (deg == null) return "—";
      const pts = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];
      return pts[Math.round(deg / 22.5) % 16] + ` (${Math.round(deg)}°)`;
    },
    compassShort: (deg) => {
      if (deg == null) return "—";
      const pts = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];
      return pts[Math.round(deg / 22.5) % 16];
    },
    elev: (f) => (f.elevation_deg == null ? "—" : `${Math.round(f.elevation_deg)}° up`),
    slant: (f) => (f.slant_range_km == null ? "—" : `${f.slant_range_km} km line-of-sight`),
    // "👁 look WSW, 52° up" — exactly where to point your eyes.
    lookHint: (f) => {
      if (f.bearing_deg == null) return null;
      const dir = fmt.compassShort(f.bearing_deg);
      if (f.is_overhead) return `👁 nearly straight up — look ${dir}`;
      if (f.elevation_deg == null) return `👁 look ${dir}`;
      return `👁 look ${dir}, ${Math.round(f.elevation_deg)}° above horizon`;
    },
    route: (f) => {
      if (!f.route) return null;
      const o = f.route.origin_iata || "???";
      const d = f.route.destination_iata || "???";
      if (o === "???" && d === "???") return null;
      return { o, d, on: f.route.origin_name, dn: f.route.destination_name };
    },
  };

  function flightTitle(f) {
    return f.callsign || f.registration || f.icao24.toUpperCase();
  }

  // ---- rendering -------------------------------------------------------
  function renderList() {
    let flights = [...state.flights.values()];
    el.mapCount.textContent = `${flights.length} contact${flights.length === 1 ? "" : "s"}`;

    // Surface anything (nearly) directly overhead.
    const overhead = flights
      .filter((f) => f.is_overhead)
      .sort((a, b) => (b.elevation_deg ?? 0) - (a.elevation_deg ?? 0));
    updateOverheadBanner(overhead);

    if (flights.length === 0) {
      el.flightList.innerHTML = `<li class="empty">No aircraft in range right now. Skies are quiet ✦</li>`;
      return;
    }

    // Overhead flights float to the top of the board; everything else stays
    // nearest-first (the backend already sorted by ground distance).
    const overheadIds = new Set(overhead.map((f) => f.icao24));
    flights = [...overhead, ...flights.filter((f) => !overheadIds.has(f.icao24))];

    el.flightList.innerHTML = flights
      .map((f) => {
        const r = fmt.route(f);
        const sub = [f.airline, r ? `${r.o} → ${r.d}` : f.aircraft_type, f.origin_country]
          .filter(Boolean)
          .join(" · ") || "unidentified contact";
        const active = f.icao24 === state.selected ? "active" : "";
        const oh = f.is_overhead ? "overhead" : "";
        const rot = f.true_track_deg ?? 0;
        const look = fmt.lookHint(f);
        const badge = f.is_overhead ? `<span class="oh-badge">↑ OVERHEAD</span>` : "";
        return `
          <li class="strip ${active} ${oh}" data-id="${f.icao24}">
            <span class="glyph" style="transform: rotate(${rot}deg)">➤</span>
            <span class="meta">
              <div class="cs">${flightTitle(f)} ${badge}</div>
              <div class="sub">${sub}</div>
              ${look ? `<div class="look">${look}</div>` : ""}
            </span>
            <span class="tele">
              <div class="dist">${f.distance_km != null ? f.distance_km + " km" : "—"}</div>
              <div class="alt">${fmt.alt(f)}</div>
              <div class="elev">${fmt.elev(f)}</div>
            </span>
          </li>`;
      })
      .join("");

    el.flightList.querySelectorAll(".strip").forEach((node) => {
      node.addEventListener("click", () => selectFlight(node.dataset.id, true));
    });
  }

  function updateOverheadBanner(overhead) {
    if (!overhead || overhead.length === 0) {
      el.overheadBanner.classList.add("hidden");
      return;
    }
    const top = overhead[0];
    const look = fmt.lookHint(top) || "";
    el.overheadText.textContent =
      `${flightTitle(top)} OVERHEAD` +
      (overhead.length > 1 ? ` (+${overhead.length - 1} more)` : "") +
      (look ? `  ·  ${look}` : "");
    el.overheadBanner.classList.remove("hidden");
  }

  // Called once per snapshot: create/remove markers and update each plane's
  // authoritative target + velocity. It never moves a marker directly — the
  // animation loop does, so motion stays smooth between snapshots.
  function reconcileSnapshot() {
    const seen = new Set();
    for (const f of state.flights.values()) {
      if (f.lat == null || f.lon == null) continue;
      seen.add(f.icao24);
      const heading = f.true_track_deg;
      let a = state.anim.get(f.icao24);
      if (a) {
        // Correct dead-reckoning drift toward the real fix.
        a.tgtLat = f.lat;
        a.tgtLon = f.lon;
        a.velocity = f.velocity_ms;
        a.heading = heading;
        a.onGround = f.on_ground;
      } else {
        const marker = L.marker([f.lat, f.lon], {
          icon: planeIcon(heading, f.icao24 === state.selected),
        }).addTo(map);
        marker.on("click", () => selectFlight(f.icao24, false));
        marker.bindTooltip(flightTitle(f), { direction: "top", offset: [0, -10] });
        state.markers.set(f.icao24, marker);
        state.anim.set(f.icao24, {
          icao: f.icao24,
          marker,
          el: null,
          dispLat: f.lat, dispLon: f.lon,   // current rendered position
          tgtLat: f.lat, tgtLon: f.lon,     // best-estimate true position
          velocity: f.velocity_ms,
          heading,
          dispHeading: heading ?? 0,
          onGround: f.on_ground,
          wasSelected: f.icao24 === state.selected,
        });
      }
    }
    // drop aircraft that left the airspace
    for (const [id, marker] of state.markers) {
      if (!seen.has(id)) {
        map.removeLayer(marker);
        state.markers.delete(id);
        state.anim.delete(id);
      }
    }
  }

  // 60fps loop: glide every marker toward its (dead-reckoned) target.
  function animateFrame(now) {
    let dt = (now - state.animLast) / 1000;
    state.animLast = now;
    // Clamp big gaps (e.g. background tab) so planes don't lurch on return.
    if (!isFinite(dt) || dt > 0.25) dt = 0.016;

    const posAlpha = 1 - Math.exp(-dt / 0.6); // position smoothing
    const hdgAlpha = 1 - Math.exp(-dt / 0.3); // heading smoothing

    for (const a of state.anim.values()) {
      // 1. advance the target by dead reckoning (continuous real-time motion)
      if (!a.onGround && a.velocity) {
        const p = deadReckon(a.tgtLat, a.tgtLon, a.velocity, a.heading, dt);
        a.tgtLat = p.lat;
        a.tgtLon = p.lon;
      }
      // 2. ease the rendered position toward the target (absorbs snapshot jumps)
      a.dispLat += (a.tgtLat - a.dispLat) * posAlpha;
      a.dispLon += (a.tgtLon - a.dispLon) * posAlpha;
      a.marker.setLatLng([a.dispLat, a.dispLon]);

      // 3. ease the heading and paint rotation + selection on the DOM directly
      if (a.heading != null) a.dispHeading = lerpAngle(a.dispHeading, a.heading, hdgAlpha);
      const el = a.el || (a.el = innerPlaneEl(a.marker));
      if (el) {
        el.style.transform = `rotate(${a.dispHeading || 0}deg)`;
        const sel = a.icao === state.selected;
        if (sel !== a.wasSelected) {
          el.classList.toggle("selected", sel);
          a.wasSelected = sel;
        }
      }
    }
    requestAnimationFrame(animateFrame);
  }

  function observerCrosshair() {
    return L.divIcon({
      className: "",
      iconSize: [40, 40],
      iconAnchor: [20, 20],
      html: `<div class="observer-cross">
        <span class="oc-ring"></span>
        <span class="oc-h"></span><span class="oc-v"></span>
        <span class="oc-dot"></span>
      </div>`,
    });
  }

  function renderObserver() {
    if (!state.location) return;
    const { lat, lon } = state.location;
    const acc = state.accuracy != null ? ` (±${Math.round(state.accuracy)} m)` : "";
    const label = `📍 ${lat.toFixed(5)}, ${lon.toFixed(5)}${acc}`;
    if (state.observer) {
      state.observer.setLatLng([lat, lon]).setTooltipContent(label);
      state.ring.setLatLng([lat, lon]).setRadius(state.radiusKm * 1000);
    } else {
      state.observer = L.marker([lat, lon], { icon: observerCrosshair(), zIndexOffset: 1000 })
        .addTo(map)
        .bindTooltip(label, { direction: "top", offset: [0, -14] });
      state.ring = L.circle([lat, lon], {
        radius: state.radiusKm * 1000,
        className: "observer-ring",
        color: "#5bd8ff", weight: 1, opacity: 0.45, fillOpacity: 0.04,
      }).addTo(map);
    }
  }

  // ---- selection + detail ---------------------------------------------
  function selectFlight(icao24, pan) {
    state.selected = icao24;
    const f = state.flights.get(icao24);
    if (!f) return;

    if (pan) {
      const a = state.anim.get(icao24);
      const target = a ? [a.dispLat, a.dispLon] : f.lat != null ? [f.lat, f.lon] : null;
      if (target) map.panTo(target);
    }
    renderList();
    renderDetail(f);
  }

  function renderDetail(f) {
    el.detail.classList.remove("hidden");
    el.detailTitle.textContent = flightTitle(f);

    const r = fmt.route(f);
    const routeHtml = r
      ? `<div class="route-line">
           <span class="apt">${r.o}</span>
           <span class="arrow">✈→</span>
           <span class="apt">${r.d}</span>
         </div>
         <div class="sub" style="color:var(--text-dim);font-size:0.72rem;margin:-0.2rem 0 0.5rem">
           ${[r.on, r.dn].filter(Boolean).join("  →  ")}
         </div>`
      : `<div class="sub" style="color:var(--text-faint);font-size:0.74rem;margin-bottom:.5rem">route not available for this callsign</div>`;

    const look = fmt.lookHint(f);
    const lookHtml = look
      ? `<div class="look-banner ${f.is_overhead ? "is-overhead" : ""}">${look}</div>`
      : "";

    const rows = [
      ["AIRLINE", f.airline || f.airline_icao || "—"],
      ["AIRCRAFT", f.aircraft_type || "—"],
      ["REGISTRATION", f.registration || "—"],
      ["ICAO24", f.icao24.toUpperCase()],
      ["REG. COUNTRY", f.origin_country || "—"],
      ["ALTITUDE", fmt.alt(f)],
      ["GROUND SPEED", fmt.spd(f)],
      ["HEADING", fmt.compass(f.true_track_deg)],
      ["VERTICAL", fmt.vrate(f)],
      ["LOOK BEARING", fmt.compass(f.bearing_deg)],
      ["ELEVATION", f.elevation_deg != null ? `${Math.round(f.elevation_deg)}° above horizon` : "—"],
      ["GROUND DIST.", f.distance_km != null ? f.distance_km + " km" : "—"],
      ["LINE-OF-SIGHT", f.slant_range_km != null ? f.slant_range_km + " km" : "—"],
    ];

    el.detailBody.innerHTML =
      lookHtml +
      routeHtml +
      `<dl class="detail-grid">` +
      rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("") +
      `</dl>`;

    el.chatLog.innerHTML = "";
    addChat("bot", `Ask me anything about ${flightTitle(f)} — its aircraft, route, or what it's doing right now. ✈`);
  }

  el.closeDetail.addEventListener("click", () => {
    el.detail.classList.add("hidden");
    state.selected = null;
    renderList();
  });

  // ---- chat ------------------------------------------------------------
  function addChat(role, text) {
    const div = document.createElement("div");
    div.className = `msg ${role}`;
    div.textContent = text;
    el.chatLog.appendChild(div);
    el.chatLog.scrollTop = el.chatLog.scrollHeight;
    return div;
  }

  async function sendChat() {
    const q = el.chatInput.value.trim();
    if (!q || !state.selected) return;
    const flight = state.flights.get(state.selected);
    el.chatInput.value = "";
    addChat("user", q);
    const thinking = addChat("bot", "▍ consulting the flight deck…");
    thinking.classList.add("thinking");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, flight }),
      });
      const data = await res.json();
      thinking.classList.remove("thinking");
      thinking.textContent = res.ok ? data.answer : `⚠ ${data.detail || "chat failed"}`;
    } catch (e) {
      thinking.classList.remove("thinking");
      thinking.textContent = `⚠ network error: ${e.message}`;
    }
    el.chatLog.scrollTop = el.chatLog.scrollHeight;
  }

  el.chatSend.addEventListener("click", sendChat);
  el.chatInput.addEventListener("keydown", (e) => { if (e.key === "Enter") sendChat(); });

  // ---- live tracking ---------------------------------------------------
  function applySnapshot(snap) {
    state.flights = new Map(snap.flights.map((f) => [f.icao24, f]));
    reconcileSnapshot();
    renderList();
    if (state.selected && state.flights.has(state.selected)) {
      renderDetail(state.flights.get(state.selected));
    }
    setStatus("live", `LIVE · ${snap.count} CONTACTS`);
  }

  function startTracking() {
    if (!state.location) return;
    if (state.ws) { state.ws.close(); state.ws = null; }

    // Clear any planes from a previous location so they don't drift in view.
    for (const marker of state.markers.values()) map.removeLayer(marker);
    state.markers.clear();
    state.anim.clear();
    state.flights.clear();

    renderObserver();
    // Zoom to suit the radius: tight for "above me", wide for regional scans.
    const r = state.radiusKm;
    const zoom = r <= 2 ? 13 : r <= 5 ? 12 : r <= 10 ? 11 : r <= 25 ? 10 : r <= 50 ? 9 : r <= 100 ? 8 : 7;
    map.setView([state.location.lat, state.location.lon], zoom);
    el.mapLocation.textContent = state.location.name;
    showCoords();
    setStatus("live", "ACQUIRING…");

    const proto = location.protocol === "https:" ? "wss" : "ws";
    const params = new URLSearchParams({
      lat: state.location.lat,
      lon: state.location.lon,
      radius_km: state.radiusKm,
      name: state.location.name,
    });
    const ws = new WebSocket(`${proto}://${location.host}/ws/flights?${params}`);
    state.ws = ws;

    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === "snapshot") applySnapshot(msg.data);
      else if (msg.type === "error") setStatus("error", msg.message.slice(0, 40));
    };
    ws.onerror = () => setStatus("error", "CONNECTION ERROR");
    ws.onclose = () => { if (state.ws === ws) setStatus("idle", "DISCONNECTED"); };
  }

  // ---- location entry --------------------------------------------------
  async function searchLocation() {
    const q = el.locationInput.value.trim();
    if (!q) return;
    setStatus("idle", "GEOCODING…");
    // Typed location: stop following GPS and clear the accuracy readout.
    if (state.watchId != null) {
      navigator.geolocation.clearWatch(state.watchId);
      state.watchId = null;
    }
    state.accuracy = null;
    // If the user typed raw "lat, lon", show it at full precision on the map.
    const m = q.match(/^\s*(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)\s*$/);
    try {
      const res = await fetch(`/api/geocode?q=${encodeURIComponent(q)}`);
      if (!res.ok) {
        const e = await res.json();
        setStatus("error", "NOT FOUND");
        alert(e.detail || "Location not found");
        return;
      }
      state.location = await res.json();
      if (m) state.location.name = "Pinned coordinates";
      startTracking();
    } catch (e) {
      setStatus("error", "GEOCODE FAILED");
    }
  }

  // rough metres between two coords (for detecting real movement)
  function metresBetween(a, b) {
    const R = 6371008.8;
    const dLat = ((b.lat - a.lat) * Math.PI) / 180;
    const dLon = ((b.lon - a.lon) * Math.PI) / 180;
    const la1 = (a.lat * Math.PI) / 180;
    const la2 = (b.lat * Math.PI) / 180;
    const h =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  }

  function showCoords() {
    if (!state.location) { el.mapCoords.textContent = ""; return; }
    const { lat, lon } = state.location;
    const acc = state.accuracy != null ? `  ±${Math.round(state.accuracy)} m` : "";
    // 5 decimal places ≈ 1.1 m precision — house-level.
    el.mapCoords.textContent = `📍 ${lat.toFixed(5)}, ${lon.toFixed(5)}${acc}`;
  }

  function useMyLocation() {
    if (!navigator.geolocation) {
      alert("Geolocation unavailable in this browser.");
      return;
    }
    setStatus("idle", "LOCATING…");
    if (state.watchId != null) navigator.geolocation.clearWatch(state.watchId);

    state.watchId = navigator.geolocation.watchPosition(
      (pos) => {
        const fix = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        state.accuracy = pos.coords.accuracy;
        const first = state.location == null;
        const moved = !first && metresBetween(state.location, fix) > 150;

        state.location = { name: "Above my location", ...fix };
        el.locationInput.value = `${fix.lat.toFixed(5)}, ${fix.lon.toFixed(5)}`;
        showCoords();

        if (first || moved) {
          startTracking();      // (re)centre the search on the new fix
        } else {
          renderObserver();     // just refine the pin in place
        }
      },
      () => setStatus("error", "LOCATION DENIED"),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  }

  // ---- init ------------------------------------------------------------
  async function checkLLM() {
    try {
      const res = await fetch("/api/health");
      const h = await res.json();
      state.llmEnabled = h.llm_enabled;
    } catch { state.llmEnabled = false; }
    if (!state.llmEnabled) {
      el.chatInput.disabled = true;
      el.chatSend.disabled = true;
      el.chatDisabled.classList.remove("hidden");
    }
  }

  function bind() {
    el.searchBtn.addEventListener("click", searchLocation);
    el.locationInput.addEventListener("keydown", (e) => { if (e.key === "Enter") searchLocation(); });
    el.geoBtn.addEventListener("click", useMyLocation);
    el.radiusSelect.addEventListener("change", () => {
      state.radiusKm = Number(el.radiusSelect.value);
      if (state.location) startTracking();
    });
  }

  function init() {
    initMap();
    bind();
    checkLLM();
    setStatus("idle", "STANDBY");
    // Kick off the smooth-motion render loop (runs for the page lifetime).
    state.animLast = performance.now();
    requestAnimationFrame(animateFrame);
  }

  return { init };
})();

document.addEventListener("DOMContentLoaded", App.init);
