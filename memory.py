# ME - private memory
# Everything ME remembers about you: your notes, daily check-ins and conversations.
# On the laptop: one file, my_memory.json (kept out of GitHub by .gitignore).
# Online (phone): one row in your own private Supabase project, set by PRIVATE_SUPABASE_URL and _KEY.

import json
import os
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
        _client = create_client(url, key)
    return _client


def load_memory():
    empty = {"about": "", "checkins": [], "chat": []}
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


def add_checkin(memory, checkin):
    checkin["date"] = today()
    memory["checkins"] = [c for c in memory["checkins"] if c["date"] != checkin["date"]]   # one per day
    memory["checkins"].append(checkin)
    save_memory(memory)


def last_plan(memory):
    # The most recent check-in before today that had a plan, so ME can ask how it went.
    for checkin in reversed(memory["checkins"]):
        if checkin["date"] < today() and checkin.get("plan"):
            return checkin
    return None


def checkins_text(memory, days=7):
    lines = []
    for c in memory["checkins"][-days:]:
        line = f"{c['date']}: mood {c.get('mood', '?')}."
        if c.get("on_mind"):
            line += f" On his mind: {c['on_mind']}."
        if c.get("decision"):
            line += f" Decision and why: {c['decision']}."
        if c.get("plan"):
            line += f" Plan for the next day: {c['plan']}."
        if c.get("plan_result"):
            line += f" Previous plan ({c.get('previous_plan', '')}): {c['plan_result']}. {c.get('plan_why', '')}"
        lines.append(line)
    return "\n".join(lines) if lines else "No check-ins yet."


def chat_text(memory, messages=12):
    names = {"user": "Dileep", "assistant": "ME"}
    return "\n".join(f"{names[m['role']]}: {m['text']}" for m in memory["chat"][-messages:]) or "This is the first conversation."
