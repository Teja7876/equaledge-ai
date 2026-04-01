import json
import os
import shutil
from typing import List

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


SECONDARY_FILES = [
    "advanced_qa.json",
    "category_lookup.json",
    "definitions_verbatim.json",
    "governance_and_grievance.json",
    "offences_and_penalties.json",
    "reservation_logic_expanded.json"
]

BASE_PATH = "data/domains/legal/"
PERSIST_DIR = "chroma_secondary"
COLLECTION_NAME = "statutory_secondary"


def flatten_json(obj, parent_key=""):
    """
    Recursively extract text from nested JSON structures.
    Returns list of string values.
    """
    texts = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            texts.extend(flatten_json(v, k))
    elif isinstance(obj, list):
        for item in obj:
            texts.extend(flatten_json(item, parent_key))
    elif isinstance(obj, str):
        cleaned = obj.strip()
        if len(cleaned) > 20:
            texts.append(cleaned)

    return texts


def load_secondary_documents() -> List[Document]:
    documents = []

    for filename in SECONDARY_FILES:
        path = os.path.join(BASE_PATH, filename)

        if not os.path.exists(path):
            print(f"Skipping missing file: {filename}")
            continue

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        extracted_texts = flatten_json(data)

        for text in extracted_texts:
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "layer": "secondary",
                        "source": filename
                    }
                )
            )

    return documents


def rebuild_collection():
    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR)


def build_secondary_index():
    print("Loading secondary documents...")
    docs = load_secondary_documents()
    print(f"Total extracted text blocks: {len(docs)}")

    if not docs:
        print("No secondary documents found.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=120
    )

    chunked_docs = splitter.split_documents(docs)
    print(f"Total secondary chunks created: {len(chunked_docs)}")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    rebuild_collection()

    Chroma.from_documents(
        documents=chunked_docs,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME
    )

    print("Secondary index built successfully.")


if __name__ == "__main__":
    build_secondary_index()
