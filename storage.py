# ME - storage
# Saves and loads results as JSON, so nothing is lost when the program ends.

import json 
import os 

RESULTS_FILE = "results.json"

def load_results(filename=RESULTS_FILE):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_result(record, filename=RESULTS_FILE):
    results = load_results(filename)
    results.append(record)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)