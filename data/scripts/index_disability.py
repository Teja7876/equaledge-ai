import json
import os
import shutil
from typing import List

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Folder containing only disability-specific category files
DISABILITY_FOLDER = "data/domains/legal/disability_specific/"

# Chroma settings
PERSIST_DIR = "chroma_disability"
COLLECTION_NAME = "statutory_disability"


def extract_text(obj):
    """
    Recursively extract meaningful text blocks from JSON.
    """
    blocks = []

    if isinstance(obj, dict):
        for value in obj.values():
            blocks.extend(extract_text(value))

    elif isinstance(obj, list):
        for item in obj:
            blocks.extend(extract_text(item))

    elif isinstance(obj, str):
        cleaned = obj.strip()
        if len(cleaned) > 30:  # ignore tiny fragments
            blocks.append(cleaned)

    return blocks


def load_documents() -> List[Document]:
    documents = []

    if not os.path.exists(DISABILITY_FOLDER):
        print("Disability folder not found.")
        return documents

    for filename in os.listdir(DISABILITY_FOLDER):
        if not filename.endswith(".json"):
            continue

        path = os.path.join(DISABILITY_FOLDER, filename)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Skipping {filename} due to error: {e}")
            continue

        blocks = extract_text(data)

        for block in blocks:
            documents.append(
                Document(
                    page_content=block,
                    metadata={
                        "layer": "disability_specific",
                        "source": filename
                    }
                )
            )

    return documents


def rebuild():
    """
    Remove existing Chroma directory before rebuilding.
    """
    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR)


def build_index():
    print("Loading disability-specific documents...")
    docs = load_documents()
    print(f"Disability raw blocks: {len(docs)}")

    if not docs:
        print("No disability documents found.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(docs)
    print(f"Disability chunks: {len(chunks)}")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    rebuild()

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME
    )

    print("Disability index built successfully.")


if __name__ == "__main__":
    build_index()
