# ME - onboarding game (terminal version)
# Plays scenes, updates the profile from each choice, and records answer speed.
# Scenes: see "Scene bank v1" in the Domain map (draft).

import json
import time
import random
from sincerity import sincerity_report
from storage import save_result
from datetime import datetime

SCENES_FILE = "scenes.json"
GAME_RESULTS_FILE = "game_results.json"
START = 4.0   # everyone starts in the middle (later: the 1M-dataset average)
# "It depends" follow-up: reason -> the two situations to compare
DEPENDS_ON = {
    "1": ("Mood", "when you're in a good mood", "when you're tired or irritated"),
    "2": ("Who I'm with", "with close friends", "with strangers"),
    "3": ("Money", "when money is no problem", "when money is tight"),
    "4": ("Time", "when you have plenty of time", "when you're in a hurry"),
}
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


def ask_depends(options):
    print("  It depends on what?")
    for key, (reason, case_a, case_b) in DEPENDS_ON.items():
        print(f"  {key}. {reason}")
    key = ask_number("Your answer (1-4): ", ["1", "2", "3", "4"])
    reason, case_a, case_b = DEPENDS_ON[key]

    cases = {}
    for case in [case_a, case_b]:
        n = ask_number(f"  And {case}? (1-4): ", ["1", "2", "3", "4"])
        cases[case] = options[int(n) - 1]
    return reason, cases

def play(scenes):
    profile = {}
    log = []
    for scene in scenes:
        print()
        print(scene["text"])
        options = scene["options"][:]   # [:] makes a copy, so scenes.json stays untouched
        random.shuffle(options)
        for number, option in enumerate(options, start=1):
            print(f"  {number}. {option['text']}")
        print("  5. It depends")

        start_time = time.time()
        choice = ask_number("Your choice (1-5): ", ["1", "2", "3", "4", "5"])
        seconds = round(time.time() - start_time, 1)

        entry = {"scene": scene["id"], "number": int(choice), "seconds": seconds}
        if choice == "5":
            reason, cases = ask_depends(options)
            entry["choice"] = f"It depends on {reason}"
            entry["depends_on"] = reason
            entry["cases"] = {case: option["text"] for case, option in cases.items()}
            entry["effects"] = average_effects([option["effects"] for option in cases.values()])
        else:
            option = options[int(choice) - 1]
            entry["choice"] = option["text"]
            entry["effects"] = option["effects"]

        for dimension, change in entry["effects"].items():
            profile[dimension] = clamp(profile.get(dimension, START) + change)
        log.append(entry)
    return profile, log


if __name__ == "__main__":
    person = input("Who is playing? ").strip().title()
    scenes, version = load_scenes()
    profile, log = play(scenes)
    print("\n--- What ME learned ---")
    for dimension, score in profile.items():
        print(f"{dimension}: {score}")
    for entry in log:
        print(f"{entry['scene']}: '{entry['choice']}' in {entry['seconds']} s")
        if "cases" in entry:
            for case, choice_text in entry["cases"].items():
                print(f"    {case}: {choice_text}")
    warnings = sincerity_report(log, scenes)
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
        "profile": profile,
        "log": log,
        "warnings": warnings,
    }
    save_result(record, GAME_RESULTS_FILE)
    print(f"\nSaved to {GAME_RESULTS_FILE} ({person}).")