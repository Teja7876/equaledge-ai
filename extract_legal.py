import json
from data.src.services.rpwd_engine import RPWD_SECTIONS

output = []

for key, value in RPWD_SECTIONS.items():
    output.append({
        "id": key,
        "section": value.get("section"),
        "title": value.get("title"),
        "intent": value.get("intent"),
        "keywords": value.get("keywords"),
        "text": value.get("text")
    })

with open("data/rpwd_sections.json", "w") as f:
    json.dump(output, f, indent=2)

print("✅ Extracted", len(output), "sections")
