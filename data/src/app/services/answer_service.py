import re
from typing import Dict, Any, List, Optional
from legal_router import LegalRouter

router = LegalRouter()

ACT_NAME = "Rights of Persons with Disabilities Act, 2016"
DATASET_MODE = "Dataset-backed"


# ---------------------------------------------------
# Text Cleaning Layer
# ---------------------------------------------------

def clean_text(text: str) -> str:
    """
    Normalizes extracted legal text safely.
    """
    if not text:
        return ""

    # Collapse excessive whitespace and newlines
    text = re.sub(r"\s+", " ", text)

    # Fix common PDF word split issue
    text = re.sub(r"\bdi\s+sabilities\b", "disabilities", text)

    return text.strip()


# ---------------------------------------------------
# Confidence Engine
# ---------------------------------------------------

def compute_confidence(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "Low"

    distance = results[0].get("distance", 1.0)

    if distance <= 0.35:
        return "Very High"
    if distance <= 0.55:
        return "High"
    if distance <= 0.75:
        return "Medium"

    return "Low"


# ---------------------------------------------------
# Intent Detection
# ---------------------------------------------------

def detect_intent_section(query: str) -> Optional[str]:
    if not query:
        return None

    q = query.lower()

    if "employment" in q or "job" in q:
        return "34"
    if "education" in q:
        return "32"
    if "scheme" in q or "development" in q:
        return "37"

    return None


# ---------------------------------------------------
# Clause Extraction
# ---------------------------------------------------

def extract_clause(section: str, content: str) -> Optional[str]:
    if not section or not content:
        return None

    patterns = {
        "34": r"(Every appropriate Government.*?namely:—)",
        "32": r"(All Government institutions.*?benchmark disabilities\.)",
        "37": r"(The appropriate Government.*?development programmes.*?)"
    }

    pattern = patterns.get(section)
    if not pattern:
        return None

    match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)

    if not match:
        return None

    return clean_text(match.group(1))


# ---------------------------------------------------
# Structured Answer Builder
# ---------------------------------------------------

def extract_structured_answer(results: List[Dict[str, Any]], query: str) -> Optional[Dict[str, Any]]:
    if not results:
        return None

    target_section = detect_intent_section(query)

    for result in results[:6]:
        metadata = result.get("metadata") or {}

        section = str(metadata.get("section", "") or "").strip()
        heading = str(metadata.get("heading", "") or "").strip()
        content = result.get("content") or ""

        if target_section and section != target_section:
            continue

        clause = extract_clause(section, content)

        if clause:
            return {
                "section": section,
                "heading": heading,
                "act": ACT_NAME,
                "quoted_text": clause
            }

    # Fallback: return top metadata even if no clause match
    top_metadata = results[0].get("metadata") or {}

    section = str(top_metadata.get("section", "") or "").strip()
    heading = str(top_metadata.get("heading", "") or "").strip()

    if section:
        return {
            "section": section,
            "heading": heading,
            "act": ACT_NAME,
            "quoted_text": None
        }

    return None


# ---------------------------------------------------
# Main Answer Generator
# ---------------------------------------------------

def generate_answer(query: str) -> Dict[str, Any]:
    results = router.search(query, k=6)

    if not results:
        return {
            "section": None,
            "heading": None,
            "act": ACT_NAME,
            "quoted_text": None,
            "confidence": "Low",
            "mode": DATASET_MODE,
            "results": []
        }

    confidence = compute_confidence(results)
    structured = extract_structured_answer(results, query)

    if not structured:
        return {
            "section": None,
            "heading": None,
            "act": ACT_NAME,
            "quoted_text": None,
            "confidence": confidence,
            "mode": DATASET_MODE,
            "results": results[:3]
        }

    return {
        "section": structured["section"],
        "heading": structured["heading"],
        "act": structured["act"],
        "quoted_text": structured["quoted_text"],
        "confidence": confidence,
        "mode": DATASET_MODE,
        "results": results[:3]
    }
