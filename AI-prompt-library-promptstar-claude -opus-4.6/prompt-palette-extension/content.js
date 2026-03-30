// content.js — PromptStar v2: All features

(function () {
  if (document.getElementById("pp-root")) return;

  let isOpen = false, searchQuery = "", activeTab = "templates", showSettings = false;
  let discoverResults = [], discoverLoading = false, copiedId = null, expandedId = null;
  let darkMode = true, starMood = "wave", savedId = null, deletedId = null;
  let starClicks = 0, starDizzy = false;
  try { darkMode = localStorage.getItem("ps-theme") !== "light"; } catch {}

  let mPos, mSize;
  try { mPos = JSON.parse(localStorage.getItem("ps-pos")); mSize = JSON.parse(localStorage.getItem("ps-size")); } catch {}
  if (!mPos) mPos = { top: null, right: 24 };
  if (!mSize) mSize = { w: 430, h: 750 };

  const root = document.createElement("div");
  root.id = "pp-root";
  document.body.appendChild(root);
  const shadow = root.attachShadow({ mode: "open" });

  const fl = document.createElement("link");
  fl.rel = "stylesheet";
  fl.href = "https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&family=Outfit:wght@300;400;500;600;700;800&family=Geist+Mono:wght@400;500&display=swap";
  shadow.appendChild(fl);

  const style = document.createElement("style");
  shadow.appendChild(style);

  const backdrop = document.createElement("div");
  backdrop.className = "bk";
  backdrop.addEventListener("click", toggle);
  shadow.appendChild(backdrop);

  const modal = document.createElement("div");
  modal.className = "m";
  shadow.appendChild(modal);

  // ── Icons ──
  const IC = {
    doc: `<svg width="18" height="18" viewBox="0 0 20 20" fill="none"><path d="M6 2h5.5L15 5.5V17a1 1 0 01-1 1H6a1 1 0 01-1-1V3a1 1 0 011-1z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M11 2v4h4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M7.5 10h5M7.5 13h3.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>`,
    people: `<svg width="18" height="18" viewBox="0 0 20 20" fill="none"><circle cx="7.5" cy="6.5" r="2.5" stroke="currentColor" stroke-width="1.4"/><path d="M2.5 16.5c0-2.5 2-4.5 5-4.5s5 2 5 4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><circle cx="14" cy="7" r="2" stroke="currentColor" stroke-width="1.2" opacity=".45"/><path d="M14 11.5c2.2.3 3.5 1.8 3.5 3.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" opacity=".45"/></svg>`,
    chart: `<svg width="18" height="18" viewBox="0 0 20 20" fill="none"><rect x="3" y="10" width="3" height="7" rx="1" stroke="currentColor" stroke-width="1.4"/><rect x="8.5" y="6" width="3" height="11" rx="1" stroke="currentColor" stroke-width="1.4"/><rect x="14" y="3" width="3" height="14" rx="1" stroke="currentColor" stroke-width="1.4"/></svg>`,
    envelope: `<svg width="18" height="18" viewBox="0 0 20 20" fill="none"><rect x="2.5" y="4.5" width="15" height="11" rx="2" stroke="currentColor" stroke-width="1.4"/><path d="M2.5 6.5L10 11.5l7.5-5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    magnifier: `<svg width="18" height="18" viewBox="0 0 20 20" fill="none"><circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.4"/><path d="M12.5 12.5L17 17" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M6.5 8.5h4M8.5 6.5v4" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" opacity=".4"/></svg>`,
    sparkle: `<svg width="18" height="18" viewBox="0 0 20 20" fill="none"><path d="M10 2l1.5 4.5H16l-3.6 2.7 1.4 4.3L10 10.7 6.2 13.5l1.4-4.3L4 6.5h4.5L10 2z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>`,
    gear: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="2.5" stroke="currentColor" stroke-width="1.3"/><path d="M8 1v2m0 10v2m-5-7H1m14 0h-2M3.05 3.05l1.41 1.41m7.08 7.08l1.41 1.41M3.05 12.95l1.41-1.41m7.08-7.08l1.41-1.41" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>`,
    save: `<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2.5 1.5h7l2.5 2.5v7.5a1 1 0 01-1 1h-8.5a1 1 0 01-1-1v-9a1 1 0 011-1z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/><rect x="4.5" y="8" width="5" height="3" rx=".5" stroke="currentColor" stroke-width="1.1"/><path d="M5 1.5v3h4v-3" stroke="currentColor" stroke-width="1.1"/></svg>`,
    trash: `<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 4h8l-.6 7.5a1 1 0 01-1 .9H4.6a1 1 0 01-1-.9L3 4z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/><path d="M2.5 4h9M5.5 2h3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/><path d="M5.5 6.5v3m3-3v3" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/></svg>`,
  };
  function ic(n) { return IC[n] || IC.sparkle; }

  // ── Blue starfish with more moods ──
  function starfish(mood) {
    const ec = darkMode ? '#1a1a1c' : '#1a2a40';
    const ac = {wave:'sf-wave',celebrate:'sf-cel',thinking:'sf-thk',search:'sf-src',idle:'sf-idl',dizzy:'sf-diz',love:'sf-love',sleep:'sf-slp'}[mood]||'sf-idl';
    let eyes = `<circle cx="37" cy="34" r="2.5" fill="${ec}"/><circle cx="50" cy="34" r="2.5" fill="${ec}"/>`;
    if (mood==='celebrate') eyes = `<path d="M35 33c0-2 4-2 4 0" stroke="${ec}" stroke-width="1.8" stroke-linecap="round" fill="none"/><path d="M48 33c0-2 4-2 4 0" stroke="${ec}" stroke-width="1.8" stroke-linecap="round" fill="none"/>`;
    if (mood==='thinking') eyes = `<circle cx="37" cy="34" r="2.5" fill="${ec}"/><circle cx="50" cy="33" r="2.5" fill="${ec}"/><circle cx="51" cy="32" r="1" fill="#fff" opacity=".7"/>`;
    if (mood==='dizzy') eyes = `<g class="dizzy-eyes"><path d="M35 32l4 4m0-4l-4 4" stroke="${ec}" stroke-width="1.5" stroke-linecap="round"/><path d="M48 32l4 4m0-4l-4 4" stroke="${ec}" stroke-width="1.5" stroke-linecap="round"/></g>`;
    if (mood==='love') eyes = `<path d="M34 33c1-2 3-2 4 0 1-2 3-2 4 0-1 3-4 4-4 4s-3-1-4-4z" fill="#ff6b8a"/><path d="M47 33c1-2 3-2 4 0 1-2 3-2 4 0-1 3-4 4-4 4s-3-1-4-4z" fill="#ff6b8a"/>`;
    if (mood==='sleep') eyes = `<path d="M35 34h4M48 34h4" stroke="${ec}" stroke-width="1.8" stroke-linecap="round"/>`;
    let mouth = `<path d="M40 42c1.5 2.5 5.5 2.5 7 0" stroke="${ec}" stroke-width="1.5" stroke-linecap="round" fill="none"/>`;
    if (mood==='celebrate'||mood==='love') mouth = `<path d="M39 41c2 4 7 4 9 0" stroke="${ec}" stroke-width="1.5" stroke-linecap="round" fill="none"/>`;
    if (mood==='thinking') mouth = `<circle cx="44" cy="43" r="2" stroke="${ec}" stroke-width="1.3" fill="none"/>`;
    if (mood==='search') mouth = `<path d="M41 42h5" stroke="${ec}" stroke-width="1.5" stroke-linecap="round"/>`;
    if (mood==='dizzy') mouth = `<path d="M40 43c1.5-1.5 5.5-1.5 7 0" stroke="${ec}" stroke-width="1.5" stroke-linecap="round" fill="none"/>`;
    if (mood==='sleep') mouth = `<circle cx="44" cy="44" r="1.5" fill="${ec}" opacity=".4"/>`;
    let extras = '';
    if (mood==='sleep') extras = `<text x="62" y="22" font-size="10" fill="${darkMode?'rgba(255,255,255,.4)':'rgba(0,0,0,.25)'}" font-family="sans-serif" font-weight="700">z</text><text x="68" y="16" font-size="8" fill="${darkMode?'rgba(255,255,255,.3)':'rgba(0,0,0,.18)'}" font-family="sans-serif" font-weight="700">z</text>`;
    if (mood==='love') extras = `<circle cx="24" cy="20" r="3" fill="#ff6b8a" opacity=".5"/><circle cx="66" cy="18" r="2" fill="#ff6b8a" opacity=".4"/>`;
    return `<svg class="sf ${ac}" width="56" height="56" viewBox="0 0 86 86" fill="none"><defs><linearGradient id="sfg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#6DB3F8"/><stop offset="100%" stop-color="#4A8AE5"/></linearGradient></defs><g class="sf-arms"><path d="M43 10L40 28 46 28Z" fill="url(#sfg)" class="arm-top"/><path d="M68 24L56 36 60 40Z" fill="url(#sfg)" class="arm-tr"/><path d="M74 56L56 48 54 54Z" fill="url(#sfg)" class="arm-br"/><path d="M12 56L30 48 32 54Z" fill="url(#sfg)" class="arm-bl"/><path d="M18 24L30 36 26 40Z" fill="url(#sfg)" class="arm-tl"/></g><circle cx="43" cy="42" r="18" fill="url(#sfg)"/><circle cx="33" cy="40" r="4" fill="rgba(90,160,255,.3)"/><circle cx="54" cy="40" r="4" fill="rgba(90,160,255,.3)"/>${eyes}<circle cx="38.5" cy="33" r="1" fill="#fff" opacity=".9"/><circle cx="51.5" cy="33" r="1" fill="#fff" opacity=".9"/>${mouth}${extras}</svg>`;
  }

  const MSGS = {
    wave:["Hey there! Pick a prompt!","Welcome back!","Ready to create?","Let's go!"],
    search:["Looking through templates...","Let me find that...","Searching..."],
    thinking:["Hmm, interesting role...","Searching the web...","Give me a sec..."],
    celebrate:["Copied! You're a star!","Nice pick!","Great choice!","Nailed it!"],
    idle:["I'm here if you need me!","Try the Discover tab!","Click me!"],
    dizzy:["Whoa! Too many clicks!","I'm seeing stars!","Easy there!"],
    love:["I love this prompt!","Saved with love!","Great taste!"],
    sleep:["zzz... click me to wake up","Just resting my arms...","Five more minutes..."],
  };
  function speech() { const a=MSGS[starMood]||MSGS.idle; return a[Math.floor(Math.random()*a.length)]; }

  function getKey() { try { return localStorage.getItem("ps-api-key")||""; } catch { return ""; } }
  function setKey(k) { try { localStorage.setItem("ps-api-key", k); } catch {} }

  function applyPos() {
    if (mPos.top!==null) { modal.style.top=mPos.top+'px'; modal.style.left=mPos.left+'px'; modal.style.right='auto'; modal.style.transform='none'; }
    else { modal.style.top='50%'; modal.style.right=mPos.right+'px'; modal.style.left='auto'; modal.style.transform='translateY(-50%)'; }
    modal.style.width=Math.max(340,Math.min(mSize.w,window.innerWidth-32))+'px';
    modal.style.height=Math.max(400,Math.min(mSize.h,window.innerHeight-32))+'px';
  }

  function render() {
    style.textContent = getCSS(darkMode);
    modal.classList.toggle("open", isOpen);
    backdrop.classList.toggle("vis", isOpen);
    if (!isOpen) return;
    applyPos();
    PROMPT_TEMPLATES = loadTemplates();

    const fil = PROMPT_TEMPLATES.filter(t => { if(!searchQuery) return true; const q=searchQuery.toLowerCase(); return t.title.toLowerCase().includes(q)||t.tags.some(g=>g.includes(q))||t.prompt.toLowerCase().includes(q); });
    const themeSvg = darkMode ? `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="3.5" stroke="currentColor" stroke-width="1.3"/><path d="M8 2v1.5m0 9V14m-4.24-1.76l1.06-1.06m6.36-6.36l1.06-1.06M2 8h1.5m9 0H14M3.76 3.76l1.06 1.06m6.36 6.36l1.06 1.06" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>` : `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M13.4 10.2A5.5 5.5 0 015.8 2.6 6.5 6.5 0 1013.4 10.2z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>`;
    const hasKey = !!getKey();

    modal.innerHTML = `
      <div class="drag" id="dragH">
        <div class="seg">
          <button class="s ${activeTab==="templates"&&!showSettings?"on":""}" data-t="templates">Templates</button>
          <button class="s ${activeTab==="discover"&&!showSettings?"on":""}" data-t="discover">Discover${!hasKey?' ⚙':''}
</button>
        </div>
        <div class="top-r">
          <button class="thm" id="thm">${themeSvg}</button>
          <button class="gear" id="gear">${IC.gear}</button>
          <button class="xb" id="xb"><svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2.5 2.5l7 7m0-7l-7 7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button>
        </div>
      </div>
      <div class="star-hdr">
        <div class="star-char" id="starChar">${starfish(starMood)}</div>
        <div class="star-info">
          <span class="star-name">PromptStar</span>
          <div class="star-bubble">${speech()}</div>
        </div>
      </div>
      <div class="bd">${showSettings?rSettings():(activeTab==="templates"?rT(fil):rD())}</div>
      <div class="rh" id="resH"></div>`;
    bindAll();
  }

  // ── Settings panel ──
  function rSettings() {
    const key = getKey();
    const masked = key ? key.slice(0,12)+'...' + key.slice(-4) : '';
    return `<div class="settings">
      <div class="set-title">Settings</div>
      <div class="set-section">
        <label class="set-label">Claude API Key</label>
        <p class="set-desc">Required for the Discover tab. Your key stays in your browser only.</p>
        <div class="set-row">
          <input class="set-inp" id="apiInp" type="password" placeholder="sk-ant-..." value="${key}"/>
          <button class="set-btn" id="saveKey">Save</button>
        </div>
        ${key ? `<p class="set-status">Connected ${masked}</p>` : `<p class="set-status set-warn">No key set. Discover won't work.</p>`}
      </div>
      <div class="set-section">
        <label class="set-label">Saved Templates</label>
        <p class="set-desc">${PROMPT_TEMPLATES.length} templates (${PROMPT_TEMPLATES.filter(t=>!t.builtin).length} saved from Discover)</p>
      </div>
      <button class="set-back" id="setBack">← Back</button>
    </div>`;
  }

  // ── Templates tab with delete ──
  function rT(ts) {
    if(starMood!=='celebrate'&&starMood!=='search'&&starMood!=='dizzy'&&starMood!=='love'&&starMood!=='sleep') starMood=searchQuery?'search':'wave';
    const sb=`<div class="sb"><svg class="si" width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="5.8" cy="5.8" r="4.3" stroke="currentColor" stroke-width="1.3"/><path d="M9 9l3.5 3.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg><input class="sinp" id="sinp" placeholder="Search templates..." value="${searchQuery}"/></div>`;
    if(!ts.length) return sb+`<div class="mt">No templates yet</div>`;
    return sb+`<div class="g">${ts.map((t,i)=>{const ex=expandedId===t.id;const isDel=deletedId===t.id;return`<div class="c${ex?" ex":""}${isDel?" del":""}" style="--d:${i*30}ms"><div class="ct" data-x="${t.id}"><div class="ci">${ic(t.icon)}</div><div class="cf"><span class="cn">${esc(t.title)}${!t.builtin?'<span class="saved-badge">saved</span>':''}</span><div class="cg">${t.tags.map(g=>`<span class="pl">${g}</span>`).join("")}</div></div><svg class="cv" width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M3.5 5l3 3 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>${ex?`<div class="cb"><pre class="co">${esc(t.prompt)}</pre><div class="cb-acts"><button class="cp" data-cp="${t.id}">${copiedId===t.id?'<svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M2 6L4 8 9 3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Copied':'<svg width="11" height="11" viewBox="0 0 11 11" fill="none"><rect x="3.5" y="3.5" width="5.5" height="5.5" rx="1" stroke="currentColor" stroke-width="1.1"/><path d="M2 8V2.3a.3.3 0 01.3-.3H8" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/></svg> Copy'}</button><button class="del-btn" data-del="${t.id}">${IC.trash} Delete</button></div></div>`:""}</div>`;}).join("")}</div>`;
  }

  // ── Discover tab with save ──
  function rD() {
    if(!discoverLoading&&!discoverResults.length&&starMood!=='dizzy'&&starMood!=='love'&&starMood!=='sleep') starMood='idle';
    const hasKey = !!getKey();
    if(!hasKey) return `<div class="no-key"><p class="nk-title">API Key Required</p><p class="nk-desc">Add your Claude API key in Settings (gear icon) to discover prompts with AI.</p><button class="nk-btn" id="goSettings">Open Settings</button></div>`;
    return `<div class="dsc"><div class="db"><input class="di" id="di" placeholder="Enter your role, e.g. Product Manager..."/><button class="dbtn" id="dbtn" ${discoverLoading?"disabled":""}>${discoverLoading?'<span class="sp"></span>':'Find'}</button></div>${discoverResults.length?`<div class="dl">Results</div><div class="g">${discoverResults.map((r,i)=>{const isSaved=savedId==="sv-"+i;const alreadySaved=PROMPT_TEMPLATES.find(t=>t.id===r._id);return`<div class="c ex" style="--d:${i*30}ms"><div class="ct"><div class="ci">${ic(r.icon||"sparkle")}</div><div class="cf"><span class="cn">${esc(r.title)}</span>${r.source?`<span class="csr">${esc(r.source)}</span>`:""}</div></div><div class="cb"><pre class="co">${esc(r.prompt)}</pre><div class="cb-acts"><button class="cp" data-dc="${i}">${copiedId==="d-"+i?'<svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M2 6L4 8 9 3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Copied':'<svg width="11" height="11" viewBox="0 0 11 11" fill="none"><rect x="3.5" y="3.5" width="5.5" height="5.5" rx="1" stroke="currentColor" stroke-width="1.1"/><path d="M2 8V2.3a.3.3 0 01.3-.3H8" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/></svg> Copy'}</button>${alreadySaved?`<span class="saved-tag">Saved ✓</span>`:`<button class="save-btn${isSaved?' saved':''}" data-sv="${i}">${isSaved?'Saved ✓':IC.save+' Save to Templates'}</button>`}</div></div></div>`;}).join("")}</div>`:""}</div>`;
  }

  function bindAll() {
    shadow.getElementById("xb")?.addEventListener("click",toggle);
    shadow.getElementById("thm")?.addEventListener("click",()=>{darkMode=!darkMode;try{localStorage.setItem("ps-theme",darkMode?"dark":"light")}catch{};render();});
    shadow.getElementById("gear")?.addEventListener("click",()=>{showSettings=!showSettings;render();});
    shadow.getElementById("setBack")?.addEventListener("click",()=>{showSettings=false;render();});
    shadow.getElementById("goSettings")?.addEventListener("click",()=>{showSettings=true;render();});
    shadow.getElementById("saveKey")?.addEventListener("click",()=>{
      const v=shadow.getElementById("apiInp")?.value?.trim();
      if(v){setKey(v);starMood='celebrate';showSettings=false;render();}
    });

    // Starfish — more interactive: rapid clicks = dizzy, then cycles through moods
    shadow.getElementById("starChar")?.addEventListener("click",()=>{
      starClicks++;
      if(starClicks>=5){starMood='dizzy';starDizzy=true;starClicks=0;render();setTimeout(()=>{starDizzy=false;starMood='wave';render();},2500);return;}
      if(starDizzy)return;
      const moods=['wave','idle','celebrate','love','sleep'];
      starMood=moods[Math.floor(Math.random()*moods.length)];
      render();
      // Reset click counter after pause
      setTimeout(()=>{starClicks=0;},1500);
    });

    shadow.querySelectorAll(".s").forEach(t=>t.addEventListener("click",()=>{activeTab=t.dataset.t;showSettings=false;render();}));
    const si=shadow.getElementById("sinp");
    if(si){si.addEventListener("input",e=>{searchQuery=e.target.value;starMood=searchQuery?'search':'wave';render();shadow.getElementById("sinp")?.focus();});setTimeout(()=>si.focus(),50);}
    shadow.querySelectorAll("[data-x]").forEach(el=>el.addEventListener("click",()=>{expandedId=expandedId===el.dataset.x?null:el.dataset.x;render();}));
    shadow.querySelectorAll("[data-cp]").forEach(b=>b.addEventListener("click",e=>{e.stopPropagation();const t=PROMPT_TEMPLATES.find(x=>x.id===b.dataset.cp);if(t){starMood='celebrate';cpTxt(t.prompt,t.id);}}));
    shadow.querySelectorAll("[data-dc]").forEach(b=>b.addEventListener("click",e=>{e.stopPropagation();const i=+b.dataset.dc;if(discoverResults[i]){starMood='celebrate';cpTxt(discoverResults[i].prompt,"d-"+i);}}));

    // Save from discover
    shadow.querySelectorAll("[data-sv]").forEach(b=>b.addEventListener("click",e=>{
      e.stopPropagation();const i=+b.dataset.sv;const r=discoverResults[i];
      if(!r)return;
      const newT={id:r._id||'sv-'+Date.now()+'-'+i, icon:r.icon||'sparkle', title:r.title, tags:r.source?[r.source]:['discovered'], prompt:r.prompt, builtin:false};
      saveTemplate(newT);PROMPT_TEMPLATES=loadTemplates();
      savedId="sv-"+i;starMood='love';render();
      setTimeout(()=>{savedId=null;render();},2000);
    }));

    // Delete template
    shadow.querySelectorAll("[data-del]").forEach(b=>b.addEventListener("click",e=>{
      e.stopPropagation();const id=b.dataset.del;
      deletedId=id;render();
      setTimeout(()=>{deleteTemplate(id);PROMPT_TEMPLATES=loadTemplates();expandedId=null;deletedId=null;starMood='idle';render();},300);
    }));

    shadow.getElementById("dbtn")?.addEventListener("click",disc);
    shadow.getElementById("di")?.addEventListener("keydown",e=>{if(e.key==="Enter")disc();});

    // Drag
    const dh=shadow.getElementById("dragH");
    if(dh){let dragging=false,sx,sy,ox,oy;
      dh.addEventListener("mousedown",e=>{if(e.target.closest('.s,.thm,.xb,.gear'))return;dragging=true;const r=modal.getBoundingClientRect();ox=r.left;oy=r.top;sx=e.clientX;sy=e.clientY;modal.style.transition='none';e.preventDefault();});
      document.addEventListener("mousemove",e=>{if(!dragging)return;mPos={top:Math.max(0,Math.min(oy+(e.clientY-sy),window.innerHeight-100)),left:Math.max(0,Math.min(ox+(e.clientX-sx),window.innerWidth-100)),right:null};applyPos();});
      document.addEventListener("mouseup",()=>{if(dragging){dragging=false;modal.style.transition='';try{localStorage.setItem("ps-pos",JSON.stringify(mPos))}catch{}}});
    }
    // Resize
    const rh=shadow.getElementById("resH");
    if(rh){let resizing=false,sx,sy,ow,oh;
      rh.addEventListener("mousedown",e=>{resizing=true;sx=e.clientX;sy=e.clientY;ow=modal.offsetWidth;oh=modal.offsetHeight;modal.style.transition='none';e.preventDefault();e.stopPropagation();});
      document.addEventListener("mousemove",e=>{if(!resizing)return;mSize={w:Math.max(340,Math.min(ow+(e.clientX-sx),window.innerWidth-32)),h:Math.max(400,Math.min(oh+(e.clientY-sy),window.innerHeight-32))};modal.style.width=mSize.w+'px';modal.style.height=mSize.h+'px';});
      document.addEventListener("mouseup",()=>{if(resizing){resizing=false;modal.style.transition='';try{localStorage.setItem("ps-size",JSON.stringify(mSize))}catch{}}});
    }
  }

  async function disc(){const inp=shadow.getElementById("di"),role=inp?.value?.trim();if(!role||discoverLoading)return;discoverLoading=true;discoverResults=[];starMood='thinking';render();const ni=shadow.getElementById("di");if(ni)ni.value=role;try{const res=await fetch("https://api.anthropic.com/v1/messages",{method:"POST",headers:{"Content-Type":"application/json","x-api-key":getKey(),"anthropic-version":"2023-06-01","anthropic-dangerous-direct-browser-access":"true"},body:JSON.stringify({model:"claude-sonnet-4-20250514",max_tokens:1500,system:`Return EXACTLY a JSON array of 4 LLM prompt templates for the given role. Each: {"icon":"sparkle","title":"short name","source":"origin","prompt":"template with [placeholders]"}. ONLY JSON.`,messages:[{role:"user",content:`Best LLM prompt templates for: ${role}`}]})});const d=await res.json(),txt=d.content?.map(c=>c.text||"").join("")||"";discoverResults=JSON.parse(txt.replace(/```json|```/g,"").trim());discoverResults.forEach((r,i)=>r._id='disc-'+Date.now()+'-'+i);starMood='celebrate';}catch(e){discoverResults=[{icon:"sparkle",title:"Error — check your API key",source:"",prompt:"Make sure your key is correct in Settings."}];starMood='idle';}discoverLoading=false;render();const fi=shadow.getElementById("di");if(fi)fi.value=role;}

  function toggle(){isOpen=!isOpen;expandedId=null;showSettings=false;starMood='wave';render();}
  function cpTxt(t,id){navigator.clipboard.writeText(t).then(()=>{copiedId=id;render();setTimeout(()=>{copiedId=null;starMood='wave';render();},2000);});}
  function esc(s){const d=document.createElement("div");d.textContent=s;return d.innerHTML;}

  chrome.runtime.onMessage.addListener(m=>{if(m.action==="toggle-palette")toggle();});
  document.addEventListener("keydown",e=>{if(e.key==="Escape"&&isOpen)toggle();});
  render();

  function getCSS(dk){
    const v=dk?{glass:'rgba(22,22,24,.78)',card:'rgba(255,255,255,.06)',cardH:'rgba(255,255,255,.09)',cardEx:'rgba(255,255,255,.10)',inp:'rgba(255,255,255,.06)',inpF:'rgba(255,255,255,.10)',bdr:'rgba(255,255,255,.08)',segBg:'rgba(255,255,255,.08)',segOn:'rgba(255,255,255,.15)',txt:'#FFF',txt2:'rgba(255,255,255,.55)',txt3:'rgba(255,255,255,.30)',ico:'rgba(255,255,255,.35)',icoEx:'rgba(255,255,255,.70)',pill:'rgba(255,255,255,.08)',pillT:'rgba(255,255,255,.35)',code:'rgba(0,0,0,.25)',cta:'#FFF',ctaT:'#000',ctaH:'rgba(255,255,255,.85)',xb:'rgba(255,255,255,.10)',xbH:'rgba(255,255,255,.18)',foc:'rgba(255,255,255,.20)',shd:'0 32px 100px rgba(0,0,0,.45),0 0 0 .5px rgba(255,255,255,.08)',bub:'rgba(255,255,255,.10)',bubB:'rgba(255,255,255,.08)',danger:'rgba(255,80,80,.15)',dangerT:'#ff6b6b',dangerH:'rgba(255,80,80,.25)'}:{glass:'rgba(248,248,250,.82)',card:'rgba(0,0,0,.03)',cardH:'rgba(0,0,0,.05)',cardEx:'rgba(0,0,0,.06)',inp:'rgba(0,0,0,.04)',inpF:'rgba(0,0,0,.06)',bdr:'rgba(0,0,0,.06)',segBg:'rgba(0,0,0,.05)',segOn:'rgba(255,255,255,.85)',txt:'#1D1D1F',txt2:'rgba(0,0,0,.50)',txt3:'rgba(0,0,0,.25)',ico:'rgba(0,0,0,.30)',icoEx:'rgba(0,0,0,.65)',pill:'rgba(0,0,0,.05)',pillT:'rgba(0,0,0,.35)',code:'rgba(0,0,0,.03)',cta:'#1D1D1F',ctaT:'#FFF',ctaH:'rgba(0,0,0,.75)',xb:'rgba(0,0,0,.06)',xbH:'rgba(0,0,0,.10)',foc:'rgba(0,0,0,.12)',shd:'0 32px 100px rgba(0,0,0,.12),0 0 0 .5px rgba(0,0,0,.06)',bub:'rgba(0,0,0,.04)',bubB:'rgba(0,0,0,.06)',danger:'rgba(255,59,48,.08)',dangerT:'#FF3B30',dangerH:'rgba(255,59,48,.15)'};
    return `
    @import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&family=Outfit:wght@300;400;500;600;700;800&family=Geist+Mono:wght@400;500&display=swap');
    :host{--f:"Outfit",-apple-system,BlinkMacSystemFont,sans-serif;--fc:"Caveat",cursive;--fm:"Geist Mono","SF Mono",ui-monospace,monospace}
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    .bk{position:fixed;inset:0;background:rgba(0,0,0,${dk?'.45':'.18'});backdrop-filter:blur(${dk?'4':'12'}px);-webkit-backdrop-filter:blur(${dk?'4':'12'}px);opacity:0;pointer-events:none;transition:opacity .2s;z-index:1}.bk.vis{opacity:1;pointer-events:auto}
    .m{position:fixed;background:${v.glass};backdrop-filter:saturate(180%) blur(40px);-webkit-backdrop-filter:saturate(180%) blur(40px);border:1px solid ${v.bdr};border-radius:24px;box-shadow:${v.shd};opacity:0;pointer-events:none;transition:opacity .2s,transform .3s cubic-bezier(.2,1,.3,1);z-index:2;display:flex;flex-direction:column;overflow:hidden;font-family:var(--f);color:${v.txt};-webkit-font-smoothing:antialiased;min-width:340px;min-height:400px}
    .m.open{opacity:1;pointer-events:auto}
    .drag{display:flex;align-items:center;justify-content:space-between;padding:16px 18px 10px;flex-shrink:0;cursor:grab;user-select:none}.drag:active{cursor:grabbing}
    .seg{display:flex;background:${v.segBg};border-radius:10px;padding:3px}
    .s{all:unset;cursor:pointer;padding:7px 16px;font-family:var(--f);font-size:12.5px;font-weight:600;color:${v.txt3};border-radius:8px;transition:all .2s}.s:hover{color:${v.txt2}}.s.on{background:${v.segOn};color:${v.txt};box-shadow:0 1px 3px rgba(0,0,0,${dk?'.25':'.06'})}
    .top-r{display:flex;align-items:center;gap:4px}
    .thm,.xb,.gear{all:unset;cursor:pointer;width:30px;height:30px;display:flex;align-items:center;justify-content:center;border-radius:50%;color:${v.txt3};transition:all .12s}.xb{background:${v.xb}}.thm:hover,.xb:hover,.gear:hover{background:${v.xbH};color:${v.txt2}}

    .star-hdr{display:flex;align-items:center;gap:12px;padding:2px 20px 12px;flex-shrink:0}
    .star-char{cursor:pointer;flex-shrink:0;transition:transform .2s}.star-char:hover{transform:scale(1.1) rotate(-5deg)}.star-char:active{transform:scale(.88) rotate(10deg)}
    .star-info{flex:1;min-width:0}
    .star-name{font-family:var(--fc);font-weight:700;font-size:30px;letter-spacing:.5px;display:block;line-height:1;background:linear-gradient(135deg,#6DB3F8,#5B9CF5,#4A8AE5);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;transform:rotate(-1.5deg);display:inline-block}
    .star-bubble{font-size:11.5px;font-weight:500;color:${v.txt2};background:${v.bub};border:1px solid ${v.bubB};border-radius:10px;padding:4px 10px;margin-top:4px;display:inline-block;animation:bubIn .3s ease}
    @keyframes bubIn{from{opacity:0;transform:translateY(3px) scale(.95)}to{opacity:1;transform:translateY(0) scale(1)}}

    .sf-wave .arm-tr{animation:wA 1s ease-in-out infinite;transform-origin:56px 36px}@keyframes wA{0%,100%{transform:rotate(0)}50%{transform:rotate(18deg)}}
    .sf-cel .sf-arms{animation:ce .4s ease infinite alternate}@keyframes ce{from{transform:scale(1) rotate(0)}to{transform:scale(1.06) rotate(5deg)}}
    .sf-thk{animation:th 2s ease-in-out infinite}@keyframes th{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
    .sf-src .arm-top{animation:sA .8s ease infinite;transform-origin:43px 28px}@keyframes sA{0%,100%{transform:rotate(0)}50%{transform:rotate(-10deg)}}
    .sf-idl{animation:id 3s ease-in-out infinite}@keyframes id{0%,100%{transform:rotate(0)}50%{transform:rotate(3deg)}}
    .sf-diz{animation:diz .3s ease infinite}@keyframes diz{0%{transform:rotate(-8deg)}50%{transform:rotate(8deg)}100%{transform:rotate(-8deg)}}
    .sf-love{animation:lv 1s ease infinite}@keyframes lv{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}
    .sf-slp{animation:slp 3s ease-in-out infinite}@keyframes slp{0%,100%{transform:translateY(0) rotate(-2deg)}50%{transform:translateY(2px) rotate(2deg)}}
    .dizzy-eyes{animation:de .4s linear infinite}@keyframes de{to{transform:rotate(360deg);transform-origin:43px 34px}}

    .bd{flex:1;overflow-y:auto;padding:0 20px 28px;-webkit-overflow-scrolling:touch}.bd::-webkit-scrollbar{width:0;display:none}
    .sb{position:relative;margin-bottom:12px}.si{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:${v.txt3};pointer-events:none}
    .sinp{all:unset;display:block;width:100%;padding:11px 14px 11px 40px;background:${v.inp};border:1px solid ${v.bdr};border-radius:12px;font-family:var(--f);font-size:14px;color:${v.txt};box-sizing:border-box;transition:all .15s}.sinp::placeholder{color:${v.txt3}}.sinp:focus{background:${v.inpF};border-color:${v.foc};box-shadow:0 0 0 2px ${v.foc}}
    .g{display:flex;flex-direction:column;gap:6px}
    .c{background:${v.card};border:1px solid ${v.bdr};border-radius:16px;overflow:hidden;transition:all .2s;animation:up .2s ease both;animation-delay:var(--d,0ms)}@keyframes up{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}.c:hover{background:${v.cardH}}.c.ex{background:${v.cardEx};border-color:${dk?'rgba(255,255,255,.12)':'rgba(0,0,0,.08)'}}
    .c.del{opacity:0;transform:scale(.95) translateX(30px);transition:all .3s ease}
    .ct{display:flex;align-items:center;gap:12px;padding:13px 16px;cursor:pointer;user-select:none}
    .ci{width:36px;height:36px;display:flex;align-items:center;justify-content:center;background:${v.card};border:1px solid ${v.bdr};border-radius:10px;flex-shrink:0;color:${v.ico};transition:all .15s}.c.ex .ci{color:${v.icoEx};background:${dk?'rgba(255,255,255,.10)':'rgba(0,0,0,.06)'}}
    .cf{flex:1;min-width:0}.cn{display:block;font-weight:600;font-size:13.5px;color:${v.txt};margin-bottom:3px;letter-spacing:-.15px}
    .saved-badge{font-size:9px;font-weight:700;padding:1px 6px;background:rgba(91,156,245,.15);color:#5B9CF5;border-radius:500px;margin-left:6px;vertical-align:middle}
    .cg{display:flex;gap:4px;flex-wrap:wrap}.pl{font-size:10px;font-weight:600;padding:2px 9px;background:${v.pill};color:${v.pillT};border-radius:500px}
    .csr{font-size:10.5px;color:${v.txt3}}
    .cv{color:${v.txt3};flex-shrink:0;transition:transform .2s cubic-bezier(.2,1,.3,1)}.c.ex .cv{transform:rotate(180deg);color:${v.txt2}}
    .cb{padding:0 16px 13px;animation:fi .12s ease}@keyframes fi{from{opacity:0}to{opacity:1}}
    .co{font-family:var(--fm);font-size:11.5px;line-height:1.7;color:${v.txt2};background:${v.code};border-radius:10px;padding:14px;margin-bottom:10px;white-space:pre-wrap;word-break:break-word;max-height:150px;overflow-y:auto;border:1px solid ${v.bdr}}.co::-webkit-scrollbar{width:0;display:none}
    .cb-acts{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
    .cp{all:unset;cursor:pointer;display:inline-flex;align-items:center;gap:5px;padding:6px 14px;background:${v.cta};color:${v.ctaT};font-family:var(--f);font-size:11.5px;font-weight:600;border-radius:500px;transition:all .12s}.cp:hover{background:${v.ctaH};transform:translateY(-.5px)}
    .del-btn{all:unset;cursor:pointer;display:inline-flex;align-items:center;gap:4px;padding:6px 12px;background:${v.danger};color:${v.dangerT};font-family:var(--f);font-size:11px;font-weight:600;border-radius:500px;transition:all .12s}.del-btn:hover{background:${v.dangerH}}
    .save-btn{all:unset;cursor:pointer;display:inline-flex;align-items:center;gap:4px;padding:6px 12px;background:rgba(91,156,245,.12);color:#5B9CF5;font-family:var(--f);font-size:11px;font-weight:600;border-radius:500px;transition:all .15s}.save-btn:hover{background:rgba(91,156,245,.22)}.save-btn.saved{color:#5B9CF5;opacity:.7}
    .saved-tag{font-size:11px;font-weight:600;color:#5B9CF5;opacity:.6;padding:6px 0}

    .db{display:flex;gap:6px;margin-bottom:16px}.di{all:unset;flex:1;padding:11px 14px;background:${v.inp};border:1px solid ${v.bdr};border-radius:12px;font-family:var(--f);font-size:14px;color:${v.txt};box-sizing:border-box;transition:all .15s}.di::placeholder{color:${v.txt3}}.di:focus{background:${v.inpF};border-color:${v.foc};box-shadow:0 0 0 2px ${v.foc}}
    .dbtn{all:unset;cursor:pointer;padding:11px 20px;background:${v.cta};color:${v.ctaT};font-family:var(--f);font-size:13.5px;font-weight:600;border-radius:12px;transition:all .12s;white-space:nowrap}.dbtn:hover:not(:disabled){background:${v.ctaH};transform:translateY(-.5px)}.dbtn:disabled{opacity:.35;cursor:wait}
    .dl{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;color:${v.txt3};margin-bottom:8px}
    .sp{display:inline-block;width:13px;height:13px;border:2px solid ${dk?'rgba(0,0,0,.2)':'rgba(255,255,255,.3)'};border-top-color:${v.ctaT};border-radius:50%;animation:sp .5s linear infinite}@keyframes sp{to{transform:rotate(360deg)}}
    .mt{text-align:center;padding:36px 0;font-size:14px;color:${v.txt3};font-weight:500}

    /* No key state */
    .no-key{text-align:center;padding:32px 16px}.nk-title{font-size:16px;font-weight:700;margin-bottom:6px}.nk-desc{font-size:13px;color:${v.txt3};margin-bottom:16px;line-height:1.5}
    .nk-btn{all:unset;cursor:pointer;padding:10px 20px;background:${v.cta};color:${v.ctaT};font-family:var(--f);font-size:13px;font-weight:600;border-radius:12px;transition:all .12s}.nk-btn:hover{background:${v.ctaH}}

    /* Settings */
    .settings{padding:4px 0}
    .set-title{font-size:17px;font-weight:700;margin-bottom:16px;letter-spacing:-.3px}
    .set-section{margin-bottom:20px}
    .set-label{font-size:13px;font-weight:700;display:block;margin-bottom:4px}
    .set-desc{font-size:12px;color:${v.txt3};margin-bottom:10px;line-height:1.4}
    .set-row{display:flex;gap:6px}
    .set-inp{all:unset;flex:1;padding:10px 14px;background:${v.inp};border:1px solid ${v.bdr};border-radius:10px;font-family:var(--fm);font-size:12px;color:${v.txt};box-sizing:border-box;transition:all .15s}.set-inp:focus{background:${v.inpF};border-color:${v.foc};box-shadow:0 0 0 2px ${v.foc}}
    .set-btn{all:unset;cursor:pointer;padding:10px 18px;background:${v.cta};color:${v.ctaT};font-family:var(--f);font-size:13px;font-weight:600;border-radius:10px;transition:all .12s}.set-btn:hover{background:${v.ctaH}}
    .set-status{font-size:11px;color:#5B9CF5;margin-top:8px;font-weight:500}.set-warn{color:${v.dangerT}}
    .set-back{all:unset;cursor:pointer;font-family:var(--f);font-size:13px;font-weight:600;color:#5B9CF5;padding:4px 0;transition:opacity .12s}.set-back:hover{opacity:.7}

    .rh{position:absolute;bottom:0;right:0;width:24px;height:24px;cursor:nwse-resize;z-index:10}.rh::after{content:'';position:absolute;bottom:6px;right:6px;width:10px;height:10px;border-right:2px solid ${v.txt3};border-bottom:2px solid ${v.txt3};border-radius:0 0 3px 0;opacity:.5}.rh:hover::after{opacity:.8}
    @media(max-width:480px){.m{right:8px!important;width:calc(100vw - 16px)!important;border-radius:20px}}
    `;
  }
})();
