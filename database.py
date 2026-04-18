# database.py
# Handles all SQLite operations.
# Three tables:
#   users    — verified email accounts
#   chats    — each conversation session per user
#   messages — individual messages inside a chat

import sqlite3
import uuid
from datetime import datetime

DB_PATH = "hobby_bot.db"


def get_conn():
    """Open a connection with row_factory so rows behave like dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # better concurrent reads
    return conn


def init_db():
    """Create all tables if they don't exist. Call once on startup."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         TEXT PRIMARY KEY,
                email      TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chats (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                title       TEXT NOT NULL DEFAULT 'New chat',
                status      TEXT NOT NULL DEFAULT 'active',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                profile     TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id         TEXT PRIMARY KEY,
                chat_id    TEXT NOT NULL,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                msg_type   TEXT DEFAULT 'text',
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats(id)
            );
        """)


# ── USERS ─────────────────────────────────────

def get_or_create_user(email: str) -> dict:
    """Return existing user or create a new one."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        if row:
            return dict(row)
        uid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO users (id, email, created_at) VALUES (?, ?, ?)",
            (uid, email, now)
        )
        return {"id": uid, "email": email, "created_at": now}


# ── CHATS ─────────────────────────────────────

def create_chat(user_id: str, title: str = "New chat") -> dict:
    """Create a new chat session for a user."""
    cid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO chats (id, user_id, title, status, created_at, updated_at)
               VALUES (?, ?, ?, 'active', ?, ?)""",
            (cid, user_id, title, now, now)
        )
    return {"id": cid, "user_id": user_id, "title": title,
            "status": "active", "created_at": now, "updated_at": now}


def get_chats(user_id: str) -> list:
    """Return all chats for a user, newest first."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT c.*,
               (SELECT content FROM messages
                WHERE chat_id = c.id ORDER BY created_at DESC LIMIT 1) as last_message
               FROM chats c
               WHERE c.user_id = ?
               ORDER BY c.updated_at DESC""",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_chat(chat_id: str) -> dict | None:
    """Return a single chat by ID."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM chats WHERE id = ?", (chat_id,)
        ).fetchone()
        return dict(row) if row else None


def update_chat_title(chat_id: str, title: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE chats SET title = ?, updated_at = ? WHERE id = ?",
            (title, datetime.utcnow().isoformat(), chat_id)
        )


def update_chat_profile(chat_id: str, profile_json: str):
    """Store the user's personality profile JSON on the chat."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE chats SET profile = ?, updated_at = ? WHERE id = ?",
            (profile_json, datetime.utcnow().isoformat(), chat_id)
        )


def update_chat_status(chat_id: str, status: str):
    """Status: active | saved | archived"""
    with get_conn() as conn:
        conn.execute(
            "UPDATE chats SET status = ?, updated_at = ? WHERE id = ?",
            (status, datetime.utcnow().isoformat(), chat_id)
        )


def delete_chat(chat_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))


# ── MESSAGES ──────────────────────────────────

def add_message(chat_id: str, role: str, content: str, msg_type: str = "text") -> dict:
    """
    Append a message to a chat.
    role:     'bot' | 'user'
    msg_type: 'text' | 'question' | 'results' | 'followup'
    """
    mid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO messages (id, chat_id, role, content, msg_type, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (mid, chat_id, role, content, msg_type, now)
        )
        # bump chat's updated_at
        conn.execute(
            "UPDATE chats SET updated_at = ? WHERE id = ?",
            (now, chat_id)
        )
    return {"id": mid, "chat_id": chat_id, "role": role,
            "content": content, "msg_type": msg_type, "created_at": now}


def get_messages(chat_id: str) -> list:
    """Return all messages in a chat, oldest first."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC",
            (chat_id,)
        ).fetchall()
        return [dict(r) for r in rows]
