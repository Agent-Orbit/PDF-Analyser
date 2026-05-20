from rag import pdf_parser,embedder,retriever,llm

chunks = response = pdf_parser.get_chunks("uploads\LifeInvader Ad's Internal Policy (EN3).pdf")

embeddings = embedder.embed_chunks(chunks)
"""
q = "Refine this raw ad input according to rules: Selling 2 apartmet"
q_emb = embedder.embed_query(q)

index = retriever.build_index(embeddings)
ret_chunks = retriever.get_topK_chunks(chunks,index,q_emb)
history=[]
res,hist = llm.getResponse("Qwen",chunks,ret_chunks,index,q,history=history)

print("===" * 20)

q = "Refine this ad: i need a cosmodog"
q_emb = embedder.embed_query(q)
ret_chunks = retriever.get_topK_chunks(chunks,index,q_emb)
res,hist = llm.getResponse("Qwen",chunks,ret_chunks,index,q,history=history)
print(hist)
"""
print(min(5,len(chunks)))

print(chunks[:5])


