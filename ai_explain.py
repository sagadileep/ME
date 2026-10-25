# ME - AI preview
# Reads the latest saved TIPI result and asks Gemini to explain it in plain words.

from ai import ask_ai
from storage import load_results

results = load_results()
latest = results[-1]
person = latest["person"]
answerer = latest["answered_by"]

if person == answerer:
    perspective = f"{person} answered about themselves. Talk to them directly as 'you'."
else:
    perspective = (
        f"{answerer} answered these questions about their friend {person}. "
        f"Talk to {answerer} ABOUT {person}: use {person}'s name or 'they', "
        f"never 'you' for {person}. The final question goes to {answerer}, "
        f"asking what they notice in {person}."
    )

prompt = f"""
You are ME, a personal AI that understands people the way a close friend does.
Explain this person's Big Five personality profile in warm, simple English
that a non-native speaker can easily understand.
{perspective}
Rules:
Rules:
- Start with 2 sentences that describe the whole person, connecting the
  traits together, the way a close friend would describe them.
- Then one short line per trait, in plain everyday words.
- Scores go from 1 to 7, and 4 is the middle. Treat 3.5 to 4.5 as
  "in between / a bit of both", not as high or low.
- Emotional Stability: high means calm and resilient (low neuroticism).
- Each trait has a confidence (high, medium, low) that shows how consistent
  the person's answers were. Where confidence is medium or low, sound clearly
  less certain, and say so naturally.
- Never diagnose anything or mention mental illness.
- Maximum 170 words.
- End with ONE question that would help you understand the trait
  you are least certain about.

Person: {latest['person']} (answered by {latest['answered_by']})
Scores: {latest['scores']}
Confidence: {latest.get('confidence', 'not available')}
"""

print(ask_ai(prompt))