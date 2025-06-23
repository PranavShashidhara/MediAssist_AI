import os
import json
import logging
import boto3
import time
import sys
from botocore.exceptions import ClientError
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# === CONFIGURATION ===
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") 
PINECONE_REGION = "us-east-1"
INDEX_NAME = "medical-demo"
BEDROCK_REGION = "us-east-1"
MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"  

# === SETUP LOGGING ===
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# === Load Sentence Embedding Model ===
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2", token=HF_TOKEN)

# === Connect to Pinecone ===
print("Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# === Bedrock Setup ===
bedrock = boto3.client(service_name='bedrock-runtime', region_name=BEDROCK_REGION)

# === Custom Exception ===
class ModelError(Exception):
    def __init__(self, message):
        self.message = message

# === Smooth Text Display Function ===
def smooth_print(text, delay=0.03):
    """Print text with a typewriter effect"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()  # New line at the end

def smooth_print_words(text, delay=0.1):
    """Print text word by word for faster display"""
    words = text.split()
    for i, word in enumerate(words):
        if i > 0:
            print(' ', end='', flush=True)
        print(word, end='', flush=True)
        time.sleep(delay)
    print()  # New line at the end

def smooth_print_sentences(text, delay=0.3):
    """Print text sentence by sentence"""
    # Split by common sentence endings
    sentences = []
    current_sentence = ""
    
    for char in text:
        current_sentence += char
        if char in '.!?':
            sentences.append(current_sentence.strip())
            current_sentence = ""
    
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    for sentence in sentences:
        print(sentence, end=' ', flush=True)
        time.sleep(delay)
    print()  # New line at the end

# === Text Generation with Claude ===
def generate_text(prompt, temperature=0.3):
    # Updated payload structure for Claude via Bedrock
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "temperature": temperature,
        "top_p": 1.0,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    })

    try:
        response = bedrock.invoke_model(
            body=body,
            modelId=MODEL_ID,
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())

        if "error" in response_body:
            raise ModelError(f"Text generation error: {response_body['error']}")

        # Claude response structure is different - content is in a list
        content = response_body.get("content", [])
        if content and len(content) > 0:
            return content[0].get("text", "[No output]")
        else:
            return "[No output]"

    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error(f"AWS Client Error: {message}")
        raise

# === Pinecone Query ===
def get_context_from_pinecone(query_text, top_k=5, namespace=None):
    print(f"\nRetrieving context from Pinecone for: \"{query_text}\"")
    query_vector = model.encode(query_text).tolist()

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace
    )

    context_texts = []
    for i, match in enumerate(results['matches']):
        metadata = match.get("metadata", {})
        text = metadata.get("text", "")
        if text:
            context_texts.append(text)

    return "\n".join(context_texts)

# === Claude-based Assistant ===
def medical_assistant(user_input):
    prompt = f"You are a kind, empathetic medical assistant. Respond calmly and clearly.\nQuestion: {user_input}"
    return generate_text(prompt, temperature=0.6)

# === RAG Assistant with Claude ===
def contains_hindi(text):
    return any('\u0900' <= c <= '\u097F' for c in text)

def medical_rag_assistant(user_input, context):
    if contains_hindi(context):
        # Ignore context if it is in Hindi
        prompt = (
            "You are a helpful medical assistant. Respond calmly and clearly to the user's question.\n"
            f"Question: {user_input}"
        )
    else:
        prompt = (
        "You are a helpful medical assistant. Try to answer the user's question using the provided context below.\n"
        "If relevant information is present in the context, prioritize it. If not, fall back on your general medical knowledge to give a calm, empathetic, and helpful answer.\n\n"
        f"Context:\n{context if context.strip() else '[No relevant context]'}\n\n"
        f"Question: {user_input}"
        )
    return generate_text(prompt, temperature=0.3)

# === CLI ===
if __name__ == "__main__":
    print("Choose mode:\n1. Assistant only\n2. RAG (retrieve + answer)\n")
    mode = input("Enter 1 or 2: ").strip()

    while True:
        user_input = input("\nEnter your medical question (or 'exit' to quit): ")
        if user_input.lower() == "exit":
            break

        try:
            if mode == "1":
                response = medical_assistant(user_input)
            else:
                context = get_context_from_pinecone(user_input, top_k=5)
                response = medical_rag_assistant(user_input, context)

            print(f"\n🩺 Response:")
            smooth_print_words(response, delay=0.08)

        except ModelError as e:
            print(f"Model error occurred: {e.message}")
        except Exception as e:
            print(f"Unexpected error: {e}")