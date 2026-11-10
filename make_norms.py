# ME - real averages ("norms") for the Big Five
# Reads the Open-Source Psychometrics IPIP-FFM dataset (about 1 million people, 2016-2018)
# and writes norms.json: the average and spread of each trait on ME's 1-7 scale.
# Usage:  python make_norms.py "..\IPIP-FFM-data-8Nov2018\data-final.csv"
# The dataset stays outside this folder; only the small norms.json goes to GitHub.

import csv
import json
import math
import sys

TRAITS = {"OPN": "Openness", "CSN": "Conscientiousness", "EXT": "Extraversion",
          "AGR": "Agreeableness", "EST": "Emotional Stability"}
# Questions worded the other way round ("I don't talk a lot") are flipped: 1 becomes 5.
REVERSED = {"EXT": [2, 4, 6, 8, 10], "EST": [2, 4], "AGR": [1, 3, 5, 7],
            "CSN": [2, 4, 6, 8], "OPN": [2, 4, 6]}
MIN_SECONDS, MAX_SECONDS = 100, 3600   # 50 questions: faster than 100 s was not read


def to_me_scale(score):
    # The dataset uses 1-5, ME uses 1-7.
    return 1 + (score - 1) * 6 / 4


def person_scores(row):
    # One person's five trait scores, or None if the answers are not clean.
    if row.get("IPC") != "1":                    # one entry per internet address
        return None
    try:
        seconds = float(row["testelapse"])
        answers = {key: int(row[key]) for key in row if key[:3] in TRAITS and key[3:].isdigit()}
    except (ValueError, TypeError):
        return None
    if not MIN_SECONDS <= seconds <= MAX_SECONDS or len(answers) != 50:
        return None
    if any(a < 1 or a > 5 for a in answers.values()) or len(set(answers.values())) == 1:
        return None                              # 0 means skipped; all-same means not read
    scores = {}
    for code, name in TRAITS.items():
        values = []
        for number in range(1, 11):
            answer = answers[f"{code}{number}"]
            values.append(6 - answer if number in REVERSED[code] else answer)
        average = sum(values) / 10
        if code == "EST":
            average = 6 - average                # the EST questions measure worry; flip to stability
        scores[name] = to_me_scale(average)
    return scores


def make_norms(path):
    count = 0
    sums = {name: 0.0 for name in TRAITS.values()}
    squares = {name: 0.0 for name in TRAITS.values()}
    with open(path, encoding="utf-8") as file:
        for row in csv.DictReader(file, delimiter="\t"):
            scores = person_scores(row)
            if scores is None:
                continue
            count += 1
            for name, score in scores.items():
                sums[name] += score
                squares[name] += score * score
    norms = {"source": "IPIP-FFM open dataset, openpsychometrics.org, 2016-2018",
             "people": count, "scale": "1-7", "traits": {}}
    for name in sums:
        mean = sums[name] / count
        spread = math.sqrt(squares[name] / count - mean * mean)
        norms["traits"][name] = {"mean": round(mean, 2), "sd": round(spread, 2)}
    return norms


if __name__ == "__main__":
    norms = make_norms(sys.argv[1])
    with open("norms.json", "w", encoding="utf-8") as file:
        json.dump(norms, file, indent=2)
    print(f"Clean answers from {norms['people']} people")
    for name, values in norms["traits"].items():
        print(f"  {name}: average {values['mean']}, spread {values['sd']}")
