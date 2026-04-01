import os
import json
import logging
import time
from typing import Dict, Any, Optional, Tuple

import requests
from requests.exceptions import RequestException
import redis

from src.legal_router import LegalRouter
from src.definitions_engine import DefinitionsEngine
from src.sections_engine import SectionsEngine
from src.rules_engine import RulesEngine
from src.citation_verifier import CitationVerifier
from src.legal_graph import LegalGraph


# ------------------------------------------------
# Configuration
# ------------------------------------------------

REQUEST_TIMEOUT = 15
MAX_EXTRACT_LENGTH = 4000
CACHE_TTL_SECONDS = 300
MAX_SECTIONS_TO_MERGE = 5

PROVIDER_PRIORITY = os.getenv(
    "PROVIDER_PRIORITY",
    "gemini,ollama"
).lower().split(",")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ------------------------------------------------
# Legal Answer Engine
# ------------------------------------------------

class LegalAnswerEngine:

    def __init__(self):

        self.router = LegalRouter()
        self.definitions_engine = DefinitionsEngine()
        self.sections_engine = SectionsEngine()
        self.rules_engine = RulesEngine()
        self.citation_verifier = CitationVerifier()
        self.legal_graph = LegalGraph()

        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
            logger.info("Redis cache enabled")

        except Exception as e:
            logger.warning("Redis unavailable: %s", e)
            self.redis_client = None


    # ------------------------------------------------
    # Utilities
    # ------------------------------------------------

    def _normalize_query(self, query: str) -> str:
        return " ".join(query.strip().lower().split())


    def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:

        if not self.redis_client:
            return None

        try:
            cached = self.redis_client.get(key)

            if cached:
                logger.info("Redis cache hit")
                return json.loads(cached)

        except Exception as e:
            logger.warning("Redis read failed: %s", e)

        return None


    def _set_cache(self, key: str, value: Dict[str, Any]) -> None:

        if not self.redis_client:
            return

        try:
            self.redis_client.setex(
                key,
                CACHE_TTL_SECONDS,
                json.dumps(value)
            )

        except Exception as e:
            logger.warning("Redis write failed: %s", e)


    # ------------------------------------------------
    # Prompt Builder
    # ------------------------------------------------

    def _build_prompt(self, query: str, text: str, citations: str) -> str:

        trimmed = text[:MAX_EXTRACT_LENGTH]

        return f"""
You are a statutory legal assistant.

Rules:
- Use ONLY the provided statutory extracts.
- Do NOT use external knowledge.
- Cite sections precisely.
- If extracts do not clearly answer the question, say so explicitly.

User Question:
{query}

Statutory Extracts:
{trimmed}

Citations:
{citations}

Provide a clear and legally precise answer.
"""


    # ------------------------------------------------
    # HTTP Helper
    # ------------------------------------------------

    def _safe_post(self, url: str, headers=None, json=None) -> Optional[dict]:

        try:
            response = requests.post(
                url,
                headers=headers,
                json=json,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code != 200:
                logger.warning("Provider HTTP %s", response.status_code)
                return None

            return response.json()

        except RequestException as e:
            logger.warning("Provider request failed: %s", e)
            return None


    # ------------------------------------------------
    # LLM Providers
    # ------------------------------------------------

    def _call_gemini(self, prompt: str) -> Optional[str]:

        if not GEMINI_API_KEY:
            logger.warning("Gemini API key missing")
            return None

        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024
            }
        }

        data = self._safe_post(endpoint, json=payload)

        if not data:
            return None

        candidates = data.get("candidates", [])

        if not candidates:
            return None

        parts = candidates[0].get("content", {}).get("parts", [])

        return parts[0].get("text") if parts else None


    def _call_ollama(self, prompt: str) -> Optional[str]:

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }

        data = self._safe_post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload
        )

        return data.get("response") if data else None


    # ------------------------------------------------
    # Provider Router
    # ------------------------------------------------

    def _generate_answer(self, prompt: str) -> Tuple[Optional[str], Optional[str]]:

        for provider in PROVIDER_PRIORITY:

            provider = provider.strip()

            logger.info("Trying provider: %s", provider)

            if provider == "gemini":
                result = self._call_gemini(prompt)

            elif provider == "ollama":
                result = self._call_ollama(prompt)

            else:
                continue

            if result:
                logger.info("Provider %s succeeded", provider)
                return result.strip(), provider

        return None, None


    # ------------------------------------------------
    # Public Method
    # ------------------------------------------------

    def answer(self, query: str) -> Dict[str, Any]:

        start = time.time()

        normalized_query = self._normalize_query(query)

        # ------------------------------------------------
        # Cache
        # ------------------------------------------------

        cached = self._get_cached(normalized_query)

        if cached:
            cached["response_time"] = round(time.time() - start, 3)
            return cached


        # ------------------------------------------------
        # Definitions Engine
        # ------------------------------------------------

        definition = self.definitions_engine.search(query)

        if definition:

            definition["response_time"] = round(time.time() - start, 3)

            self._set_cache(normalized_query, definition)

            return definition


        # ------------------------------------------------
        # Sections Engine + Legal Graph
        # ------------------------------------------------

        section = self.sections_engine.search(query)

        if section:

            related = self.legal_graph.get_related_sections(section["citation"])

            if related:
                section["related_sections"] = related

            section["response_time"] = round(time.time() - start, 3)

            self._set_cache(normalized_query, section)

            return section


        # ------------------------------------------------
        # Rules Engine
        # ------------------------------------------------

        rule = self.rules_engine.search(query)

        if rule:

            rule["response_time"] = round(time.time() - start, 3)

            self._set_cache(normalized_query, rule)

            return rule


        # ------------------------------------------------
        # Vector RAG Search
        # ------------------------------------------------

        results = self.router.search(query)

        if not results:

            response = {
                "answer": "No relevant statutory material found.",
                "confidence": "Low",
                "citation": None,
                "provider": None
            }

            self._set_cache(normalized_query, response)

            response["response_time"] = round(time.time() - start, 3)

            return response


        top = results[:MAX_SECTIONS_TO_MERGE]

        merged_text = "\n\n---\n\n".join(
            r["text"] for r in top if r.get("text")
        )

        citations = sorted({
            r["citation"] for r in top if r.get("citation")
        })

        merged_citations = "; ".join(citations) if citations else "N/A"


        prompt = self._build_prompt(
            query,
            merged_text,
            merged_citations
        )


        # ------------------------------------------------
        # LLM Reasoning
        # ------------------------------------------------

        model_answer, provider_used = self._generate_answer(prompt)

        if not model_answer:

            logger.warning("LLM failed, using fallback extract")

            model_answer = merged_text[:2000]

            provider_used = "fallback"


        # ------------------------------------------------
        # Citation Verification
        # ------------------------------------------------

        verified = self.citation_verifier.verify(model_answer)

        if not verified:

            logger.warning("Citation verification failed")

            model_answer = merged_text[:2000]

            provider_used = "verified_fallback"


        response = {
            "answer": model_answer,
            "confidence": "Moderate",
            "citation": merged_citations,
            "provider": provider_used
        }

        self._set_cache(normalized_query, response)

        response["response_time"] = round(time.time() - start, 3)

        return response