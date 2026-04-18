# app.py — HobbyBot v4
# Key changes:
#   - /api/chats/<id>/stream  → SSE streaming endpoint (Claude > Grok > Gemini fallback)
#   - /api/chats/<id>/answer  → quiz answers still work, but input is never locked
#   - /api/chats/<id>/chat    → free-form message at ANY point (even during quiz)
#   - Persistent 30-day session (Fix 1 from v3, unchanged)

import json, os, re, sys
from datetime import timedelta
from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
from dotenv import load_dotenv
import google.generativeai as genai

from chatbot import ConversationManager, QUESTIONS
from email_otp import send_otp_email, verify_otp
from database import (
    init_db, get_or_create_user, create_chat, get_chats,
    get_chat, get_messages, add_message, update_chat_title,
    update_chat_profile, update_chat_status, delete_chat
)
from hobbies import HOBBIES

base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, ".env"))

try:
    import anthropic
    claude_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    use_claude = bool(os.environ.get("ANTHROPIC_API_KEY"))
except ImportError:
    claude_client = None
    use_claude = False

try:
    from groq import Groq
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
    use_groq = bool(os.environ.get("GROQ_API_KEY"))
except ImportError:
    groq_client = None
    use_groq = False

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "hobbybot-secret-change-me")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.config["SESSION_COOKIE_SAMESITE"]    = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"]    = True

# Configure AI models (Claude > Grok > Gemini fallback)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
gemini_model = genai.GenerativeModel(
    model_name   = "gemini-2.0-flash",
    generation_config = genai.GenerationConfig(
        max_output_tokens = 1024,
        temperature       = 0.7,
    )
)

quiz_sessions: dict[str, ConversationManager] = {}


# ── HELPERS ───────────────────────────────────

def valid_email(e: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", e))

def require_auth():
    uid   = session.get("user_id")
    email = session.get("email")
    return {"id": uid, "email": email} if uid and email else None

def auto_title(answers: dict) -> str:
    c = answers.get("creative_type", "").lower()
    g = answers.get("goal", "").lower()
    if   "visual"  in c: base = "Visual arts discovery"
    elif "word"    in c or "writing" in c: base = "Writing & blogging path"
    elif "sound"   in c or "music"   in c: base = "Music production path"
    elif "hands"   in c: base = "DIY crafts discovery"
    else: base = "Hobby discovery"
    if "career" in g or "hustle" in g: base += " — career track"
    return base

def build_system_prompt(chat: dict) -> str:
    """
    System prompt prepended to the conversation for Gemini.
    Gemini doesn't have a dedicated system role — we inject this
    as context at the start of the first message.
    """
    profile_ctx = ""
    if chat.get("profile"):
        try:
            p = json.loads(chat["profile"])
            profile_ctx = f"""
The user's hobby profile (from their quiz):
- Personality: {p.get('personality', 'ambivert')}
- Interests: {', '.join(p.get('interests', []))}
- Time available: {p.get('time', 'flexible')}
- Goal: {p.get('goal', 'express')}
- Energy level: {p.get('energy', 'moderate')}
Always tailor responses to this profile.
"""
        except Exception:
            pass

    return f"""You are HobbyBot — a friendly AI that helps people discover and grow through hobbies.
You are warm, direct, practical, and encouraging.
{profile_ctx}
RULES:
- Use markdown: **bold**, bullet points, `code` for tool names.
- Keep replies under 250 words unless a detailed plan is requested.
- Always give concrete next steps, never vague advice.
- Suggest free tools first before paid ones.
- Never say you are Gemini or made by Google. You are HobbyBot.
- If asked about a hobby, give specific actionable guidance.
"""


# ── PAGE ──────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── AUTH ──────────────────────────────────────

@app.route("/api/auth/check")
def auth_check():
    user = require_auth()
    if user:
        return jsonify({"logged_in": True, "email": user["email"],
                        "user_id": user["id"], "chats": get_chats(user["id"])})
    return jsonify({"logged_in": False})

@app.route("/api/send-otp", methods=["POST"])
def send_otp():
    data  = request.get_json()
    email = data.get("email", "").strip().lower()
    purpose = data.get("purpose", "verify")
    if not email:
        return jsonify({"success": False, "error": "Please enter your email."})
    if not valid_email(email):
        return jsonify({"success": False, "error": "Invalid email address."})
    session["pending_email"] = email
    session["otp_purpose"]   = purpose
    return jsonify(send_otp_email(email, purpose))

@app.route("/api/verify-otp", methods=["POST"])
def verify_otp_route():
    data    = request.get_json()
    otp     = data.get("otp", "").strip()
    email   = session.get("pending_email")
    purpose = session.get("otp_purpose", "verify")

    if not otp:   return jsonify({"valid": False, "reason": "Please enter the OTP."})
    if not email: return jsonify({"valid": False, "reason": "Session expired."})

    result = verify_otp(email, otp)
    if not result["valid"]: return jsonify(result)

    if purpose == "verify":
        user = get_or_create_user(email)
        session.permanent  = True
        session["user_id"] = user["id"]
        session["email"]   = email
        return jsonify({"valid": True, "email": email,
                        "user_id": user["id"], "chats": get_chats(user["id"])})
    elif purpose == "save":
        return jsonify({"valid": True, "purpose": "save"})
    return jsonify(result)

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


# ── CHATS ─────────────────────────────────────

@app.route("/api/chats")
def list_chats():
    user = require_auth()
    if not user: return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_chats(user["id"]))

@app.route("/api/chats", methods=["POST"])
def new_chat():
    user = require_auth()
    if not user: return jsonify({"error": "Unauthorized"}), 401

    chat    = create_chat(user["id"])
    mgr     = ConversationManager()
    mgr.step = 1
    quiz_sessions[chat["id"]] = mgr
    first_q = mgr.get_next_message()

    greeting = (
        "Hey! I'm **HobbyBot** 👋\n\n"
        "I'll match you with hobbies that actually fit your personality and lifestyle. "
        "I have **5 quick questions** — click an option or just type your answer freely. "
        "You can also skip ahead and ask me anything directly!"
    )
    add_message(chat["id"], "bot", greeting, "text")
    add_message(chat["id"], "bot", first_q["content"], "question")

    return jsonify({"chat": chat, "greeting": greeting, "first_question": first_q})

@app.route("/api/chats/<chat_id>", methods=["DELETE"])
def remove_chat(chat_id):
    user = require_auth()
    if not user: return jsonify({"error": "Unauthorized"}), 401
    chat = get_chat(chat_id)
    if not chat or chat["user_id"] != user["id"]:
        return jsonify({"error": "Not found"}), 404
    delete_chat(chat_id)
    quiz_sessions.pop(chat_id, None)
    return jsonify({"ok": True})

@app.route("/api/chats/<chat_id>/messages")
def load_messages(chat_id):
    user = require_auth()
    if not user: return jsonify({"error": "Unauthorized"}), 401
    chat = get_chat(chat_id)
    if not chat or chat["user_id"] != user["id"]:
        return jsonify({"error": "Not found"}), 404

    messages   = get_messages(chat_id)
    mgr        = quiz_sessions.get(chat_id)
    quiz_state = None

    if not chat.get("profile"):
        if mgr:
            nxt = mgr.get_next_message()
            if nxt["type"] == "question":
                quiz_state = nxt
        else:
            new_mgr  = ConversationManager()
            answered = sum(1 for m in messages if m["role"] == "user")
            new_mgr.step = answered + 1
            quiz_sessions[chat_id] = new_mgr
            if new_mgr.step <= len(QUESTIONS):
                quiz_state = new_mgr.get_next_message()

    return jsonify({"chat": chat, "messages": messages, "quiz_state": quiz_state})


# ── QUIZ ANSWER (button click) ────────────────

@app.route("/api/chats/<chat_id>/answer", methods=["POST"])
def answer_question(chat_id):
    """Handles a button-click quiz answer. Still works alongside free chat."""
    user = require_auth()
    if not user: return jsonify({"error": "Unauthorized"}), 401

    data        = request.get_json()
    question_id = data.get("question_id")
    answer      = data.get("answer")
    if not question_id or not answer:
        return jsonify({"error": "Missing fields"}), 400

    chat = get_chat(chat_id)
    if not chat or chat["user_id"] != user["id"]:
        return jsonify({"error": "Not found"}), 404

    add_message(chat_id, "user", answer, "text")

    mgr = quiz_sessions.get(chat_id)
    if not mgr:
        mgr = ConversationManager()
        msgs = get_messages(chat_id)
        mgr.step = sum(1 for m in msgs if m["role"] == "user")
        quiz_sessions[chat_id] = mgr

    mgr.submit_answer(question_id, answer)
    nxt = mgr.get_next_message()

    if nxt["type"] == "question":
        add_message(chat_id, "bot", nxt["content"], "question")
        return jsonify(nxt)

    elif nxt["type"] == "results":
        update_chat_profile(chat_id, json.dumps(mgr.profile))
        title = auto_title(mgr.answers)
        update_chat_title(chat_id, title)
        summary = f"Here are your top {len(nxt['recommendations'])} hobby matches!"
        add_message(chat_id, "bot", summary, "results")
        return jsonify({"type": "results",
                        "recommendations": nxt["recommendations"],
                        "title": title})
    return jsonify(nxt)


# ── STREAMING CHAT ────────────────────────────

@app.route("/api/chats/<chat_id>/stream", methods=["POST"])
def stream_chat(chat_id):
    """
    FIX: All data (auth, chat, history, system prompt) is extracted
    BEFORE the generator starts. Flask sessions are not accessible
    inside a generator after the request context is torn down.
    """
    # ── 1. Auth check (must happen in request context) ──
    user = require_auth()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # ── 2. Parse body (must happen in request context) ──
    body     = request.get_json(silent=True) or {}
    user_msg = body.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    # ── 3. Validate chat ownership ──
    chat = get_chat(chat_id)
    if not chat or chat["user_id"] != user["id"]:
        return jsonify({"error": "Not found"}), 404

    # ── 4. Save user message to DB now ──
    add_message(chat_id, "user", user_msg, "chat")

    # ── 5. Build Claude message list (before generator) ──
    history = get_messages(chat_id)[-30:]
    raw = []
    for m in history:
        # Skip quiz option prompts — they confuse Claude
        if m["msg_type"] in ("question",):
            continue
        if not m["content"].strip():
            continue
        role = "user" if m["role"] == "user" else "assistant"
        raw.append({"role": role, "content": m["content"]})

    # Merge consecutive same-role messages (Claude API requirement)
    merged = []
    for msg in raw:
        if merged and merged[-1]["role"] == msg["role"]:
            merged[-1]["content"] += "\n" + msg["content"]
        else:
            merged.append({"role": msg["role"], "content": msg["content"]})

    # Guarantee last message is user
    if not merged:
        merged = [{"role": "user", "content": user_msg}]
    elif merged[-1]["role"] != "user":
        merged.append({"role": "user", "content": user_msg})

    # ── 6. Freeze all values generator needs ──
    system_prompt = build_system_prompt(chat)
    frozen_chat_id = chat_id   # string — safe to close over

    # ── 7. Generator — Claude > Grok > Gemini fallback ──
    def generate():
        full_text = ""
        try:
            if use_claude:
                # Try Claude first
                try:
                    messages = [{"role": "system", "content": system_prompt}] + merged
                    with claude_client.messages.stream(
                        model="claude-3-haiku-20240307",
                        max_tokens=1024,
                        temperature=0.7,
                        messages=messages
                    ) as stream:
                        for chunk in stream:
                            if chunk.type == "content_block_delta" and hasattr(chunk.delta, 'text'):
                                text = chunk.delta.text
                                if text:
                                    full_text += text
                                    payload = json.dumps({"type": "token", "text": text}, ensure_ascii=False)
                                    yield f"data: {payload}\n\n"
                except Exception as claude_error:
                    if "rate limit" in str(claude_error).lower() or "429" in str(claude_error):
                        # Claude rate limited, try Grok
                        if use_groq:
                            try:
                                messages = [{"role": "system", "content": system_prompt}] + merged
                                stream = groq_client.chat.completions.create(
                                    model="llama-3.1-8b-instant",
                                    messages=messages,
                                    max_tokens=1024,
                                    temperature=0.7,
                                    stream=True
                                )
                                for chunk in stream:
                                    text = chunk.choices[0].delta.content or ""
                                    if text:
                                        full_text += text
                                        payload = json.dumps({"type": "token", "text": text}, ensure_ascii=False)
                                        yield f"data: {payload}\n\n"
                            except Exception:
                                # Grok failed, fall back to Gemini
                                pass  # Will fall through to else
                        # Fall back to Gemini
                        gemini_history = []
                        for msg in merged[:-1]:
                            gemini_history.append({
                                "role":  "user" if msg["role"] == "user" else "model",
                                "parts": [msg["content"]]
                            })
                        chat_session = gemini_model.start_chat(history=gemini_history)
                        current_msg = merged[-1]["content"]
                        if not gemini_history:
                            current_msg = system_prompt + "\n\n---\n\n" + current_msg
                        response = chat_session.send_message(current_msg, stream=True)
                        for chunk in response:
                            text = chunk.text if hasattr(chunk, "text") else ""
                            if not text:
                                continue
                            full_text += text
                            payload = json.dumps({"type": "token", "text": text}, ensure_ascii=False)
                            yield f"data: {payload}\n\n"
                    else:
                        raise claude_error
            elif use_groq:
                # Try Grok
                try:
                    messages = [{"role": "system", "content": system_prompt}] + merged
                    stream = groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=messages,
                        max_tokens=1024,
                        temperature=0.7,
                        stream=True
                    )
                    for chunk in stream:
                        text = chunk.choices[0].delta.content or ""
                        if text:
                            full_text += text
                            payload = json.dumps({"type": "token", "text": text}, ensure_ascii=False)
                            yield f"data: {payload}\n\n"
                except Exception as groq_error:
                    if "rate limit" in str(groq_error).lower() or "429" in str(groq_error):
                        # Grok rate limited, fall back to Gemini
                        gemini_history = []
                        for msg in merged[:-1]:
                            gemini_history.append({
                                "role":  "user" if msg["role"] == "user" else "model",
                                "parts": [msg["content"]]
                            })
                        chat_session = gemini_model.start_chat(history=gemini_history)
                        current_msg = merged[-1]["content"]
                        if not gemini_history:
                            current_msg = system_prompt + "\n\n---\n\n" + current_msg
                        response = chat_session.send_message(current_msg, stream=True)
                        for chunk in response:
                            text = chunk.text if hasattr(chunk, "text") else ""
                            if not text:
                                continue
                            full_text += text
                            payload = json.dumps({"type": "token", "text": text}, ensure_ascii=False)
                            yield f"data: {payload}\n\n"
                    else:
                        raise groq_error
            else:
                # Use Gemini
                gemini_history = []
                for msg in merged[:-1]:
                    gemini_history.append({
                        "role":  "user" if msg["role"] == "user" else "model",
                        "parts": [msg["content"]]
                    })

                chat_session = gemini_model.start_chat(history=gemini_history)

                current_msg = merged[-1]["content"]

                if not gemini_history:
                    current_msg = system_prompt + "\n\n---\n\n" + current_msg

                response = chat_session.send_message(current_msg, stream=True)

                for chunk in response:
                    text = chunk.text if hasattr(chunk, "text") else ""
                    if not text:
                        continue
                    full_text += text
                    payload = json.dumps({"type": "token", "text": text}, ensure_ascii=False)
                    yield f"data: {payload}\n\n"

            # Done event
            yield f"data: {json.dumps({'type': 'done', 'full': full_text})}\n\n"

            # Persist full reply to DB
            add_message(frozen_chat_id, "bot", full_text, "chat")

        except Exception as exc:
            err_msg = str(exc)
            print(f"[AI ERROR] {err_msg}", file=sys.stderr)

            # Give a user-friendly message for common errors
            if "API_KEY" in err_msg or "api key" in err_msg.lower():
                friendly = "API key missing or invalid. Check your API keys in .env"
            elif "quota" in err_msg.lower() or "429" in err_msg or "rate limit" in err_msg.lower():
                friendly = "Rate limit hit. Wait 1 minute and try again."
            elif "SAFETY" in err_msg:
                friendly = "Message blocked by safety filter. Please rephrase."
            else:
                friendly = f"Error: {err_msg[:120]}"

            yield f"data: {json.dumps({'type': 'error', 'message': friendly})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        }
    )


# ── SAVE WITH OTP ─────────────────────────────

@app.route("/api/chats/<chat_id>/save", methods=["POST"])
def save_request(chat_id):
    user = require_auth()
    if not user: return jsonify({"error": "Unauthorized"}), 401
    session["pending_email"] = user["email"]
    session["otp_purpose"]   = "save"
    return jsonify(send_otp_email(user["email"], "save"))

@app.route("/api/chats/<chat_id>/confirm-save", methods=["POST"])
def confirm_save(chat_id):
    user = require_auth()
    if not user: return jsonify({"error": "Unauthorized"}), 401
    data  = request.get_json()
    otp   = data.get("otp", "").strip()
    email = session.get("pending_email")
    result = verify_otp(email, otp)
    if not result["valid"]: return jsonify(result)
    update_chat_status(chat_id, "saved")
    return jsonify({"valid": True})

@app.route("/api/hobby/<hobby_key>")
def hobby_detail(hobby_key):
    hobby = HOBBIES.get(hobby_key)
    if not hobby: return jsonify({"error": "Not found"}), 404
    return jsonify(hobby)



# ── PUBLIC PROFILE — SHARE ────────────────────

import hashlib

def get_share_token(chat_id: str) -> str:
    """Generate a short deterministic token from chat_id."""
    return hashlib.sha256(chat_id.encode()).hexdigest()[:12]


@app.route('/api/chats/<chat_id>/share', methods=['POST'])
def create_share(chat_id):
    user = require_auth()
    if not user: return jsonify({'error': 'Unauthorized'}), 401

    chat = get_chat(chat_id)
    if not chat or chat['user_id'] != user['id']:
        return jsonify({'error': 'Not found'}), 404
    if not chat.get('profile'):
        return jsonify({'token': None})

    token = get_share_token(chat_id)
    return jsonify({'token': token})


@app.route('/p/<token>')
def public_profile(token):
    """
    Public profile page — no login needed.
    Finds the chat matching this token and renders a beautiful
    standalone page with the user's hobby results.
    """
    # Find matching chat by checking all chats
    # (in production you'd store tokens in DB — fine for prototype)
    from database import get_conn
    with get_conn() as conn:
        rows = conn.execute(
            'SELECT * FROM chats WHERE profile IS NOT NULL'
        ).fetchall()

    matched = None
    for row in rows:
        chat = dict(row)
        if get_share_token(chat['id']) == token:
            matched = chat
            break

    if not matched:
        return '<h2 style="font-family:sans-serif;padding:2rem">Profile not found or not yet shared.</h2>', 404

    # Get the quiz recommendations by rebuilding from profile
    profile = json.loads(matched['profile'])
    from chatbot import get_recommendations
    recs = get_recommendations(profile, top_n=5)

    # Get the user email (first 2 chars only for privacy)
    from database import get_conn
    with get_conn() as conn:
        user_row = conn.execute('SELECT email FROM users WHERE id=?', (matched['user_id'],)).fetchone()
    email_hint = ''
    if user_row:
        parts = user_row['email'].split('@')
        email_hint = parts[0][:2] + '***@' + parts[1] if len(parts) == 2 else ''

    return render_template('profile.html',
        title=matched['title'],
        email_hint=email_hint,
        recs=recs,
        profile=profile,
        token=token
    )


# ── RUN ───────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("=" * 52)
    print("  HobbyBot v4 → http://localhost:5000")
    print("=" * 52)
    # threaded=True is important for SSE streaming
    app.run(debug=True, port=5000, threaded=True)
