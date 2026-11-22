# Siya - the Valmiki Ramayana
# Loads all translated passages (from ramayana_verses.json) so Siya quotes the real text.
# Two ways to find passages: a few key stories chosen by hand, and a simple word search over all of it.

import json
import math
import re
from collections import Counter

from memory import database

RAMAYANA_FILE = "ramayana_verses.json"
BUCKET = "private"

# Key stories, read in full on 22 Nov 2026 (see "The guide" tab in the Master Plan).
KEY_STORIES = {
    "hanuman_speaks": ("Hanuman finds the right moment and words to comfort frightened Sita",
                       ["Sundara 30.16", "Sundara 30.19", "Sundara 30.38", "Sundara 30.42"]),
    "honest_counsel": ("Vibhishana gives Ravana unwelcome but honest advice; flatterers are enemies",
                       ["Yuddha 14.17", "Yuddha 14.22"]),
    "truth": ("Rama refuses a clever argument and keeps his word: truth is the root of everything",
              ["Ayodhya 109.2", "Ayodhya 109.4", "Ayodhya 109.13"]),
    "caring_questions": ("Rama checks on Bharata with caring questions: decide with a few wise people, share",
                         ["Ayodhya 100.19", "Ayodhya 100.23", "Ayodhya 100.53", "Ayodhya 100.76"]),
    "calm_in_loss": ("Rama hears of his exile, stays cheerful, yet names what hurts him",
                     ["Ayodhya 19.6", "Ayodhya 19.37", "Ayodhya 19.40"]),
    "anger": ("Rama calms Lakshmana's anger and refuses to blame Kaikeyi",
              ["Ayodhya 22.3", "Ayodhya 22.25", "Ayodhya 22.30"]),
    "grief": ("Rama consoles grieving Bharata: every union ends in separation; do what is right",
              ["Ayodhya 105.16", "Ayodhya 105.26", "Ayodhya 105.31", "Ayodhya 105.39"]),
    "friendship": ("Rama and Sugriva take each other's hands and make a promise of friendship",
                   ["Kishkindha 5.11", "Kishkindha 5.12"]),
    "good_character": ("Valmiki asks who is truly good: truthful, grateful, free of anger and envy",
                       ["Bala 1.2", "Bala 1.3", "Bala 1.4"]),
}

STOPWORDS = set("""a an the and or but if of to in on at by for with from as is are was were be been being
this that these those it its he she they them his her their you your i me my we our not no so than then
there here what which who whom when where why how all any each also very can will shall would should may
might must do does did have has had o said thus""".split())


def words(text):
    return [w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS and len(w) > 2]


def load_ramayana():
    try:
        with open(RAMAYANA_FILE, encoding="utf-8") as file:
            passages = json.load(file)["verses"]
    except FileNotFoundError:
        passages = json.loads(database().storage.from_(BUCKET).download(RAMAYANA_FILE))["verses"]
    by_ref = {}
    for passage in passages:
        passage["words"] = Counter(words(passage["translation"]))
        for ref in passage["refs"]:
            by_ref[ref] = passage
    counts = Counter(w for passage in passages for w in passage["words"])
    rarity = {w: math.log(len(passages) / n) for w, n in counts.items()}   # rare words matter more
    return {"passages": passages, "by_ref": by_ref, "rarity": rarity}


def search(ramayana, query, top=3):
    # Passages that share the most (and rarest) words with the query.
    terms = set(words(query))
    scored = []
    for passage in ramayana["passages"]:
        score = sum(ramayana["rarity"].get(t, 0) for t in terms if t in passage["words"])
        if score:
            scored.append((score, passage["ref"]))
    return [ref for score, ref in sorted(scored, reverse=True)[:top]]


def key_story_refs(ramayana, story):
    refs = KEY_STORIES.get(story, ("", []))[1]
    return [ref for ref in refs if ref in ramayana["by_ref"]]


def quote(passage):
    return f"Ramayana, {passage['kanda']} Kanda {passage['ref'].split(' ')[1]}: \"{passage['translation']}\""
