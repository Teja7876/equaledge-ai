from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

db = Chroma(
    persist_directory="vector_store",
    collection_name="statutory_core",
    embedding_function=embedding
)

# DO NOT FILTER
results = db.similarity_search(
    "What is Section 34 reservation under RPwD Act?",
    k=5
)

for doc in results:
    print("-----")
    print("Source:", doc.metadata.get("source_file"))
    print("Section Anchor:", doc.metadata.get("section_anchor"))
    print(doc.page_content[:500])
    print()
