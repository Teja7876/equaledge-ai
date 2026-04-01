import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

import chromadb
from langchain_community.vectorstores import Chroma


# ------------------------------------------------
# Configuration
# ------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PRIMARY_DIR = os.path.join(BASE_DIR, "chroma", "primary")
SECONDARY_DIR = os.path.join(BASE_DIR, "chroma", "secondary")

PRIMARY_COLLECTION = "statutory_primary"
SECONDARY_COLLECTION = "statutory_secondary"

MAX_RESULTS = 5

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ------------------------------------------------
# Legal Router
# ------------------------------------------------

class LegalRouter:

    def __init__(self):

        logger.info("Initializing LegalRouter")

        try:

            if not os.path.exists(PRIMARY_DIR):
                raise FileNotFoundError(
                    f"Primary vector store missing: {PRIMARY_DIR}"
                )

            self.client = chromadb.Client()

            # Load primary database
            self.primary_db = Chroma(
                client=self.client,
                persist_directory=PRIMARY_DIR,
                collection_name=PRIMARY_COLLECTION
            )

            # Load secondary database if available
            if os.path.exists(SECONDARY_DIR):

                self.secondary_db = Chroma(
                    client=self.client,
                    persist_directory=SECONDARY_DIR,
                    collection_name=SECONDARY_COLLECTION
                )

            else:
                logger.warning("Secondary vector store not found")
                self.secondary_db = None

            logger.info("Vector databases loaded")

        except Exception as e:

            logger.error("Vector database initialization failed")
            logger.error(str(e))

            self.primary_db = None
            self.secondary_db = None


    # ------------------------------------------------
    # Detect Section Queries
    # ------------------------------------------------

    def detect_section(self, query: str) -> Optional[str]:

        match = re.search(r"\bsection\s+(\d+)\b", query, re.IGNORECASE)

        if match:
            return match.group(1)

        return None


    # ------------------------------------------------
    # Format semantic results
    # ------------------------------------------------

    def _format_results(
        self,
        results: List[Tuple[Any, float]]
    ) -> List[Dict[str, Any]]:

        formatted: List[Dict[str, Any]] = []

        for doc, distance in results:

            content = (doc.page_content or "").strip()

            if not content:
                continue

            formatted.append({
                "content": content,
                "metadata": doc.metadata or {},
                "distance": float(distance)
            })

        formatted.sort(key=lambda x: x["distance"])

        return formatted


    # ------------------------------------------------
    # Confidence scoring
    # ------------------------------------------------

    def _compute_confidence(self, distance: float) -> str:

        if distance == 0.0:
            return "Very High"

        if distance <= 0.40:
            return "High"

        if distance <= 0.75:
            return "Moderate"

        return "Low"


    # ------------------------------------------------
    # Format final answer
    # ------------------------------------------------

    def _format_answer(self, result: Dict[str, Any]) -> Dict[str, Any]:

        metadata = result.get("metadata", {})

        section = metadata.get("section", "Unknown")
        heading = metadata.get("heading", "")
        source = metadata.get("source", "")

        confidence = self._compute_confidence(result["distance"])

        return {
            "citation": f"Section {section}, {source}",
            "heading": heading,
            "confidence": confidence,
            "text": result["content"]
        }


    # ------------------------------------------------
    # Core Search Logic
    # ------------------------------------------------

    def search(self, query: str, k: int = 6) -> List[Dict[str, Any]]:

        logger.info("Query received: %s", query)

        if self.primary_db is None:

            logger.warning("Vector database unavailable")

            return [{
                "citation": "Unavailable",
                "heading": "",
                "confidence": "Low",
                "text": "Vector database unavailable."
            }]

        # --------------------------------------------
        # Deterministic section lookup
        # --------------------------------------------

        section_number = self.detect_section(query)

        if section_number:

            try:

                deterministic = self.primary_db.get(
                    where={"section": section_number}
                )

                docs = deterministic.get("documents", [])
                metas = deterministic.get("metadatas", [])

                results: List[Dict[str, Any]] = []

                for doc, meta in zip(docs, metas):

                    results.append({
                        "content": doc,
                        "metadata": meta,
                        "distance": 0.0
                    })

                if results:

                    logger.info("Section %s matched deterministically", section_number)

                    return [
                        self._format_answer(r)
                        for r in results[:MAX_RESULTS]
                    ]

            except Exception as e:

                logger.warning("Deterministic lookup failed: %s", str(e))


        # --------------------------------------------
        # Primary semantic search
        # --------------------------------------------

        try:

            semantic = self.primary_db.similarity_search_with_score(query, k=k)

            formatted = self._format_results(semantic)

            if formatted:

                return [
                    self._format_answer(r)
                    for r in formatted[:MAX_RESULTS]
                ]

        except Exception as e:

            logger.warning("Primary semantic search failed: %s", str(e))


        # --------------------------------------------
        # Secondary fallback search
        # --------------------------------------------

        if self.secondary_db:

            try:

                semantic = self.secondary_db.similarity_search_with_score(query, k=k)

                formatted = self._format_results(semantic)

                if formatted:

                    logger.info("Secondary database used as fallback")

                    return [
                        self._format_answer(r)
                        for r in formatted[:MAX_RESULTS]
                    ]

            except Exception as e:

                logger.warning("Secondary search failed: %s", str(e))


        # --------------------------------------------
        # Final fallback
        # --------------------------------------------

        return [{
            "citation": "Unavailable",
            "heading": "",
            "confidence": "Low",
            "text": "No relevant legal material found."
        }]