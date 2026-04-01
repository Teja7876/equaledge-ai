from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

emb = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = Chroma(
    persist_directory="definitions_db",
    embedding_function=emb
)

query = "reservation for persons with disabilities in education"

results = db.similarity_search(query, k=5)

for r in results:
    print("-----")
    print("SOURCE:", r.metadata.get("source"))
    print(r.page_content[:500])
    print()
