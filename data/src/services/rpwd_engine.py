from typing import Dict, Optional, List
import re

# ------------------------------------------------
# RPwD Legal Knowledge Base
# ------------------------------------------------

RPWD_SECTIONS: Dict[str, Dict[str, object]] = {

    "reservation_jobs": {
        "section": "Section 34",
        "title": "Reservation in Government Employment",
        "intent": "employment",
        "keywords": [
            "reservation", "job reservation", "employment reservation",
            "government job", "quota", "job quota",
            "employment quota", "government employment",
            "work reservation", "public sector jobs"
        ],
        "text": (
            "The Rights of Persons with Disabilities Act 2016 mandates a minimum "
            "of four percent reservation in government employment for persons "
            "with benchmark disabilities."
        ),
    },

    "inclusive_education": {
        "section": "Section 16",
        "title": "Inclusive Education",
        "intent": "education",
        "keywords": [
            "education", "school", "college", "university",
            "students with disabilities", "inclusive education",
            "education support", "education rights",
            "disabled students", "school access"
        ],
        "text": (
            "Educational institutions funded or recognized by the government "
            "must provide inclusive education and appropriate support to "
            "students with disabilities."
        ),
    },

    "non_discrimination_education": {
        "section": "Section 17",
        "title": "Non-Discrimination in Education",
        "intent": "discrimination",
        "keywords": [
            "education discrimination",
            "school discrimination",
            "deny admission",
            "reject student",
            "discrimination in school",
            "education equality",
            "school rights"
        ],
        "text": (
            "No educational institution shall discriminate against any student "
            "on the ground of disability."
        ),
    },

    "reasonable_accommodation": {
        "section": "Section 2(y)",
        "title": "Reasonable Accommodation",
        "intent": "accommodation",
        "keywords": [
            "reasonable accommodation",
            "adjustment",
            "modification",
            "assistive support",
            "workplace accommodation",
            "support adjustment",
            "assistive services",
            "support modification"
        ],
        "text": (
            "Reasonable accommodation means necessary and appropriate "
            "modifications or adjustments ensuring persons with disabilities "
            "can enjoy rights equally with others."
        ),
    },

    "equality_non_discrimination": {
        "section": "Section 3",
        "title": "Equality and Non-Discrimination",
        "intent": "rights",
        "keywords": [
            "equality",
            "equal rights",
            "equal opportunity",
            "disability rights",
            "legal protection",
            "rights law",
            "human rights",
            "disability protection"
        ],
        "text": (
            "Persons with disabilities have the right to equality, dignity, "
            "and protection against discrimination."
        ),
    },

    "research_training": {
        "section": "Section 39",
        "title": "Research and Training",
        "intent": "research",
        "keywords": [
            "research",
            "training",
            "rehabilitation training",
            "disability research",
            "rehabilitation research"
        ],
        "text": (
            "The government shall promote research and training in disability "
            "rehabilitation and related fields."
        ),
    },

    "accessibility_ict": {
        "section": "Section 42",
        "title": "Accessible Information and Communication Technology",
        "intent": "technology",
        "keywords": [
            "accessible technology",
            "accessible website",
            "digital accessibility",
            "assistive technology",
            "screen reader",
            "online accessibility",
            "digital platform accessibility"
        ],
        "text": (
            "The government must ensure that information and communication "
            "technology is accessible to persons with disabilities."
        ),
    },

    "barrier_free_buildings": {
        "section": "Section 46",
        "title": "Barrier-Free Access in Public Buildings",
        "intent": "accessibility",
        "keywords": [
            "wheelchair access",
            "accessible building",
            "barrier free",
            "accessible infrastructure",
            "ramps",
            "public building access",
            "building accessibility",
            "transport accessibility"
        ],
        "text": (
            "Public buildings and infrastructure must be made accessible "
            "to persons with disabilities."
        ),
    },
}

# ------------------------------------------------
# Synonyms
# ------------------------------------------------

SYNONYMS = {
    "pwd": "persons with disabilities",
    "disabled": "persons with disabilities",
    "handicapped": "persons with disabilities",
    "blind": "visual impairment",
    "deaf": "hearing impairment",
    "wheelchair": "mobility disability",
    "quota": "reservation",
    "govt": "government",
}

# ------------------------------------------------
# Disability Concept Mapping
# ------------------------------------------------

DISABILITY_CONCEPTS = {

    "visual_impairment": [
        "blind", "visually impaired", "low vision"
    ],

    "hearing_impairment": [
        "deaf", "hard of hearing", "hearing loss"
    ],

    "mobility_disability": [
        "wheelchair", "mobility disability",
        "locomotor disability"
    ],

    "intellectual_disability": [
        "intellectual disability",
        "mental disability",
        "developmental disability"
    ],

    "autism": [
        "autism", "autistic"
    ],

    "cerebral_palsy": [
        "cerebral palsy"
    ]
}

# ------------------------------------------------
# Intent Keywords
# ------------------------------------------------

INTENT_KEYWORDS = {

    "employment": ["job", "employment", "work", "career"],

    "education": [
        "education", "school", "college",
        "university", "student"
    ],

    "discrimination": [
        "discrimination", "deny", "reject",
        "refuse admission"
    ],

    "accommodation": [
        "accommodation", "adjustment",
        "modification", "support"
    ],

    "accessibility": [
        "accessible", "wheelchair",
        "barrier", "infrastructure"
    ],

    "technology": [
        "technology", "website",
        "digital", "software"
    ],

    "research": [
        "research", "training",
        "rehabilitation"
    ],

    "rights": [
        "rights", "law",
        "legal protection", "equality"
    ]
}

# ------------------------------------------------
# Text Normalization
# ------------------------------------------------

def normalize_question(text: str) -> str:

    text = text.lower().strip()

    text = re.sub(r"[^\w\s]", " ", text)

    for k, v in SYNONYMS.items():
        text = text.replace(k, v)

    text = re.sub(r"\s+", " ", text)

    return text


# ------------------------------------------------
# Disability Concept Detection
# ------------------------------------------------

def detect_disability_concepts(question: str) -> List[str]:

    concepts = []

    for concept, words in DISABILITY_CONCEPTS.items():

        for word in words:

            if word in question:
                concepts.append(concept)

    return concepts


# ------------------------------------------------
# Intent Detection
# ------------------------------------------------

def detect_intent(question: str) -> Optional[str]:

    for intent, keywords in INTENT_KEYWORDS.items():

        for keyword in keywords:

            if keyword in question:
                return intent

    return None


# ------------------------------------------------
# Section Detection
# ------------------------------------------------

def detect_section(question: str) -> Optional[Dict[str, object]]:

    q = normalize_question(question)

    intent = detect_intent(q)

    disability_concepts = detect_disability_concepts(q)

    best_section = None
    best_score = 0

    for section in RPWD_SECTIONS.values():

        score = 0

        if intent and section["intent"] == intent:
            score += 6

        if disability_concepts:
            score += 2

        for keyword in section["keywords"]:

            if keyword in q:
                score += 3

        if score > best_score:
            best_score = score
            best_section = section

    return best_section


# ------------------------------------------------
# Answer Generator
# ------------------------------------------------

def generate_rpwd_answer(question: str) -> Dict[str, str]:

    section = detect_section(question)

    if not section:

        return {
            "answer": (
                "The question could not be mapped to a specific section of the "
                "Rights of Persons with Disabilities Act 2016."
            ),
            "source": "RPwD Act 2016",
        }

    return {
        "answer": f"{section['title']} ({section['section']}): {section['text']}",
        "source": "Rights of Persons with Disabilities Act 2016",
    }