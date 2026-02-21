import pandas as pd 
import faiss # used to seach similar data points in the large dataset.
import pickle # savigng and reloading the data 
import os
from sentence_transformers import SentenceTransformer # used to convert text data into vector format.   


# step 1 load the dataset

BASE_DIR = r"d:\Cross Lingual Project(gujarati)"
DATA_FILE = os.path.join(BASE_DIR, "data", "combined","gujarati_dialects.csv")
MODEL_OUT = os.path.join(BASE_DIR, "models", "rag")

os.makedirs(MODEL_OUT, exist_ok=True)

def load_processed_data(file_path):
    if not os.path.exists(file_path):
        print(f"❌ ERROR: File not found at {file_path}")
        return None, None

    print(f"📂 Reading dataset from: {file_path}")

    # Using utf-8-sig to handle Gujarati Unicode characters properly
    df = pd.read_csv(file_path, encoding="utf-8-sig")

    # Verify we have the right columns before proceeding
    required_cols = ['sentence', 'dialect']
    if not all(col in df.columns for col in required_cols):
        print(f"❌ ERROR: CSV must contain 'sentence' and 'dialect' columns.")
        return None, None

    # Convert to lists for the embedding model in Step 2
    sentences = df['sentence'].tolist()
    dialects  = df['dialect'].tolist()

    print(f"✅ Successfully loaded {len(sentences)} sentences.")
    print(f"📊 Dialect breakdown: {df['dialect'].value_counts().to_dict()}")

    return sentences, dialects

# Step 2 & 3: Embed and Index
def build_and_save_index(sentences, dialects):
    print("\n🧠 Loading SentenceTransformer model: google/muril-base-cased...")
    # Using MuRIL which we already downloaded in Phase 2
    model = SentenceTransformer("google/muril-base-cased")
    
    print(f"⚙️  Embedding {len(sentences)} sentences...")
    embeddings = model.encode(sentences, show_progress_bar=True, batch_size=32)
    
    # The embeddings are returned as float32 numpy arrays 
    dim = embeddings.shape[1]
    print(f"📏 Embedding dimension: {dim}")
    
    print("\n🗄️  Building FAISS index...")
    # L2 distance (Inner Product is also good, but L2 is standard for distance)
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    
    print(f"✅ Added {index.ntotal} vectors to FAISS index.")
    
    # Save the FAISS index
    index_path = os.path.join(MODEL_OUT, "dialect_rag_index.faiss")
    faiss.write_index(index, index_path)
    print(f"💾 Saved FAISS index to: {index_path}")
    
    # Save the metadata (we need to know what text belongs to vector ID 5, for example)
    metadata = {
        "sentences": sentences,
        "dialects": dialects
    }
    meta_path = os.path.join(MODEL_OUT, "rag_metadata.pkl")
    with open(meta_path, "wb") as f:
        pickle.dump(metadata, f)
    print(f"💾 Saved Metadata to: {meta_path}")

if __name__ == "__main__":
    print("="*50)
    print("  RAG VECTOR DB BUILDER  ")
    print("="*50)
    # Test the loader
    sentences, dialects = load_processed_data(DATA_FILE)
    if sentences:
        build_and_save_index(sentences, dialects)