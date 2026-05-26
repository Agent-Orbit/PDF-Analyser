from sentence_transformers import SentenceTransformer
import numpy as np
import faiss


model = SentenceTransformer("BAAI/bge-base-en-v1.5")
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

def embed_chunks(chunks_d):
    
    chunks = [c["text"] for c in chunks_d]
    embeddings = model.encode(chunks)
    embeddings = np.array(embeddings, dtype="float32")
    faiss.normalize_L2(embeddings)
    return embeddings

def embed_query(query):

    prefixed = BGE_QUERY_PREFIX + query
    embedding = model.encode([prefixed])
    embedding = np.array(embedding,dtype="float32")
    faiss.normalize_L2(embedding)
    return embedding



