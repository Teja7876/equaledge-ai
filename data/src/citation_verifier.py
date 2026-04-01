import re
from typing import List


class CitationVerifier:

    def __init__(self):

        # Known RPwD sections
        self.valid_sections = set(str(i) for i in range(1, 110))


    def extract_sections(self, text: str) -> List[str]:

        matches = re.findall(r"Section\s*(\d+)", text, re.IGNORECASE)

        return matches


    def verify(self, text: str) -> bool:

        sections = self.extract_sections(text)

        if not sections:
            return True

        for s in sections:

            if s not in self.valid_sections:
                return False

        return True
