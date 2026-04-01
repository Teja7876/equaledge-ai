import os
import json
import re
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# ==========================
# CONFIG
# ==========================

DATA_PATH = "data"
COLLECTION_NAME = "statutory_core"
DB_PATH = "vector_store"

MIN_TEXT_LENGTH = 40
MAX_TEXT_LENGTH = 5000

# ==========================
# EMBEDDING
# ==========================

embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

# ==========================
# HELPERS
# ==========================

def extract_section_anchor(text):
    match = re.search(r'\b\d{1,3}\.', text)
    return match.group(0) if match else None


def flatten_json(data, parent_key=""):
    items = []

    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            items.extend(flatten_json(value, new_key))

    elif isinstance(data, list):
        for index, value in enumerate(data):
            new_key = f"{parent_key}[{index}]"
            items.extend(flatten_json(value, new_key))

    elif isinstance(data, str):
        clean_text = data.strip()
        if MIN_TEXT_LENGTH <= len(clean_text) <= MAX_TEXT_LENGTH:
            items.append((parent_key, clean_text))

    return items


# ==========================
# MAIN INDEXING
# ==========================

def build_index():

    # Clear previous collection
    try:
        existing_db = Chroma(
            persist_directory=DB_PATH,
            collection_name=COLLECTION_NAME,
            embedding_function=embedding
        )
        existing_db.delete_collection()
        print("Existing collection cleared.")
    except Exception:
        print("No previous collection found. Creating new one.")

    documents = []

    for root, dirs, files in os.walk(DATA_PATH):

        if not ("domains/legal" in root or "disability_categories" in root):
            continue

        for file in files:

            if not file.endswith(".json"):
                continue

            path = os.path.join(root, file)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            flattened_items = flatten_json(data)

            for key_path, text in flattened_items:

                if any(meta in key_path.lower() for meta in [
                    "canonical_id",
                    "verification_status",
                    "publication_date",
                    "last_verified_date"
                ]):
                    continue

                section_anchor = extract_section_anchor(text)

                doc = Document(
                    page_content=text,
                    metadata={
                        "source_file": path,
                        "json_path": key_path,
                        "section_anchor": section_anchor,
                        "collection_layer": "statutory_core"
                    }
                )

                documents.append(doc)

    print("Total documents prepared:", len(documents))

    if not documents:
        print("No documents found. Check filtering logic.")
        return

    Chroma.from_documents(
        documents=documents,
        embedding=embedding,
        persist_directory=DB_PATH,
        collection_name=COLLECTION_NAME
    )

    print("Statutory core index built successfully.")


if __name__ == "__main__":
    build_index()
