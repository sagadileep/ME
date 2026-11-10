# ME - study analysis
# Reads a CSV export of the Supabase "plays" table and prints how well ME is doing.
# Usage:  python analyze.py plays_rows.csv
# The export holds study data: it must stay on this laptop (*.csv is in .gitignore).

import csv
import json
import math
import sys
from collections import Counter

RUSH_LIMIT = 2   # players with this many speed-click reminders (or more) are left out


def load_rows(path):
    with open(path, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def is_careless(row):
    # Sincerity warnings from the game, or several speed-click reminders.
    game = json.loads(row["game"]) if row["game"] else {}
    return bool(game.get("warnings")) or game.get("rush_nudges", 0) >= RUSH_LIMIT


def show_funnel(rows):
    print(f"\nPLAYERS: {len(rows)} started")
    stopped = Counter(row["last_step"] for row in rows if row["status"] in ("started", "playing", "game_done"))
    finished = [row for row in rows if row["test"]]
    print(f"  finished the 8 questions: {len(finished)}")
    print(f"  gave feedback:            {sum(1 for row in rows if row['feedback'])}")
    if stopped:
        print("  stopped early at:", ", ".join(f"{step} ({n})" for step, n in stopped.most_common()))
    print("  age groups:", dict(Counter(row["age_group"] for row in rows)))
    print("  life stages:", dict(Counter(row["life_stage"] for row in rows)))
    models = Counter(json.loads(row["game"]).get("model", "start-4") for row in rows if row["game"])
    print("  ME version used:", dict(models))


def show_feedback(rows):
    print("\nFEEDBACK")
    print("  how long it felt:", dict(Counter(row["feedback"] for row in rows if row["feedback"])))
    for row in rows:
        comment = row["comment"].strip()
        if comment and comment.lower() not in ("nil", "no", "none", "-"):
            print(f"  {row['code']}: \"{comment}\"")


def softmax(scores):
    top = max(scores.values())
    powers = {key: math.exp(value - top) for key, value in scores.items()}
    total = sum(powers.values())
    return {key: value / total for key, value in powers.items()}


def evaluate(tests, person_weight, crowd_weight):
    # Leave-one-out: each player's crowd is learned from the OTHER players only.
    top = two = 0
    chance = 0.0
    n = 0
    for i, test in enumerate(tests):
        others = [row for j, other in enumerate(tests) if j != i for row in other]
        for row in test:
            options = list(row["chances"])
            picks = Counter(o["pick"] for o in others if o["question"] == row["question"])
            total = sum(picks.values())
            scores = {}
            for option in options:
                crowd = (picks[option] + 1) / (total + len(options))   # +1 so no option gets zero
                scores[option] = (person_weight * math.log(row["chances"][option])
                                  + crowd_weight * math.log(crowd))
            chances = softmax(scores)
            order = sorted(options, key=lambda option: (-chances[option], option))
            top += order[0] == row["pick"]
            two += row["pick"] in order[:2]
            chance += chances[row["pick"]]
            n += 1
    return top / n, two / n, chance / n


def show_predictions(rows):
    honest = [row for row in rows if row["test"] and not is_careless(row)]
    left_out = [row["code"] for row in rows if row["test"] and is_careless(row)]
    tests = [json.loads(row["test"]) for row in honest]
    n = sum(len(test) for test in tests)
    print(f"\nPREDICTIONS: {len(honest)} honest players, {n} predictions")
    if left_out:
        print(f"  left out as careless: {', '.join(left_out)}")
    if len(honest) < 2:
        print("  Not enough players yet.")
        return

    print(f"\n  {'method':<30}{'top pick':>10}{'top two':>10}{'avg chance':>12}")
    print(f"  {'random guessing':<30}{'25%':>10}{'50%':>10}{'25%':>12}")
    methods = [("ME (person only)", 1, 0), ("crowd only", 0, 1),
               ("person + crowd (half)", 1, 0.5), ("person + crowd (full)", 1, 1)]
    for name, person_weight, crowd_weight in methods:
        top, two, chance = evaluate(tests, person_weight, crowd_weight)
        print(f"  {name:<30}{top:>10.0%}{two:>10.0%}{chance:>12.1%}")

    rows_flat = [row for test in tests for row in test]
    never = [row for row in rows_flat if row["never"]]
    if never:
        right = sum(row["never_correct"] for row in never)
        print(f"\n  never-pick right: {right} of {len(never)} ({right / len(never):.0%}, random 25%)")
    for linked, label in ((True, "linked to the game"), (False, "not linked")):
        part = [row for row in rows_flat if row["touched_by_game"] == linked]
        if part:
            right = sum(row["top_correct"] for row in part)
            print(f"  top pick on questions {label}: {right} of {len(part)} ({right / len(part):.0%})")

    print("\n  most popular answers (crowd favourites):")
    by_question = {}
    for row in rows_flat:
        by_question.setdefault(row["question"], Counter())[row["pick"]] += 1
    for question, picks in by_question.items():
        favourite, count = picks.most_common(1)[0]
        print(f"    {question:<10} {favourite} ({count} of {sum(picks.values())})")
    if len(honest) < 20:
        print(f"\n  Note: only {len(honest)} players, so these numbers can still swing by about 10 points.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "plays_rows.csv"
    rows = load_rows(path)
    show_funnel(rows)
    show_feedback(rows)
    show_predictions(rows)
