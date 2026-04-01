import json
import os


class SectionsEngine:

    def __init__(self):

        base_dir = os.path.dirname(os.path.dirname(__file__))

        path = os.path.join(
            base_dir,
            "data_storage",
            "raw",
            "domains",
            "legal",
            "RPWD_2016_FULL_ACT_STRUCTURED.json"
        )

        with open(path, "r") as f:
            self.data = json.load(f)

        self.sections = self.data.get("sections", [])


    def search(self, query: str):

        q = query.lower()

        for section in self.sections:

            section_number = str(section.get("section", "")).lower()
            section_title = section.get("title", "").lower()
            section_text = section.get("text", "")

            if section_number in q or section_title in q:

                return {
                    "answer": section_text,
                    "citation": section_number,
                    "confidence": "Very High",
                    "provider": "statute_section_engine"
                }

        return None
