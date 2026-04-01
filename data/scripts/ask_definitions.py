from dotenv import load_dotenv
import os

load_dotenv()
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama

DB_PATH = "definitions_db"

# Load embedding model once
embedding = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

# Load vector DB once
vectorstore = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embedding
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

# Load LLM once
llm = Ollama(model="phi3:mini")


def main():
    print("EqualEdge Legal Definitions Engine Ready.")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("Ask: ").strip()

        if not query:
            continue

        if query.lower() == "exit":
            break

        docs = retriever.invoke(query)

        if not docs:
            print("\nNOT FOUND\n")
            continue

        context = docs[0].page_content

        prompt = f"""
You are a strict legal definitions engine.

Return ONLY the exact definition sentence from the context.
Do not paraphrase.
Do not explain.
Do not add interpretation.
Do not include importance.
If the definition is not found, reply exactly:
NOT FOUND.

Context:
{context}

Question:
{query}

Definition:
"""

        response = llm.invoke(prompt)

        print("\nAnswer:\n")
        print(response.strip())
        print("\n" + "-" * 50 + "\n")


if __name__ == "__main__":
    main()
