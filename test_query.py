"""Sanity-check query against the local ChromaDB policy collection."""

import chromadb

DB_PATH = "chroma_db"
COLLECTION_NAME = "governance_policies"

queries = [
    "the code has a password typed directly into it",
]


def main() -> None:
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)

    for query in queries:
        print(f"Query: {query!r}")
        results = collection.query(query_texts=[query], n_results=3)
        for i, (doc_id, distance, metadata) in enumerate(
            zip(results["ids"][0], results["distances"][0], results["metadatas"][0])
        ):
            print(f"  {i+1}. {doc_id} — {metadata['title']} (distance={distance:.4f})")
        print()


if __name__ == "__main__":
    main()
