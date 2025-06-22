import os
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
import pinecone
HF_TOKEN = os.getenv('HF_TOKEN') 
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY') 
PINECONE_ENV = 'us-east-1'
INDEX_NAME = 'medical-demo'
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
if INDEX_NAME not in pinecone.list_indexes():
    pinecone.create_index(INDEX_NAME, dimension=384, metric='cosine')
index = pinecone.Index(INDEX_NAME)
pubmed_ds = load_dataset('qiaojin/PubMedQA', 'pqa_labeled', use_auth_token=HF_TOKEN)['train']
ehrsql_ds = load_dataset('nannullna/ehrsql_mimic_iii', use_auth_token=HF_TOKEN)['train']
model = SentenceTransformer('all-MiniLM-L6-v2')

def upload_to_pinecone(data, prefix, text_fn, meta_fn):
    for i, row in enumerate(data[:100]):
        text = text_fn(row)
        embedding = model.encode(text)
        meta = meta_fn(row)
        index.upsert([(f'{prefix}-{i}', embedding.tolist(), meta)])
upload_to_pinecone(pubmed_ds, prefix='pubmedqa', text_fn=lambda r: f"{r['question']} {r['context']} {r['long_answer']}", meta_fn=lambda r: {'source': 'pubmedqa', 'label': r['final_decision']})
upload_to_pinecone(ehrsql_ds, prefix='ehrsql', text_fn=lambda r: f"{r['question']} {r['sql_query']}", meta_fn=lambda r: {'source': 'ehrsql', 'sql_query': r['sql_query']})
print('✅ Uploaded 100 samples each from PubMedQA and EHRSQL to Pinecone.')