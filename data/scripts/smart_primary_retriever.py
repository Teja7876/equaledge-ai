import re
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


PERSIST_DIR = "chroma_primary"
COLLECTION_NAME = "statutory_primary"


class SmartPrimaryRetriever:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.db = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=self.embeddings,
            collection_name=COLLECTION_NAME
        )

    def detect_section_number(self, query: str):
        match = re.search(r'section\s+(\d+)', query, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def deterministic_fetch(self, section_number: str, k=3):
        """
        Direct metadata-based retrieval (no embeddings involved)
        """
        return self.db.get(
            where={"section": section_number}
        )

    def semantic_search(self, query: str, k=3):
        return self.db.similarity_search(query, k=k)

    def search(self, query: str, k=3):
        section_number = self.detect_section_number(query)

        if section_number:
            print(f"[Deterministic Fetch] Section {section_number}")
            results = self.deterministic_fetch(section_number)
            
            # Convert raw get() result to similar format
            documents = []
            for doc, meta in zip(results["documents"], results["metadatas"]):
                documents.append({
                    "content": doc,
                    "metadata": meta
                })
            return documents

        print("[Semantic Search]")
        docs = self.semantic_search(query, k=k)

        return [
            {
                "content": d.page_content,
                "metadata": d.metadata
            }
            for d in docs
        ]


if __name__ == "__main__":
    retriever = SmartPrimaryRetriever()

    query = "Section 34 reservation in government establishments"
    results = retriever.search(query)

    for i, r in enumerate(results, 1):
        print(f"\nResult {i}")
        print("Metadata:", r["metadata"])
        print("Preview:", r["content"][:400])
