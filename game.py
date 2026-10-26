# ME - onboarding game (terminal version)
# Plays scenes, updates the profile from each choice, and records answer speed.
# Scenes: see "Scene bank v1" in the Domain map (draft).

import json
import time

SCENES_FILE = "scenes.json"

START = 4.0   # everyone starts in the middle (later: the 1M-dataset average)

def load_scenes():
    with open(SCENES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["scenes"]

def clamp(score):
    return min(7.0, max(1.0, score))


def play(scenes):
    profile = {}
    log = []
    for scene in scenes:
        print()
        print(scene["text"])
        for number, option in enumerate(scene["options"], start=1):
            print(f"  {number}. {option['text']}")

        start_time = time.time()
        choice = input("Your choice (1-4): ").strip()
        while choice not in ["1", "2", "3", "4"]:
            choice = input("Please type 1, 2, 3 or 4: ").strip()
        seconds = round(time.time() - start_time, 1)

        option = scene["options"][int(choice) - 1]
        for dimension, change in option["effects"].items():
            profile[dimension] = clamp(profile.get(dimension, START) + change)

        log.append({"scene": scene["id"], "choice": option["text"], "seconds": seconds})
    return profile, log


if __name__ == "__main__":
    scenes = load_scenes()
    profile, log = play(scenes)
    print("\n--- What ME learned ---")
    for dimension, score in profile.items():
        print(f"{dimension}: {score}")
    for entry in log:
        print(f"{entry['scene']}: '{entry['choice']}' in {entry['seconds']} s")