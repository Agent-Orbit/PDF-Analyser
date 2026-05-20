import faiss

def build_index(embeddings):

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    return index


def get_topK_chunks(chunks,index,q_emb,k=5):

    retrieved_chunks = []
    k = min(k, len(chunks))

    distances, indices = index.search(q_emb,k=k)

    for score,idx in zip(distances[0], indices[0]):

        
        retrieved_chunks.append({
            "text": chunks[idx],
            "score": f"{score:.4f}"
        })

        
    
    return retrieved_chunks