import json
import os

FILE = "buttons.json"

def load_buttons():
    if not os.path.exists(FILE):
        return []
    with open(FILE, "r") as f:
        return json.load(f)

def save_buttons(buttons):
    with open(FILE, "w") as f:
        json.dump(buttons, f, indent=2)
