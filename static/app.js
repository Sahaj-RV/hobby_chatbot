// app.js — HobbyBot v4
// Core new features:
//   streamMessage()  — reads SSE stream, renders tokens as they arrive
//   renderMarkdown() — converts **bold**, bullets, `code` to HTML
//   Input is NEVER disabled — user can type at any point

// ── STATE ─────────────────────────────────────
const S = {
  email: null, userId: null,
  chats: [], activeChatId: null,
  activeChatProfile: null,
  quizActive: false, currentQ: null,
  isStreaming: false,   // blocks sending while Claude is mid-response
  isListening: false,   // voice input state
  recognition: null,    // speech recognition instance
};

const HINTS = [
  "What tools do I need to start?",
  "How do I earn money from this?",
  "Give me a week 2 plan",
  "What are common beginner mistakes?",
  "How much time do I need daily?",
  "Compare two hobbies for me",
];

// ═════════════════════════════════════════════
// INIT — check persistent session
// ═════════════════════════════════════════════
window.addEventListener("DOMContentLoaded", async () => {
  buildOtpBoxes("otp-boxes");
  initTheme();
  const r = await api("/api/auth/check");
  if (r.logged_in) {
    S.email  = r.email;
    S.userId = r.user_id;
    S.chats  = r.chats || [];
    launchApp();
  }
});

// ═════════════════════════════════════════════
// AUTH
// ═════════════════════════════════════════════
async function sendOtp() {
  const emailEl = $("email-input"), errEl = $("email-err"), btn = $("send-btn");
  const email   = emailEl.value.trim();
  errEl.textContent = ""; emailEl.classList.remove("err");

  if (!email) { emailEl.classList.add("err"); errEl.textContent = "Please enter your email."; return; }

  btn.disabled = true; $("send-btn-text").textContent = "Sending…";
  const r = await api("/api/send-otp", { email, purpose: "verify" });
  btn.disabled = false; $("send-btn-text").textContent = "Send verification code";

  if (r.success) {
    S.email = email;
    $("otp-email-display").textContent = email;
    buildOtpBoxes("otp-boxes");
    showCard("card-otp");
    document.querySelector("#otp-boxes .otp-d")?.focus();
  } else {
    emailEl.classList.add("err"); errEl.textContent = r.error || "Something went wrong.";
  }
}

async function verifyOtp() {
  const otp = collectOtp("otp-boxes"), errEl = $("otp-err"), btn = $("verify-btn");
  errEl.textContent = "";
  if (otp.length < 6) { markOtpErr("otp-boxes"); errEl.textContent = "Enter all 6 digits."; return; }

  btn.disabled = true; $("verify-btn-text").textContent = "Verifying…";
  const r = await api("/api/verify-otp", { otp });
  btn.disabled = false; $("verify-btn-text").textContent = "Verify & enter HobbyBot";

  if (r.valid) {
    S.email = r.email; S.userId = r.user_id; S.chats = r.chats || [];
    launchApp();
  } else {
    markOtpErr("otp-boxes"); errEl.textContent = r.reason || "Invalid code.";
  }
}

async function resendOtp() {
  clearOtpBoxes("otp-boxes"); $("otp-err").textContent = "";
  const r = await api("/api/send-otp", { email: S.email, purpose: "verify" });
  if (r.success) toast("New code sent!"); else $("otp-err").textContent = r.error;
}

function showCard(id) {
  ["card-email","card-otp"].forEach(c => $(c).classList.add("hidden"));
  $(id).classList.remove("hidden");
}

async function signOut() { await api("/api/logout", {}); location.reload(); }

// ═════════════════════════════════════════════
// APP LAUNCH
// ═════════════════════════════════════════════
function launchApp() {
  $("login-page").classList.add("hidden");
  $("app").classList.remove("hidden");
  const initials = (S.email || "U").slice(0, 2).toUpperCase();
  $("u-av").textContent    = initials;
  $("u-name").textContent  = S.email.split("@")[0];
  $("u-email").textContent = S.email;
  renderChatList(S.chats);
  if (!S.chats.length) startNewChat(); else showEmptyState();
}

// ═════════════════════════════════════════════
// SIDEBAR
// ═════════════════════════════════════════════
function renderChatList(chats) {
  const el = $("chat-list"); el.innerHTML = "";
  if (!chats.length) {
    el.innerHTML = `<div style="padding:18px 12px;font-size:12px;color:var(--sb-muted);text-align:center">No chats yet</div>`;
    return;
  }
  const now = Date.now();
  const G = { Today: [], Yesterday: [], Earlier: [] };
  chats.forEach(c => {
    const age = now - new Date(c.updated_at).getTime();
    if      (age < 86400000)  G.Today.push(c);
    else if (age < 172800000) G.Yesterday.push(c);
    else                      G.Earlier.push(c);
  });
  Object.entries(G).forEach(([label, items]) => {
    if (!items.length) return;
    const lbl = ce("div","sb-section-lbl"); lbl.textContent = label; el.appendChild(lbl);
    items.forEach(c => el.appendChild(makeChatItem(c)));
  });
}

function makeChatItem(chat) {
  const item = ce("div","chat-item" + (chat.id === S.activeChatId ? " active" : ""));
  item.dataset.id = chat.id;
  const bc = chat.status==="saved" ? "b-saved" : chat.status==="active" ? "b-active" : "b-draft";
  const bl = chat.status==="saved" ? "Saved"   : chat.status==="active" ? "Active"   : "Draft";
  item.innerHTML = `
    <div class="ci-title">${esc(chat.title)}</div>
    <div class="ci-meta">
      <span class="ci-badge ${bc}">${bl}</span>
      <span class="ci-time">${relTime(chat.updated_at)}</span>
    </div>`;
  item.onclick = () => openChat(chat.id);
  return item;
}

function filterChats(q) {
  const s = q.toLowerCase();
  document.querySelectorAll(".chat-item").forEach(el =>
    el.style.display = el.querySelector(".ci-title").textContent.toLowerCase().includes(s) ? "" : "none");
}

// ═════════════════════════════════════════════
// CHAT OPERATIONS
// ═════════════════════════════════════════════
async function startNewChat() {
  const r = await api("/api/chats", {});
  S.chats.unshift(r.chat);
  S.activeChatId = r.chat.id;
  S.activeChatProfile = null;
  S.quizActive   = true;
  S.currentQ     = r.first_question;

  renderChatList(S.chats);
  showChatView(r.chat);
  clearMsgs();
  appendMsg("bot", r.greeting);
  showQuizOptions(r.first_question);
}

async function openChat(chatId) {
  if (S.activeChatId === chatId) return;
  S.activeChatId = chatId;
  markActive(chatId);

  const r = await api(`/api/chats/${chatId}/messages`);
  S.quizActive = !!r.quiz_state;
  S.currentQ   = r.quiz_state;
  S.activeChatProfile = r.chat.profile ? JSON.parse(r.chat.profile) : null;

  showChatView(r.chat);
  clearMsgs();

  r.messages.forEach(m => {
    if (m.msg_type === "results") return;
    appendMsg(m.role === "bot" ? "bot" : "user", m.content, false);
  });

  if (r.quiz_state) showQuizOptions(r.quiz_state);
  else              clearQuizOptions();

  setHints(); scrollMsgs();
}

async function deleteChat() {
  if (!S.activeChatId || !confirm("Delete this chat?")) return;
  await apidel(`/api/chats/${S.activeChatId}`);
  S.chats = S.chats.filter(c => c.id !== S.activeChatId);
  S.activeChatId = null;
  renderChatList(S.chats);
  showEmptyState();
}

// ═════════════════════════════════════════════
// QUIZ OPTIONS (shown above input, not replacing it)
// ═════════════════════════════════════════════
function showQuizOptions(q) {
  S.currentQ = q;
  // Show question as bot message only if it's a new question
  appendMsg("bot", q.content);

  const tray = $("opts-tray"); tray.innerHTML = "";

  // Capture the entire question object at button-creation time.
  // Do NOT reference S.currentQ inside the click handler — it may
  // have been cleared by the time the user clicks.
  const capturedQ = { ...q };

  q.options.forEach(opt => {
    const btn = ce("button", "opt-btn");
    btn.textContent = opt;
    btn.onclick = () => pickQuizAnswer(opt, capturedQ);
    tray.appendChild(btn);
  });
}

function clearQuizOptions() {
  $("opts-tray").innerHTML = "";
  S.quizActive = false;
  S.currentQ   = null;
}

async function pickQuizAnswer(answer, question) {
  if (!question || S.isStreaming) return;

  // Capture question_id before clearing state
  const qid = question.question_id;
  clearQuizOptions();
  appendMsg("user", answer);

  const tid = showTyping();
  const r   = await api(`/api/chats/${S.activeChatId}/answer`, {
    question_id: qid, answer
  });
  removeEl(tid);

  if (r.type === "question") {
    showQuizOptions(r);
  } else if (r.type === "results") {
    S.quizActive = false;
    S.currentQ   = null;
    updateTitle(S.activeChatId, r.title);
    appendMsg("bot", "Here are your top hobby matches! 🎉");
    renderResultCards(r.recommendations);
    setHints();
  }
}

// ═════════════════════════════════════════════
// MAIN SEND — always available, streams response
// ═════════════════════════════════════════════
function onKey(e) {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

async function sendMessage() {
  const input = $("msg-input");
  const msg   = input.value.trim();
  if (!msg || S.isStreaming || !S.activeChatId) return;

  input.value = ""; autoGrow(input);
  appendMsg("user", msg);
  clearQuizOptions();   // typing a message dismisses quiz buttons

  // Stream Claude's response
  await streamMessage(msg);
}

// ═════════════════════════════════════════════
// STREAMING — the core new feature
// ═════════════════════════════════════════════
async function streamMessage(userMsg) {
  S.isStreaming = true;
  $("send-msg-btn").disabled = true;

  const bubble = createStreamBubble();
  let fullText = "";

  try {
    const response = await fetch(`/api/chats/${S.activeChatId}/stream`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ message: userMsg }),
    });

    // Non-2xx means auth/validation error — read JSON body
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      bubble.innerHTML = `<span class="err-inline">⚠ ${esc(err.error || "Request failed")}</span>`;
      return;
    }

    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let   buffer  = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      // Accumulate decoded bytes — a single network chunk may contain
      // multiple SSE events OR a partial one. We split on \n\n (SSE boundary).
      buffer += decoder.decode(value, { stream: true });

      // Split on double-newline (SSE event boundary)
      const parts = buffer.split("\n\n");
      // Last element is either empty or an incomplete event — keep in buffer
      buffer = parts.pop();

      for (const part of parts) {
        // Each part may have multiple lines; find the "data:" line
        for (const line of part.split("\n")) {
          if (!line.startsWith("data:")) continue;
          const raw = line.slice(5).trim();
          if (!raw) continue;

          let evt;
          try { evt = JSON.parse(raw); } catch (e) {
            console.warn("SSE parse error:", raw, e);
            continue;
          }

          if (evt.type === "token") {
            fullText += evt.text;
            bubble.innerHTML = renderMarkdown(fullText) + '<span class="cursor">▋</span>';
            scrollMsgs();

          } else if (evt.type === "done") {
            bubble.innerHTML = renderMarkdown(evt.full || fullText);
            scrollMsgs();

          } else if (evt.type === "error") {
            bubble.innerHTML = `<span class="err-inline">⚠ ${esc(evt.message)}</span>`;
            console.error("AI error:", evt.message);
          }
        }
      }
    }

    // Safety: if done event never came, render what we have
    if (fullText && bubble.querySelector(".cursor")) {
      bubble.innerHTML = renderMarkdown(fullText);
    }

  } catch (err) {
    bubble.innerHTML = `<span class="err-inline">⚠ Connection lost. Please try again.</span>`;
    console.error("Stream fetch error:", err);
  } finally {
    const cur = bubble.querySelector(".cursor");
    if (cur) cur.remove();
    S.isStreaming = false;
    $("send-msg-btn").disabled = false;
    $("msg-input").focus();
  }
}

function createStreamBubble() {
  const msgs   = $("msgs");
  const row    = ce("div", "msg");
  const av     = ce("div", "av"); av.textContent = "✦";
  const bubble = ce("div", "bubble stream-bubble");
  bubble.innerHTML = '<span class="cursor">▋</span>';
  row.appendChild(av);
  row.appendChild(bubble);
  msgs.appendChild(row);
  scrollMsgs();
  return bubble;
}

// ═════════════════════════════════════════════
// MARKDOWN RENDERER
// Converts Claude's markdown to safe HTML
// ═════════════════════════════════════════════
function renderMarkdown(text) {
  if (!text) return "";

  let html = esc(text);  // escape first, then selectively un-escape for markdown

  // Code blocks  ```...```
  html = html.replace(/```([^`]*?)```/gs, (_, code) =>
    `<pre><code>${code.trim()}</code></pre>`);

  // Inline code  `...`
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Bold  **...**
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  // Italic  *...*  (only when not part of **)
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, "<em>$1</em>");

  // Horizontal rule  ---
  html = html.replace(/^---$/gm, "<hr/>");

  // Headers  ## heading
  html = html.replace(/^### (.+)$/gm, "<h4>$1</h4>");
  html = html.replace(/^## (.+)$/gm,  "<h3>$1</h3>");
  html = html.replace(/^# (.+)$/gm,   "<h2>$1</h2>");

  // Bullet lists  - item  or  • item
  html = html.replace(/^[•\-] (.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>");
  // Fix nested <ul> wrapping every line separately
  html = html.replace(/<\/ul>\s*<ul>/g, "");

  // Numbered lists  1. item
  html = html.replace(/^\d+\. (.+)$/gm, "<oli>$1</oli>");
  html = html.replace(/(<oli>.*<\/oli>)/gs, "<ol>$1</ol>");
  html = html.replace(/<\/ol>\s*<ol>/g, "");
  html = html.replace(/<oli>/g, "<li>").replace(/<\/oli>/g, "</li>");

  // Line breaks → <br> (but not inside pre blocks)
  html = html.replace(/\n/g, "<br/>");

  // Fix <br/> inside pre/ul/ol/li (messy)
  html = html.replace(/<pre><code>(.*?)<\/code><\/pre>/gs, (m, code) =>
    `<pre><code>${code.replace(/<br\/>/g, "\n")}</code></pre>`);
  html = html.replace(/<(ul|ol|li|h2|h3|h4|hr)>(.*?)<br\/>/gs, "<$1>$2");

  return html;
}

// ═════════════════════════════════════════════
// MESSAGE RENDERING
// ═════════════════════════════════════════════
function appendMsg(role, text, animate = true) {
  const msgs = $("msgs");
  const row  = ce("div", role === "bot" ? "msg" : "msg u");
  if (animate) row.style.animation = "fadeUp .22s ease";

  const av = ce("div", role === "bot" ? "av" : "av u-av");
  av.textContent = role === "bot" ? "✦" : (S.email || "U").slice(0,1).toUpperCase();

  const bubble = ce("div", "bubble");
  bubble.innerHTML = role === "bot" ? renderMarkdown(text) : esc(text);

  if (role === "bot") { row.appendChild(av); row.appendChild(bubble); }
  else                { row.appendChild(av); row.appendChild(bubble); row.style.flexDirection="row-reverse"; }

  msgs.appendChild(row);
  scrollMsgs();
}

function showTyping() {
  const id  = "t-" + Date.now();
  const row = ce("div","msg");
  row.id = id;
  row.innerHTML = `<div class="av">✦</div>
    <div class="bubble"><div class="typing-row">
      <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    </div></div>`;
  $("msgs").appendChild(row); scrollMsgs();
  return id;
}

function renderResultCards(recs) {
  const msgs  = $("msgs");
  const row   = ce("div","msg");
  const av    = ce("div","av"); av.textContent = "✦";
  const wrap  = ce("div","result-wrap");

  recs.forEach((rec, i) => {
    const card = ce("div", i === 0 ? "hcard top-hcard" : "hcard");
    card.innerHTML = `
      <div class="hcard-head">
        <div>
          ${i===0?'<div class="best-badge">Best match</div>':""}
          <div class="hcard-name">${esc(rec.name)}</div>
        </div>
        <div class="hcard-pct">${rec.score}%</div>
      </div>
      <div class="hbar"><div class="hbar-fill" style="width:${rec.score}%"></div></div>
      <div class="hcard-why">${esc(rec.data.why_it_fits)}</div>
      <div class="hcard-tags">
        <span class="htag">${rec.data.difficulty}</span>
        <span class="htag">${rec.data.time_needed}</span>
        <span class="htag">${rec.data.cost}</span>
      </div>
      <button class="hcard-btn" onclick="openHobbyModal('${rec.key}')">View 7-day plan →</button>`;
    wrap.appendChild(card);
  });

  row.appendChild(av); row.appendChild(wrap);
  msgs.appendChild(row); scrollMsgs();
}

// ═════════════════════════════════════════════
// UI HELPERS
// ═════════════════════════════════════════════
function showChatView(chat) {
  $("empty-state").classList.add("hidden");
  $("chat-view").classList.remove("hidden");
  $("chat-bar-title").textContent = chat.title || "New chat";
  $("chat-bar-meta").textContent  = `HobbyBot · ${chat.status}`;
}

function showEmptyState() {
  $("empty-state").classList.remove("hidden");
  $("chat-view").classList.add("hidden");
}

function clearMsgs() {
  $("msgs").innerHTML = "";
  $("opts-tray").innerHTML = "";
  $("hints-row").innerHTML = "";
}

function getHabitKey() {
  return `hobbybot-habit-${S.userId || 'guest'}`;
}

function loadHabitState() {
  const raw = localStorage.getItem(getHabitKey());
  if (!raw) return { habit: '', streak: 0, lastCompleted: null };
  try { return JSON.parse(raw); } catch { return { habit: '', streak: 0, lastCompleted: null }; }
}

function saveHabitState(state) {
  localStorage.setItem(getHabitKey(), JSON.stringify(state));
}

function closeHabitModal(evt) {
  if (evt && evt.target !== evt.currentTarget) return;
  $("habit-modal").classList.add("hidden");
}

function closeIncomeModal(evt) {
  if (evt && evt.target !== evt.currentTarget) return;
  $("income-modal").classList.add("hidden");
}

function closeMoodModal(evt) {
  if (evt && evt.target !== evt.currentTarget) return;
  $("mood-modal").classList.add("hidden");
}

function closeRoadmapModal(evt) {
  if (evt && evt.target !== evt.currentTarget) return;
  $("roadmap-modal").classList.add("hidden");
}

function toggleVoiceInput() {
  if (!S.recognition) {
    initSpeechRecognition();
  }

  if (S.isListening) {
    stopVoiceInput();
  } else {
    startVoiceInput();
  }
}

function initSpeechRecognition() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    toast('Voice input not supported in this browser');
    return;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  S.recognition = new SpeechRecognition();
  S.recognition.continuous = false;
  S.recognition.interimResults = false;
  S.recognition.lang = 'en-US';

  S.recognition.onstart = () => {
    S.isListening = true;
    $('voice-btn').classList.add('active');
    $('msg-input').placeholder = 'Listening...';
  };

  S.recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    $('msg-input').value = transcript;
    autoGrow($('msg-input'));
    stopVoiceInput();
  };

  S.recognition.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    toast('Voice input failed. Try again.');
    stopVoiceInput();
  };

  S.recognition.onend = () => {
    stopVoiceInput();
  };
}

function startVoiceInput() {
  if (S.isStreaming) return;
  try {
    S.recognition.start();
  } catch (e) {
    toast('Could not start voice input');
  }
}

function stopVoiceInput() {
  S.isListening = false;
  $('voice-btn').classList.remove('active');
  $('msg-input').placeholder = 'Ask anything — or click an option above…';

  if (S.recognition) {
    S.recognition.stop();
  }
}

function openMoodSuggestions() {
  if (!S.userId) { toast('Sign in to use mood-based suggestions.'); return; }
  const profile = S.activeChatProfile || {};

  $('mood-content').innerHTML = `
    <div style="font-size:26px;margin-bottom:8px">😊 Mood-based suggestions</div>
    <p class="modal-sub">Tell us how you're feeling and we'll suggest hobbies that match your current mood.</p>
    <div class="mood-grid">
      <button class="mood-btn" onclick="selectMood('energetic')">⚡ Energetic</button>
      <button class="mood-btn" onclick="selectMood('relaxed')">😌 Relaxed</button>
      <button class="mood-btn" onclick="selectMood('creative')">🎨 Creative</button>
      <button class="mood-btn" onclick="selectMood('adventurous')">🗺️ Adventurous</button>
      <button class="mood-btn" onclick="selectMood('social')">👥 Social</button>
      <button class="mood-btn" onclick="selectMood('focused')">🎯 Focused</button>
      <button class="mood-btn" onclick="selectMood('stressed')">😰 Stressed</button>
      <button class="mood-btn" onclick="selectMood('bored')">😴 Bored</button>
    </div>
    <div id="mood-results" style="margin-top:16px;"></div>
  `;
  $('mood-modal').classList.remove('hidden');
}

async function selectMood(mood) {
  const resultsEl = $('mood-results');
  resultsEl.innerHTML = '<div style="text-align:center;padding:20px;">Finding suggestions...</div>';

  try {
    const response = await api('/api/mood-suggestions', { mood, profile: S.activeChatProfile });
    if (response.suggestions) {
      resultsEl.innerHTML = `
        <div style="font-size:16px;font-weight:600;margin-bottom:12px">Suggestions for when you're feeling ${mood}:</div>
        ${response.suggestions.map(s => `
          <div class="mood-suggestion">
            <div class="mood-suggestion-name">${esc(s.name)}</div>
            <div class="mood-suggestion-reason">${esc(s.reason)}</div>
          </div>
        `).join('')}
      `;
    } else {
      resultsEl.innerHTML = '<div style="color:#666;text-align:center;padding:20px;">No suggestions found for this mood.</div>';
    }
  } catch (e) {
    resultsEl.innerHTML = '<div style="color:#ef4444;text-align:center;padding:20px;">Failed to get suggestions. Try again.</div>';
  }
}

function openRoadmap() {
  if (!S.userId) { toast('Sign in to generate a roadmap.'); return; }
  if (!S.activeChatProfile) { toast('Complete the quiz first to get a personalized roadmap.'); return; }

  $('roadmap-content').innerHTML = `
    <div style="font-size:26px;margin-bottom:8px">📋 30/60/90 Day Roadmap</div>
    <p class="modal-sub">Get a structured plan to turn your hobby into a sustainable habit and potentially a side income.</p>
    <div class="roadmap-controls">
      <button class="btn-cta" onclick="generateRoadmap()">Generate Roadmap</button>
    </div>
    <div id="roadmap-results" style="margin-top:16px;"></div>
  `;
  $('roadmap-modal').classList.remove('hidden');
}

async function generateRoadmap() {
  const resultsEl = $('roadmap-results');
  resultsEl.innerHTML = '<div style="text-align:center;padding:20px;">Generating your roadmap...</div>';

  try {
    const response = await api('/api/generate-roadmap', { profile: S.activeChatProfile });
    if (response.roadmap) {
      resultsEl.innerHTML = `
        <div class="roadmap-container">
          <div class="roadmap-phase">
            <div class="roadmap-phase-title">📅 30 Days: Foundation</div>
            <div class="roadmap-phase-content">${response.roadmap.thirty_days}</div>
          </div>
          <div class="roadmap-phase">
            <div class="roadmap-phase-title">🚀 60 Days: Growth</div>
            <div class="roadmap-phase-content">${response.roadmap.sixty_days}</div>
          </div>
          <div class="roadmap-phase">
            <div class="roadmap-phase-title">💰 90 Days: Monetization</div>
            <div class="roadmap-phase-content">${response.roadmap.ninety_days}</div>
          </div>
        </div>
      `;
    } else {
      resultsEl.innerHTML = '<div style="color:#666;text-align:center;padding:20px;">Could not generate roadmap. Try again.</div>';
    }
  } catch (e) {
    resultsEl.innerHTML = '<div style="color:#ef4444;text-align:center;padding:20px;">Failed to generate roadmap. Try again.</div>';
  }
}

function openHabitTracker() {
  if (!S.userId) { toast('Sign in to use the habit tracker.'); return; }
  const profile = S.activeChatProfile || {};
  const state = loadHabitState();
  const today = new Date().toISOString().slice(0, 10);
  const completedToday = state.lastCompleted === today;
  const suggested = profile.goal === 'side_hustle' ? 'Spend 15 minutes on your side hustle habit' : profile.goal === 'career' ? 'Practice one career-building habit today' : profile.goal === 'learn' ? 'Build one new skill step today' : 'Do one small hobby task today';
  const habitLabel = state.habit || suggested;
  const streak = state.streak || 0;
  const completedLabel = completedToday ? 'Yes — great job!' : 'Not yet';

  $("habit-content").innerHTML = `
    <div style="font-size:26px;margin-bottom:8px">📅 Daily habit tracker</div>
    <p class="modal-sub">Keep a simple daily habit and build momentum with a visible streak.</p>
    <div class="field-row">
      <label class="field-label">Habit name</label>
      <input id="habit-name-input" class="field-input" value="${esc(habitLabel)}" placeholder="e.g. Practice 15 minutes of guitar" />
    </div>
    <div class="field-row">
      <div class="field-label">Today's completed?</div>
      <div style="font-size:14px;color:var(--muted);">${esc(completedLabel)}</div>
    </div>
    <div class="field-row">
      <div class="field-label">Current streak</div>
      <div style="font-size:14px;color:var(--muted);">${streak} day${streak===1?'':'s'}</div>
    </div>
    <div class="modal-actions">
      <button class="btn-cta" onclick="saveHabitName()">Save habit</button>
      <button class="btn-cta" onclick="completeHabit()">Mark complete</button>
    </div>
    <p style="font-size:13px;color:var(--muted);margin-top:12px;">Tip: check in every day to keep your streak alive.</p>
  `;
  $("habit-modal").classList.remove("hidden");
}

function saveHabitName() {
  const input = $("habit-name-input");
  if (!input) return;
  const habit = input.value.trim();
  if (!habit) { toast('Enter a habit name first.'); return; }
  const state = loadHabitState();
  state.habit = habit;
  saveHabitState(state);
  toast('Daily habit saved.');
}

function completeHabit() {
  const input = $("habit-name-input");
  const habit = input?.value.trim() || '';
  if (!habit) { toast('Enter a habit name first.'); return; }
  const state = loadHabitState();
  const today = new Date().toISOString().slice(0, 10);
  if (state.lastCompleted === today) { toast('Already completed today.'); return; }
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
  state.habit = habit;
  state.streak = state.lastCompleted === yesterday ? (state.streak || 0) + 1 : 1;
  state.lastCompleted = today;
  saveHabitState(state);
  toast(`Habit completed! Streak: ${state.streak} day${state.streak===1?'':'s'}.`);
  openHabitTracker();
}

function openIncomeCalculator() {
  const profile = S.activeChatProfile || {};
  const goal = profile.goal ? profile.goal.replace('_', ' ') : 'hobby progress';
  const goalLine = profile.goal === 'side_hustle' ? 'This supports your side hustle goal directly.' : `Your current goal is ${esc(goal)}.`;
  $("income-content").innerHTML = `
    <div style="font-size:26px;margin-bottom:8px">💰 Income calculator</div>
    <p class="modal-sub">Estimate how much your hobby time can earn if you turn it into a side hustle.</p>
    <div class="field-row"><label class="field-label">Goal context</label><div style="font-size:14px;color:var(--muted);">${esc(goalLine)}</div></div>
    <div class="field-row"><label class="field-label">Hourly rate</label><input id="income-hourly" class="field-input" type="number" min="0" step="0.01" placeholder="e.g. 25" /></div>
    <div class="field-row"><label class="field-label">Hours per week</label><input id="income-hours" class="field-input" type="number" min="0" step="0.5" placeholder="e.g. 10" /></div>
    <div class="field-row"><label class="field-label">Weeks per month</label><input id="income-weeks" class="field-input" type="number" min="1" step="1" value="4" /></div>
    <div class="modal-actions"><button class="btn-cta" onclick="calculateIncome()">Calculate</button></div>
    <div id="income-results" style="margin-top:14px;font-size:14px;color:var(--muted);"></div>
  `;
  $("income-modal").classList.remove("hidden");
}

function calculateIncome() {
  const hourly = parseFloat($("income-hourly").value);
  const hours = parseFloat($("income-hours").value);
  const weeks  = parseFloat($("income-weeks").value);
  const resultsEl = $("income-results");
  if (Number.isNaN(hourly) || Number.isNaN(hours) || Number.isNaN(weeks) || hourly <= 0 || hours <= 0 || weeks <= 0) {
    resultsEl.textContent = 'Enter valid numbers for rate, hours, and weeks.';
    return;
  }
  const monthly = hourly * hours * weeks;
  const yearly  = monthly * 12;
  resultsEl.innerHTML = `
    <div><strong>Estimated monthly income:</strong> $${monthly.toFixed(2)}</div>
    <div><strong>Estimated annual income:</strong> $${yearly.toFixed(2)}</div>
    <div style="margin-top:8px;color:var(--muted);">Use this to compare hobby time vs other priorities and build a stronger side hustle plan.</div>
  `;
}


function setHints() {
  const el = $("hints-row"); el.innerHTML = "";
  HINTS.forEach(h => {
    const chip = ce("span","hint-chip");
    chip.textContent = h;
    chip.onclick = () => {
      $("msg-input").value = h;
      sendMessage();
    };
    el.appendChild(chip);
  });
}

function scrollMsgs() { const el=$("msgs"); el.scrollTop = el.scrollHeight; }
function markActive(id) {
  document.querySelectorAll(".chat-item").forEach(el =>
    el.classList.toggle("active", el.dataset.id === id));
}
function updateTitle(chatId, title) {
  const c = S.chats.find(x => x.id === chatId);
  if (c) c.title = title;
  $("chat-bar-title").textContent = title;
  const el = document.querySelector(`.chat-item[data-id="${chatId}"] .ci-title`);
  if (el) el.textContent = title;
}
function autoGrow(el) { el.style.height="auto"; el.style.height=Math.min(el.scrollHeight,120)+"px"; }

// ═════════════════════════════════════════════
// SAVE & HOBBY MODAL
// ═════════════════════════════════════════════
async function initiateSave() {
  const r = await api(`/api/chats/${S.activeChatId}/save`, {});
  if (r.success) {
    buildOtpBoxes("save-otp-boxes");
    $("save-modal").classList.remove("hidden");
    document.querySelector("#save-otp-boxes .otp-d")?.focus();
  } else toast("Could not send code: " + (r.error || "error"));
}

async function confirmSave() {
  const otp=collectOtp("save-otp-boxes"), err=$("save-otp-err");
  err.textContent="";
  if (otp.length<6) { markOtpErr("save-otp-boxes"); err.textContent="Enter all 6 digits."; return; }
  const r = await api(`/api/chats/${S.activeChatId}/confirm-save`,{otp});
  if (r.valid) {
    closeSaveModal(); toast("Chat saved! ✓");
    const c=S.chats.find(x=>x.id===S.activeChatId);
    if(c){c.status="saved"; renderChatList(S.chats);}
  } else { markOtpErr("save-otp-boxes"); err.textContent=r.reason||"Invalid OTP."; }
}

function closeSaveModal() { $("save-modal").classList.add("hidden"); clearOtpBoxes("save-otp-boxes"); }

async function openHobbyModal(key) {
  const r = await api(`/api/hobby/${key}`);
  $("hobby-content").innerHTML = `
    <h2 class="hd-h2">${esc(r.name)}</h2>
    <p class="hd-desc">${esc(r.description)}</p>
    <div class="hd-tags">
      <span class="tool-pill">${r.difficulty}</span>
      <span class="tool-pill">${r.time_needed}</span>
      <span class="tool-pill">${r.cost}</span>
    </div>
    <div class="hd-section"><h4>Why this fits you</h4>
      <p style="font-size:13px;line-height:1.6">${esc(r.why_it_fits)}</p></div>
    <div class="hd-section"><h4>7-day starter plan</h4>
      ${r.seven_day_plan.map(s=>`<div class="plan-step">${esc(s)}</div>`).join("")}</div>
    <div class="hd-section"><h4>Tools</h4>
      <div class="tool-pills">${r.tools.map(t=>`<span class="tool-pill">${esc(t)}</span>`).join("")}</div></div>
    <div class="hd-section"><h4>Mistakes to avoid</h4>
      ${r.mistakes_to_avoid.map(m=>`<div class="mistake"><span class="mx">✕</span><span>${esc(m)}</span></div>`).join("")}</div>
    <div class="hd-section"><h4>Career path</h4>
      <p style="font-size:13px;line-height:1.6">${esc(r.career_path)}</p></div>`;
  $("hobby-modal").classList.remove("hidden");
}

function closeHobbyModal(e) {
  if (!e||e.target===$("hobby-modal")) $("hobby-modal").classList.add("hidden");
}


// ═════════════════════════════════════════════
// FEATURE 1 — DARK MODE
// ═════════════════════════════════════════════
function toggleDark() {
  const isDark = document.body.classList.toggle('dark');
  localStorage.setItem('hb-theme', isDark ? 'dark' : 'light');
  $('theme-btn').textContent = isDark ? '☀️' : '🌙';
}

function initTheme() {
  const saved = localStorage.getItem('hb-theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (saved === 'dark' || (!saved && prefersDark)) {
    document.body.classList.add('dark');
    const btn = $('theme-btn');
    if (btn) btn.textContent = '☀️';
  }
}

// ═════════════════════════════════════════════
// FEATURE 2 — PDF EXPORT
// ═════════════════════════════════════════════
function exportPDF() {
  if (!S.activeChatId) { toast('Open a chat first'); return; }
  // Add a temporary print header
  const header = document.createElement('div');
  header.id = 'print-header';
  header.style.cssText = 'display:none;padding:0 0 16px;border-bottom:2px solid #7C3AED;margin-bottom:20px';
  header.innerHTML = `
    <div style="font-size:22px;font-weight:700;color:#7C3AED">✦ HobbyBot</div>
    <div style="font-size:14px;color:#666;margin-top:4px">Hobby Discovery Report · ${new Date().toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric'})}</div>
    <div style="font-size:13px;color:#888;margin-top:2px">${S.email || ''}</div>
  `;
  document.querySelector('.msgs').prepend(header);

  // Show header only during print
  const style = document.createElement('style');
  style.id = 'print-header-show';
  style.textContent = '@media print { #print-header { display:block !important } }';
  document.head.appendChild(style);

  window.print();

  // Clean up after print dialog closes
  setTimeout(() => {
    header.remove();
    style.remove();
  }, 1000);

  toast('Print dialog opened — save as PDF');
}

// ═════════════════════════════════════════════
// FEATURE 3 — PUBLIC PROFILE / SHARE LINK
// ═════════════════════════════════════════════
async function shareProfile() {
  if (!S.activeChatId) { toast('Open a chat with results first'); return; }

  // Create/get the public profile token for this chat
  const r = await api(`/api/chats/${S.activeChatId}/share`, {});
  if (!r.token) { toast('No results to share yet — finish the quiz first'); return; }

  const url = `${location.origin}/p/${r.token}`;
  $('share-url').value = url;
  $('share-popup').classList.remove('hidden');
}

function closeSharePopup() {
  $('share-popup').classList.add('hidden');
}

async function copyShareUrl() {
  const url = $('share-url').value;
  try {
    await navigator.clipboard.writeText(url);
    toast('Link copied to clipboard!');
  } catch {
    $('share-url').select();
    document.execCommand('copy');
    toast('Link copied!');
  }
  closeSharePopup();
}

// ═════════════════════════════════════════════
// OTP HELPERS
// ═════════════════════════════════════════════
function buildOtpBoxes(cid) {
  const el=$(cid); el.innerHTML="";
  for(let i=0;i<6;i++){
    const inp=document.createElement("input");
    inp.className="otp-d"; inp.maxLength=1; inp.type="text"; inp.inputMode="numeric";
    inp.addEventListener("input",e=>{
      const v=e.target.value.replace(/\D/g,"");
      inp.value=v?v[v.length-1]:"";
      inp.classList.toggle("filled",!!inp.value);
      if(inp.value&&inp.nextElementSibling) inp.nextElementSibling.focus();
    });
    inp.addEventListener("keydown",e=>{
      if(e.key==="Backspace"&&!inp.value&&inp.previousElementSibling) inp.previousElementSibling.focus();
      if(e.key==="Enter"){
        if(cid==="otp-boxes") verifyOtp();
        if(cid==="save-otp-boxes") confirmSave();
      }
    });
    inp.addEventListener("paste",e=>{
      e.preventDefault();
      const d=e.clipboardData.getData("text").replace(/\D/g,"");
      const boxes=el.querySelectorAll(".otp-d");
      boxes.forEach((b,j)=>{b.value=d[j]||"";b.classList.toggle("filled",!!b.value);});
      boxes[Math.min(d.length,5)].focus();
    });
    el.appendChild(inp);
  }
}
function collectOtp(cid){return Array.from(document.querySelectorAll(`#${cid} .otp-d`)).map(i=>i.value).join("");}
function markOtpErr(cid){document.querySelectorAll(`#${cid} .otp-d`).forEach(i=>i.classList.add("err"));}
function clearOtpBoxes(cid){document.querySelectorAll(`#${cid} .otp-d`).forEach(i=>{i.value="";i.classList.remove("filled","err");});}

// ═════════════════════════════════════════════
// UTILS
// ═════════════════════════════════════════════
const $ = id => document.getElementById(id);
const ce = (tag,cls) => { const el=document.createElement(tag); el.className=cls; return el; };
const removeEl = id => { const el=$(id); if(el) el.remove(); };

async function api(url, body) {
  const opts = body !== undefined
    ? { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) }
    : {};
  return (await fetch(url, {
    ...opts,
    credentials: "include"   // 🔥 REQUIRED
  })).json();
}
async function apidel(url) { return (await fetch(url,{method:"DELETE"})).json(); }

function toast(msg,ms=3000){
  const el=$("toast"); el.textContent=msg; el.classList.remove("hidden");
  setTimeout(()=>el.classList.add("hidden"),ms);
}
function esc(s){
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
function relTime(iso){
  const d=Date.now()-new Date(iso).getTime();
  if(d<60000) return "just now";
  if(d<3600000) return Math.floor(d/60000)+"m ago";
  if(d<86400000) return Math.floor(d/3600000)+"h ago";
  return Math.floor(d/86400000)+"d ago";
}
