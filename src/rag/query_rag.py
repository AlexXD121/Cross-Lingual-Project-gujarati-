import os
import faiss
import pickle
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

BASE_DIR = r"d:\Cross Lingual Project(gujarati)"
MODEL_OUT = os.path.join(BASE_DIR, "models", "rag")
INDEX_PATH = os.path.join(MODEL_OUT, "dialect_rag_index.faiss")
META_PATH = os.path.join(MODEL_OUT, "rag_metadata.pkl")

_tokenizer = None
_model = None
_index = None
_metadata = None
_device = None

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def load_rag_backend():
    global _tokenizer, _model, _index, _metadata, _device
    
    if _model is None:
        print("🧠 Loading MuRIL embedding model...")
        _tokenizer = AutoTokenizer.from_pretrained("google/muril-base-cased")
        _model = AutoModel.from_pretrained("google/muril-base-cased", use_safetensors=True)
        _model.eval()
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model = _model.to(_device)
    
    if _metadata is None:
        if not os.path.exists(META_PATH): raise FileNotFoundError("Metadata missing.")
        with open(META_PATH, "rb") as f: _metadata = pickle.load(f)
            
    if _index is None:
        if not os.path.exists(INDEX_PATH): raise FileNotFoundError("FAISS index missing.")
        _index = faiss.read_index(INDEX_PATH)
        
    return _tokenizer, _model, _index, _metadata, _device


def search_rag(query_text, dialect_filter=None, top_k=3):
    tokenizer, model, index, metadata, device = load_rag_backend()
    
    # 1. Embed query (Mean Pooling + L2 Normalize for Cosine Similarity)
    encoded_input = tokenizer([query_text], padding=True, truncation=True, max_length=128, return_tensors='pt').to(device)
    with torch.no_grad():
        model_output = model(**encoded_input)
    
    query_vector = mean_pooling(model_output, encoded_input['attention_mask'])
    query_vector = F.normalize(query_vector, p=2, dim=1).cpu().numpy()
    
    # 2. Search FAISS (Inner Product since vectors are L2 normalized = Cosine Similarity)
    search_k = top_k * 4 if dialect_filter else top_k 
    Scores, I = index.search(query_vector, search_k)
    
    results = []
    for j in range(len(I[0])):
        idx = I[0][j]
        score = Scores[0][j] # Higher is better (Cosine Sim 0 to 1)
        if idx == -1: continue
            
        sentence = metadata["sentences"][idx]
        dialect = metadata["dialects"][idx]
        
        if dialect_filter and dialect != dialect_filter:
            continue
            
        results.append({
            "text": sentence,
            "dialect": dialect,
            "similarity": round(float(score), 4)
        })
        if len(results) >= top_k:
            break
            
    return results

if __name__ == "__main__":
    print("=" * 50)
    print("   RAG SEARCH TEST   ")
    print("=" * 50)
    
    test_queries = [
        "પોયરો ક્યાં ગયો",           # Surti sounding query
        "આ ખૂબ સારી વાત છે"          # Standard Gujarati sounding query
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        matches = search_rag(query, top_k=3)
        print("  Top Matches (Any Dialect):")
        for i, m in enumerate(matches):
            print(f"    {i+1}. [{m['dialect']}] {m['text']} (Sim: {m['similarity']})")
