import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from app.config import EMBED_MODEL, FAISS_INDEX, METADATA_FILE, TOP_K

AUTHORITY_DEFAULT = 1.0


class HybridRetriever:
    def __init__(self, data_path="data"):
        self.data_path = data_path
        self.model = SentenceTransformer(EMBED_MODEL)
        self.top_k = TOP_K

        if os.path.exists(FAISS_INDEX) and os.path.exists(METADATA_FILE):
            try:
                self._load_index()
            except Exception:
                print("Index corrupted. Rebuilding...")
                self._build_index()
        else:
            self._build_index()

    # -----------------------------
    # Extract meaningful text only
    # -----------------------------
    def _extract_text(self, data):
        """
        Extracts only meaningful textual content
        instead of embedding raw JSON structure.
        """
        text_parts = []

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and len(value.strip()) > 20:
                    text_parts.append(value.strip())
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and len(item.strip()) > 20:
                            text_parts.append(item.strip())

        return "\n".join(text_parts)

    # -----------------------------
    # Collect documents
    # -----------------------------
    def _collect_documents(self):
        docs = []

        for root, _, files in os.walk(self.data_path):
            for file in files:
                if not file.endswith(".json"):
                    continue

                path = os.path.join(root, file)

                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    continue

                if isinstance(data, dict) and "content_chunks" in data:
                    for chunk in data["content_chunks"]:
                        if isinstance(chunk, str) and len(chunk.strip()) > 20:
                            docs.append({
                                "text": chunk.strip(),
                                "authority_weight": float(
                                    data.get("authority_weight", AUTHORITY_DEFAULT)
                                ),
                                "source_type": data.get("source_type"),
                                "gazette_id": data.get("gazette_id"),
                                "file": file
                            })

                elif isinstance(data, dict):
                    extracted_text = self._extract_text(data)

                    if extracted_text:
                        docs.append({
                            "text": extracted_text,
                            "authority_weight": float(
                                data.get("authority_weight", AUTHORITY_DEFAULT)
                            ),
                            "source_type": data.get("source_type"),
                            "gazette_id": None,
                            "file": file
                        })

        if not docs:
            raise ValueError("No valid documents found in dataset.")

        return docs

    # -----------------------------
    # Build FAISS index
    # -----------------------------
    def _build_index(self):
        print("Building FAISS index...")

        self.documents = self._collect_documents()
        texts = [d["text"] for d in self.documents]

        embeddings = self.model.encode(texts, show_progress_bar=True)
        embeddings = np.array(embeddings).astype("float32")

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)

        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)

        faiss.write_index(self.index, FAISS_INDEX)

        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.documents, f)

        self.bm25 = BM25Okapi([t.split() for t in texts])

        print("Index built successfully.")

    # -----------------------------
    # Load index
    # -----------------------------
    def _load_index(self):
        print("Loading existing FAISS index...")

        self.index = faiss.read_index(FAISS_INDEX)

        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        texts = [d["text"] for d in self.documents]
        self.bm25 = BM25Okapi([t.split() for t in texts])

        print("Index loaded successfully.")

    # -----------------------------
    # Hybrid Search
    # -----------------------------
    def search(self, query):
        if not query.strip():
            return []

        # Semantic search
        q_embed = self.model.encode([query])
        q_embed = np.array(q_embed).astype("float32")
        faiss.normalize_L2(q_embed)

        sem_scores, sem_indices = self.index.search(q_embed, self.top_k)

        # Keyword search
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # Normalize BM25
        max_bm25 = max(bm25_scores) if len(bm25_scores) > 0 else 1.0
        if max_bm25 == 0:
            max_bm25 = 1.0

        results = []

        for rank, idx in enumerate(sem_indices[0]):
            semantic_score = float(sem_scores[0][rank])

            keyword_score = float(bm25_scores[idx]) / max_bm25

            authority = float(
                self.documents[idx].get("authority_weight", AUTHORITY_DEFAULT)
            )

            # Normalize authority (assuming typical range 0–5)
            authority_norm = min(authority / 5.0, 1.0)

            final_score = (
                0.5 * semantic_score +
                0.3 * keyword_score +
                0.2 * authority_norm
            )

            result_doc = self.documents[idx].copy()
            result_doc.update({
                "semantic_score": semantic_score,
                "keyword_score": keyword_score,
                "authority_score": authority_norm,
                "final_score": final_score
            })

            results.append(result_doc)

        results.sort(key=lambda x: x["final_score"], reverse=True)

        return results[:self.top_k]
