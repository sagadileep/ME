# ME - one profile per person
# Brings together what a person SAYS (questionnaire) and what they DO (game),
# and combines them into one best estimate per trait.

from storage import load_results
from scoring import TRAITS
from game import GAME_RESULTS_FILE

START = 4.0               # no information yet: the middle of the 1-7 scale
QUESTIONNAIRE_WEIGHT = 2  # TIPI measures each trait with 2 questions
GAP = 1.5                 # says vs does this far apart is worth noticing
PRIOR_STRENGTH = 2        # shrinkage: every estimate starts with 2 'neutral' scenes at 4.0

class Profile:
    def __init__(self, name):
        self.name = name
        self.says = {}          # questionnaire scores
        self.does = {}          # game scores
        self.evidence = {}      # how many scenes each game score is built on
        self.depends = []       # the person's "it depends" answers
        self.life_stage = None

    def load(self):
        for record in load_results():
            if record["person"] == self.name and record["answered_by"] == self.name:
                self.says = record["scores"]
        for game in load_results(GAME_RESULTS_FILE):
            if game["person"] == self.name:
                self.does = game["profile"]
                self.evidence = game.get("evidence", {})
                self.life_stage = game.get("life_stage")
                self.depends = [entry for entry in game["log"] if "cases" in entry]

    def trait(self, name):
        # Best estimate: a weighted average of what they say and what they do.
        total = START * PRIOR_STRENGTH
        weights = PRIOR_STRENGTH
        if name in self.says:
            total = total + self.says[name] * QUESTIONNAIRE_WEIGHT
            weights = weights + QUESTIONNAIRE_WEIGHT
        if name in self.does:
            scenes = self.evidence.get(name, 1)
            total = total + self.does[name] * scenes
            weights = weights + scenes
        return round(total / weights, 2)

    def shrunk(self, name):
        # Game score pulled toward the middle when it rests on few scenes.
        scenes = self.evidence.get(name, 1)
        raw = self.does[name]
        return round((raw * scenes + START * PRIOR_STRENGTH) / (scenes + PRIOR_STRENGTH), 2)
    
    def gaps(self):
        # Traits where what the person says and what they do differ a lot.
        found = []
        for name in TRAITS:
            if name in self.says and name in self.does:
                difference = self.shrunk(name) - self.says[name]
                if abs(difference) >= GAP:
                    found.append((name, self.says[name], self.shrunk(name)))
        return found
    
    def summary(self):
        print(f"--- {self.name} ---")
        for name in TRAITS:
            says = self.says.get(name, "-")
            does = self.shrunk(name) if name in self.does else "-"            
            print(f"{name}: says {says}, does {does} -> ME's estimate {self.trait(name)}")
        for entry in self.depends:
            print(f"It depends ({entry['scene']}): {entry['depends_on']}")
        for name, says, does in self.gaps():
            print(f"Gap in {name}: says {says}, chooses like {does}")

if __name__ == "__main__":
    for name in ["Dileep", "Keerthi", "Lokesh M"]:
        person = Profile(name)
        person.load()
        person.summary()
        print()