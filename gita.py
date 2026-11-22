# ME - the Bhagavad Gita, verse by verse
# Loads all 701 verses (Sanskrit, transliteration, English by Swami Sivananda) from gita_verses.json,
# so ME can quote the real text instead of quoting from the AI's memory.

import json
import re

from memory import database

GITA_FILE = "gita_verses.json"
GITA_BUCKET = "private"        # online: the file lives in this private Supabase storage folder


def load_gita():
    try:
        with open(GITA_FILE, encoding="utf-8") as file:
            verses = json.load(file)["verses"]
    except FileNotFoundError:
        verses = json.loads(database().storage.from_(GITA_BUCKET).download(GITA_FILE))["verses"]
    return {verse["ref"]: verse for verse in verses}   # "2.47" -> the verse


def find_refs(text):
    # All verse references like "2.47" or "18.63" in a text, in order, without repeats.
    refs = []
    for chapter, verse in re.findall(r"\b(1[0-8]|[1-9])\.(\d{1,2})\b", text):
        ref = f"{int(chapter)}.{int(verse)}"
        if ref not in refs:
            refs.append(ref)
    return refs


def quote(verse):
    # One verse as plain text for the AI: reference, transliteration and translation.
    return f"Gita {verse['ref']}: \"{verse['translation']}\" (Sanskrit: {verse['transliteration']})"


if __name__ == "__main__":
    gita = load_gita()
    print(f"{len(gita)} verses loaded")
    for ref in ["2.47", "18.63"]:
        print(quote(gita[ref]))
