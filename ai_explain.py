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


# Which game measures belong to which part of the person
DECISION_STYLE = ["Maximizing", "Intuitive", "Relies on others"]
VALUES = ["Security", "Stimulation", "Benevolence", "Achievement"]
TASTE = ["Minimal vs expressive", "Classic vs trendy", "Dark vs bright", "Warm vs cool", "Natural vs polished"]


def pick(profile, evidence, names):
    # The scores for some dimensions, each with how many scenes it rests on.
    return {name: f"{round(profile[name], 1)} (from {evidence.get(name, 1)} scenes)"
            for name in names if name in profile}


def build_prompt(person, reader, game=None, use_files=True, test_lines=None):
    # Everything ME knows about one person, turned into a prompt for the AI.
    # game: a game result to use directly; use_files=False reads no saved files (web demo).
    # test_lines: what ME predicted in the prediction test and what the person chose.
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
        profile = game["profile"]
        evidence = game.get("evidence", {})
        data.append(f"What {person} DOES (game choices, {game['date']}): {pick(profile, evidence, TRAITS)}")
        data.append(f"Decision style (1-7): {pick(profile, evidence, DECISION_STYLE) or 'not measured'}")
        data.append(f"Values (1-7, from what they would do with money): {pick(profile, evidence, VALUES) or 'not measured'}")
        data.append(f"Taste (1-7, low = first word, high = second word): {pick(profile, evidence, TASTE) or 'not measured'}")
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
    if test_lines:
        data.append("Prediction test (ME guessed before the person answered):")
        data.extend(test_lines)
    data_text = "\n".join(data)

    prompt = f"""
You are ME, a personal AI that understands people the way a close friend does.
Explain this person in warm, simple English that a non-native speaker can easily understand.

{perspective}

Write a personal portrait with these short sections, each with a small heading.
Skip a section when there is no data for it.

1. Who you are: 2-3 sentences that connect the personality traits the way a
   close friend would describe someone, then one short plain line per Big Five
   trait.
2. How you decide: from the decision style scores.
3. What matters to you: from the values scores.
4. Your taste: from the taste scores (for example warm and natural, or dark and polished).
5. It depends: their "it depends" answers and explanations, as real examples of
   how they change with mood, people, money or time.
6. What ME guessed about you: from the prediction test. For each guess, explain
   WHY ME expected it, using only the "why" given in the data (option -> value ->
   trait -> evidence from their game). Never invent a different reason. If the data
   says "no strong reason yet", say ME was mostly guessing. Where ME was wrong, use
   the value of the option the person actually chose to say gently what may matter
   more to them. Pick the 3-4 most telling questions, not all 8. Be honest that ME
   is still learning.
7. End with ONE question about the biggest difference between words and choices,
   or about what ME is least sure of.

Rules:
- Scores go from 1 to 7, and 4 is the middle. Treat 3.5 to 4.5 as
  "in between / a bit of both", not as high or low.
- A score that rests on only 1 scene is a first guess: say so with words like
  "maybe" or "it seems". Do not present it as a fact.
- Emotional Stability: high means calm and resilient.
- The questionnaire is what the person SAYS about themselves. The game is what
  they actually CHOSE in everyday scenes.
- Where words and choices differ a lot, mention it gently and with curiosity,
  like a friend who noticed something. Never call the person a liar or wrong.
- If friends' views are given, you may mention how others see the person.
- Where confidence is low or there are sincerity warnings, sound clearly less certain.
- Never diagnose anything or mention mental illness.
- Warm, simple English that a non-native speaker can easily understand.
- Maximum 420 words.

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
