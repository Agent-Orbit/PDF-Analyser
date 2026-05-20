from rag import pdf_parser,embedder,retriever,llm

chunks = response = pdf_parser.get_chunks("uploads\LifeInvader Ad's Internal Policy (EN3).pdf")
embeddings = embedder.embed_chunks(chunks)
q = "Refine this raw ad input according to rules: Selling house 23. price is 23 m"
q_emb = embedder.embed_query(q)

index = retriever.build_index(embeddings)
ret_chunks = retriever.get_topK_chunks(chunks,index,q_emb)
print(llm.getResponse("Qwen",chunks,ret_chunks,index,q))

print("===" * 20)

q = "Whats the max amount of houses we can advertise in a single ad"
q_emb = embedder.embed_query(q)
ret_chunks = retriever.get_topK_chunks(chunks,index,q_emb)
print(llm.getResponse("Qwen",chunks,ret_chunks,index,q))
