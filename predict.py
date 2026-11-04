# ME - prediction
# Gives a chance for every option of a prediction question, from a person's profile.
# Model: multinomial logit (McFadden 1974). Weights start from research,
# later they are learned from players' answers.

import json
import math
from person import Profile, START

TEST_FILE = "prediction_test.json"


def load_test():
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def question_for_age(question, age_group):
    # Same options and weights for every age; only the words change.
    version = question["versions"][age_group]
    options = []
    for option in question["options"]:
        text = version["options"].get(option["id"], option["text"])
        options.append({"id": option["id"], "text": text, "weights": option["weights"]})
    return version["text"], options


def predict(profile, options, strength):
    # 1. A total per option: weight x how far the trait is from the middle.
    totals = []
    for option in options:
        total = 0
        for trait, weight in option["weights"].items():
            centred = (profile.trait(trait) - START) / 3
            total = total + weight * centred
        totals.append(total * strength)
    # 2. Softmax: turn the totals into chances that add up to 1.
    powers = [math.exp(total) for total in totals]
    return [p / sum(powers) for p in powers]


if __name__ == "__main__":
    test = load_test()
    person = Profile("Dileep")
    person.load()
    age_group = "16-24"

    for question in test["questions"]:
        text, options = question_for_age(question, age_group)
        chances = predict(person, options, test["strength"])
        top = chances.index(max(chances))
        never = chances.index(min(chances))
        print(f"\n{question['domain']}: {text}")
        for number, option in enumerate(options):
            mark = "  <- ME's pick" if number == top else ("  <- never pick" if number == never else "")
            print(f"  {round(chances[number] * 100)}%  {option['text']}{mark}")