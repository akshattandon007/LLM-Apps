// ── Proppy Popup ─────────────────────────────────────────────────────────────

const $ = id => document.getElementById(id);

// ── Koala quips ───────────────────────────────────────────────────────────────
const MOODS = [
  "munching eucalyptus & ready to find you a home...",
  "I once napped 22 hours. Then found 14 listings. Talent.",
  "judging every estate agent photo on your behalf 🔍",
  "calculating how many eucalyptus trees fit in your garden...",
  "Rightmove is loading... I may nap briefly.",
  "100% focused. Absolutely not thinking about leaves.",
  "sniffing out overpriced properties so you don't have to",
  "every house I find is better than living in a tree. probably.",
  "secretly hoping you pick somewhere with a nice garden 🌿",
  "currently haunting Zoopla. it's fine. they expect it.",
];

let moodIdx = 0;
function rotateMood() {
  moodIdx = (moodIdx + 1) % MOODS.length;
  $('moodText').textContent = MOODS[moodIdx];
}
setInterval(rotateMood, 6000);

// Koala blink animation
function startBlink() {
  setInterval(() => {
    const l = $('eyeL'), r = $('eyeR');
    if (!l || !r) return;
    l.setAttribute('ry', '0.5'); r.setAttribute('ry', '0.5');
    setTimeout(() => { l.setAttribute('ry', '3.5'); r.setAttribute('ry', '3.5'); }, 150);
  }, 4000);
}
startBlink();

// Koala head wiggle on click
$('koalaHead')?.addEventListener('click', () => {
  const quips = ["🐨 *happy koala noises*", "I smell eucalyptus... and a 3-bed semi!", "Don't tap me, I'm working!", "zzz... oh! yes! houses! on it!"];
  const q = quips[Math.floor(Math.random() * quips.length)];
  $('moodText').textContent = q;
  $('koalaHead').style.transform = 'rotate(15deg) scale(1.1)';
  setTimeout(() => { $('koalaHead').style.transform = ''; }, 400);
});

// ── Tab switching ─────────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    $(`tab-${tab.dataset.tab}`).classList.add('active');
  });
});

// ── Chip toggles ─────────────────────────────────────────────────────────────
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => chip.classList.toggle('selected'));
});

// ── Chat state ────────────────────────────────────────────────────────────────
let chatHistory = [];

function getTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

const KOALA_PIP = `<svg class="msg-pip" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="7" cy="13" rx="6.5" ry="6.5" fill="#B0BEC5"/>
  <ellipse cx="7" cy="13" rx="4" ry="4" fill="#E0E0E0"/>
  <ellipse cx="33" cy="13" rx="6.5" ry="6.5" fill="#B0BEC5"/>
  <ellipse cx="33" cy="13" rx="4" ry="4" fill="#E0E0E0"/>
  <ellipse cx="20" cy="22" rx="14" ry="13" fill="#CFD8DC"/>
  <ellipse cx="20" cy="25" rx="9" ry="7" fill="#ECEFF1"/>
  <ellipse cx="15" cy="19" rx="2.5" ry="2.8" fill="#263238"/>
  <ellipse cx="25" cy="19" rx="2.5" ry="2.8" fill="#263238"/>
  <ellipse cx="20" cy="24" rx="3" ry="2" fill="#546E7A"/>
</svg>`;

function appendMsg(text, sender = 'proppy', isHtml = false) {
  const msgs = $('messages');
  const div = document.createElement('div');
  div.className = `msg ${sender}`;

  if (sender === 'proppy') {
    const inner = document.createElement('div');
    inner.className = 'msg-inner';
    inner.innerHTML = KOALA_PIP;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    if (isHtml) bubble.innerHTML = text;
    else bubble.textContent = text;
    inner.appendChild(bubble);
    div.appendChild(inner);
  } else {
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    if (isHtml) bubble.innerHTML = text;
    else bubble.textContent = text;
    div.appendChild(bubble);
  }

  const time = document.createElement('div');
  time.className = 'msg-time';
  time.textContent = getTime();
  div.appendChild(time);

  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function showTyping() {
  $('typing').classList.add('show');
  $('moodText').textContent = 'sniffing the internet for houses... 🔍';
  $('messages').scrollTop = $('messages').scrollHeight;
}
function hideTyping() {
  $('typing').classList.remove('show');
  rotateMood();
}

function renderListing(l) {
  return `<div class="listing-card">
    <div class="lc-title">🏠 ${l.title || 'Property'}</div>
    <div class="lc-price">${l.price || 'POA'}</div>
    <div class="lc-detail">${l.address || ''}</div>
    <div class="lc-detail">${l.details || ''}</div>
    ${l.source ? `<div class="lc-source">via ${l.source}</div>` : ''}
    ${l.url ? `<a class="lc-link" href="${l.url}" target="_blank">View listing ↗</a>` : ''}
  </div>`;
}

// ── Send message ──────────────────────────────────────────────────────────────
async function sendMessage() {
  const input = $('chatInput');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  input.style.height = 'auto';
  appendMsg(text, 'user');
  chatHistory.push({ role: 'user', content: text });

  $('sendBtn').disabled = true;
  showTyping();

  try {
    const config = await getStoredConfig();
    const prefs  = await getStoredPrefs();

    const reply = await proppyChat({
      apiKey: config.anthropicKey || '',
      message: text,
      history: chatHistory,
      preferences: prefs,
    });

    hideTyping();

    if (reply.text) {
      appendMsg(reply.text, 'proppy');
      chatHistory.push({ role: 'assistant', content: reply.text });
    }
    (reply.listings || []).forEach(l => appendMsg(renderListing(l), 'proppy', true));

    if (reply.prefs_update && Object.keys(reply.prefs_update).length) {
      const existing = await getStoredPrefs();
      await chrome.storage.local.set({ prefs: { ...existing, ...reply.prefs_update } });
      await loadPrefsUI();
    }

  } catch (err) {
    hideTyping();
    appendMsg(`Oof. ${err.message} 🐨`, 'proppy');
  }

  $('sendBtn').disabled = false;
  await chrome.storage.local.set({ chatHistory: chatHistory.slice(-40) });
}

$('sendBtn').addEventListener('click', sendMessage);
$('chatInput').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
$('chatInput').addEventListener('input', function () {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 80) + 'px';
});

// ── Refresh ───────────────────────────────────────────────────────────────────
$('refreshBtn').addEventListener('click', async () => {
  const status = $('searchStatus');
  status.classList.add('show');
  status.textContent = 'Sniffing...';

  try {
    const config = await getStoredConfig();
    const prefs  = await getStoredPrefs();
    if (!prefs.location && !prefs.budgetMax) {
      status.classList.remove('show');
      document.querySelector('[data-tab="chat"]').click();
      appendMsg("Fill in your wishlist first — even a koala needs coordinates! 🐨📋", 'proppy');
      return;
    }
    const result = await proppySearch({ apiKey: config.anthropicKey || '', preferences: prefs });
    status.textContent = 'Done!';
    setTimeout(() => status.classList.remove('show'), 2500);
    document.querySelector('[data-tab="chat"]').click();
    const n = result.listings?.length || 0;
    appendMsg(`Found ${n} ${n === 1 ? 'property' : 'properties'} — Proppy delivers! 🐨🏠`, 'proppy');
    (result.listings || []).slice(0, 6).forEach(l => appendMsg(renderListing(l), 'proppy', true));
  } catch (err) {
    status.classList.remove('show');
    appendMsg(`Search blew up: ${err.message}`, 'proppy');
  }
});

// ── New listings from background ──────────────────────────────────────────────
chrome.runtime.onMessage.addListener(msg => {
  if (msg.type === 'NEW_LISTINGS') {
    document.querySelector('[data-tab="chat"]').click();
    appendMsg(`🔔 Just sniffed out ${msg.count} fresh listings while you were away!`, 'proppy');
    (msg.listings || []).slice(0, 3).forEach(l => appendMsg(renderListing(l), 'proppy', true));
  }
});

// ── Prefs UI ──────────────────────────────────────────────────────────────────
async function loadPrefsUI() {
  const p = await getStoredPrefs();
  if (p.location)  $('pref-location').value = p.location;
  if (p.commute)   $('pref-commute').value  = p.commute;
  if (p.budgetMin) $('pref-min').value      = p.budgetMin;
  if (p.budgetMax) $('pref-max').value      = p.budgetMax;
  if (p.bedsMin)   $('pref-beds-min').value = p.bedsMin;
  if (p.bedsMax)   $('pref-beds-max').value = p.bedsMax;
  const setChips = (id, vals = []) =>
    document.querySelectorAll(`#${id} .chip`).forEach(c =>
      c.classList.toggle('selected', vals.includes(c.dataset.val)));
  setChips('pref-types',     p.types     || []);
  setChips('pref-ownership', p.ownership || []);
  setChips('pref-features',  p.features  || []);
}

$('savePrefs').addEventListener('click', async () => {
  const chips = id => [...document.querySelectorAll(`#${id} .chip.selected`)].map(c => c.dataset.val);
  const prefs = {
    location:  $('pref-location').value,
    commute:   $('pref-commute').value,
    budgetMin: $('pref-min').value,
    budgetMax: $('pref-max').value,
    bedsMin:   $('pref-beds-min').value,
    bedsMax:   $('pref-beds-max').value,
    types:     chips('pref-types'),
    ownership: chips('pref-ownership'),
    features:  chips('pref-features'),
  };
  await chrome.storage.local.set({ prefs });
  document.querySelector('[data-tab="chat"]').click();
  appendMsg("Wishlist saved! Now I know exactly what to sniff for 🐨✨", 'proppy');
});

// ── Config UI ─────────────────────────────────────────────────────────────────
async function loadConfigUI() {
  const c = await getStoredConfig();
  if (c.anthropicKey) $('anthropicKey').value = c.anthropicKey;
  if (c.notify !== undefined) $('notifyToggle').checked = c.notify;
  if (c.interval) $('searchInterval').value = c.interval;
}

$('saveConfig').addEventListener('click', async () => {
  const config = {
    anthropicKey: $('anthropicKey').value.trim(),
    notify:   $('notifyToggle').checked,
    interval: parseInt($('searchInterval').value),
  };
  await chrome.storage.local.set({ config });
  chrome.runtime.sendMessage({ type: 'UPDATE_ALARM', interval: config.interval }).catch(() => {});
  $('connectionStatus').innerHTML = '<span class="status-dot ok"></span><span>Config saved ✓</span>';
});

$('testConnection').addEventListener('click', async () => {
  const statusEl = $('connectionStatus');
  const key = $('anthropicKey').value;
  statusEl.innerHTML = '<span class="status-dot idle"></span><span>Testing...</span>';
  try {
    await testApiKey(key);
    statusEl.innerHTML = '<span class="status-dot ok"></span><span>API key works ✓ Proppy is ready to hunt! 🐨</span>';
  } catch (err) {
    statusEl.innerHTML = `<span class="status-dot err"></span><span>${err.message}</span>`;
  }
});

// ── Init ──────────────────────────────────────────────────────────────────────
(async () => {
  await loadConfigUI();
  await loadPrefsUI();
  const saved = await chrome.storage.local.get('chatHistory');
  if (saved.chatHistory?.length) {
    $('messages').innerHTML = '';
    chatHistory = saved.chatHistory;
    chatHistory.forEach(m => appendMsg(m.content, m.role === 'user' ? 'user' : 'proppy'));
  }
})();
