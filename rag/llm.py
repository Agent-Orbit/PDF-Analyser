import requests
import json
from rag import embedder, retriever
import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq


def get_groqapi():

    load_dotenv()
    try:
        return st.secrets["GROQ_API_KEY"]
    except:
        return os.getenv("GROQ_API_KEY")

    


def ask_Qwen(prompt, history=None):

    model = "qwen2.5:7b"
    messages = (history or []) + [{"role": "user", "content": prompt}]

    response = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": model, "messages": messages, "stream": False}
    )

    return response.json()["message"]["content"]

groq_client = Groq(api_key=get_groqapi())

def ask_groq(prompt, history=None,isStream=True):

    messages = (history or []) + [{"role": "user", "content": prompt}]

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.2,
        stream=isStream
    )

    if isStream:

        return response
    
    else:

        return response.choices[0].message.content




def ask_AI(model, prompt, history=None,isStream=True):

    if model == "Qwen":
        return ask_Qwen(prompt, history)
    
    elif model == "llama-3.3-70b-versatile":
        
        return ask_groq(prompt,history,isStream=isStream)


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
        Do not wrap your entire response in a code block. Dont respond like according to data or like saying the text chunks i
        received. Behave professionally and respond properly.

        Follow these rules strictly:
        - For questions about the document: answer ONLY from the provided context.
        - For general conversational questions (greetings, clarifying a word, general knowledge): answer normally and helpfully.
        - NEVER invent statistics, numbers, dates, or names that aren't in the context.
        - If a document-specific question can't be answered from context, say: 'I could not find this in the document.


        Data: {chunks}
        Question: {question}
        Chat history with you(Can be None too): {history}
        """

    elif prompt_type == "FirstQ":

        return f"""You are a PDF analyser.

        Given chunks and a question, you have two choices:

        CHOICE 1 - If chunks have ENOUGH information:
        Answer the question in clean markdown: use headings, bullet points, bold text, and code blocks where appropriate.
        Do not wrap your entire response in a code block.Respond in this format only:
        {{
            "need_more": False,
            "response": you response
        }}

        CHOICE 2 - If chunks are MISSING information:
        Respond ONLY with this JSON, nothing else, no markdown:
        {{
            "need_more": True,
            "queries": ["specific query 1", "specific query 2"]
        }}

        Dont respond like according to data or like saying the text chunks i
        received. Behave professionally and respond properly.

        Follow these rules strictly:
        - For questions about the document: answer ONLY from the provided context.
        - For general conversational questions (greetings, clarifying a word, general knowledge): answer normally and helpfully.
        - NEVER invent statistics, numbers, dates, or names that aren't in the context.
        - If a document-specific question can't be answered from context, say: 'I could not find this in the document.


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


        Dont respond like according to data or like saying the text chunks i
        received. Behave professionally and respond properly.

        Follow these rules strictly:
        - For questions about the document: answer ONLY from the provided context.
        - For general conversational questions (greetings, clarifying a word, general knowledge): answer normally and helpfully.
        - NEVER invent statistics, numbers, dates, or names that aren't in the context.
        - If a document-specific question can't be answered from context, say: 'I could not find this in the document.

        Chunks: {chunks}
        Question: {question}
        Chat history with you(Can be None too): {history}
        """
    
def format_chunks(ret_chunks):
    return "\n\n".join(
        f"[Page {c['page']}] {c['text']}" for c in ret_chunks
    )

def getReport(model,chunks_d):

    data = " ".join([c["text"] for c in chunks_d])

    prompt = f""" You are a PDF analyser. You will be provided with PDF's main data. Generate a report based on PDF's
        topic and important things to focucs on.
        Format your response in clean markdown: use headings, bullet points, bold text, and code blocks where appropriate.
        Do not wrap your entire response in a code block.

        Dont respond like according to data or like saying the text chunks i
        received. Behave professionally and respond properly.

        Answer ONLY using the provided context. If the answer is not in the context, say exactly:
        'I could not find this in the document.' Never use outside knowledge.
        
        Data: {data}"""
    
    response = ask_AI(model,prompt,isStream=False)

    return response



def getResponse(model, chunks, ret_chunks, index, question, history=None, isBetter=False):

    if not isBetter:

        prompt = getPrompt("ZeroQ", format_chunks(ret_chunks), question, history=history)
        response = ask_AI(model, prompt, history)
        

    else:

        prompt = getPrompt("FirstQ", format_chunks(ret_chunks), question, history=history)
        response = ask_AI(model, prompt, history,isStream=False)

        max_rounds = 3
        round = 0
        all_chunks = ret_chunks

        while round < max_rounds:

            more_chunks = get_moreChunks(chunks, index, response)

            if not more_chunks:
                break

            all_chunks.extend(more_chunks)
            round += 1
        
            if round >= max_rounds:
                break

            prompt = getPrompt("FirstQ", format_chunks(all_chunks), question, history=history)
            response = ask_AI(model, prompt, history, isStream=False)
        
        prompt = getPrompt("SecondQ", format_chunks(all_chunks), question, history=history)
        response = ask_AI(model, prompt, history)


        

    
        

    return response,history



def appendHistory(summary, history):

    if history is None:
        history = []

    history.append({"role": "user", "content": summary})
    history.append({"role": "assistant", "content": "Acknowledged."})

    return history



def summarize_turn(model, question, response):

    prompt = f"""Summarize this exchange in 1-2 sentences. Preserve key facts, names, and context only. Be concise.

    User: {question}
    Assistant: {response}
    """

    result = ask_AI(model, prompt,isStream=False)
    return result if result else f"User asked: {question}"

def getKeySentences(model, userPrompt):

    prompt = f"""Make 3-5 key sentences from this question to find relevant text in a document.
        Return ONLY a Python list of strings, nothing else. No explanation, no markdown.
        Example: ["sentence1", "sentence2", "sentence3"]

        Question: {userPrompt}"""

    if model == "llama-3.3-70b-versatile":
        
        return json.loads(ask_groq(prompt,isStream=False))



def main():
    pass


if __name__ == "__main__":
    main()