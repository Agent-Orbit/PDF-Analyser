import faiss

def build_index(embeddings):

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    return index


def get_topK_chunks(chunks_d, index, q_emb, k=5, threshold=0.45):

    retrieved_chunks = []
    k = min(k, len(chunks_d))

    distances, indices = index.search(q_emb, k=k)

    for score, idx in zip(distances[0], indices[0]):

        if score >= threshold:
            retrieved_chunks.append({
                "text": chunks_d[idx]["text"],
                "page": chunks_d[idx]["page"],
                "score": f"{score:.4f}"
            })

    return retrieved_chunks