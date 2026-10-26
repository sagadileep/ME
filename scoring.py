# ME - TIPI scoring
# Turns 10 TIPI answers (1-7) into Big Five scores.
# Gosling, Rentfrow & Swann (2003): reverse item = 8 - answer,
# trait score = average of its normal and reversed item.
TRAITS = ["Extraversion", "Agreeableness", "Conscientiousness", "Emotional Stability","Openness"]
# Which answers belong to each trait: (normal item position, reversed item position)
PAIRS = {
    "Extraversion": (0, 5),
    "Agreeableness": (6, 1),
    "Conscientiousness": (2, 7),
    "Emotional Stability": (8, 3),
    "Openness": (4, 9),
}

def reverse(answer):
    return 8 - answer 

def average(a, b):
    return (a + b) / 2


def score_tipi(answers):
    scores = {}
    scores["Extraversion"] = average(answers[0], reverse(answers[5]))
    scores["Agreeableness"] = average(answers[6], reverse(answers[1]))
    scores["Conscientiousness"] = average(answers[2], reverse(answers[7]))
    scores["Emotional Stability"] = average(answers[8], reverse(answers[3]))
    scores["Openness"] = average(answers[4], reverse(answers[9]))
    return scores 


def describe(score):
    if score < 3.5:
        return "low"
    elif score < 5.5:
        return "medium"
    else:
        return "high"

def confidence_tipi(answers):
    confidence = {}
    for trait, (normal, reversed_item) in PAIRS.items():
        gap = abs(answers[normal] - reverse(answers[reversed_item]))

        if gap <= 1:
            confidence[trait] = "high" 
        elif gap <= 3:
            confidence[trait] = "medium"
        else:
            confidence[trait] = "low"
    return confidence
if __name__ == "__main__":
    my_answers = [5, 2, 6, 3, 7, 4, 6, 1, 5, 2]
    my_scores = score_tipi(my_answers)
    for trait, score in my_scores.items():
        print(f"{trait}: {score} ({describe(score)})")
    friend = [4, 2, 6, 2, 6, 6, 5, 2, 6, 5]
    print(confidence_tipi(friend))