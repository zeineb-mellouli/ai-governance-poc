"""Load policies/policies.yaml into a local, persistent ChromaDB collection."""

import yaml
import chromadb

POLICIES_PATH = "policies/policies.yaml"
DB_PATH = "chroma_db"
COLLECTION_NAME = "governance_policies"


def load_policies(path: str) -> list[dict]:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data["policies"]


def main() -> None:
    policies = load_policies(POLICIES_PATH)

    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    ids = [p["policy_id"] for p in policies]
    documents = [
        f"{p['title']}\n\n{p['description'].strip()}\n\nApplies when: {p['applies_when'].strip()}"
        for p in policies
    ]
    metadatas = [
        {
            "title": p["title"],
            "severity": p["severity"],
            "evaluation_hint": p["evaluation_hint"].strip(),
        }
        for p in policies
    ]

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    print(f"Loaded {len(policies)} policies into collection '{COLLECTION_NAME}' at {DB_PATH}/")


if __name__ == "__main__":
    main()
