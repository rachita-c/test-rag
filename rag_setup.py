import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer


client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("policies")

model = SentenceTransformer("all-MiniLM-L6-v2")

policy_files = [
    "policies/pii_policy.md",
    "policies/security_policy.md",
    "policies/code_review_policy.md",
]

for path in policy_files:
    content = Path(path).read_text()
    embedding = model.encode(content).tolist()

    collection.upsert(
        documents=[content],
        embeddings=[embedding],
        ids=[path],
    )

print("Policies indexed successfully.")
