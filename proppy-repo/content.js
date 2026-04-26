// Proppy — injected chat widget using Shadow DOM for full style isolation
(function () {
  if (document.getElementById('proppy-host')) return;

  // ── Shadow DOM host — fully isolated from page CSS ─────────────────────
  const host = document.createElement('div');
  host.id = 'proppy-host';
  Object.assign(host.style, {
    position: 'fixed', bottom: '0', right: '0',
    width: '0', height: '0',
    zIndex: '2147483647',
    overflow: 'visible',
    pointerEvents: 'none',
  });
  document.body.appendChild(host);
  const shadow = host.attachShadow({ mode: 'open' });

  // ── All CSS inside the shadow — zero leakage either way ───────────────
  const css = `
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=Nunito+Sans:wght@400;600;700&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    /* Typography scale — 4-step: 11 / 13 / 15 / 20 */
    :host { font-family: 'Nunito Sans', sans-serif; font-size: 14px; line-height: 1.5; }

    /* ── LAUNCHER ─────────────────────────────────────────────────────── */
    #launcher {
      position: fixed; bottom: 28px; right: 28px;
      display: flex; flex-direction: column; align-items: center;
      cursor: pointer; user-select: none; pointer-events: all;
    }

    .tip {
      background: #1A1A2E; color: #fff;
      font-family: 'Nunito', sans-serif; font-size: 12px; font-weight: 800;
      padding: 5px 12px; border-radius: 20px;
      border: 2px solid rgba(28,176,246,.35);
      box-shadow: 0 4px 16px rgba(28,176,246,.25);
      white-space: nowrap; margin-bottom: 10px;
      opacity: 0; transform: translateY(4px) scale(.92);
      transition: all .22s cubic-bezier(.34,1.56,.64,1);
      pointer-events: none;
    }
    #launcher:hover .tip { opacity: 1; transform: translateY(0) scale(1); }

    .mascot-wrap {
      position: relative;
      filter: drop-shadow(0 8px 24px rgba(28,176,246,.4)) drop-shadow(0 3px 6px rgba(0,0,0,.18));
      transition: transform .28s cubic-bezier(.34,1.56,.64,1);
    }
    #launcher:hover .mascot-wrap { transform: translateY(-10px) scale(1.08); }
    #launcher:active .mascot-wrap { transform: scale(.93) translateY(2px); }

    .badge {
      position: absolute; top: -4px; right: -4px;
      background: #FF4B4B; color: #fff;
      border-radius: 50%; width: 20px; height: 20px;
      font-size: 10px; font-weight: 900; font-family: 'Nunito', sans-serif;
      border: 2.5px solid #fff; box-shadow: 0 2px 6px rgba(0,0,0,.28);
      display: none; align-items: center; justify-content: center;
    }
    .badge.show { display: flex; }

    /* mascot anims */
    @keyframes float {
      0%,100%{ transform:translateY(0) scaleX(1) scaleY(1) }
      30%{ transform:translateY(-12px) scaleX(.95) scaleY(1.05) }
      60%{ transform:translateY(-6px) scaleX(1.02) scaleY(.98) }
    }
    @keyframes blink {
      0%,88%,100%{ transform:scaleY(1) }
      91%{ transform:scaleY(.05) }
      94%{ transform:scaleY(1) }
      96%{ transform:scaleY(.05) }
    }
    @keyframes ear-l { 0%,100%{transform:rotate(0)} 40%{transform:rotate(-10deg)} 70%{transform:rotate(-4deg)} }
    @keyframes ear-r { 0%,100%{transform:rotate(0)} 40%{transform:rotate(10deg)} 70%{transform:rotate(4deg)} }
    @keyframes shadow-a { 0%,100%{transform:scaleX(1);opacity:.12} 45%{transform:scaleX(.6);opacity:.05} }

    .m-all  { animation: float 2.8s ease-in-out infinite; transform-origin: bottom center; }
    .m-eye  { animation: blink 4s ease-in-out infinite; transform-origin: center; }
    .m-earl { animation: ear-l 2.8s ease-in-out infinite; transform-origin: bottom right; }
    .m-earr { animation: ear-r 2.8s ease-in-out infinite; transform-origin: bottom left; animation-delay:.3s; }
    .m-shad { animation: shadow-a 2.8s ease-in-out infinite; transform-origin: center; }

    /* ── PANEL ────────────────────────────────────────────────────────── */
    #panel {
      position: fixed; bottom: 110px; right: 28px;
      width: 360px; height: 580px;
      background: #F5F5F5; border-radius: 20px; overflow: hidden;
      display: flex; flex-direction: column;
      box-shadow: 0 20px 60px rgba(0,0,0,.22), 0 0 0 1.5px rgba(28,176,246,.2);
      transform: scale(.88) translateY(16px);
      transform-origin: bottom right;
      transition: transform .3s cubic-bezier(.34,1.4,.64,1), opacity .3s ease;
      opacity: 0; pointer-events: none;
    }
    #panel.open { transform: scale(1) translateY(0); opacity: 1; pointer-events: all; }

    /* ── HEADER ── */
    .hdr {
      background: #1CB0F6;
      padding: 12px 16px;
      display: flex; align-items: center; justify-content: space-between;
      flex-shrink: 0;
    }
    .hdr-brand { display: flex; align-items: center; gap: 10px; }
    .hdr-name {
      font-family: 'Nunito', sans-serif; font-size: 20px; font-weight: 900;
      color: #fff; letter-spacing: -.4px; line-height: 1;
      text-shadow: 0 2px 0 rgba(0,0,0,.15);
    }
    .hdr-sub { font-size: 11px; font-weight: 700; color: rgba(255,255,255,.82); margin-top: 1px; }
    .hdr-close {
      background: rgba(255,255,255,.2); border: 1.5px solid rgba(255,255,255,.35);
      border-radius: 8px; padding: 5px 10px; font-size: 14px; font-weight: 900;
      color: #fff; cursor: pointer; line-height: 1; font-family: 'Nunito', sans-serif;
      transition: background .15s;
    }
    .hdr-close:hover { background: rgba(255,255,255,.35); }

    /* ── TABS ── */
    .tabs {
      display: flex; background: #fff;
      border-bottom: 2px solid #EBEBEB; flex-shrink: 0;
    }
    .tab {
      flex: 1; padding: 11px 4px;
      font-family: 'Nunito', sans-serif; font-size: 12px; font-weight: 800;
      color: #AAAAAA; background: none; border: none; cursor: pointer;
      border-bottom: 3px solid transparent; margin-bottom: -2px;
      transition: color .15s, border-color .15s;
    }
    .tab.on { color: #1CB0F6; border-bottom-color: #1CB0F6; }

    /* ── PANELS ── */
    .pane { display: none; flex: 1; flex-direction: column; overflow: hidden; min-height: 0; }
    .pane.on { display: flex; }

    /* ── CHAT ── */
    .msgs {
      flex: 1; overflow-y: auto; overflow-x: hidden;
      padding: 16px; display: flex; flex-direction: column; gap: 12px;
      min-height: 0;
    }
    /* Custom scrollbar */
    .msgs::-webkit-scrollbar { width: 4px; }
    .msgs::-webkit-scrollbar-track { background: transparent; }
    .msgs::-webkit-scrollbar-thumb { background: #DDD; border-radius: 4px; }

    .row { display: flex; flex-direction: column; width: 100%; }
    .row.bot { align-items: flex-start; }
    .row.usr { align-items: flex-end; }

    .bubble {
      /* Critical: constrain width so text wraps, never overflows */
      max-width: 78%;
      width: fit-content;
      padding: 10px 14px;
      font-family: 'Nunito Sans', sans-serif;
      font-size: 14px; font-weight: 500; line-height: 1.6;
      color: #2C2C2C;
      word-break: break-word; overflow-wrap: break-word;
    }
    .row.bot .bubble {
      background: #fff; border-radius: 4px 18px 18px 18px;
      border: 1.5px solid #E8E8E8; box-shadow: 0 2px 0 #E8E8E8;
    }
    .row.usr .bubble {
      background: #1CB0F6; color: #fff;
      border-radius: 18px 18px 4px 18px;
      border: 1.5px solid #0A91D0; box-shadow: 0 2px 0 #0A91D0;
      font-weight: 600;
    }
    .ts {
      font-size: 11px; color: #BBBBBB; font-weight: 600;
      margin-top: 4px; padding: 0 4px;
    }
    .row.usr .ts { text-align: right; }

    /* Listing card */
    .card {
      max-width: 90%; width: 100%;
      background: #fff; border-radius: 14px;
      border: 1.5px solid #E8E8E8; box-shadow: 0 2px 0 #E8E8E8;
      padding: 12px 14px; margin-top: 4px;
      overflow: hidden;
    }
    .card-src { font-size: 10px; font-weight: 900; color: #1CB0F6; text-transform: uppercase; letter-spacing: .6px; margin-bottom: 4px; }
    .card-title { font-family: 'Nunito', sans-serif; font-size: 14px; font-weight: 900; color: #2C2C2C; margin-bottom: 3px; }
    .card-price { font-family: 'Nunito', sans-serif; font-size: 18px; font-weight: 900; color: #58CC02; margin-bottom: 3px; }
    .card-detail { font-size: 12px; font-weight: 500; color: #888; line-height: 1.5; }
    .card-link {
      display: inline-block; margin-top: 10px;
      background: #1CB0F6; color: #fff;
      font-family: 'Nunito', sans-serif; font-size: 12px; font-weight: 800;
      padding: 6px 14px; border-radius: 20px;
      border: 1.5px solid #0A91D0; box-shadow: 0 3px 0 #0A91D0;
      text-decoration: none; cursor: pointer;
    }

    /* Typing indicator */
    .typing-wrap { padding: 0 16px 8px; }
    .typing {
      display: none; background: #fff;
      border: 1.5px solid #E8E8E8; border-radius: 4px 14px 14px 14px;
      padding: 10px 14px; width: fit-content; box-shadow: 0 2px 0 #E8E8E8;
    }
    .typing.on { display: flex; align-items: center; gap: 5px; }
    .dot {
      width: 7px; height: 7px; background: #CCC; border-radius: 50%;
      animation: bop 1.1s infinite;
    }
    .dot:nth-child(2){ animation-delay:.18s }
    .dot:nth-child(3){ animation-delay:.36s }
    @keyframes bop{ 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-6px)} }

    /* Input row */
    .input-row {
      padding: 10px 12px; border-top: 2px solid #EBEBEB;
      background: #fff; display: flex; align-items: flex-end; gap: 8px;
      flex-shrink: 0;
    }
    textarea {
      flex: 1; border: 1.5px solid #E0E0E0; border-radius: 20px;
      padding: 9px 14px; font-family: 'Nunito Sans', sans-serif;
      font-size: 14px; font-weight: 500; color: #2C2C2C;
      background: #F5F5F5; outline: none; resize: none;
      min-height: 40px; max-height: 80px; line-height: 1.4;
      transition: border-color .18s;
    }
    textarea:focus { border-color: #1CB0F6; background: #fff; }
    textarea::placeholder { color: #BBBBBB; }
    .send {
      background: #1CB0F6; border: 1.5px solid #0A91D0;
      border-radius: 50%; width: 40px; height: 40px;
      cursor: pointer; color: #fff; font-size: 16px;
      flex-shrink: 0; display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 0 #0A91D0; transition: all .1s;
    }
    .send:hover { background: #0A91D0; }
    .send:active { transform: translateY(3px); box-shadow: 0 1px 0 #0A91D0; }
    .send:disabled { background: #DDD; border-color: #CCC; box-shadow: 0 3px 0 #CCC; cursor: not-allowed; }

    /* ── WISHLIST ── */
    .scroll { flex: 1; overflow-y: auto; padding: 12px 14px 20px; min-height: 0; }
    .scroll::-webkit-scrollbar { width: 4px; }
    .scroll::-webkit-scrollbar-thumb { background: #DDD; border-radius: 4px; }

    .section {
      background: #fff; border-radius: 14px;
      border: 1.5px solid #EBEBEB; box-shadow: 0 2px 0 #EBEBEB;
      padding: 14px; margin-bottom: 10px;
    }
    .section:last-child { margin-bottom: 0; }

    .sec-head {
      font-family: 'Nunito', sans-serif; font-size: 13px; font-weight: 900;
      color: #2C2C2C; margin-bottom: 12px;
      display: flex; align-items: center; gap: 6px;
    }

    /* Input fields inside sections */
    .lbl { font-size: 11px; font-weight: 800; color: #AAAAAA; text-transform: uppercase; letter-spacing: .7px; margin-bottom: 5px; }
    .f { margin-bottom: 10px; }
    .f:last-child { margin-bottom: 0; }
    input[type=text], input[type=number], select {
      width: 100%;
      border: 1.5px solid #E0E0E0; border-radius: 10px;
      padding: 10px 12px;
      font-family: 'Nunito Sans', sans-serif; font-size: 14px; font-weight: 500;
      color: #2C2C2C; background: #F5F5F5;
      outline: none; transition: border-color .18s, background .18s;
      -webkit-appearance: auto; appearance: auto;
    }
    input[type=text]:focus, input[type=number]:focus, select:focus {
      border-color: #1CB0F6; background: #fff;
    }
    input::placeholder { color: #BBBBBB; font-size: 13px; }
    .g2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

    /* Chips */
    .chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip {
      padding: 7px 13px; border-radius: 20px;
      border: 1.5px solid #E0E0E0;
      font-family: 'Nunito', sans-serif; font-size: 12px; font-weight: 800;
      color: #888; background: #F5F5F5; cursor: pointer;
      box-shadow: 0 2px 0 #E0E0E0;
      transition: all .12s; user-select: none; white-space: nowrap;
    }
    .chip.on {
      background: #E6F4FF; border-color: #0A91D0; color: #0A91D0;
      box-shadow: 0 2px 0 #0A91D0;
    }
    .chip:active { transform: translateY(2px); box-shadow: none; }

    /* Buttons */
    .btn-primary {
      width: 100%; padding: 13px 0; margin-top: 12px;
      background: #1CB0F6; color: #fff;
      border: 1.5px solid #0A91D0; border-radius: 14px;
      font-family: 'Nunito', sans-serif; font-size: 16px; font-weight: 900;
      cursor: pointer; box-shadow: 0 4px 0 #0A91D0;
      transition: all .1s; display: block; text-align: center;
    }
    .btn-primary:hover { background: #0A91D0; }
    .btn-primary:active { transform: translateY(3px); box-shadow: 0 1px 0 #0A91D0; }

    .btn-secondary {
      width: 100%; padding: 11px 0;
      background: #F5F5F5; color: #2C2C2C;
      border: 1.5px solid #E0E0E0; border-radius: 12px;
      font-family: 'Nunito', sans-serif; font-size: 14px; font-weight: 800;
      cursor: pointer; box-shadow: 0 3px 0 #E0E0E0;
      transition: all .1s; display: block; text-align: center;
    }
    .btn-secondary:hover { border-color: #1CB0F6; color: #1CB0F6; background: #E6F4FF; }
    .btn-secondary:active { transform: translateY(2px); box-shadow: none; }

    /* ── CONFIG ── */
    .notice {
      background: #FFFBEB; border: 1.5px solid #F5C518; border-radius: 12px;
      padding: 12px 14px; margin-bottom: 10px;
      font-size: 13px; font-weight: 600; color: #5C4A00; line-height: 1.6;
    }
    .status {
      display: flex; align-items: center; gap: 8px;
      font-size: 12px; font-weight: 700; color: #888;
      padding: 10px 0 8px;
    }
    .dot-status {
      width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
      background: #CCC; border: 1.5px solid rgba(0,0,0,.08);
      transition: background .2s;
    }
    .dot-status.ok  { background: #58CC02; border-color: #3A9900; }
    .dot-status.err { background: #FF4B4B; border-color: #CC0000; }

    .toggle-row {
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 0; border-bottom: 1.5px solid #F0F0F0; margin-bottom: 12px;
    }
    .toggle-lbl { font-size: 14px; font-weight: 700; color: #2C2C2C; }
    .tog { position: relative; width: 44px; height: 24px; }
    .tog input { opacity: 0; width: 0; height: 0; }
    .tog-slider {
      position: absolute; inset: 0; background: #DDD; border-radius: 24px;
      cursor: pointer; transition: background .2s; border: 1.5px solid rgba(0,0,0,.08);
    }
    .tog-slider:before {
      content: ''; position: absolute; width: 16px; height: 16px;
      left: 3px; bottom: 3px; background: #fff; border-radius: 50%;
      transition: transform .2s; box-shadow: 0 1px 3px rgba(0,0,0,.2);
    }
    .tog input:checked + .tog-slider { background: #58CC02; border-color: #3A9900; }
    .tog input:checked + .tog-slider:before { transform: translateX(20px); }
  `;

  // ── Koala SVG mascot (Duolingo-style: bold outlines, flat fills, transparent layers) ──
  const KOALA_LAUNCHER = `
    <svg width="72" height="80" viewBox="0 0 90 100" xmlns="http://www.w3.org/2000/svg">
      <ellipse class="m-shad" cx="45" cy="97" rx="24" ry="4" fill="#1CB0F6" opacity="0.12"/>
      <g class="m-all">

        <!-- EARS — large fluffy koala ears, key distinguishing feature -->
        <g class="m-earl">
          <circle cx="16" cy="30" r="16" fill="#A0C4D8"/>
          <circle cx="16" cy="30" r="10" fill="#C8E6F0"/>
          <circle cx="16" cy="30" r="6"  fill="#E8F6FF" opacity=".7"/>
        </g>
        <g class="m-earr">
          <circle cx="74" cy="30" r="16" fill="#A0C4D8"/>
          <circle cx="74" cy="30" r="10" fill="#C8E6F0"/>
          <circle cx="74" cy="30" r="6"  fill="#E8F6FF" opacity=".7"/>
        </g>

        <!-- BODY -->
        <ellipse cx="45" cy="72" rx="28" ry="26" fill="#1CB0F6"/>
        <!-- chest/belly patch -->
        <ellipse cx="45" cy="78" rx="17" ry="16" fill="#E8F6FF" opacity=".85"/>
        <!-- body fur texture (transparent arcs) -->
        <path d="M24 60 Q35 55 45 60 Q55 55 66 60" fill="none" stroke="rgba(255,255,255,.22)" stroke-width="1.5" stroke-linecap="round"/>
        <path d="M21 68 Q33 63 45 68 Q57 63 69 68" fill="none" stroke="rgba(255,255,255,.18)" stroke-width="1.5" stroke-linecap="round"/>

        <!-- ARMS — short stubby koala arms -->
        <ellipse cx="18" cy="76" rx="9" ry="6" fill="#0E99D6" opacity=".85" transform="rotate(-25 18 76)"/>
        <ellipse cx="72" cy="76" rx="9" ry="6" fill="#0E99D6" opacity=".85" transform="rotate(25 72 76)"/>

        <!-- LEGS/FEET -->
        <ellipse cx="34" cy="95" rx="9" ry="5" fill="#0E99D6" opacity=".8"/>
        <ellipse cx="56" cy="95" rx="9" ry="5" fill="#0E99D6" opacity=".8"/>

        <!-- HEAD -->
        <circle cx="45" cy="44" r="28" fill="#1CB0F6"/>
        <circle cx="45" cy="44" r="28" fill="rgba(93,211,255,.5)"/>
        <!-- head fur texture -->
        <path d="M24 34 Q35 28 45 34 Q55 28 66 34" fill="none" stroke="rgba(255,255,255,.28)" stroke-width="1.5" stroke-linecap="round"/>

        <!-- HOUSE HAT — orange roof triangle (Proppy signature) -->
        <polygon points="45,7 19,29 71,29" fill="#FF9600"/>
        <polygon points="45,11 23,28 40,28" fill="rgba(255,255,255,.16)"/>
        <!-- chimney -->
        <rect x="58" y="13" width="7" height="12" rx="2" fill="#3C3C3C" opacity=".88"/>
        <rect x="56" y="12" width="11" height="4" rx="2" fill="#222" opacity=".85"/>
        <circle cx="62" cy="8" r="3" fill="#DDD" opacity=".6"/>
        <circle cx="65" cy="5" r="2" fill="#DDD" opacity=".4"/>

        <!-- BIG KOALA NOSE — prominent oval, signature feature -->
        <ellipse cx="45" cy="50" rx="10" ry="7" fill="#1A1A2E"/>
        <ellipse cx="45" cy="50" rx="10" ry="7" fill="none" stroke="rgba(255,255,255,.15)" stroke-width="1"/>
        <!-- nose highlight -->
        <ellipse cx="42" cy="47" rx="3" ry="2" fill="rgba(255,255,255,.35)"/>

        <!-- EYES — large round, Duolingo character style -->
        <circle cx="32" cy="38" r="10" fill="white"/>
        <circle cx="58" cy="38" r="10" fill="white"/>
        <!-- eye socket shadow (transparent depth) -->
        <circle cx="32" cy="39" r="9"  fill="rgba(28,176,246,.06)"/>
        <circle cx="58" cy="39" r="9"  fill="rgba(28,176,246,.06)"/>

        <g class="m-eye">
          <!-- iris -->
          <circle cx="33" cy="39" r="6" fill="#2C1A0E"/>
          <circle cx="59" cy="39" r="6" fill="#2C1A0E"/>
          <!-- pupil -->
          <circle cx="33" cy="39" r="3.8" fill="#0A0A0A"/>
          <circle cx="59" cy="39" r="3.8" fill="#0A0A0A"/>
          <!-- catchlight primary -->
          <ellipse cx="31" cy="37" rx="2.2" ry="1.8" fill="white"/>
          <ellipse cx="57" cy="37" rx="2.2" ry="1.8" fill="white"/>
          <!-- catchlight secondary -->
          <circle cx="35" cy="41" r=".9" fill="white" opacity=".55"/>
          <circle cx="61" cy="41" r=".9" fill="white" opacity=".55"/>
        </g>

        <!-- EYEBROWS — thick expressive, Duo-style -->
        <path d="M22 28 Q31 22 40 27" fill="none" stroke="#0A2040" stroke-width="3.5" stroke-linecap="round" opacity=".8"/>
        <path d="M50 27 Q59 22 68 28" fill="none" stroke="#0A2040" stroke-width="3.5" stroke-linecap="round" opacity=".8"/>

        <!-- BLUSH (transparent circles, koala cheeks) -->
        <ellipse cx="20" cy="48" rx="7" ry="5" fill="#FF9600" opacity=".22"/>
        <ellipse cx="70" cy="48" rx="7" ry="5" fill="#FF9600" opacity=".22"/>

        <!-- MOUTH — gentle smile -->
        <path d="M37 57 Q45 63 53 57" fill="none" stroke="#0A2040" stroke-width="2" stroke-linecap="round" opacity=".7"/>

        <!-- tiny house door on belly -->
        <rect x="39" y="84" width="12" height="10" rx="2.5" fill="#FF9600" opacity=".85"/>
        <circle cx="49" cy="89" r="1.2" fill="#CC6600" opacity=".8"/>
        <!-- tiny windows -->
        <rect x="24" y="72" width="6" height="6" rx="1.5" fill="#84D8FF" opacity=".75"/>
        <line x1="27" y1="72" x2="27" y2="78" stroke="rgba(28,176,246,.35)" stroke-width=".8"/>
        <line x1="24" y1="75" x2="30" y2="75" stroke="rgba(28,176,246,.35)" stroke-width=".8"/>
        <rect x="60" y="72" width="6" height="6" rx="1.5" fill="#84D8FF" opacity=".75"/>
        <line x1="63" y1="72" x2="63" y2="78" stroke="rgba(28,176,246,.35)" stroke-width=".8"/>
        <line x1="60" y1="75" x2="66" y2="75" stroke="rgba(28,176,246,.35)" stroke-width=".8"/>

      </g>
    </svg>`;

  const KOALA_HDR = `
    <svg width="40" height="40" viewBox="0 0 90 90" xmlns="http://www.w3.org/2000/svg">
      <circle cx="18" cy="30" r="14" fill="#A0C4D8"/>
      <circle cx="18" cy="30" r="8"  fill="#C8E6F0"/>
      <circle cx="72" cy="30" r="14" fill="#A0C4D8"/>
      <circle cx="72" cy="30" r="8"  fill="#C8E6F0"/>
      <ellipse cx="45" cy="65" rx="25" ry="23" fill="#1CB0F6"/>
      <ellipse cx="45" cy="70" rx="15" ry="14" fill="#E8F6FF" opacity=".8"/>
      <circle cx="45" cy="40" r="26" fill="#1CB0F6"/>
      <polygon points="45,6 20,25 70,25" fill="#FF9600"/>
      <rect x="56" y="12" width="7" height="11" rx="2" fill="#3C3C3C" opacity=".88"/>
      <ellipse cx="45" cy="45" rx="9" ry="6.5" fill="#1A1A2E"/>
      <ellipse cx="41" cy="43" rx="2.5" ry="1.8" fill="rgba(255,255,255,.35)"/>
      <circle cx="33" cy="35" r="9" fill="white"/>
      <circle cx="57" cy="35" r="9" fill="white"/>
      <circle cx="34" cy="36" r="5.5" fill="#2C1A0E"/>
      <circle cx="58" cy="36" r="5.5" fill="#2C1A0E"/>
      <circle cx="32" cy="34" r="2"   fill="white"/>
      <circle cx="56" cy="34" r="2"   fill="white"/>
      <path d="M23 25 Q31 20 39 24" fill="none" stroke="#0A2040" stroke-width="3" stroke-linecap="round" opacity=".8"/>
      <path d="M51 24 Q59 20 67 25" fill="none" stroke="#0A2040" stroke-width="3" stroke-linecap="round" opacity=".8"/>
      <path d="M36 52 Q45 58 54 52" fill="none" stroke="#0A2040" stroke-width="1.8" stroke-linecap="round" opacity=".7"/>
      <rect x="39" y="75" width="12" height="9" rx="2" fill="#FF9600" opacity=".85"/>
    </svg>`;

  // ── Shadow DOM content ──────────────────────────────────────────────────
  shadow.innerHTML = `
    <style>${css}</style>

    <div id="launcher">
      <div class="tip">Proppy — find your dream home 🏡</div>
      <div class="mascot-wrap">
        <span class="badge" id="badge">!</span>
        ${KOALA_LAUNCHER}
      </div>
    </div>

    <div id="panel">
      <!-- Header -->
      <div class="hdr">
        <div class="hdr-brand">
          ${KOALA_HDR}
          <div>
            <div class="hdr-name">Proppy</div>
            <div class="hdr-sub">Your chaotic house hunter 🏡</div>
          </div>
        </div>
        <button class="hdr-close" id="close-btn">✕</button>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button class="tab on"  data-p="chat">💬 Chat</button>
        <button class="tab"     data-p="wish">⭐ Wishlist</button>
        <button class="tab"     data-p="cfg">⚙️ Config</button>
      </div>

      <!-- ── CHAT PANE ── -->
      <div class="pane on" id="pane-chat">
        <div class="msgs" id="msgs">
          <div class="row bot">
            <div class="bubble">
              Hey there! 👋 I'm <strong>Proppy</strong> — your AI house hunter.<br><br>
              I search Rightmove, Zoopla and the whole internet so you don't have to.<br><br>
              <em>Where are you looking to buy or rent?</em> 🌍
            </div>
            <div class="ts">just now</div>
          </div>
        </div>
        <div class="typing-wrap">
          <div class="typing" id="typing">
            <div class="dot"></div><div class="dot"></div><div class="dot"></div>
          </div>
        </div>
        <div class="input-row">
          <textarea id="input" placeholder="Tell Proppy what you're after..." rows="1"></textarea>
          <button class="send" id="send-btn">➤</button>
        </div>
      </div>

      <!-- ── WISHLIST PANE ── -->
      <div class="pane" id="pane-wish">
        <div class="scroll">

          <div class="section">
            <div class="sec-head">📍 Location</div>
            <div class="f">
              <div class="lbl">City or area</div>
              <input type="text" id="w-loc" placeholder="e.g. London, Bristol, Manchester">
            </div>
            <div class="f">
              <div class="lbl">Max commute (mins)</div>
              <input type="number" id="w-commute" placeholder="e.g. 30">
            </div>
          </div>

          <div class="section">
            <div class="sec-head">💰 Budget</div>
            <div class="g2">
              <div class="f">
                <div class="lbl">Min (£)</div>
                <input type="number" id="w-min" placeholder="0">
              </div>
              <div class="f">
                <div class="lbl">Max (£)</div>
                <input type="number" id="w-max" placeholder="500,000">
              </div>
            </div>
          </div>

          <div class="section">
            <div class="sec-head">🏠 Property type</div>
            <div class="chips" id="w-types">
              <span class="chip" data-v="flat">Flat</span>
              <span class="chip" data-v="house">House</span>
              <span class="chip" data-v="terraced">Terraced</span>
              <span class="chip" data-v="semi-detached">Semi-det.</span>
              <span class="chip" data-v="detached">Detached</span>
              <span class="chip" data-v="bungalow">Bungalow</span>
              <span class="chip" data-v="studio">Studio</span>
            </div>
          </div>

          <div class="section">
            <div class="sec-head">🔑 Ownership</div>
            <div class="chips" id="w-own">
              <span class="chip" data-v="buy">Buy</span>
              <span class="chip" data-v="rent">Rent</span>
              <span class="chip" data-v="shared-ownership">Shared</span>
            </div>
          </div>

          <div class="section">
            <div class="sec-head">🛏 Bedrooms</div>
            <div class="g2">
              <div class="f">
                <div class="lbl">Min</div>
                <select id="w-bmin"><option value="">Any</option><option>1</option><option>2</option><option>3</option><option>4</option><option>5+</option></select>
              </div>
              <div class="f">
                <div class="lbl">Max</div>
                <select id="w-bmax"><option value="">Any</option><option>1</option><option>2</option><option>3</option><option>4</option><option>5+</option></select>
              </div>
            </div>
          </div>

          <div class="section">
            <div class="sec-head">✨ Must haves</div>
            <div class="chips" id="w-feat">
              <span class="chip" data-v="garden">Garden</span>
              <span class="chip" data-v="parking">Parking</span>
              <span class="chip" data-v="garage">Garage</span>
              <span class="chip" data-v="new-build">New Build</span>
              <span class="chip" data-v="period">Period</span>
              <span class="chip" data-v="pets">Pets OK</span>
              <span class="chip" data-v="no-chain">No Chain</span>
              <span class="chip" data-v="epc-c">EPC C+</span>
            </div>
          </div>

          <button class="btn-primary" id="save-wish">Save wishlist ✨</button>
        </div>
      </div>

      <!-- ── CONFIG PANE ── -->
      <div class="pane" id="pane-cfg">
        <div class="scroll">
          <div class="notice">
            🔑 Proppy talks to Anthropic directly — no server required. Add your API key and she's ready to hunt.
          </div>

          <div class="section">
            <div class="lbl">Anthropic API key</div>
            <input type="password" id="c-key" placeholder="sk-ant-..." style="margin-top:4px">
            <div class="status">
              <span class="dot-status" id="c-dot"></span>
              <span id="c-txt">Not tested yet</span>
            </div>
            <button class="btn-secondary" id="c-test">Test connection 🔌</button>
          </div>

          <div class="section">
            <div class="toggle-row">
              <span class="toggle-lbl">Notify on new listings</span>
              <label class="tog"><input type="checkbox" id="c-notify" checked><span class="tog-slider"></span></label>
            </div>
            <div class="lbl">Search interval</div>
            <select id="c-interval" style="margin-top:4px">
              <option value="60">Every hour</option>
              <option value="360">Every 6 hours</option>
              <option value="720" selected>Every 12 hours</option>
              <option value="1440">Daily</option>
            </select>
          </div>

          <button class="btn-primary" id="save-cfg" style="background:#1CB0F6;border-color:#0A91D0;box-shadow:0 4px 0 #0A91D0;">
            Save config 💾
          </button>
        </div>
      </div>
    </div>
  `;

  // ── Wire JS ─────────────────────────────────────────────────────────────
  const $ = id => shadow.getElementById(id);
  const $$ = sel => shadow.querySelectorAll(sel);

  // toggle panel
  const panel = $('panel');
  $('launcher').addEventListener('click', () => {
    panel.classList.toggle('open');
    $('badge').classList.remove('show');
  });
  $('close-btn').addEventListener('click', () => panel.classList.remove('open'));

  // tabs
  $$('.tab').forEach(t => t.addEventListener('click', () => {
    $$('.tab').forEach(x => x.classList.remove('on'));
    $$('.pane').forEach(x => x.classList.remove('on'));
    t.classList.add('on');
    $('pane-' + t.dataset.p).classList.add('on');
  }));

  // chips
  $$('.chip').forEach(c => c.addEventListener('click', () => c.classList.toggle('on')));

  // ── CHAT ────────────────────────────────────────────────────────────────
  let history = [];
  const nowT = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  function addMsg(html, who) {
    const msgs = $('msgs');
    const row = document.createElement('div');
    row.className = 'row ' + (who === 'user' ? 'usr' : 'bot');
    const bub = document.createElement('div');
    bub.className = who === 'listing' ? 'card' : 'bubble';
    bub.innerHTML = html;
    const ts = document.createElement('div');
    ts.className = 'ts'; ts.textContent = nowT();
    row.appendChild(bub); row.appendChild(ts);
    msgs.appendChild(row);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function cardHTML(l) {
    return `<div class="card-src">${l.source || 'Listing'}</div>
      <div class="card-title">🏠 ${l.title || 'Property'}</div>
      <div class="card-price">${l.price || 'POA'}</div>
      <div class="card-detail">${l.details || ''}</div>
      ${l.url ? `<a class="card-link" href="${l.url}" target="_blank">View listing ↗</a>` : ''}`;
  }

  async function send() {
    const inp = $('input');
    const txt = inp.value.trim();
    if (!txt) return;
    inp.value = ''; inp.style.height = 'auto';
    addMsg(txt, 'user');
    history.push({ role: 'user', content: txt });

    $('send-btn').disabled = true;
    $('typing').classList.add('on');
    $('msgs').scrollTop = 99999;

    try {
      const { config = {} } = await chrome.storage.local.get('config');
      const { prefs = {} }  = await chrome.storage.local.get('prefs');

      const reply = await new Promise((res, rej) => {
        chrome.runtime.sendMessage({
          type: 'CHAT', apiKey: config.anthropicKey || '',
          message: txt, history: history.slice(-20), preferences: prefs,
        }, r => chrome.runtime.lastError ? rej(new Error(chrome.runtime.lastError.message)) : res(r));
      });

      $('typing').classList.remove('on');

      if (reply.error) { addMsg('Yikes! ' + reply.error, 'bot'); }
      else {
        if (reply.text) { addMsg(reply.text, 'bot'); history.push({ role: 'assistant', content: reply.text }); }
        (reply.listings || []).forEach(l => {
          const row = document.createElement('div'); row.className = 'row bot';
          const card = document.createElement('div'); card.className = 'card'; card.style.maxWidth = '95%';
          card.innerHTML = cardHTML(l);
          const ts = document.createElement('div'); ts.className = 'ts'; ts.textContent = nowT();
          row.appendChild(card); row.appendChild(ts);
          $('msgs').appendChild(row); $('msgs').scrollTop = 99999;
        });
        if (reply.prefs_update && Object.keys(reply.prefs_update).length) {
          const { prefs: ex = {} } = await chrome.storage.local.get('prefs');
          await chrome.storage.local.set({ prefs: { ...ex, ...reply.prefs_update } });
          loadWish();
        }
      }
    } catch (err) {
      $('typing').classList.remove('on');
      addMsg('Something went wrong: ' + err.message, 'bot');
    }

    $('send-btn').disabled = false;
    await chrome.storage.local.set({ chatHistory: history.slice(-40) });
  }

  $('send-btn').addEventListener('click', send);
  $('input').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } });
  $('input').addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 80) + 'px';
  });

  // Load saved chat
  chrome.storage.local.get('chatHistory').then(d => {
    if (d.chatHistory?.length) {
      $('msgs').innerHTML = '';
      history = d.chatHistory;
      history.forEach(m => addMsg(m.content, m.role === 'user' ? 'user' : 'bot'));
    }
  }).catch(() => {});

  // ── WISHLIST ─────────────────────────────────────────────────────────────
  async function loadWish() {
    const { prefs: p = {} } = await chrome.storage.local.get('prefs').catch(() => ({}));
    if (p.location)  $('w-loc').value    = p.location;
    if (p.commute)   $('w-commute').value= p.commute;
    if (p.budgetMin) $('w-min').value    = p.budgetMin;
    if (p.budgetMax) $('w-max').value    = p.budgetMax;
    if (p.bedsMin)   $('w-bmin').value   = p.bedsMin;
    if (p.bedsMax)   $('w-bmax').value   = p.bedsMax;
    [['w-types','types'],['w-own','ownership'],['w-feat','features']].forEach(([id, key]) => {
      shadow.querySelectorAll(`#${id} .chip`).forEach(c =>
        c.classList.toggle('on', (p[key]||[]).includes(c.dataset.v)));
    });
  }
  loadWish();

  $('save-wish').addEventListener('click', async () => {
    const chips = id => [...shadow.querySelectorAll(`#${id} .chip.on`)].map(c => c.dataset.v);
    const prefs = {
      location:  $('w-loc').value,
      commute:   $('w-commute').value,
      budgetMin: $('w-min').value,
      budgetMax: $('w-max').value,
      bedsMin:   $('w-bmin').value,
      bedsMax:   $('w-bmax').value,
      types:     chips('w-types'),
      ownership: chips('w-own'),
      features:  chips('w-feat'),
    };
    await chrome.storage.local.set({ prefs });
    shadow.querySelector('[data-p="chat"]').click();
    addMsg('Wishlist saved! 🏡 I\'ll keep hunting for your perfect place.', 'bot');
  });

  // ── CONFIG ───────────────────────────────────────────────────────────────
  async function loadCfg() {
    const { config: c = {} } = await chrome.storage.local.get('config').catch(() => ({}));
    if (c.anthropicKey) $('c-key').value = c.anthropicKey;
    if (c.interval)     $('c-interval').value = c.interval;
    if (c.notify !== undefined) $('c-notify').checked = c.notify;
  }
  loadCfg();

  $('save-cfg').addEventListener('click', async () => {
    const config = {
      anthropicKey: $('c-key').value.trim(),
      notify: $('c-notify').checked,
      interval: parseInt($('c-interval').value),
    };
    await chrome.storage.local.set({ config });
    chrome.runtime.sendMessage({ type: 'UPDATE_ALARM', interval: config.interval }).catch(() => {});
    $('c-dot').className = 'dot-status ok';
    $('c-txt').textContent = 'Config saved ✓';
  });

  $('c-test').addEventListener('click', async () => {
    const dot = $('c-dot'); const txt = $('c-txt');
    const key = $('c-key').value.trim();
    dot.className = 'dot-status'; txt.textContent = 'Testing...';
    try {
      await new Promise((res, rej) => {
        chrome.runtime.sendMessage({ type: 'TEST_KEY', apiKey: key }, r =>
          chrome.runtime.lastError ? rej(new Error(chrome.runtime.lastError.message))
          : r?.ok ? res() : rej(new Error(r?.error || 'Invalid key')));
      });
      dot.className = 'dot-status ok'; txt.textContent = 'API key works ✓ Ready!';
    } catch (err) {
      dot.className = 'dot-status err'; txt.textContent = err.message;
    }
  });

  // ── Messages from background ──────────────────────────────────────────────
  chrome.runtime.onMessage.addListener(msg => {
    if (msg.type === 'NEW_LISTINGS' && msg.count > 0) {
      const badge = $('badge');
      if (badge) { badge.textContent = msg.count > 9 ? '9+' : msg.count; badge.classList.add('show'); }
      if (panel.classList.contains('open')) {
        addMsg(`🔔 ${msg.count} fresh listings matching your wishlist!`, 'bot');
      }
    }
  });

  // ── Session ───────────────────────────────────────────────────────────────
  chrome.storage.local.get('lastBrowserSession').then(d => {
    const now = Date.now();
    if (now - (d.lastBrowserSession || 0) > 30 * 60 * 1000) {
      chrome.storage.local.set({ lastBrowserSession: now });
      chrome.runtime.sendMessage({ type: 'PAGE_LOADED' }).catch(() => {});
    }
  }).catch(() => {});

  chrome.storage.local.get('lastSearchResults').then(d => {
    if (d.lastSearchResults?.length) {
      const badge = $('badge');
      if (badge) { badge.textContent = d.lastSearchResults.length > 9 ? '9+' : d.lastSearchResults.length; badge.classList.add('show'); }
    }
  }).catch(() => {});

})();
