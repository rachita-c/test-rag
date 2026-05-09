import chromadb
from sentence_transformers import SentenceTransformer


client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("policies")

model = SentenceTransformer("all-MiniLM-L6-v2")

query = "customer email exposure in API response"
query_embedding = model.encode(query).tolist()

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=2,
)

for doc in results["documents"][0]:
    print("\n--- Retrieved Document ---")
    print(doc)
