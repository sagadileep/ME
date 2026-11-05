# ME - web app (Streamlit)
# The onboarding game in the browser. Reuses the game logic from game.py.

import os
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
from style import apply_style, brain_tree

TEST_RESULTS_FILE = "test_results.json"

# Online demo: set ME_DEMO = "1" in the hosting secrets. Then nothing is saved
# and no saved results of other people are ever read.
DEMO = os.environ.get("ME_DEMO") == "1"
ACCESS_CODE = os.environ.get("ME_ACCESS_CODE")   # if set, players need this code

START_STEPS = 3      # name, age and life stage count as real steps of the journey
TEST_QUESTIONS = 8

AGE_GROUPS = ["16-24", "25-44", "45-64", "65+"]
LIFE_STAGES = ["school", "studying", "working", "retired", "other"]
REASONS = {reason: (case_a, case_b) for reason, case_a, case_b in DEPENDS_ON.values()}
NO_REASON = "No, I just answered differently"

st.set_page_config(page_title="ME", layout="centered")
# Session state: ME's memory between reruns
state = st.session_state
if "step" not in state:
    state.step = "start"
    state.scene_index = 0
    state.log = []
    state.depending = False

apply_style(big_logo=(state.step == "start"))


def progress():
    # The real share of the journey that is done: start + scenes + twin check + test.
    total = START_STEPS + len(state.scenes) + 1 + TEST_QUESTIONS
    done = START_STEPS + len(state.log)
    if state.step in ("chapter2", "test", "done"):
        done += 1
    done += state.get("q_index", 0)
    return done / total


def show_progress(chapter):
    # Dileep's decision (5 Nov): the bar moves faster at the start and slower near the end
    # (fast-to-slow, Villar et al. 2013), to keep players comfortable. The tree uses the same value.
    shown = progress() ** 0.6
    st.progress(shown)
    st.caption(chapter)
    brain_tree(shown)


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
    state.game_record = {
        "person": state.name,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "demo" if DEMO else "web",
        "scenes_version": state.version,
        "age_group": state.age_group,
        "life_stage": state.life_stage,
        "profile": state.profile,
        "evidence": state.evidence,
        "log": state.log,
        "twin_followups": followups,
        "warnings": state.warnings,
    }
    person = Profile(state.name)
    if not DEMO:
        save_result(state.game_record, GAME_RESULTS_FILE)
        person.load()   # also brings in a questionnaire, if this person has one
    person.use_game(state.game_record)
    state.test = load_test()
    state.questions = []
    for question in state.test["questions"]:
        text, options = question_for_age(question, state.age_group)
        chances = predict(person, options, state.test["strength"])
        by_id = {option["id"]: chance for option, chance in zip(options, chances)}
        random.shuffle(options)   # shown order changes; chances stay linked by option id
        state.questions.append({
            "id": question["id"],
            "domain": question["domain"],
            "touched_by_game": question["touched_by_game"],
            "text": text,
            "options": options,
            "chances": by_id,
        })
    state.q_index = 0
    state.test_rows = []
    state.step = "chapter2"
    st.rerun()


if state.step == "start":
    st.write("**A 5-minute game in 3 short chapters.** There are no right answers: pick what you would really do.")
    st.write("At the end, see how well ME guessed you.")
    code = st.text_input("Access code", type="password") if ACCESS_CODE else None
    name = st.text_input("Your first name")
    age_group = st.radio("Your age", ["Under 16"] + AGE_GROUPS, index=None, horizontal=True)
    life_stage = st.radio("What are you mostly doing right now?", LIFE_STAGES, index=None, horizontal=True)
    if DEMO:
        agree = st.checkbox("I understand this is a demo: nothing I answer is saved.")
    else:
        agree = st.checkbox("I agree that ME saves my answers on this laptop for testing.")
    if st.button("Start"):
        if ACCESS_CODE and code != ACCESS_CODE:
            st.error("That access code is not right.")
        elif age_group == "Under 16":
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

    if state.scene_index > 0 or state.depending:
        if st.button("← Back"):
            if state.depending:
                state.depending = False       # back from "It depends" to the options
            else:
                state.log.pop()               # forget the last answer
                state.scene_index -= 1
                state.shown_at = time.time()
            st.rerun()

    show_progress("Chapter 1 of 3 · You in everyday life")
    st.subheader(text, anchor=False)

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

    if st.button("← Back"):
        state.log.pop()
        state.scene_index = len(state.scenes) - 1
        state.shown_at = time.time()
        state.step = "scene"
        st.rerun()

    show_progress("Chapter 1 of 3 · You in everyday life")
    st.subheader("ME noticed something", anchor=False)
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

elif state.step == "chapter2":
    show_progress("Chapter 1 done")
    st.subheader("Chapter 2 of 3 · Can ME guess you?", anchor=False)
    st.write("ME has just made a secret guess for each of the next 8 questions, based on how you played. "
             "Answer honestly: you will see how well it guessed at the end.")
    if st.button("Let's see", type="primary"):
        state.step = "test"
        st.rerun()

elif state.step == "test":
    q = state.questions[state.q_index]
    ask_never = state.q_index % 2 == 0   # never-pick on 4 of the 8 questions
    texts = [option["text"] for option in q["options"]]
    if state.q_index > 0 and st.button("← Back"):
        state.test_rows.pop()
        state.q_index -= 1
        st.rerun()

    show_progress("Chapter 2 of 3 · Can ME guess you? No right or wrong answers")
    st.subheader(q["text"], anchor=False)
    pick = st.radio("Your choice", texts, index=None, key=f"pick_{q['id']}")
    never = None
    if ask_never:
        never = st.radio("Which would you NEVER pick?", texts, index=None, key=f"never_{q['id']}")
    if st.button("Next"):
        if not pick or (ask_never and not never):
            st.warning("Please answer before going on.")
        elif ask_never and pick == never:
            st.warning("Your choice and your never-pick must be different.")
        else:
            ids = [option["id"] for option in q["options"]]
            pick_id = ids[texts.index(pick)]
            never_id = ids[texts.index(never)] if never else None
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
                "never_correct": never_id == order[-1] if never_id else None,
                "chance_of_pick": round(chances[pick_id], 3),
            })
            state.q_index += 1
            if state.q_index == len(state.questions) and not DEMO:
                save_result({
                    "person": state.name,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "source": "web",
                    "test_version": state.test["version"],
                    "age_group": state.age_group,
                    "rows": state.test_rows,
                }, TEST_RESULTS_FILE)
            if state.q_index == len(state.questions):
                state.step = "done"
            st.rerun()

elif state.step == "done":
    rows = state.test_rows
    n = len(rows)
    top = sum(row["top_correct"] for row in rows)
    two = sum(row["in_top_two"] for row in rows)
    asked = [row for row in rows if row["never"]]
    never = sum(row["never_correct"] for row in asked)
    average = sum(row["chance_of_pick"] for row in rows) / n

    st.progress(1.0)
    st.caption("Chapter 3 of 3 · Your portrait")
    brain_tree(1.0)
    st.subheader(f"Thanks, {state.name}! How well did ME know you?", anchor=False)
    st.write(f"**Top pick correct:** {top} of {n} (random guessing: 2 of 8)")
    st.write(f"**Your answer in ME's top two:** {two} of {n} (random: 4 of 8)")
    st.write(f"**Never-pick correct:** {never} of {len(asked)} (random: 1 of 4)")
    st.write(f"**Average chance ME gave your real answers:** {round(average * 100)}% (random: 25%)")

    st.subheader("What ME learned from the game", anchor=False)
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
        test_lines = []
        for q, row in zip(state.questions, state.test_rows):
            text_of = {option["id"]: option["text"] for option in q["options"]}
            guess = max(row["chances"], key=row["chances"].get)
            test_lines.append(
                f"{q.get('domain', q['id'])} ({q['text']}): ME's top guess '{text_of[guess]}' "
                f"({round(row['chances'][guess] * 100)}%); person chose '{text_of[row['pick']]}'"
                + (f"; never-pick '{text_of[row['never']]}'" if row["never"] else "")
            )
        prompt = build_prompt(state.name, state.name, game=state.game_record,
                              use_files=not DEMO, test_lines=test_lines)
        with st.status("ME is writing your portrait...") as status:
            st.write(f"Read your {len(state.log)} choices in the game")
            st.write("Compared what you said with what you chose")
            st.write(f"Checked ME's {len(state.test_rows)} guesses against your answers")
            st.write("Writing your portrait...")
            try:
                started = time.time()
                state.explanation = ask_ai(prompt)
                seconds = round(time.time() - started)
                status.update(label=f"Your portrait is ready ({seconds} s)", state="complete")
            except Exception:
                status.update(label="The AI is busy right now. Please try again in a minute.", state="error")
    if state.get("explanation"):
        st.markdown(state.explanation)
