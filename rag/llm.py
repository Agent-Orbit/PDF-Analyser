import requests
import json
from rag import embedder,retriever


def ask_Qwen(prompt, history=None):

    model = "qwen2.5:7b"
    
    if history:

        messages = history + [{"role": "user", "content": prompt}]
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": model, "messages": messages, "stream": False}
        )

        return response.json()["message"]["content"]
    
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )

    return response.json()["response"]


def ask_AI(model, prompt, history=None):

    if model == "Qwen":
        return ask_Qwen(prompt, history)


def get_moreChunks(chunks, index, response):

    try:
        parsed = json.loads(response)
        more_chunks = []

        if parsed.get("need_more"):

            for q in parsed.get("queries", []):

                q_emb = embedder.embed_query(q)
                ret_chunks = retriever.get_topK_chunks(chunks, index, q_emb)
                more_chunks.extend(ret_chunks)

        return more_chunks

    except json.JSONDecodeError:

        return None


def getPrompt(prompt_type, chunks, question, more_chunks=None, history=None):

    if prompt_type == "FirstQ":

        return f"""You are a PDF analyser.

        Given chunks and a question, you have two choices:

        CHOICE 1 - If chunks have ENOUGH information:
        Answer the question directly in plain text.

        CHOICE 2 - If chunks are MISSING information:
        Respond ONLY with this JSON, nothing else:
        {{
            "need_more": true,
            "queries": ["specific query 1", "specific query 2"]
        }}

        Chunks: {chunks}
        Question: {question}
        """

    elif prompt_type == "SecondQ":

        return f"""You are a PDF analyser.

        Answer the question using the chunks provided.
        If the answer is still not in the chunks, say you don't know.

        Chunks: {chunks}
        Additional chunks: {more_chunks}
        Question: {question}"""


def getResponse(model, chunks,ret_chunks, index, question, history=None):

    prompt = getPrompt("FirstQ", ret_chunks, question)
    response = ask_AI(model, prompt, history)

    more_chunks = get_moreChunks(chunks, index, response)

    if more_chunks is not None:

        prompt = getPrompt("SecondQ", chunks, question, more_chunks)
        response = ask_AI(model, prompt, history)

    if history is not None:

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": response})

    return response


def main():
    pass


if __name__ == "__main__":
    main()