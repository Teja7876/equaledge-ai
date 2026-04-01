import json
import os
import shutil
from typing import List

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ==============================
# CONFIGURATION
# ==============================

RPWD_PATH = "data/domains/legal/RPWD_2016_FULL_ACT_STRUCTURED.json"
CONSTITUTION_PATH = "data/core/constitution_disability_core.json"

PERSIST_DIR = "chroma_primary"
COLLECTION_NAME = "statutory_primary"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ==============================
# LOAD RPWD ACT
# ==============================

def load_rpwd_documents() -> List[Document]:
    with open(RPWD_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    sections = data.get("sections", [])
    documents = []

    for section in sections:
        section_number = section.get("section_number", "")
        heading = section.get("section_heading", "")
        text = section.get("section_text", "")

        full_text = f"Section {section_number}: {heading}\n\n{text}"

        documents.append(
            Document(
                page_content=full_text,
                metadata={
                    "layer": "primary",
                    "source": "RPwD Act, 2016",
                    "authority_level": "Statutory",
                    "section": section_number,
                    "heading": heading,
                    "weight": 1.0
                }
            )
        )

    return documents


# ==============================
# LOAD CONSTITUTION CORE
# ==============================

def load_constitution_documents() -> List[Document]:
    with open(CONSTITUTION_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = []

    for article in data:
        article_number = article.get("article", "")
        title = article.get("title", "")
        text = article.get("text", "")
        relevance = article.get("disability_relevance", "Contextual")
        weight = article.get("weight", 0.5)

        full_text = f"{article_number}: {title}\n\n{text}"

        documents.append(
            Document(
                page_content=full_text,
                metadata={
                    "layer": "primary",
                    "source": "Constitution of India",
                    "authority_level": "Constitutional",
                    "article": article_number,
                    "title": title,
                    "disability_relevance": relevance,
                    "weight": weight
                }
            )
        )

    return documents


# ==============================
# REBUILD COLLECTION
# ==============================

def rebuild_collection():
    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR)


# ==============================
# BUILD PRIMARY INDEX
# ==============================

def build_primary_index():

    print("Loading RPwD Act documents...")
    rpwd_docs = load_rpwd_documents()
    print(f"RPwD sections loaded: {len(rpwd_docs)}")

    print("Loading Constitution disability core...")
    constitution_docs = load_constitution_documents()
    print(f"Constitution articles loaded: {len(constitution_docs)}")

    all_docs = rpwd_docs + constitution_docs
    print(f"Total documents before chunking: {len(all_docs)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150
    )

    chunked_docs = splitter.split_documents(all_docs)
    print(f"Total chunks created: {len(chunked_docs)}")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL
    )

    rebuild_collection()

    db = Chroma.from_documents(
        documents=chunked_docs,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME
    )


    print("Primary statutory index built successfully.")


# ==============================
# ENTRY POINT
# ==============================

if __name__ == "__main__":
    build_primary_index()
