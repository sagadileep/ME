# ME - storage
# Saves and loads results as JSON, so nothing is lost when the program ends.

import json 
import os 

RESULTS_FILE = "results.json"

def load_results():
    if not os.path.exists(RESULTS_FILE):
        return[]
    with open(RESULTS_FILE, "r", encoding="utf-8")as f:
        return json.load(f)

def save_result(record):
    results = load_results()
    results.append(record)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)