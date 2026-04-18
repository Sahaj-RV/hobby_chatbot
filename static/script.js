// static/script.js — Full updated version with OTP flows

// ─────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────
let currentQuestionId = null;
let verifiedEmail     = null;
let resultsShown      = false;

// ─────────────────────────────────────────────
// SCREEN SWITCHER
// ─────────────────────────────────────────────
function showScreen(id) {
  document.querySelectorAll(".screen, .modal-overlay").forEach(el => {
    el.classList.add("hidden");
  });
  document.getElementById(id).classList.remove("hidden");
}

// ─────────────────────────────────────────────
// ── SCREEN 1: EMAIL ENTRY ─────────────────────
// ─────────────────────────────────────────────

async function sendOtp() {
  const emailInput = document.getElementById("email-input");
  const errorEl    = document.getElementById("email-error");
  const btn        = document.getElementById("send-otp-btn");
  const email      = emailInput.value.trim();

  // Clear previous error
  errorEl.textContent = "";
  emailInput.classList.remove("error");

  if (!email) {
    errorEl.textContent = "Please enter your email address.";
    emailInput.classList.add("error");
    return;
  }

  // Disable button while sending
  btn.disabled    = true;
  btn.textContent = "Sending…";

  const res  = await fetch("/api/send-otp", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ email, purpose: "verify" })
  });
  const data = await res.json();

  btn.disabled    = false;
  btn.textContent = "Send verification code";

  if (data.success) {
    // Show OTP screen
    document.getElementById("otp-email-display").textContent = email;
    document.getElementById("save-email-display").textContent = email;
    verifiedEmail = email;
    showScreen("screen-otp");
    setupOtpInputs("otp-inputs");
    document.querySelector("#otp-inputs .otp-digit").focus();
  } else {
    errorEl.textContent = data.error || "Something went wrong. Please try again.";
    emailInput.classList.add("error");
  }
}

// ─────────────────────────────────────────────
// ── SCREEN 2: OTP VERIFICATION ────────────────
// ─────────────────────────────────────────────

function setupOtpInputs(containerId) {
  // Wire up the 6 individual OTP digit boxes:
  // auto-advance on input, backspace goes back, paste fills all
  const container = document.getElementById(containerId);
  const inputs    = container.querySelectorAll(".otp-digit");

  inputs.forEach((input, i) => {
    // Reset state
    input.value = "";
    input.classList.remove("filled", "error");

    input.addEventListener("input", e => {
      const val = e.target.value.replace(/\D/g, "");  // digits only
      input.value = val ? val[val.length - 1] : "";    // keep one digit

      if (input.value) {
        input.classList.add("filled");
        if (i < inputs.length - 1) inputs[i + 1].focus(); // advance
      } else {
        input.classList.remove("filled");
      }
    });

    input.addEventListener("keydown", e => {
      if (e.key === "Backspace" && !input.value && i > 0) {
        inputs[i - 1].focus();   // go back on delete
      }
      if (e.key === "Enter") {
        // Trigger verify when Enter pressed on last digit
        if (containerId === "otp-inputs")      verifyOtp();
        if (containerId === "save-otp-inputs") confirmSave();
      }
    });

    // Handle paste — fill all digits at once
    input.addEventListener("paste", e => {
      e.preventDefault();
      const pasted = e.clipboardData.getData("text").replace(/\D/g, "");
      inputs.forEach((inp, j) => {
        inp.value = pasted[j] || "";
        inp.classList.toggle("filled", !!inp.value);
      });
      // Focus the last filled or next empty
      const lastFilled = Math.min(pasted.length, inputs.length) - 1;
      inputs[Math.min(lastFilled + 1, inputs.length - 1)].focus();
    });
  });
}

function getOtpValue(containerId) {
  const inputs = document.querySelectorAll(`#${containerId} .otp-digit`);
  return Array.from(inputs).map(i => i.value).join("");
}

function markOtpError(containerId) {
  document.querySelectorAll(`#${containerId} .otp-digit`).forEach(i => {
    i.classList.add("error");
  });
}

function clearOtpError(containerId) {
  document.querySelectorAll(`#${containerId} .otp-digit`).forEach(i => {
    i.classList.remove("error");
    i.value = "";
    i.classList.remove("filled");
  });
}

async function verifyOtp() {
  const otp     = getOtpValue("otp-inputs");
  const errorEl = document.getElementById("otp-error");
  const btn     = document.getElementById("verify-otp-btn");

  errorEl.textContent = "";

  if (otp.length < 6) {
    markOtpError("otp-inputs");
    errorEl.textContent = "Please enter all 6 digits.";
    return;
  }

  btn.disabled    = true;
  btn.textContent = "Verifying…";

  const res  = await fetch("/api/verify-otp", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ otp })
  });
  const data = await res.json();

  btn.disabled    = false;
  btn.textContent = "Verify & continue";

  if (data.valid) {
    // Verified! Switch to chat screen
    showScreen("screen-chat");
    document.getElementById("verified-badge").innerHTML =
      `✓ Verified as ${data.email}`;

    // Kick off the first question
    showQuestion(data.first_question);

  } else {
    markOtpError("otp-inputs");
    errorEl.textContent = data.reason || "Invalid OTP. Please try again.";
  }
}

async function resendOtp() {
  const email = document.getElementById("email-input").value.trim();
  clearOtpError("otp-inputs");
  document.getElementById("otp-error").textContent = "";

  const res  = await fetch("/api/send-otp", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ email, purpose: "verify" })
  });
  const data = await res.json();

  if (data.success) {
    showToast("New code sent! Check your inbox.");
    document.querySelector("#otp-inputs .otp-digit").focus();
  } else {
    document.getElementById("otp-error").textContent = data.error;
  }
}

function goBack() {
  showScreen("screen-email");
}

// ─────────────────────────────────────────────
// ── SCREEN 3: CHAT ────────────────────────────
// ─────────────────────────────────────────────

const messagesEl    = () => document.getElementById("messages");
const optionsEl     = () => document.getElementById("options-area");
const progressWrap  = () => document.getElementById("progress-wrap");
const progressFill  = () => document.getElementById("progress-fill");
const progressLabel = () => document.getElementById("progress-label");

function showQuestion(msg) {
  currentQuestionId = msg.question_id;

  const pct = ((msg.step - 1) / msg.total) * 100;
  progressWrap().style.display   = "flex";
  progressFill().style.width     = pct + "%";
  progressLabel().textContent    = `Question ${msg.step} of ${msg.total}`;

  addBotMessage(msg.content);
  renderOptions(msg.options);
}

function renderOptions(options) {
  optionsEl().innerHTML = "";
  options.forEach(opt => {
    const btn = document.createElement("button");
    btn.className   = "option-btn";
    btn.textContent = opt;
    btn.onclick     = () => selectOption(opt);
    optionsEl().appendChild(btn);
  });
}

async function selectOption(answer) {
  addUserMessage(answer);
  optionsEl().innerHTML = "";

  const typingId = showTyping();

  const res  = await fetch("/api/answer", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ question_id: currentQuestionId, answer })
  });
  const data = await res.json();

  removeTyping(typingId);

  if (data.type === "question") {
    setTimeout(() => showQuestion(data), 300);
  } else if (data.type === "results") {
    progressFill().style.width     = "100%";
    progressLabel().textContent    = "Complete!";
    setTimeout(() => showResults(data), 300);
  }
}

function showResults(data) {
  resultsShown = true;
  addBotMessage("Here are your top hobby matches, ranked just for you!");

  const header = document.createElement("div");
  header.className   = "results-header";
  header.textContent = `Top ${data.recommendations.length} picks for you`;
  messagesEl().appendChild(header);

  data.recommendations.forEach((rec, i) => {
    setTimeout(() => renderHobbyCard(rec, i === 0), i * 150);
  });

  // Show "Save results" button after cards appear
  setTimeout(() => {
    const saveBtn = document.createElement("button");
    saveBtn.className   = "save-btn";
    saveBtn.textContent = "💾 Save my results";
    saveBtn.onclick     = initiateSave;
    messagesEl().appendChild(saveBtn);
    scrollToBottom();
  }, data.recommendations.length * 150 + 400);
}

function renderHobbyCard(rec, isTop) {
  const card = document.createElement("div");
  card.className = isTop ? "hobby-card top-match" : "hobby-card";
  card.innerHTML = `
    <div class="hobby-card-header">
      <div>
        ${isTop ? '<div style="font-size:11px;color:#0F6E56;font-weight:500;margin-bottom:4px;">Best match</div>' : ""}
        <div class="hobby-name">${rec.name}</div>
      </div>
      <div class="hobby-pct">${rec.score}%<br><span>match</span></div>
    </div>
    <div class="match-bar-bg">
      <div class="match-bar-fill" style="width:${rec.score}%"></div>
    </div>
    <div class="hobby-why">${rec.data.why_it_fits}</div>
    <div class="hobby-meta">
      <span class="meta-pill">${rec.data.difficulty}</span>
      <span class="meta-pill">${rec.data.time_needed}</span>
      <span class="meta-pill">${rec.data.cost}</span>
    </div>
    <button class="explore-btn" onclick="openHobbyDetail('${rec.key}')">
      View 7-day plan & full guide →
    </button>
  `;
  messagesEl().appendChild(card);
  scrollToBottom();
}

// ─────────────────────────────────────────────
// ── SCREEN 4: SAVE WITH OTP ───────────────────
// ─────────────────────────────────────────────

async function initiateSave() {
  const res  = await fetch("/api/save-results", { method: "POST" });
  const data = await res.json();

  if (data.success) {
    // Show save OTP overlay
    document.getElementById("screen-save-otp").classList.remove("hidden");
    setupOtpInputs("save-otp-inputs");
    document.querySelector("#save-otp-inputs .otp-digit").focus();
  } else {
    showToast("Could not send code: " + (data.error || "Unknown error"));
  }
}

async function confirmSave() {
  const otp     = getOtpValue("save-otp-inputs");
  const errorEl = document.getElementById("save-otp-error");

  errorEl.textContent = "";

  if (otp.length < 6) {
    markOtpError("save-otp-inputs");
    errorEl.textContent = "Please enter all 6 digits.";
    return;
  }

  const res  = await fetch("/api/confirm-save", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ otp })
  });
  const data = await res.json();

  if (data.valid) {
    closeSaveOtp();
    showToast("✓ Results saved successfully!");
  } else {
    markOtpError("save-otp-inputs");
    errorEl.textContent = data.reason || "Invalid OTP. Try again.";
  }
}

function closeSaveOtp() {
  document.getElementById("screen-save-otp").classList.add("hidden");
  clearOtpError("save-otp-inputs");
}

// ─────────────────────────────────────────────
// ── HOBBY DETAIL MODAL ────────────────────────
// ─────────────────────────────────────────────

async function openHobbyDetail(hobbyKey) {
  const res  = await fetch(`/api/hobby/${hobbyKey}`);
  const data = await res.json();

  document.getElementById("modal-content").innerHTML = `
    <h2>${data.name}</h2>
    <p class="modal-sub">${data.description}</p>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:1rem">
      <span class="tool-pill">${data.difficulty}</span>
      <span class="tool-pill">${data.time_needed}</span>
      <span class="tool-pill">${data.cost}</span>
    </div>
    <div class="modal-section">
      <h3>Why this fits you</h3>
      <p style="font-size:14px;line-height:1.6;color:#3d3d3a">${data.why_it_fits}</p>
    </div>
    <div class="modal-section">
      <h3>7-day starter plan</h3>
      ${data.seven_day_plan.map(s => `<div class="plan-step">${s}</div>`).join("")}
    </div>
    <div class="modal-section">
      <h3>Tools to get started</h3>
      <div class="tool-list">
        ${data.tools.map(t => `<span class="tool-pill">${t}</span>`).join("")}
      </div>
    </div>
    <div class="modal-section">
      <h3>Common beginner mistakes</h3>
      ${data.mistakes_to_avoid.map(m => `
        <div class="mistake-item">
          <span class="mistake-icon">✕</span><span>${m}</span>
        </div>`).join("")}
    </div>
    <div class="modal-section">
      <h3>Career & income path</h3>
      <p style="font-size:14px;line-height:1.6;color:#3d3d3a">${data.career_path}</p>
    </div>
  `;
  document.getElementById("modal-overlay").classList.remove("hidden");
}

function closeModal(e) {
  if (!e || e.target === document.getElementById("modal-overlay")) {
    document.getElementById("modal-overlay").classList.add("hidden");
  }
}

// ─────────────────────────────────────────────
// ── RESTART ───────────────────────────────────
// ─────────────────────────────────────────────

async function restartChat() {
  await fetch("/api/restart", { method: "POST" });
  verifiedEmail = null;
  resultsShown  = false;
  document.getElementById("email-input").value = "";
  document.getElementById("email-error").textContent  = "";
  messagesEl().innerHTML  = "";
  optionsEl().innerHTML   = "";
  progressWrap().style.display = "none";
  progressFill().style.width   = "0%";
  showScreen("screen-email");
}

// ─────────────────────────────────────────────
// ── HELPERS ───────────────────────────────────
// ─────────────────────────────────────────────

function addBotMessage(text) {
  const div = document.createElement("div");
  div.className = "msg-bot";
  div.innerHTML = `<div class="avatar">✦</div><div class="bubble">${text}</div>`;
  messagesEl().appendChild(div);
  scrollToBottom();
}

function addUserMessage(text) {
  const div = document.createElement("div");
  div.className = "msg-user";
  div.innerHTML = `<div class="bubble">${text}</div>`;
  messagesEl().appendChild(div);
  scrollToBottom();
}

function showTyping() {
  const id  = "typing-" + Date.now();
  const div = document.createElement("div");
  div.className = "msg-bot typing";
  div.id        = id;
  div.innerHTML = `
    <div class="avatar">✦</div>
    <div class="bubble">
      <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    </div>`;
  messagesEl().appendChild(div);
  scrollToBottom();
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function scrollToBottom() {
  window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
}

function showToast(msg) {
  const t = document.createElement("div");
  t.className   = "toast";
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

// ─────────────────────────────────────────────
// INIT — show email screen on load
// ─────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  showScreen("screen-email");
});
