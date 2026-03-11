import json, os
from datetime import datetime


class HistoryManager:

    def __init__(self, path):
        self.path = path

    def load(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as file:
            return json.load(file)

    def add_entry(self, entry):
        history = self.load()
        history.append(entry)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=4)
