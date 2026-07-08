"""Sanity-check query against the local ChromaDB policy collection."""

import chromadb

DB_PATH = "chroma_db"
COLLECTION_NAME = "governance_policies"

queries = [
    "the code has a password typed directly into it",
    "we loaded the dataset and started training on it right away without checking for duplicates or missing values",
    "the nightly batch job just prints status messages to the console, nothing is saved anywhere",
    "a connection string with the real password baked into the script",
    "the notebook output shows a table of customers with their real names and email addresses visible",
    "the repo has a notebook called final_v2_ACTUAL.ipynb and no README explaining the project",
    "the training script doesn't set a random seed and the dependencies aren't pinned to specific versions",
    "we're publishing a table for other teams to use but never documented what one row represents or what the key is",
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
