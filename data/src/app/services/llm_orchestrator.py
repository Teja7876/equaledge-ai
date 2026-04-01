import os
import requests
from typing import Optional, Dict, Any, List


# ---------------------------------------------------
# Environment Configuration
# ---------------------------------------------------

PRIMARY_PROVIDER = os.getenv("PRIMARY_PROVIDER", "ollama").strip().lower()

PROVIDER_PRIORITY = os.getenv(
    "PROVIDER_PRIORITY",
    "ollama,gemini"
)

PROVIDER_LIST: List[str] = [
    p.strip().lower()
    for p in PROVIDER_PRIORITY.split(",")
    if p.strip()
]

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "40"))

MAX_RESPONSE_CHARS = 8000  # Safety guard


# ---------------------------------------------------
# LLM Orchestrator (Strict Grounded)
# ---------------------------------------------------

class LLMOrchestrator:

    def __init__(self):
        self.providers = PROVIDER_LIST if PROVIDER_LIST else [PRIMARY_PROVIDER]

    # ---------------------------------------------------
    # Public Interface
    # ---------------------------------------------------

    def generate(
        self,
        mode: str,
        query: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        mode:
            - "qa"
            - "reasoning"

        STRICT RULE:
            LLM is only called if quoted_text exists.
        """

        if mode not in ("qa", "reasoning"):
            return None

        if not self._valid_context(context):
            return None

        for provider in self.providers:
            try:
                response = self._call_provider(provider, mode, query, context)
                if response:
                    cleaned = response.strip()
                    if cleaned:
                        return {
                            "llm_response": cleaned[:MAX_RESPONSE_CHARS],
                            "provider": provider
                        }
            except Exception:
                # Fail quietly and try next provider
                continue

        return None

    # ---------------------------------------------------
    # Context Validation
    # ---------------------------------------------------

    def _valid_context(self, context: Dict[str, Any]) -> bool:
        if not context:
            return False
        if not context.get("quoted_text"):
            return False
        if not context.get("section"):
            return False
        return True

    # ---------------------------------------------------
    # Provider Router
    # ---------------------------------------------------

    def _call_provider(
        self,
        provider: str,
        mode: str,
        query: str,
        context: Dict[str, Any]
    ) -> Optional[str]:

        provider = provider.lower()

        if provider == "ollama":
            return self._call_ollama(mode, query, context)

        if provider == "gemini":
            return self._call_gemini(mode, query, context)

        return None

    # ---------------------------------------------------
    # Ollama (Local LLM)
    # ---------------------------------------------------

    def _call_ollama(
        self,
        mode: str,
        query: str,
        context: Dict[str, Any]
    ) -> Optional[str]:

        url = f"{OLLAMA_BASE_URL}/api/generate"

        prompt = self._build_prompt(mode, query, context)

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=LLM_TIMEOUT
            )
        except requests.RequestException:
            return None

        if response.status_code != 200:
            return None

        try:
            data = response.json()
        except ValueError:
            return None

        return data.get("response")

    # ---------------------------------------------------
    # Gemini (Stub — Wire API Later)
    # ---------------------------------------------------

    def _call_gemini(
        self,
        mode: str,
        query: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        # Add Gemini API implementation here later
        return None

    # ---------------------------------------------------
    # Strict Grounded Prompt Builder
    # ---------------------------------------------------

    def _build_prompt(
        self,
        mode: str,
        query: str,
        context: Dict[str, Any]
    ) -> str:

        base_prompt = f"""
You are a legal assistant.

STRICT RULES:
1. You must use ONLY the provided legal text.
2. You are NOT allowed to invent, extend, or assume any law.
3. If the answer is not clearly contained in the quoted section,
   respond exactly with:
   "The provided legal section does not directly address this question."

LEGAL CONTEXT:
Section: {context.get('section')}
Heading: {context.get('heading')}

Quoted Law:
\"\"\"{context.get('quoted_text')}\"\"\"

USER QUESTION:
{query}
"""

        if mode == "qa":
            base_prompt += "\nExplain the answer in simple and clear language strictly based on the quoted law."

        elif mode == "reasoning":
            base_prompt += "\nProvide structured legal reasoning and interpretation strictly grounded in the quoted law."

        return base_prompt.strip()
