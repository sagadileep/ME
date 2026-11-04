# ME - prediction test
# The person answers the 8 questions. ME's predictions are made first and stay hidden,
# then ME is scored against random guessing.

import random
from datetime import datetime
from person import Profile
from predict import load_test, question_for_age, predict
from storage import save_result
from game import ask_number

TEST_RESULTS_FILE = "test_results.json"
AGE_GROUPS = {"1": "16-24", "2": "25-44", "3": "45-64", "4": "65+"}


def ask_age_group():
    print("How old are you?")
    print("  1. 16-24   2. 25-44   3. 45-64   4. 65+")
    key = ask_number("Your answer (1-4): ", list(AGE_GROUPS))
    return AGE_GROUPS[key]


def ask_question(text, options):
    shown = options[:]
    random.shuffle(shown)
    print(f"\n{text}")
    for number, option in enumerate(shown, start=1):
        print(f"  {number}. {option['text']}")
    allowed = [str(n) for n in range(1, len(shown) + 1)]
    pick = ask_number("Your choice: ", allowed)
    others = [a for a in allowed if a != pick]
    never = ask_number("And which would you NEVER pick? ", others)
    return shown[int(pick) - 1]["id"], shown[int(never) - 1]["id"]


if __name__ == "__main__":
    name = input("Who is taking the test? ").strip().title()
    person = Profile(name)
    person.load()
    if not person.says and not person.does:
        print(f"ME knows nothing about {name} yet. Play game.py first.")
        raise SystemExit
    age_group = ask_age_group()
    test = load_test()

    rows = []
    for question in test["questions"]:
        text, options = question_for_age(question, age_group)
        chances = predict(person, options, test["strength"])   # made BEFORE the person answers
        by_chance = {option["id"]: chance for option, chance in zip(options, chances)}
        order = sorted(by_chance, key=by_chance.get, reverse=True)   # ids, most likely first

        pick, never = ask_question(text, options)
        rows.append({
            "question": question["id"],
            "touched_by_game": question["touched_by_game"],
            "chances": {key: round(value, 3) for key, value in by_chance.items()},
            "pick": pick,
            "never": never,
            "top_correct": pick == order[0],
            "in_top_two": pick in order[:2],
            "never_correct": never == order[-1],
            "chance_of_pick": round(by_chance[pick], 3),
        })

    n = len(rows)
    top = sum(row["top_correct"] for row in rows)
    two = sum(row["in_top_two"] for row in rows)
    never = sum(row["never_correct"] for row in rows)
    average = sum(row["chance_of_pick"] for row in rows) / n

    print("\n--- How well did ME know you? ---")
    print(f"Top pick correct:        {top} of {n} ({round(top / n * 100)}%)  random: 25%")
    print(f"Answer in ME's top two:  {two} of {n} ({round(two / n * 100)}%)  random: 50%")
    print(f"'Never pick' correct:    {never} of {n} ({round(never / n * 100)}%)  random: 25%")
    print(f"Chance ME gave your real answers: {round(average * 100)}% on average  random: 25%")

    record = {
        "person": name,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "test_version": test["version"],
        "age_group": age_group,
        "rows": rows,
    }
    save_result(record, TEST_RESULTS_FILE)
    print(f"\nSaved to {TEST_RESULTS_FILE}.")