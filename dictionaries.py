scores = {
    "Extraversion": 4.5,
    "Openness": 6.5,
    "Conscientiousness": 6,
    "Agreeableness": 5,
    "Emotional Stability": 2
}
print(scores.get("Happiness","not measured"))
scores["Agreeableness"] = 7.0
print(scores["Conscientiousness"])
for trait, score in scores.items():
    print(f"{trait}: {score}")
def reverse(answer):
    return 8 - answer
def average(a, b):
    return (a+b) / 2
def describe(score):
    if score < 3.5:
        return "low"
    elif score < 5.5:
        return "medium"
    else:
        return "high"
print(describe(2))
print(describe(4.5))
print(describe(6.5))