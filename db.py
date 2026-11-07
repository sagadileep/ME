# ME - study database (Supabase, EU region Frankfurt)
# One row per play, found by a random player code, never by name.
# The keys come from the hosting secrets: SUPABASE_URL and SUPABASE_KEY (the secret key).

import os
import secrets
from datetime import datetime, timezone

_client = None
CODE_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # no 0/O or 1/I, so codes are easy to read


def _db():
    global _client
    if _client is None:
        from supabase import create_client
        _client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    return _client


def new_player_code():
    return "P-" + "".join(secrets.choice(CODE_LETTERS) for _ in range(5))


last_error = None   # the most recent saving problem, so the app can show it


def save_play(row):
    # Insert or update this player's row (same code = same row).
    # Saving must never stop the game, so a failure is remembered and logged, not raised.
    global last_error
    row["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        _db().table("plays").upsert(row).execute()
        last_error = None
        return True
    except Exception as error:
        last_error = f"{type(error).__name__}: {error}"
        print(f"ME study database: could not save {row.get('code')}: {last_error}", flush=True)
        return False
