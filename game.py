# ME - onboarding game (terminal version)
# Plays scenes, updates the profile from each choice, and records answer speed.
# Scenes: loaded from scenes.json (see "Scene bank" in the Domain map).

import json
import time
import random
from sincerity import sincerity_report, twin_check
from storage import save_result
from datetime import datetime

SCENES_FILE = "scenes.json"
GAME_RESULTS_FILE = "game_results.json"
START = 4.0   # everyone starts in the middle (later: the 1M-dataset average)
STRETCH = 2.0  # turns an average change (-1.5 to +1.5) into the 1-7 scale (1 to 7)
# "It depends" follow-up: reason -> the two situations to compare
DEPENDS_ON = {
    "1": ("Mood", "when you're in a good mood", "when you're tired or irritated"),
    "2": ("Who I'm with", "with close friends", "with strangers"),
    "3": ("Money", "when money is no problem", "when money is tight"),
    "4": ("Time", "when you have plenty of time", "when you're in a hurry"),
}

# Life stage: used ONLY to choose a scene's wording, never to predict personality.
LIFE_STAGES = {"1": "school", "2": "studying", "3": "working", "4": "retired",
               "5": "home and family", "6": "other"}
MIN_AGE = 16   # under 16 needs a parent's consent (GDPR Art. 8); teen version later
def load_scenes():
    with open(SCENES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["scenes"],data["version"]

def clamp(score):
    return min(7.0, max(1.0, score))

def ask_number(prompt, allowed):
    choice = input(prompt).strip()
    while choice not in allowed:
        choice = input(f"Please type one of {allowed}: ").strip()
    return choice


def average_effects(effect_list):
    result = {}
    for effects in effect_list:
        for dimension, change in effects.items():
            result[dimension] = result.get(dimension, 0) + change / len(effect_list)
    return result


def ask_life_stage():
    print("What are you mostly doing right now?")
    print("  1. School   2. Studying   3. Working   4. Retired   5. Home and family   6. Other")
    key = ask_number("Your answer (1-6): ", list(LIFE_STAGES))
    return LIFE_STAGES[key]


def for_life_stage(scene, stage):
    # Same scene, same options and effects; only the words change for this life stage.
    options = [dict(option) for option in scene["options"]]   # copies, scenes.json stays untouched
    variant = scene.get("variants", {}).get(stage)
    if variant is None:
        return scene["text"], options
    for option, new_text in zip(options, variant.get("options", [])):
        option["text"] = new_text
    return variant["text"], options


def ask_depends(options):
    print("  It depends on what?")
    for key, (reason, case_a, case_b) in DEPENDS_ON.items():
        print(f"  {key}. {reason}")
    key = ask_number("Your answer (1-4): ", ["1", "2", "3", "4"])
    reason, case_a, case_b = DEPENDS_ON[key]

    cases = {}
    for case in [case_a, case_b]:
        allowed = [str(n) for n in range(1, len(options) + 1)]
        n = ask_number(f"  And {case}? (1-{len(options)}): ", allowed)
        cases[case] = options[int(n) - 1]
    return reason, cases

def ask_twin_followups(log, scenes, stage):
    # When twin scenes disagree, ask why instead of assuming the player lied.
    choices = {entry["scene"]: entry["choice"] for entry in log}
    texts = {scene["id"]: for_life_stage(scene, stage)[0] for scene in scenes}
    no_key = str(len(DEPENDS_ON) + 1)
    allowed = [str(n) for n in range(1, len(DEPENDS_ON) + 2)]

    followups = []
    for clash in twin_check(log, scenes):
        print()
        print("ME noticed something:")
        print(f"  {texts[clash['first']]}")
        print(f"    -> you chose: {choices[clash['first']]}")
        print(f"  {texts[clash['second']]}")
        print(f"    -> you chose: {choices[clash['second']]}")
        print("Does it depend on something?")
        for key, (reason, case_a, case_b) in DEPENDS_ON.items():
            print(f"  {key}. Yes: {reason}")
        print(f"  {no_key}. No, I just answered differently")
        answer = ask_number(f"Your answer (1-{no_key}): ", allowed)

        followup = {"first": clash["first"], "second": clash["second"], "target": clash["target"]}
        if answer == no_key:
            followup["depends_on"] = None
        else:
            followup["depends_on"] = DEPENDS_ON[answer][0]
        followups.append(followup)
    return followups

def build_profile(log):
    # Collect every change per dimension, then average them.
    changes = {}
    for entry in log:
        for dimension, change in entry["effects"].items():
            if dimension not in changes:
                changes[dimension] = []
            changes[dimension].append(change)

    profile = {}
    evidence = {}
    for dimension, values in changes.items():
        average = sum(values) / len(values)
        profile[dimension] = round(clamp(START + average * STRETCH), 2)
        evidence[dimension] = len(values)
    return profile, evidence

def play(scenes, stage):
    log = []
    for scene in scenes:
        print()
        text, options = for_life_stage(scene, stage)
        print(text)
        random.shuffle(options)
        for number, option in enumerate(options, start=1):
            print(f"  {number}. {option['text']}")
        depends_number = len(options) + 1
        print(f"  {depends_number}. It depends")

        start_time = time.time()
        allowed = [str(n) for n in range(1, depends_number + 1)]
        choice = ask_number(f"Your choice (1-{depends_number}): ", allowed)
        seconds = round(time.time() - start_time, 1)

        entry = {"scene": scene["id"], "number": int(choice), "seconds": seconds}
        if choice == str(depends_number):
            reason, cases = ask_depends(options)
            entry["choice"] = f"It depends on {reason}"
            entry["depends_on"] = reason
            entry["cases"] = {case: option["text"] for case, option in cases.items()}
            entry["effects"] = average_effects([option["effects"] for option in cases.values()])
        else:
            option = options[int(choice) - 1]
            entry["choice"] = option["text"]
            entry["effects"] = option["effects"]
        log.append(entry)
    return log


if __name__ == "__main__":
    old_enough = ask_number(f"Are you {MIN_AGE} or older? (y/n): ", ["y", "n"])
    if old_enough == "n":
        print(f"Sorry, ME is for people aged {MIN_AGE} and over for now.")
        raise SystemExit
    person = input("Who is playing? ").strip().title()
    stage = ask_life_stage()
    scenes, version = load_scenes()
    log = play(scenes, stage)
    profile, evidence = build_profile(log)
    followups = ask_twin_followups(log, scenes, stage)
    explained = [f["second"] for f in followups if f["depends_on"]]
    print("\n--- What ME learned ---")
    for entry in log:
        print(f"{entry['scene']}: '{entry['choice']}' in {entry['seconds']} s")
        if "cases" in entry:
            for case, choice_text in entry["cases"].items():
                print(f"    {case}: {choice_text}")
    for dimension, score in profile.items():
        print(f"{dimension}: {score} (from {evidence[dimension]} scenes)")
    warnings = sincerity_report(log, scenes, explained)
    if warnings:
        print("\nME is not confident in these answers yet:")
        for w in warnings:
            print(" -", w)
    else:
        print("\nAnswers look careful and consistent.")
    record = {
        "person": person,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "scenes_version": version,
        "life_stage": stage,
        "profile": profile,
        "evidence": evidence,
        "log": log,
        "twin_followups": followups,
        "warnings": warnings,
    }
    save_result(record, GAME_RESULTS_FILE)
    print(f"\nSaved to {GAME_RESULTS_FILE} ({person}).")