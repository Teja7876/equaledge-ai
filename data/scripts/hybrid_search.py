import re
from typing import List, Tuple
from rapidfuzz import fuzz
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# ==========================
# CONFIGURATION
# ==========================

DB_PATH = "definitions_db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# ==========================
# INITIALIZE VECTOR STORE
# ==========================

embedding = HuggingFaceEmbeddings(
    model_name=MODEL_NAME,
    model_kwargs={"device": "cpu"}
)

db = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embedding
)


# ==========================
# CLEAN TEXT
# ==========================

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ==========================
# HYBRID SEARCH
# ==========================

def hybrid_search(query: str, k: int = 10) -> List[Tuple]:
    """
    Hybrid search combining:
    - Vector similarity
    - Exact keyword match
    - Fuzzy match
    """

    query_norm = normalize(query)

    # Step 1 — Vector search (get larger pool)
    vector_results = db.similarity_search_with_score(query, k=50)

    scored_results = []

    for doc, vector_score in vector_results:

        text = normalize(doc.page_content)

        # Convert distance to similarity score
        semantic_score = 1 - vector_score

        # Exact keyword boost
        keyword_boost = 0
        for word in query_norm.split():
            if word in text:
                keyword_boost += 0.05

        # Exact phrase boost
        if query_norm in text:
            keyword_boost += 0.2

        # Fuzzy boost
        fuzzy_score = fuzz.partial_ratio(query_norm, text) / 100
        fuzzy_boost = fuzzy_score * 0.2

        # Final combined score
        final_score = semantic_score + keyword_boost + fuzzy_boost

        scored_results.append((doc, final_score))

    # Sort descending
    scored_results.sort(key=lambda x: x[1], reverse=True)

    return scored_results[:k]


# ==========================
# CLI EXECUTION
# ==========================

if __name__ == "__main__":
    query = input("Enter search query: ")

    results = hybrid_search(query, k=5)

    print("\nTop Results:\n")

    for doc, score in results:
        print("-----")
        print("Score:", round(score, 4))
        print("Source:", doc.metadata.get("source"))
        print(doc.page_content[:500])
        print()
