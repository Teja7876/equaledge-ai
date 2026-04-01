import json
import os


class RulesEngine:

    def __init__(self):

        base_dir = os.path.dirname(os.path.dirname(__file__))

        self.rules = []

        files = [
            "reservation_logic_expanded.json",
            "offences_and_penalties.json",
            "governance_and_grievance.json"
        ]

        for f in files:

            path = os.path.join(
                base_dir,
                "data_storage",
                "raw",
                "domains",
                "legal",
                f
            )

            if os.path.exists(path):

                with open(path, "r") as file:
                    data = json.load(file)

                if isinstance(data, dict):
                    self.rules.append(data)

                elif isinstance(data, list):
                    self.rules.extend(data)


    def search(self, query: str):

        q = query.lower()

        for rule in self.rules:

            text = json.dumps(rule).lower()

            if any(word in text for word in q.split()):

                answer = rule.get("text") or rule.get("description") or text

                citation = rule.get("section") or rule.get("law") or "RPwD Act"

                return {
                    "answer": answer,
                    "citation": citation,
                    "confidence": "High",
                    "provider": "statute_rule_engine"
                }

        return None
