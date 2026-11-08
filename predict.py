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
        options.append({"id": option["id"], "text": text, "weights": option["weights"],
                        "ladder": option.get("ladder")})
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


# The Why Chain (Reynolds & Gutman 1988): feature -> consequence -> value -> trait -> evidence.
VALUE_WORDS = {
    "security": "feeling safe, steady and in control",
    "stimulation": "excitement and new experiences",
    "self-direction": "freedom to follow your own ideas",
    "universalism": "beauty, nature and fairness",
    "benevolence": "caring for the people close to you",
    "hedonism": "enjoying life's pleasures",
    "achievement": "getting things done and doing well",
    "conformity": "fitting in with the people around you",
    "tradition": "keeping what has always worked",
}
STRONG_REASON = 0.15   # a trait must push an option at least this much to count as a reason


def why_chain(profile, option, strength):
    # Why ME expects this option: built only from the option's ladder, the person's
    # trait estimates and their own game choices. Nothing is invented.
    ladder = option.get("ladder") or {}
    pushes = {}
    for trait, weight in option["weights"].items():
        pushes[trait] = weight * (profile.trait(trait) - START) / 3 * strength
    trait = max(pushes, key=pushes.get) if pushes else None
    if trait is None or pushes[trait] < STRONG_REASON:
        return {"strong": False, "consequence": ladder.get("consequence"), "value": ladder.get("value")}

    direction = 1 if profile.trait(trait) > START else -1
    evidence = []
    for entry in profile.log:
        change = entry.get("effects", {}).get(trait, 0)
        if change * direction > 0:
            evidence.append((abs(change), entry["choice"]))
    evidence.sort(reverse=True)
    return {
        "strong": True,
        "consequence": ladder.get("consequence"),
        "value": ladder.get("value"),
        "value_words": VALUE_WORDS.get(ladder.get("value"), ladder.get("value")),
        "trait": trait,
        "trait_level": "high" if direction > 0 else "low",
        "evidence": [choice for _, choice in evidence[:2]],
    }


def why_text(option, why):
    # One plain sentence for the AI, so it can explain the guess without inventing reasons.
    if not why["strong"]:
        return (f"no strong reason yet, mostly a guess (the option {why['consequence']}, "
                f"value: {why['value']})")
    evidence = "; ".join(f"'{choice}'" for choice in why["evidence"]) or "no single scene yet"
    return (f"the option {why['consequence']} -> value: {why['value_words']} -> fits "
            f"{why['trait_level']} {why['trait']} -> evidence from the game: {evidence}")


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