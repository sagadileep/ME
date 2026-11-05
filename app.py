# ME - web app (Streamlit)
# The onboarding game in the browser. Reuses the game logic from game.py.

import random
import time
from datetime import datetime
import streamlit as st
from game import (load_scenes, for_life_stage, build_profile, average_effects,
                  DEPENDS_ON, MIN_AGE, GAME_RESULTS_FILE)
from sincerity import sincerity_report, twin_check
from storage import save_result
from ai import ask_ai
from ai_explain import build_prompt
from person import Profile
from predict import load_test, question_for_age, predict

TEST_RESULTS_FILE = "test_results.json"

AGE_GROUPS = ["16-24", "25-44", "45-64", "65+"]
LIFE_STAGES = ["school", "studying", "working", "retired", "other"]
REASONS = {reason: (case_a, case_b) for reason, case_a, case_b in DEPENDS_ON.values()}
NO_REASON = "No, I just answered differently"

st.title("ME")

# Session state: ME's memory between reruns
state = st.session_state
if "step" not in state:
    state.step = "start"
    state.scene_index = 0
    state.log = []
    state.depending = False


def next_scene(entry):
    # Save one answer and move on to the next scene (or to the twin questions).
    state.log.append(entry)
    state.depending = False
    state.scene_index += 1
    if state.scene_index == len(state.scenes):
        state.step = "twins"
    st.rerun()


def finish_game(followups):
    # Save the game, then let ME predict the test questions in secret.
    state.followups = followups
    state.profile, state.evidence = build_profile(state.log)
    explained = [f["second"] for f in followups if f["depends_on"]]
    state.warnings = sincerity_report(state.log, state.scenes, explained)
    save_result({
        "person": state.name,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "web",
        "scenes_version": state.version,
        "age_group": state.age_group,
        "life_stage": state.life_stage,
        "profile": state.profile,
        "evidence": state.evidence,
        "log": state.log,
        "twin_followups": followups,
        "warnings": state.warnings,
    }, GAME_RESULTS_FILE)

    person = Profile(state.name)
    person.load()
    state.test = load_test()
    state.questions = []
    for question in state.test["questions"]:
        text, options = question_for_age(question, state.age_group)
        chances = predict(person, options, state.test["strength"])
        by_id = {option["id"]: chance for option, chance in zip(options, chances)}
        random.shuffle(options)   # shown order changes; chances stay linked by option id
        state.questions.append({
            "id": question["id"],
            "touched_by_game": question["touched_by_game"],
            "text": text,
            "options": options,
            "chances": by_id,
        })
    state.q_index = 0
    state.test_rows = []
    state.step = "test"
    st.rerun()


if state.step == "start":
    st.write("A 5-minute game. There are no right answers: pick what you would really do.")
    name = st.text_input("Your first name")
    age_group = st.radio("Your age", ["Under 16"] + AGE_GROUPS, index=None, horizontal=True)
    life_stage = st.radio("What are you mostly doing right now?", LIFE_STAGES, index=None, horizontal=True)
    agree = st.checkbox("I agree that ME saves my answers on this laptop for testing.")
    if st.button("Start"):
        if age_group == "Under 16":
            st.error(f"Sorry, ME is for people aged {MIN_AGE} and over for now.")
        elif not (name and age_group and life_stage and agree):
            st.warning("Please fill in everything and tick the box.")
        else:
            state.name = name.strip().title()
            state.age_group = age_group
            state.life_stage = life_stage
            state.scenes, state.version = load_scenes()
            state.step = "scene"
            st.rerun()

elif state.step == "scene":
    scene = state.scenes[state.scene_index]
    key = f"options_{scene['id']}"
    if key not in state:   # shuffle once per scene, not on every rerun
        text, options = for_life_stage(scene, state.life_stage)
        random.shuffle(options)
        state[key] = (text, options)
        state.shown_at = time.time()
    text, options = state[key]

    st.caption(f"Scene {state.scene_index + 1} of {len(state.scenes)}")
    st.subheader(text)

    if not state.depending:
        for number, option in enumerate(options):
            if st.button(option["text"], key=f"{scene['id']}_{number}", width="stretch"):
                next_scene({
                    "scene": scene["id"],
                    "number": number + 1,
                    "choice": option["text"],
                    "effects": option["effects"],
                    "seconds": round(time.time() - state.shown_at, 1),
                })
        if st.button("It depends...", key=f"{scene['id']}_depends", width="stretch"):
            state.depending = True
            state.depends_seconds = round(time.time() - state.shown_at, 1)
            st.rerun()
    else:
        texts = [option["text"] for option in options]
        reason = st.radio("It depends on what?", list(REASONS), index=None, horizontal=True)
        if reason:
            case_a, case_b = REASONS[reason]
            pick_a = st.radio(f"And {case_a}?", texts, index=None, key=f"{scene['id']}_a")
            pick_b = st.radio(f"And {case_b}?", texts, index=None, key=f"{scene['id']}_b")
            if st.button("Continue"):
                if pick_a and pick_b:
                    option_a = options[texts.index(pick_a)]
                    option_b = options[texts.index(pick_b)]
                    next_scene({
                        "scene": scene["id"],
                        "number": len(options) + 1,
                        "choice": f"It depends on {reason}",
                        "depends_on": reason,
                        "cases": {case_a: pick_a, case_b: pick_b},
                        "effects": average_effects([option_a["effects"], option_b["effects"]]),
                        "seconds": state.depends_seconds,
                    })
                else:
                    st.warning("Please choose for both situations.")

elif state.step == "twins":
    clashes = twin_check(state.log, state.scenes)
    if not clashes:
        finish_game([])
    choices = {entry["scene"]: entry["choice"] for entry in state.log}
    texts = {s["id"]: for_life_stage(s, state.life_stage)[0] for s in state.scenes}

    st.subheader("ME noticed something")
    answers = []
    for clash in clashes:
        st.write(f"**{texts[clash['first']]}** You chose: *{choices[clash['first']]}*")
        st.write(f"**{texts[clash['second']]}** You chose: *{choices[clash['second']]}*")
        answer = st.radio("Does it depend on something?", list(REASONS) + [NO_REASON],
                          index=None, key=f"twin_{clash['second']}")
        answers.append(answer)
    if st.button("Continue"):
        if all(answers):
            followups = []
            for clash, answer in zip(clashes, answers):
                clash["depends_on"] = None if answer == NO_REASON else answer
                followups.append(clash)
            finish_game(followups)
        else:
            st.warning("Please answer each question.")

elif state.step == "test":
    q = state.questions[state.q_index]
    texts = [option["text"] for option in q["options"]]
    st.caption(f"Question {state.q_index + 1} of {len(state.questions)}: no right or wrong answers")
    st.subheader(q["text"])
    pick = st.radio("Your choice", texts, index=None, key=f"pick_{q['id']}")
    never = st.radio("Which would you NEVER pick?", texts, index=None, key=f"never_{q['id']}")
    if st.button("Next"):
        if not (pick and never):
            st.warning("Please answer both.")
        elif pick == never:
            st.warning("Your choice and your never-pick must be different.")
        else:
            ids = [option["id"] for option in q["options"]]
            pick_id = ids[texts.index(pick)]
            never_id = ids[texts.index(never)]
            chances = q["chances"]
            order = sorted(chances, key=chances.get, reverse=True)   # most likely first
            state.test_rows.append({
                "question": q["id"],
                "touched_by_game": q["touched_by_game"],
                "chances": {key: round(value, 3) for key, value in chances.items()},
                "pick": pick_id,
                "never": never_id,
                "top_correct": pick_id == order[0],
                "in_top_two": pick_id in order[:2],
                "never_correct": never_id == order[-1],
                "chance_of_pick": round(chances[pick_id], 3),
            })
            state.q_index += 1
            if state.q_index == len(state.questions):
                save_result({
                    "person": state.name,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "source": "web",
                    "test_version": state.test["version"],
                    "age_group": state.age_group,
                    "rows": state.test_rows,
                }, TEST_RESULTS_FILE)
                state.step = "done"
            st.rerun()

elif state.step == "done":
    rows = state.test_rows
    n = len(rows)
    top = sum(row["top_correct"] for row in rows)
    two = sum(row["in_top_two"] for row in rows)
    never = sum(row["never_correct"] for row in rows)
    average = sum(row["chance_of_pick"] for row in rows) / n

    st.subheader(f"Thanks, {state.name}! How well did ME know you?")
    st.write(f"**Top pick correct:** {top} of {n} (random guessing: 2 of 8)")
    st.write(f"**Your answer in ME's top two:** {two} of {n} (random: 4 of 8)")
    st.write(f"**Never-pick correct:** {never} of {n} (random: 2 of 8)")
    st.write(f"**Average chance ME gave your real answers:** {round(average * 100)}% (random: 25%)")

    st.subheader("What ME learned from the game")
    for dimension, score in state.profile.items():
        st.write(f"**{dimension}:** {score} (from {state.evidence[dimension]} scenes)")
    for entry in state.log:
        if "cases" in entry:
            st.write(f"*It depends on {entry['depends_on']}:* " +
                     "; ".join(f"{case}: {choice}" for case, choice in entry["cases"].items()))
    if state.warnings:
        st.info("ME is not fully confident in these answers yet: " + "; ".join(state.warnings))

    st.divider()
    st.write("Want ME to explain you in plain words? This sends your answers to an AI service (Google Gemini).")
    ai_ok = st.checkbox("Yes, send my answers to the AI")
    if st.button("Explain me", disabled=not ai_ok):
        prompt = build_prompt(state.name, state.name)
        with st.spinner("ME is thinking..."):
            try:
                state.explanation = ask_ai(prompt)
            except Exception:
                st.error("The AI is busy right now. Please try again in a minute.")
    if state.get("explanation"):
        st.markdown(state.explanation)
