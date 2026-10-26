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
\
START = 4.0   # everyone starts in the middle (later: the 1M-dataset average)

def load_scenes():
    with open(SCENES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["scenes"],data["version"]

def clamp(score):
    return min(7.0, max(1.0, score))


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

        start_time = time.time()
        choice = input("Your choice (1-4): ").strip()
        while choice not in ["1", "2", "3", "4"]:
            choice = input("Please type 1, 2, 3 or 4: ").strip()
        seconds = round(time.time() - start_time, 1)

        option = options[int(choice) - 1]
        for dimension, change in option["effects"].items():
            profile[dimension] = clamp(profile.get(dimension, START) + change)

        log.append({"scene": scene["id"], "number": int(choice), "choice": option["text"],
                    "effects": option["effects"], "seconds": seconds})
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