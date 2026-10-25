# ME - onboarding game (terminal version)
# Plays scenes, updates the profile from each choice, and records answer speed.
# Scenes: see "Scene bank v1" in the Domain map (draft).

import time

START = 4.0   # everyone starts in the middle (later: the 1M-dataset average)

SCENES = [
    {
        "id": "restaurant",
        "text": "A new restaurant. The menu has a dish you have never heard of.",
        "options": [
            {"text": "Order the unknown dish", "effects": {"Openness": 1.5}},
            {"text": "Ask the waiter, then decide", "effects": {"Openness": 0.5, "Conscientiousness": 0.5}},
            {"text": "Order a favourite you know", "effects": {"Openness": -1.0}},
            {"text": "Share many dishes to taste", "effects": {"Openness": 1.0, "Extraversion": 0.5}},
        ],
    },
    {
        "id": "party",
        "text": "You're invited to a party where you only know the host.",
        "options": [
            {"text": "Go and meet new people", "effects": {"Extraversion": 1.5}},
            {"text": "Go, stay near the host, leave early", "effects": {"Extraversion": 0.0}},
            {"text": "Suggest a small dinner instead", "effects": {"Extraversion": -0.5}},
            {"text": "Skip it for a quiet night", "effects": {"Extraversion": -1.5}},
        ],
    },
        {
        "id": "weekend",
        "text": "Friday evening. You have a completely free weekend ahead.",
        "options": [
            {"text": "Write a plan for Saturday", "effects": {"Conscientiousness": 1.5}},
            {"text": "Finish pending tasks first, then relax", "effects": {"Conscientiousness": 1.0}},
            {"text": "Decide each morning what to do", "effects": {"Conscientiousness": -1.0}},
            {"text": "Go with whatever friends suggest", "effects": {"Conscientiousness": -0.5, "Extraversion": 0.5}},
        ],
    },
]


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
    profile, log = play(SCENES)
    print("\n--- What ME learned ---")
    for dimension, score in profile.items():
        print(f"{dimension}: {score}")
    for entry in log:
        print(f"{entry['scene']}: '{entry['choice']}' in {entry['seconds']} s")