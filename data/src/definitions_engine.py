import json
import os


class DefinitionsEngine:

    def __init__(self):

        base_dir = os.path.dirname(os.path.dirname(__file__))

        path = os.path.join(
            base_dir,
            "data_storage",
            "raw",
            "domains",
            "legal",
            "definitions_verbatim.json"
        )

        with open(path, "r") as f:
            data = json.load(f)

        self.definitions = data.get("definitions", {})


    def search(self, query: str):

        q = query.lower()

        for term, definition in self.definitions.items():

            if term.replace("_", " ") in q:

                return {
                    "answer": definition["text"],
                    "citation": definition["section"],
                    "confidence": "Very High",
                    "provider": "statute_definition_engine"
                }

        return None
