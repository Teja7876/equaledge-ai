import chromadb
from chromadb.errors import NotFoundError

CHROMA_PATH = "chroma"
COLLECTION_NAME = "rpwd_legal"

# Set to False in production
RESET_COLLECTION = True


def get_collection(client):
    try:
        return client.get_collection(name=COLLECTION_NAME)
    except NotFoundError:
        return client.create_collection(name=COLLECTION_NAME)


def reset_collection(collection):
    existing = collection.get()

    if existing and existing.get("ids"):
        collection.delete(ids=existing["ids"])
        print("Collection cleared.")
    else:
        print("Collection already empty.")


def main():
    print("Connecting to Chroma...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    collection = get_collection(client)
    print(f"Collection ready: {collection.name}")

    if RESET_COLLECTION:
        reset_collection(collection)

    print("Inserting Section 16...")

    collection.add(
        documents=[
            "Section 16: The appropriate Government and the local authorities shall endeavour to promote inclusive education."
        ],
        metadatas=[
            {
                "act": "RPwD Act 2016",
                "section": "16",
                "category": "education",
                "jurisdiction": "India",
                "version": "2016"
            }
        ],
        ids=["rpwd_2016_section_16"]
    )

    print("Section 16 inserted successfully.")


if __name__ == "__main__":
    main()