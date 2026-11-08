from scoring import score_tipi, describe, confidence_tipi

from storage import save_result

from datetime import datetime
person = input("Whose personality is this about? ").strip().title()
answered_by = input("Who is answering? ").strip().title()

statements = ["Extraverted, enthusiastic",
    "Critical, quarrelsome",
    "Dependable, self-disciplined",
    "Anxious, easily upset",
    "Open to new experiences, complex",
    "Reserved, quiet",
    "Sympathetic, warm",
    "Disorganized, careless",
    "Calm, emotionally stable",
    "Conventional, uncreative",]

# Plain words for each pair. The original TIPI words stay unchanged,
# so scores still match the published questionnaire (Gosling et al. 2003).
HELP = {
    "Extraverted, enthusiastic": "outgoing, full of energy around people",
    "Critical, quarrelsome": "often finds fault, gets into arguments",
    "Dependable, self-disciplined": "reliable, keeps promises, sticks to plans",
    "Anxious, easily upset": "worries a lot, gets upset quickly",
    "Open to new experiences, complex": "curious, likes new ideas, thinks deeply",
    "Reserved, quiet": "keeps to themselves, doesn't talk much",
    "Sympathetic, warm": "caring and kind to others",
    "Disorganized, careless": "messy, forgets things, not careful",
    "Calm, emotionally stable": "relaxed, not easily stressed",
    "Conventional, uncreative": "prefers the usual way, not very creative",
}

# Answering about yourself or about someone else?
if person == answered_by:
    lead = "I see myself as"
    about = "you"
else:
    lead = f"I see {person} as"
    about = person

print(f"How well does each pair of words describe {about}?")
print("1 = disagree strongly.... 4 = neutral ... 7 = agree strongly")

answers = []

for statement in statements:
    print(f"\n   ({HELP[statement]})")
    question = f"{lead}: {statement}  (1-7) "
    answer_text = input(question).strip()
    while not answer_text.isdigit() or int(answer_text) < 1 or int(answer_text) > 7:
        print("Please enter a number from 1-7")
        answer_text = input(question).strip()
    answer = int(answer_text)
    if answer <= 2:
        print(" → You disagree.")
    elif answer <= 5:
        print(" → You're somewhere in the middle.")
    else:
        print(" → You agree.")    
    answers.append(answer)
print("Your answers:", answers)
scores = score_tipi(answers)
confidence = confidence_tipi(answers)

print()
print("--- Your ME personality profile ---")
for trait, score in scores.items():
    print(f"{trait}: {score} ({describe(score)}, confidence: {confidence[trait]})")

record = {
    "person": person, 
    "answered_by": answered_by,
    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "answers": answers, 
    "scores": scores,
    "confidence": confidence,
                                    
}
save_result(record)
print(f"\nSaved to results.json ({person}, answered by {answered_by}).")