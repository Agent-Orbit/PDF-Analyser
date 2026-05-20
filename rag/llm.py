import requests
import json
from rag import embedder, retriever
import os
import streamlit as st
from dotenv import load_dotenv
from google import genai


def get_geminiapi():

    load_dotenv()
    try:
        return st.secrets["GEMINI_API_KEY"]
    except:
        return os.getenv("GEMINI_API_KEY")

    


def ask_Qwen(prompt, history=None):

    model = "qwen2.5:7b"
    messages = (history or []) + [{"role": "user", "content": prompt}]

    response = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": model, "messages": messages, "stream": False}
    )

    return response.json()["message"]["content"]

client = genai.Client(api_key=get_geminiapi())

def ask_gemini(prompt,history = None):

    gemini_history = []

    for msg in history or []:

        role = msg.get("role", "user")

        if role == "assistant":
            role = "model"

        gemini_history.append(
            {
                "role": role,
                "parts": [
                    msg.get("content", "")
                ]
            }
        )

    api_key = get_geminiapi()
    genai.configure(api_key=api_key)
    chat = client.chats.create(
        model="gemini-2.5-flash",
        history=gemini_history
    )

    response = chat.send_message(prompt)

    return response.text


def ask_AI(model, prompt, history=None):

    if model == "Qwen":
        return ask_Qwen(prompt, history)
    
    elif model == "gemini-2.5-flash":
        
        return ask_gemini(prompt,history)


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

    if prompt_type == "ZeroQ":

        return f"""You are a PDF analyser. You are provided with data and you have to answer the user.
        Always be helpful. If you cant answer, say I dont know.
        Format your response in clean markdown: use headings, bullet points, bold text, and code blocks where appropriate.
        Do not wrap your entire response in a code block.

        Data: {chunks}
        Question: {question}
        Chat history with you(Can be None too): {history}
        """

    elif prompt_type == "FirstQ":

        return f"""You are a PDF analyser.

        Given chunks and a question, you have two choices:

        CHOICE 1 - If chunks have ENOUGH information:
        Answer the question in clean markdown: use headings, bullet points, bold text, and code blocks where appropriate.
        Do not wrap your entire response in a code block.

        CHOICE 2 - If chunks are MISSING information:
        Respond ONLY with this JSON, nothing else, no markdown:
        {{
            "need_more": true,
            "queries": ["specific query 1", "specific query 2"]
        }}

        Chunks: {chunks}
        Question: {question}
        Chat history with you(Can be None too): {history}
        """

    elif prompt_type == "SecondQ":

        return f"""You are a PDF analyser.

        Answer the question using the chunks provided.
        If the answer is still not in the chunks, say you dont know.
        Format your response in clean markdown: use headings, bullet points, bold text, and code blocks where appropriate.
        Do not wrap your entire response in a code block.

        Chunks: {chunks}
        Additional chunks: {more_chunks}
        Question: {question}
        Chat history with you(Can be None too): {history}
        """
    
  

def getReport(model,data):

    prompt = f""" You are a PDF analyser. You will be provided with PDF's main data. Generate a report based on PDF's
        topic and important things to focucs on.
        Format your response in clean markdown: use headings, bullet points, bold text, and code blocks where appropriate.
        Do not wrap your entire response in a code block.
        
        Data: {data}"""
    
    response = ask_AI(model,prompt)

    return response



def getResponse(model, chunks, ret_chunks, index, question, history=None, isBetter=False):

    if not isBetter:

        prompt = getPrompt("ZeroQ", ret_chunks, question, history=history)
        response = ask_AI(model, prompt, history)

    else:

        prompt = getPrompt("FirstQ", ret_chunks, question, history=history)
        response = ask_AI(model, prompt, history)

        more_chunks = get_moreChunks(chunks, index, response)

        if more_chunks is not None:

            
            prompt = getPrompt("SecondQ", ret_chunks, question, more_chunks, history=history)
            response = ask_AI(model, prompt, history)

    if history is not None:

        summary = summarize_turn(model, question, response)
        history.append({"role": "user", "content": summary})
        history.append({"role": "assistant", "content": "Acknowledged."})

    return response,history

def summarize_turn(model, question, response):

    prompt = f"""Summarize this exchange in 1-2 sentences. Preserve key facts, names, and context only. Be concise.

    User: {question}
    Assistant: {response}
    """

    return ask_AI(model, prompt)


def main():
    pass


if __name__ == "__main__":
    main()