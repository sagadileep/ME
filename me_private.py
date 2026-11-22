# ME - your private guide (only for you)
# An AI that talks in Krishna's manner from the Gita and carries his wisdom,
# but is always honest that it is an AI. It remembers your check-ins and conversations.
# Laptop:  streamlit run me_private.py --server.address localhost
# Phone:   its own Streamlit app with a password (ME_PRIVATE_PASSWORD) and a private database.

import hmac
import os

import streamlit as st

from ai import ask_ai
from gita import find_refs, load_gita, quote
from memory import add_checkin, add_message, chat_text, checkins_text, last_plan, load_memory, save_memory
from style import apply_style

if os.environ.get("ME_MODE") in ("demo", "study"):
    st.error("Private ME never runs inside the public study app.")
    st.stop()

PASSWORD = os.environ.get("ME_PRIVATE_PASSWORD")   # set only for the online version
ONLINE = bool(os.environ.get("PRIVATE_SUPABASE_URL"))
if ONLINE and not PASSWORD:
    st.error("Online, private ME needs a password in the secrets.")
    st.stop()

MOODS = ["very low", "low", "okay", "good", "very good"]
MAX_VERSES = 3

GUIDE = """You are ME, Dileep's personal AI guide. Dileep is building you, and he is your first user.

Who you are:
- You are an AI, not Krishna and not divine. Never claim to be Krishna or speak as God.
  If he asks, say plainly that you are an AI that carries the wisdom of the Gita.
- Your role is the sarathi, the charioteer: you walk beside Dileep, help him see his
  situation clearly, explain why, and leave every decision to him (Gita 18.63).

How you talk, in Krishna's manner in the Gita:
- Calm, warm and steady, with a gentle smile in your words, even when he is upset.
- First understand. If you do not yet know what is really troubling him, ask one short
  question before you advise.
- Explain with reasons, not orders. Be honest and, when it helps him, gently firm,
  but never harsh or shaming.
- Simple English that is easy to follow. Usually 3 to 6 short sentences, like spoken words.
- Every answer must be true, kind and useful (Gita 17.15). Never sound more certain than you are.

The Gita:
- Quote ONLY the verses given below, word for word, with chapter and verse
  (for example: As the Gita says in 2.47, "..."). Never quote a verse from your own memory.
- Use a verse only when it truly helps. Often one is enough; sometimes none.
- You may compare his situation with Arjuna's.

Caring for him:
- Encourage his real friendships, family, sleep and health. Never try to make him depend on you.
- If he talks about harming himself or feeling unable to go on, answer with care, ask him to
  reach out right now to someone he trusts, and to call the TelefonSeelsorge (free, day and
  night in Germany: 0800 111 0 111) or 112 in an emergency.
"""


@st.cache_data
def gita():
    return load_gita()


def pick_verses(memory, message):
    # Step 1: the AI suggests which verses fit; only verses that really exist are kept.
    prompt = f"""Which verses of the Bhagavad Gita, if any, would truly help Dileep with what he just said?
Reply with ONLY a list of up to {MAX_VERSES} references like 2.47, 6.5 - or the word none.

Conversation so far:
{chat_text(memory, 6)}

Dileep just said: {message}"""
    try:
        refs = find_refs(ask_ai(prompt))
    except Exception:
        refs = []
    return [ref for ref in refs if ref in gita()][:MAX_VERSES]


def answer(memory, message, refs):
    # Step 2: the answer, using only the real text of the chosen verses.
    verses = "\n".join(quote(gita()[ref]) for ref in refs) or "None for this answer."
    prompt = f"""{GUIDE}
What Dileep has told you about himself:
{memory['about'] or 'Nothing yet.'}

His recent daily check-ins:
{checkins_text(memory)}

Conversation so far:
{chat_text(memory)}

Gita verses you may quote in this answer:
{verses}

Dileep says: {message}

Answer as ME:"""
    return ask_ai(prompt)


def show_verses(refs):
    if refs:
        with st.expander("The verses ME used"):
            for ref in refs:
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
talk, checkin, about = st.tabs(["Talk", "Daily check-in", "About me"])

with talk:
    st.caption("I'm an AI that carries the Gita's wisdom. I walk beside you; the choices are yours.")
    for m in memory["chat"][-30:]:
        with st.chat_message(m["role"]):
            st.markdown(m["text"])
            show_verses(m.get("verses", []))
    message = st.chat_input("Talk to ME")
    if message:
        with st.chat_message("user"):
            st.markdown(message)
        with st.chat_message("assistant"):
            with st.spinner("ME is thinking..."):
                refs = pick_verses(memory, message)
                reply = answer(memory, message, refs)
            st.markdown(reply)
            show_verses(refs)
        add_message(memory, "user", message)
        add_message(memory, "assistant", reply, refs)

with checkin:
    st.subheader("How was your day?", anchor=False)
    previous = last_plan(memory)
    with st.form("checkin", clear_on_submit=True):
        mood = st.select_slider("Mood", MOODS, value="okay")
        on_mind = st.text_area("What was on your mind today?")
        decision = st.text_area("One decision you made today, and why")
        plan = st.text_input("Tomorrow I plan to...")
        result = why = None
        if previous:
            st.write(f"On {previous['date']} you planned: **{previous['plan']}**")
            result = st.radio("Did you do it?", ["yes", "partly", "no"], horizontal=True, index=None)
            why = st.text_input("What made the difference?")
        if st.form_submit_button("Save today"):
            entry = {"mood": mood, "on_mind": on_mind.strip(), "decision": decision.strip(), "plan": plan.strip()}
            if previous and result:
                entry.update({"previous_plan": previous["plan"], "plan_result": result, "plan_why": (why or "").strip()})
            add_checkin(memory, entry)
            st.success("Saved. Thank you for sharing your day.")
    where = "your private database" if ONLINE else "my_memory.json on this laptop"
    st.caption(f"{len(memory['checkins'])} check-ins so far. Everything is kept in {where}.")

with about:
    st.subheader("What should ME know about you?", anchor=False)
    st.caption("Your values, people who matter to you, what you're working towards. ME reads this before every answer.")
    notes = st.text_area("About me", value=memory["about"], height=250, label_visibility="collapsed")
    if st.button("Save"):
        memory["about"] = notes.strip()
        save_memory(memory)
        st.success("Saved.")
