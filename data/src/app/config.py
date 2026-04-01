import os

API_KEY = os.getenv("API_KEY", "change_this")
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-large-en-v1.5")

TOP_K = 5

FAISS_INDEX = "vector_store/faiss.index"
METADATA_FILE = "vector_store/metadata.json"
