import faiss
from rag import llm,embedder


def build_index(embeddings):

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    return index


def get_topK_chunks(chunks_d, index, q,q_emb, k=5, threshold=0.45,fallback_threshold=0.25):

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
    
    if not retrieved_chunks:


        for score, idx in zip(distances[0], indices[0]):

            if score >= fallback_threshold:
                retrieved_chunks.append({
                    "text": chunks_d[idx]["text"],
                    "page": chunks_d[idx]["page"],
                    "score": f"{score:.4f}"
                })
    
    if not retrieved_chunks:

        sentences_list = llm.getKeySentences(model="llama-3.3-70b-versatile",userPrompt=q)

        for sentence in sentences_list:

            sen_emb = embedder.embed_query(sentence)
            distances, indices = index.search(sen_emb, k=k)
            for score, idx in zip(distances[0], indices[0]):

            
                retrieved_chunks.append({
                    "text": chunks_d[idx]["text"],
                    "page": chunks_d[idx]["page"],
                    "score": f"{score:.4f}"
                })
    
    ret_chunks = []
    seen = set()

    for chunk in retrieved_chunks:

        if chunk["text"] not in seen:
            
            seen.add(chunk["text"])
            ret_chunks.append(chunk)

    return ret_chunks