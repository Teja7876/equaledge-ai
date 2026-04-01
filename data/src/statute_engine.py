import json
import os

class StatuteEngine:

    def __init__(self):

        path = os.path.join("data", "rpwd_sections.json")

        with open(path, "r") as f:
            self.sections = json.load(f)

    def search(self, query):

        q = query.lower()

        for section in self.sections:

            for keyword in section["keywords"]:

                if keyword in q:

                    return {
                        "answer": section["text"],
                        "citation": section["section"],
                        "confidence": "Very High",
                        "provider": "statute_engine"
                    }

        return None
