"""Build the ChromaDB policy collection from policies/policies.yaml.

Run from the repository root, and re-run after every edit to the policy file, 
the auditor retrieves against whatever is in the store, so a skipped rebuild
means it silently judges against the old text.

    python scripts/setup_chromadb.py
"""

from pathlib import Path

import chromadb
import yaml

POLICIES_PATH = "policies/policies.yaml"
DB_PATH = "chroma_db"
COLLECTION_NAME = "governance_policies"


def load_policies(path: str) -> list[dict]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))["policies"]


def main() -> None:
    policies = load_policies(POLICIES_PATH)
    client = chromadb.PersistentClient(path=DB_PATH)

    if any(c.name == COLLECTION_NAME for c in client.list_collections()):
        client.delete_collection(name=COLLECTION_NAME)
    collection = client.create_collection(name=COLLECTION_NAME)

    # `documents` is the text that gets embedded and drives semantic retrieval.
    # `metadatas` is returned alongside a hit but is never embedded.
    documents = [
        f"{p['title']}\n\n{p['description'].strip()}\n\n"
        f"Rule: {p['rule'].strip()}\n\n"
        f"Applies to: {', '.join(p.get('applies_to') or ['(repository-level)'])}"
        for p in policies
    ]
    metadatas = [
        {
            "title": p["title"],
            "severity": p["severity"],
            "scope": p.get("scope", "file"),
            "evaluation": p.get("evaluation", "model"),
            "rule": p["rule"].strip(),
        }
        for p in policies
    ]

    collection.add(
        ids=[p["policy_id"] for p in policies],
        documents=documents,
        metadatas=metadatas,
    )
    print(f"Loaded {len(policies)} policies into '{COLLECTION_NAME}' at {DB_PATH}/")


if __name__ == "__main__":
    main()
