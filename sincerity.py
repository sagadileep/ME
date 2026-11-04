# ME - sincerity checks
# Looks for signs that answers were not given carefully or honestly.
# Idea: careless responding research (Meade & Craig, 2012).

FAST_SECONDS = 1.0     # faster than this, nobody can read a scene
MAX_FAST = 3           # more fast answers than this = warning
MAX_SAME_SHARE = 0.8   # 80% or more answers with the same number = warning
MAX_TWIN_GAP = 2.5     # twin answers this far apart = contradiction

def speed_check(log):
    fast = 0
    for entry in log:
        if entry["seconds"] < FAST_SECONDS:
            fast = fast + 1
    return fast


def same_number_check(log):
    numbers = []
    for entry in log:
        numbers.append(entry["number"])
    most = 0
    for n in numbers:
        if numbers.count(n) > most:
            most = numbers.count(n)
    return most / len(numbers)

def twin_check(log, scenes):
    # Returns the twin pairs whose answers point in opposite directions.
    answers = {}
    for entry in log:
        answers[entry["scene"]] = entry["effects"]

    clashes = []
    for scene in scenes:
        if "twin_of" in scene:
            target = scene["target"]
            first = answers[scene["twin_of"]].get(target, 0)
            second = answers[scene["id"]].get(target, 0)
            if abs(first - second) >= MAX_TWIN_GAP:
                clashes.append({"first": scene["twin_of"], "second": scene["id"], "target": target})
    return clashes


def sincerity_report(log, scenes, explained):
    # explained = twin scenes the player explained with "it depends" (no warning for those)
    warnings = []
    fast = speed_check(log)
    if fast > MAX_FAST:
        warnings.append(f"{fast} answers came faster than {FAST_SECONDS} second")
    share = same_number_check(log)
    if share >= MAX_SAME_SHARE:
        warnings.append(f"{round(share * 100)}% of answers used the same number")
    for clash in twin_check(log, scenes):
        if clash["second"] not in explained:
            warnings.append(f"'{clash['first']}' and '{clash['second']}' disagree about {clash['target']}")
    return warnings
    