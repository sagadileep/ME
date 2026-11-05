# ME - AI explanation
# Explains one person by combining what they SAY (TIPI questionnaire)
# with what they DO (the onboarding game), including their "it depends" answers.
# The brain (this code) decides what matters; the AI only puts it into words.

from ai import ask_ai
from storage import load_results
from scoring import TRAITS
from game import GAME_RESULTS_FILE

BIG_GAP = 1.5   # words and choices this far apart are worth mentioning


def latest_for(records, person, answered_by=None):
    # Newest record about this person (optionally: answered by a certain person).
    found = None
    for record in records:
        if record["person"] == person:
            if answered_by is None or record.get("answered_by") == answered_by:
                found = record
    return found


def others_views(tipi_records, person):
    # Newest answer from each friend who described this person.
    views = {}
    for record in tipi_records:
        if record["person"] == person and record["answered_by"] != person:
            views[record["answered_by"]] = record["scores"]
    return views


def find_gaps(self_scores, game_profile):
    # Traits where what the person says and what they chose differ a lot.
    gaps = []
    for trait in TRAITS:
        if trait in self_scores and trait in game_profile:
            says = self_scores[trait]
            does = game_profile[trait]
            if abs(says - does) >= BIG_GAP:
                gaps.append(f"{trait}: says {says}, chose like {round(does, 1)}")
    return gaps


def depends_lines(game):
    # The "it depends" answers and twin follow-ups, as plain sentences.
    lines = []
    for entry in game["log"]:
        if "cases" in entry:
            parts = [f"{case}: {choice}" for case, choice in entry["cases"].items()]
            cases_text = "; ".join(parts)
            lines.append(f"Scene '{entry['scene']}' depends on {entry['depends_on']} ({cases_text})")
    for followup in game.get("twin_followups", []):
        if followup["depends_on"]:
            lines.append(f"Different choices in '{followup['first']}' and '{followup['second']}' "
                         f"({followup['target']}); the person says it depends on {followup['depends_on']}")
        else:
            lines.append(f"Different choices in '{followup['first']}' and '{followup['second']}' "
                         f"({followup['target']}); the person says there is no reason")
    return lines


def build_prompt(person, reader, game=None, use_files=True):
    # Everything ME knows about one person, turned into a prompt for the AI.
    # game: a game result to use directly; use_files=False reads no saved files (web demo).
    # Returns None when ME has no results for that person.
    tipi_records = load_results() if use_files else []
    game_records = load_results(GAME_RESULTS_FILE) if use_files else []
    tipi = latest_for(tipi_records, person, answered_by=person)
    if game is None:
        game = latest_for(game_records, person)
    views = others_views(tipi_records, person)
    if tipi is None and game is None and not views:
        return None

    if reader == person:
        perspective = f"{person} is reading this. Talk to them directly as 'you'."
    else:
        perspective = (
            f"{reader} is reading this about their friend {person}. "
            f"Talk to {reader} ABOUT {person}: use {person}'s name or 'they', never 'you' for {person}. "
            f"The final question goes to {reader}, asking what they notice in {person}."
        )

    data = []
    if tipi:
        data.append(f"What {person} SAYS (questionnaire, {tipi['date']}): {tipi['scores']}")
        data.append(f"Confidence of those answers: {tipi.get('confidence', 'not available')}")
    else:
        data.append(f"No questionnaire from {person} themselves yet.")
    if game:
        game_traits = {t: round(game["profile"][t], 1) for t in TRAITS if t in game["profile"]}
        data.append(f"What {person} DOES (game choices, {game['date']}): {game_traits}")
        other = {k: round(v, 1) for k, v in game["profile"].items() if k not in TRAITS}
        data.append(f"Other things the game measured: {other}")
        for line in depends_lines(game):
            data.append(line)
        if game["warnings"]:
            data.append(f"Sincerity warnings (be less certain): {game['warnings']}")
    else:
        data.append("No game played yet.")
    if tipi and game:
        gaps = find_gaps(tipi["scores"], game["profile"])
        data.append(f"Biggest differences between words and choices: {gaps if gaps else 'none'}")
    for friend, scores in views.items():
        data.append(f"How {friend} sees {person}: {scores}")
    data_text = "\n".join(data)

    prompt = f"""
You are ME, a personal AI that understands people the way a close friend does.
Explain this person in warm, simple English that a non-native speaker can easily understand.

{perspective}

Rules:
- Start with 2 sentences that describe the whole person, connecting the traits
  together, the way a close friend would describe them.
- Then one short line per Big Five trait, in plain everyday words.
- Scores go from 1 to 7, and 4 is the middle. Treat 3.5 to 4.5 as
  "in between / a bit of both", not as high or low.
- Emotional Stability: high means calm and resilient.
- The questionnaire is what the person SAYS about themselves. The game is what
  they actually CHOSE in everyday scenes. The game has only about 10 scenes,
  so it is a rougher measure.
- Where words and choices differ a lot, mention it gently and with curiosity,
  like a friend who noticed something. Never call the person a liar or wrong.
  Suggest that it may depend on the situation.
- Use the person's "it depends" answers as real examples (for example: open to
  new food in a good mood, the familiar dish when tired).
- If friends' views are given, you may mention how others see the person.
- Where confidence is medium or low, or there are sincerity warnings, sound
  clearly less certain.
- Never diagnose anything or mention mental illness.
- Maximum 220 words.
- End with ONE question about the biggest difference between words and choices
  (or, if there is none, about the trait you are least certain about).

Data about {person}:
{data_text}
"""

    return prompt


if __name__ == "__main__":
    person = input("Who should ME explain? ").strip().title()
    reader = input("Who is reading this? ").strip().title()
    prompt = build_prompt(person, reader)
    if prompt is None:
        records = load_results() + load_results(GAME_RESULTS_FILE)
        names = sorted({r["person"] for r in records})
        print(f"No results found for {person}. Saved people: {', '.join(names)}")
        raise SystemExit

    consent = input(f"Has {person} agreed to send these answers to the AI? (y/n) ").strip().lower()
    if consent != "y":
        print("Okay, nothing was sent.")
        raise SystemExit

    print(ask_ai(prompt))
