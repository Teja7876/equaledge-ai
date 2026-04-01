import json
import os
import shutil
from typing import List

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


COMMENTARY_FOLDER = "data/domains/legal/commentary/"
PERSIST_DIR = "chroma_commentary"
COLLECTION_NAME = "statutory_commentary"


def extract_text(obj):
    blocks = []

    if isinstance(obj, dict):
        for value in obj.values():
            blocks.extend(extract_text(value))

    elif isinstance(obj, list):
        for item in obj:
            blocks.extend(extract_text(item))

    elif isinstance(obj, str):
        cleaned = obj.strip()
        if len(cleaned) > 30:
            blocks.append(cleaned)

    return blocks


def load_documents() -> List[Document]:
    documents = []

    if not os.path.exists(COMMENTARY_FOLDER):
        print("Commentary folder not found.")
        return documents

    for filename in os.listdir(COMMENTARY_FOLDER):
        if not filename.endswith(".json"):
            continue

        path = os.path.join(COMMENTARY_FOLDER, filename)

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
                        "layer": "commentary",
                        "source": filename
                    }
                )
            )

    return documents


def rebuild():
    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR)


def build_index():
    print("Loading commentary documents...")
    docs = load_documents()
    print(f"Commentary raw blocks: {len(docs)}")

    if not docs:
        print("No commentary documents found.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120
    )

    chunks = splitter.split_documents(docs)
    print(f"Commentary chunks: {len(chunks)}")

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

    print("Commentary index built successfully.")


if __name__ == "__main__":
    build_index()
