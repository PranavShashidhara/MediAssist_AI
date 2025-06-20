import os
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# === CONFIGURATION ===
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN") 
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") 
PINECONE_REGION = "us-east-1"
INDEX_NAME = "medical-demo"

# === Load Sentence Embedding Model ===
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2", token=HF_TOKEN)

# === Connect to Pinecone ===
print("Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# === Query Function ===
def query_pinecone(query_text, top_k=5, namespace=None):
    print(f"\nQuerying Pinecone for: \"{query_text}\"")

    # Embed the query
    query_vector = model.encode(query_text).tolist()

    # Query Pinecone
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace  # optional: for scoped queries
    )

    # Print results
    for i, match in enumerate(results['matches']):
        print(f"\nResult {i+1} (Score: {match['score']:.4f}):")
        metadata = match.get("metadata", {})
        print("Text:", metadata.get("text", "[No text]"))
        print("Source:", metadata.get("source", "N/A"))
        print("Question:", metadata.get("question", "N/A"))

# === Entry Point ===
if __name__ == "__main__":
    while True:
        query_input = input("\nEnter your medical question (or 'exit' to quit): ")
        if query_input.lower() == "exit":
            break
        query_pinecone(query_input, top_k=5)
