# ME - private memory
# Everything ME remembers about you: its notes about you and your conversations.
# On the laptop: one file, my_memory.json (kept out of GitHub by .gitignore).
# Online (phone): one row in your own private Supabase project, set by PRIVATE_SUPABASE_URL and _KEY.

import json
import os
from urllib.parse import urlparse
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

MEMORY_FILE = "my_memory.json"
MEMORY_ROW = "dileep"                     # the one row in the private_memory table
try:
    TIMEZONE = ZoneInfo("Europe/Berlin")  # online servers run on UTC; dates follow your clock
except Exception:
    TIMEZONE = None                       # e.g. Windows without time-zone data: use the laptop's clock
_client = None


def database():
    # The private Supabase project, or None on the laptop.
    global _client
    url, key = os.environ.get("PRIVATE_SUPABASE_URL"), os.environ.get("PRIVATE_SUPABASE_KEY")
    if not (url and key):
        return None
    if _client is None:
        from supabase import create_client
        address = urlparse(url.strip())
        # Keep only "https://<project>.supabase.co": the library adds paths like /rest/v1 itself.
        _client = create_client(f"{address.scheme}://{address.netloc}", key.strip())
    return _client


def load_memory():
    empty = {"about": "", "notes_upto": 0, "chat": []}   # notes_upto: messages already in the notes
    db = database()
    if db:
        rows = db.table("private_memory").select("data").eq("id", MEMORY_ROW).execute().data
        return rows[0]["data"] if rows else empty
    try:
        with open(MEMORY_FILE, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return empty


def save_memory(memory):
    db = database()
    if db:
        db.table("private_memory").upsert({"id": MEMORY_ROW, "data": memory,
                                             "updated_at": datetime.now(timezone.utc).isoformat()}).execute()
        return
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory, file, ensure_ascii=False, indent=2)


def now():
    return datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M")


def today():
    return datetime.now(TIMEZONE).date().isoformat()


def add_message(memory, role, text, verses=None):
    memory["chat"].append({"time": now(), "role": role, "text": text, "verses": verses or []})
    save_memory(memory)


def hours_since_last(memory):
    # Hours since the last message in the chat, or None if there is none yet.
    if not memory["chat"]:
        return None
    last = datetime.strptime(memory["chat"][-1]["time"], "%Y-%m-%d %H:%M")
    current = datetime.strptime(now(), "%Y-%m-%d %H:%M")
    return (current - last).total_seconds() / 3600


def chat_text(messages):
    names = {"user": "Dileep", "assistant": "Siya"}
    return "\n".join(f"[{m['time']}] {names[m['role']]}: {m['text']}" for m in messages) or "(no messages yet)"
