import json
import os
from typing import Dict, List


class LegalGraph:

    def __init__(self):

        base_dir = os.path.dirname(os.path.dirname(__file__))

        graph_path = os.path.join(
            base_dir,
            "data_storage",
            "raw",
            "domains",
            "legal",
            "legal_graph.json"
        )

        self.graph = {}

        if os.path.exists(graph_path):

            with open(graph_path, "r") as f:
                self.graph = json.load(f)


    def get_related_sections(self, section: str) -> List[str]:

        return self.graph.get(section, [])
