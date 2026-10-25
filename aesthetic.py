# ME - aesthetic DNA
# Describes a person's taste: 5 style dimensions (1-7) plus a colour layer.
# Colour meanings follow Palmer & Schloss (2010): people like colours
# because of what the colours remind them of.

DIMENSIONS = {
    "Minimal vs expressive": ("minimal", "expressive"),
    "Classic vs trendy": ("classic", "trendy"),
    "Dark vs bright": ("dark", "bright"),
    "Warm vs cool": ("warm", "cool"),
    "Natural vs polished": ("natural", "polished"),
}


def to_percent(score):
    return round((score - 1) / 6 * 100)


def lean(score, low_word, high_word):
    if score <= 3:
        return f"leans {low_word}"
    elif score>= 5:
        return f"leans {high_word}"
    else:
        return f"a mix of {low_word} and {high_word}"


def describe_aesthetic(profile):
    for name, (low_word, high_word) in DIMENSIONS.items():
        score = profile["style"][name]
        print(f"{name}: {score} → {lean(score, low_word, high_word)} "
              f"({to_percent(score)}% {high_word})")

    for fav in profile["colours"]["favourite"]:
        print(f"Loves {fav['colour']}: feels \"{fav['meaning']}\", "
              f"gives {fav['feeling']}")
    print(f"Colour combinations: prefers {profile['colours']['combination']}")


if __name__ == "__main__":
    dileep = {
        "style": {
            "Minimal vs expressive": 3,
            "Classic vs trendy": 2,
            "Dark vs bright": 3,
            "Warm vs cool": 6,
            "Natural vs polished": 6,
        },
        "colours": {
            "favourite": [
                {"colour": "navy", "meaning": "majestic, class", "feeling": "confidence"},
            ],
            "disliked": ["dark yellow", "brown"],
            "combination": "contrast (navy with white)",
        },
    }
    describe_aesthetic(dileep)