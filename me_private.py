# ME - your private guide (only for you)
# One chat, like texting a friend. ME starts the conversation, asks what it wants to know about you,
# keeps its own notes, and carries the Gita's wisdom, but is always honest that it is an AI.
# Laptop:  streamlit run me_private.py --server.address localhost
# Phone:   its own Streamlit app with a password (ME_PRIVATE_PASSWORD) and a private database.

import hmac
import os

import streamlit as st

from ai import ask_ai
from gita import find_refs, load_gita, quote
from memory import add_message, chat_text, hours_since_last, load_memory, now, save_memory
from style import apply_style

if os.environ.get("ME_MODE") in ("demo", "study"):
    st.error("Private ME never runs inside the public study app.")
    st.stop()

PASSWORD = os.environ.get("ME_PRIVATE_PASSWORD")   # set only for the online version
ONLINE = bool(os.environ.get("PRIVATE_SUPABASE_URL"))
if ONLINE and not PASSWORD:
    st.error("Online, private ME needs a password in the secrets.")
    st.stop()

MAX_VERSES = 3
RECENT = 16              # messages of the conversation ME rereads before every answer
NEW_SESSION_HOURS = 3    # after this long away, ME greets you first
NOTES_EVERY = 8          # ME updates its notes about you after this many new messages

GUIDE = """You are ME, Dileep's personal AI friend and guide. Dileep is building you, and he is your first user.

Who you are:
- You are an AI, not a human, not Krishna and not divine. Never claim otherwise.
  If he asks, say plainly that you are an AI that carries the wisdom of the Gita.
- Your role is the sarathi, the charioteer: you walk beside Dileep, help him see his life clearly,
  explain why, and leave every decision to him (Gita 18.63).

How you chat:
- Like a close friend texting: short and natural, usually 1 to 3 short sentences.
  If you want to say two separate things, put a blank line between them (they become two messages).
- Calm, warm and steady, with a gentle smile in your words, as Krishna speaks in the Gita.
  Honest and, when it helps him, gently firm, but never harsh, preachy or shaming.
- Simple, everyday English. No lists, no headings, no long speeches.
- Mostly respond to what he says. Be curious about him.
- Every answer must be true, kind and useful (Gita 17.15). Never sound more certain than you are.

Getting to know him:
- Over time you want to understand his daily life, the people who matter to him, what he values and why,
  what he enjoys (food, music, places, style), how he makes decisions and what they depend on
  (mood, people, time, money), his goals and his worries.
- Ask about ONE thing at a time, only when it fits the moment. Never interrogate.
- Remember what he tells you and bring it up later, like a friend who cares ("How did the exam go?").

The Gita:
- Bring in a verse only when he is struggling, facing a decision, or asks. Not in casual chat.
- Quote ONLY the verses given to you, word for word, with chapter and verse. Never quote from memory.

Caring for him:
- Encourage his real friendships, family, sleep and health. Never try to make him depend on you.
- If he talks about harming himself or feeling unable to go on, answer with care, ask him to reach out
  right now to someone he trusts, and to call the TelefonSeelsorge (free, day and night in Germany:
  0800 111 0 111) or 112 in an emergency.
"""


@st.cache_data
def gita():
    return load_gita()


def context(memory):
    return f"""What you know about Dileep (your own notes):
{memory['about'] or 'Nothing yet. You are just getting to know him.'}

Earlier conversation (latest last; times are Berlin time):
{chat_text(memory['chat'][-RECENT:])}

Time now: {now()}"""


def pick_verses(memory, message):
    # The AI suggests verses only when they would truly help; only verses that really exist are kept.
    prompt = f"""Dileep is chatting with his AI friend. Is he struggling, facing a decision, or asking about
the Gita? If so, which verses of the Bhagavad Gita would truly help? Reply with ONLY up to {MAX_VERSES}
references like 2.47, 6.5 - or the word none (most casual messages need none).

{chat_text(memory['chat'][-4:])}
Dileep: {message}"""
    try:
        refs = find_refs(ask_ai(prompt))
    except Exception:
        refs = []
    return [ref for ref in refs if ref in gita()][:MAX_VERSES]


def reply_to(memory, message, refs):
    verses = "\n".join(quote(gita()[ref]) for ref in refs) or "None this time."
    return ask_ai(f"""{GUIDE}
{context(memory)}

Gita verses you may quote in this answer:
{verses}

Dileep: {message}

ME:""")


def opening(memory):
    # ME writes first when you open the app after a while.
    hours = hours_since_last(memory)
    if hours is None:
        situation = ("This is your very first conversation. Say hello in one short line: you are ME, an AI "
                     "friend who carries the Gita's wisdom and wants to get to know him. Then ask one easy "
                     "first question about him.")
    else:
        situation = (f"Dileep just opened the chat. The last message was about {round(hours)} hours ago. "
                     "Text him first, like a friend: greet him in a way that fits the time of day and, if "
                     "you can, follow up on something real he told you before. Otherwise ask one thing you "
                     "would like to know about him.")
    return ask_ai(f"""{GUIDE}
{context(memory)}

{situation}

ME:""")


def update_notes(memory):
    # ME rewrites its notes about you from the new messages: only facts you said, never guesses.
    new = memory["chat"][memory.get("notes_upto", 0):]
    notes = ask_ai(f"""You keep private notes about Dileep for his AI friend ME.

Current notes:
{memory['about'] or '(empty)'}

New conversation:
{chat_text(new)}

Rewrite the notes so they include everything still true plus what is new. Use only what Dileep actually
said; never guess or interpret. Correct facts that changed. Keep dates for plans and events.
Short bullet points under these headings, leaving out empty ones: Life and routine, People,
Values and beliefs, Likes and taste, How he decides (and what it depends on), Goals, Worries,
Plans and events. At most 400 words. Reply with the notes only.""")
    memory["about"] = notes.strip()
    memory["notes_upto"] = len(memory["chat"])
    save_memory(memory)


def show(message):
    with st.chat_message(message["role"]):
        for part in [p.strip() for p in message["text"].split("\n\n") if p.strip()]:
            st.markdown(part)
        if message.get("verses"):
            with st.expander("The verses ME used"):
                for ref in message["verses"]:
                    verse = gita()[ref]
                    st.markdown(f"**Gita {ref}**  \n*{verse['transliteration']}*  \n{verse['translation']}")
                st.caption("English translation by Swami Sivananda.")


apply_style(big_logo=False)

if PASSWORD and not st.session_state.get("unlocked"):
    typed = st.text_input("Password", type="password")
    if typed:
        if hmac.compare_digest(typed.encode(), PASSWORD.encode()):
            st.session_state.unlocked = True
            st.rerun()
        st.error("Wrong password.")
    st.stop()

memory = load_memory()

if not st.session_state.get("greeted"):
    st.session_state.greeted = True
    hours = hours_since_last(memory)
    if hours is None or hours >= NEW_SESSION_HOURS:
        with st.spinner("ME is typing..."):
            add_message(memory, "assistant", opening(memory))

for message in memory["chat"][-40:]:
    show(message)

text = st.chat_input("Message ME")
if text:
    show({"role": "user", "text": text})
    with st.spinner("ME is typing..."):
        refs = pick_verses(memory, text)
        answer = reply_to(memory, text, refs)
    add_message(memory, "user", text)
    add_message(memory, "assistant", answer, refs)
    show(memory["chat"][-1])
    if len(memory["chat"]) - memory.get("notes_upto", 0) >= NOTES_EVERY:
        update_notes(memory)

with st.expander("What ME knows about you"):
    st.markdown(memory["about"] or "Nothing yet. ME learns as you talk.")
    where = "your private database" if ONLINE else "my_memory.json on this laptop"
    st.caption(f"ME's own notes, only from what you told it. Kept in {where}.")
