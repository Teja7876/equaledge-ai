import json
from pathlib import Path
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_DIR = "data"
DB_PATH = "definitions_db"


def is_table_like(data):
    if not isinstance(data, list) or not data:
        return False
    if not all(isinstance(row, dict) for row in data):
        return False
    first_keys = set(data[0].keys())
    return all(set(row.keys()) == first_keys for row in data)


def render_table(data, indent=0):
    lines = []
    prefix = "  " * indent

    headers = list(data[0].keys())
    lines.append(prefix + "TABLE:")
    lines.append(prefix + " | ".join(headers))
    lines.append(prefix + "-" * 60)

    for row in data:
        row_values = [str(row.get(h, "")) for h in headers]
        lines.append(prefix + " | ".join(row_values))

    lines.append("")
    return lines


def format_recursive(data, indent=0):
    lines = []
    prefix = "  " * indent

    if isinstance(data, dict):
        for key, value in data.items():
            # Preserve original key exactly
            lines.append(f"{prefix}{key}:")
            lines.extend(format_recursive(value, indent + 1))

    elif isinstance(data, list):
        if is_table_like(data):
            lines.extend(render_table(data, indent))
        else:
            for index, item in enumerate(data):
                lines.append(f"{prefix}- Item {index + 1}:")
                lines.extend(format_recursive(item, indent + 1))

    elif isinstance(data, str):
        # DO NOT strip or modify
        for line in data.split("\n"):
            lines.append(f"{prefix}{line}")

    elif isinstance(data, (int, float, bool)):
        lines.append(f"{prefix}{data}")

    elif data is None:
        lines.append(f"{prefix}null")

    else:
        lines.append(f"{prefix}{str(data)}")

    return lines


def extract_documents_from_json(file_path):
    documents = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return documents

    title = Path(file_path).stem

    lines = []
    lines.append(f"DOCUMENT TITLE: {title}")
    lines.append(f"SOURCE FILE: {file_path}")
    lines.append("")

    lines.extend(format_recursive(data))

    content = "\n".join(lines)

    documents.append(
        Document(
            page_content=content,
            metadata={"source": file_path}
        )
    )

    return documents


def main():
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"batch_size": 32}
    )

    vectorstore = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embedding
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=120
    )

    new_chunks = []

    for json_file in Path(DATA_DIR).rglob("*.json"):
        file_path = str(json_file)
        print(f"Processing: {file_path}")

        documents = extract_documents_from_json(file_path)
        chunks = splitter.split_documents(documents)

        new_chunks.extend(chunks)

        if len(new_chunks) >= 40:
            vectorstore.add_documents(new_chunks)
            print("Saved 40 chunks...")
            new_chunks = []

    if new_chunks:
        vectorstore.add_documents(new_chunks)
        print(f"Saved remaining {len(new_chunks)} chunks")

    print("Full legal indexing complete.")


if __name__ == "__main__":
    main()
