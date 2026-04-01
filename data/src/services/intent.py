import re
from typing import Literal, TypedDict, Optional


# -----------------------------
# Intent Types
# -----------------------------

IntentType = Literal[
    "exact_section",
    "exact_rule",
    "amendment_query",
    "definition_query",
    "explanatory",
    "comparison_query",
    "semantic"
]


# -----------------------------
# Structured Output
# -----------------------------

class IntentResult(TypedDict):
    intent: IntentType
    act: Optional[str]
    section: Optional[str]
    jurisdiction: Optional[str]


# -----------------------------
# Known Legal Acts
# Expand as your corpus grows
# -----------------------------

KNOWN_ACTS = {
    "rpwd": "RPwD Act 2016",
    "rights of persons with disabilities act": "RPwD Act 2016",
    "pwd act": "RPwD Act 2016",
    "rpwd act": "RPwD Act 2016",
    "rti": "RTI Act 2005",
    "right to information act": "RTI Act 2005",
    "rte": "RTE Act 2009",
    "right to education act": "RTE Act 2009"
}


# -----------------------------
# Indian Jurisdictions
# Expand later if needed
# -----------------------------

KNOWN_JURISDICTIONS = [
    "india",
    "telangana",
    "andhra pradesh",
    "maharashtra",
    "karnataka",
    "tamil nadu",
    "delhi"
]


# -----------------------------
# Core Detection Logic
# -----------------------------

def detect_intent(query: str) -> IntentResult:
    """
    Detects:
    - intent type
    - referenced legal act
    - section number (if present)
    - jurisdiction (if mentioned)
    """

    if not query or not query.strip():
        return {
            "intent": "semantic",
            "act": None,
            "section": None,
            "jurisdiction": None,
        }

    q = query.lower().strip()

    # -----------------------------
    # Detect Section
    # -----------------------------
    section_match = re.search(r"\bsection\s+(\d+[a-zA-Z]?)\b", q)
    section_number = section_match.group(1) if section_match else None

    # -----------------------------
    # Detect Legal Act
    # -----------------------------
    detected_act = None
    for key, value in KNOWN_ACTS.items():
        if key in q:
            detected_act = value
            break

    # -----------------------------
    # Detect Jurisdiction
    # -----------------------------
    detected_jurisdiction = None
    for state in KNOWN_JURISDICTIONS:
        if state in q:
            detected_jurisdiction = state.title()
            break

    # -----------------------------
    # Intent Classification
    # -----------------------------

    # Exact Section Reference
    if section_number:
        return {
            "intent": "exact_section",
            "act": detected_act,
            "section": section_number,
            "jurisdiction": detected_jurisdiction,
        }

    # Amendment Queries
    if any(word in q for word in [
        "amend",
        "amended",
        "amendment",
        "modified",
        "changed",
        "update"
    ]):
        return {
            "intent": "amendment_query",
            "act": detected_act,
            "section": None,
            "jurisdiction": detected_jurisdiction,
        }

    # Definition Queries
    if any(word in q for word in [
        "define",
        "definition",
        "what is",
        "meaning of"
    ]):
        return {
            "intent": "definition_query",
            "act": detected_act,
            "section": None,
            "jurisdiction": detected_jurisdiction,
        }

    # Comparison Queries
    if any(word in q for word in [
        "difference between",
        "compare",
        "distinction"
    ]):
        return {
            "intent": "comparison_query",
            "act": detected_act,
            "section": None,
            "jurisdiction": detected_jurisdiction,
        }

    # Explanation / Interpretation
    if any(word in q for word in [
        "explain",
        "describe",
        "interpret",
        "analysis"
    ]):
        return {
            "intent": "explanatory",
            "act": detected_act,
            "section": None,
            "jurisdiction": detected_jurisdiction,
        }

    # Fallback Semantic Query
    return {
        "intent": "semantic",
        "act": detected_act,
        "section": None,
        "jurisdiction": detected_jurisdiction,
    }
