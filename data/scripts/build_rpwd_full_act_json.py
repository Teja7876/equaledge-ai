import re
import json
from pypdf import PdfReader

# ---------------------------
# CONFIG
# ---------------------------

PDF_PATH = "/mnt/c/Users/DELL/Downloads/rpwd2016.pdf"
OUTPUT_PATH = "data/domains/legal/RPWD_2016_FULL_ACT_STRUCTURED.json"


# ---------------------------
# CLEAN TEXT
# ---------------------------

def clean_text(text):
    # Remove excessive whitespace
    text = re.sub(r'\r', '\n', text)
    text = re.sub(r'\n{2,}', '\n', text)

    # Remove page numbers (lines with only digits)
    text = re.sub(r'\n\d+\n', '\n', text)

    # Remove Gazette footnotes
    text = re.sub(r'\n\d+\.\s+.*?Gazette.*?\n', '\n', text)

    return text.strip()


# ---------------------------
# REMOVE ARRANGEMENT OF SECTIONS
# ---------------------------

def remove_toc(text):
    toc_pattern = r'ARRANGEMENT OF SECTIONS.*?CHAPTER I'
    return re.sub(toc_pattern, 'CHAPTER I', text, flags=re.DOTALL)


# ---------------------------
# EXTRACT SECTIONS
# ---------------------------

def extract_sections(full_text):
    """
    Detect sections like:
    1. Short title and commencement.—
    2. Definitions.—
    """

    pattern = r'\n(\d{1,3})\.\s+([^\n]+?—)(.*?)(?=\n\d{1,3}\.\s+|\Z)'
    matches = re.findall(pattern, full_text, re.DOTALL)

    sections = []

    for number, heading, body in matches:
        full_section_text = f"{number}. {heading}{body}".strip()

        sections.append({
            "section_number": number,
            "section_heading": heading.replace("—", "").strip(),
            "section_text": full_section_text
        })

    return sections


# ---------------------------
# MAIN
# ---------------------------

def main():

    reader = PdfReader(PDF_PATH)

    full_text = ""

    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            full_text += extracted + "\n"

    full_text = clean_text(full_text)
    full_text = remove_toc(full_text)

    sections = extract_sections(full_text)

    structured_data = {
        "canonical_id": "RPWD_2016_FULL_ACT",
        "title": "Rights of Persons with Disabilities Act, 2016",
        "total_sections": len(sections),
        "sections": sections
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)

    print("Structured RPwD Act saved.")
    print("Total sections extracted:", len(sections))


if __name__ == "__main__":
    main()
