import json
import re

INPUT = "data/data_storage/raw/domains/healthcare/accessibility_standards_for_health_care_by_ministry_of_health_and_family_affairs.json"
OUTPUT = "data/rpwd_full.json"

with open(INPUT) as f:
    data = json.load(f)

text = data.get("verbatim_text", "")

# Clean text
text = text.replace("\n", " ")
text = re.sub(r'\s+', ' ', text)

# Split by sections
sections = re.split(r'(Section\s+\d+)', text)

results = []

for i in range(1, len(sections), 2):
    section_title = sections[i]
    content = sections[i+1] if i+1 < len(sections) else ""

    results.append({
        "section": section_title.strip(),
        "text": content.strip()[:1000]
    })

with open(OUTPUT, "w") as f:
    json.dump(results, f, indent=2)

print("✅ Extracted", len(results), "sections")
