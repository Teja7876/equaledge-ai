from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

PERSIST_DIR = "chroma_primary"
COLLECTION_NAME = "statutory_primary"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = Chroma(
    persist_directory=PERSIST_DIR,
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME
)

query = "Section 34 reservation in government establishments"

results = db.similarity_search(query, k=3)

for i, r in enumerate(results, 1):
    print(f"\nResult {i}")
    print("Metadata:", r.metadata)
    print("Preview:", r.page_content[:400])
