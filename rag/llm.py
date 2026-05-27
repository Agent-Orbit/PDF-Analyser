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

_groq_client = None

def get_client():

    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=get_groqapi())
    return _groq_client

def ask_groq(prompt, history=None,isStream=True):

    messages = (history or []) + [{"role": "user", "content": prompt}]

    response = get_client().chat.completions.create(
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


def get_moreChunks(chunks, index, response,q):

    try:
        parsed = json.loads(response)
        more_chunks = []

        if parsed.get("need_more"):

            for q in parsed.get("queries", []):

                q_emb = embedder.embed_query(q)
                ret_chunks = retriever.get_topK_chunks(chunks, index, q,q_emb)
                more_chunks.extend(ret_chunks)

        return more_chunks

    except json.JSONDecodeError:
        return None


def getPrompt(prompt_type, chunks, question, more_chunks=None, history=None):

    if prompt_type == "ZeroQ":

        return f"""You are a precise PDF analysis assistant.

        Answer the user's question using ONLY the provided document chunks.
        Format your response in clean markdown (headings, bullet points, bold, code blocks where appropriate). Never wrap your full response in a code block.

        Rules:
        - Answer document questions strictly from the chunks below. Never invent facts, numbers, names, or dates.
        - For greetings or general conversational questions, respond normally and helpfully.
        - If the answer is not in the chunks, say exactly: "I could not find this in the document."
        - Do not reference the chunks directly (e.g. avoid "according to the text" or "chunk 3 says").

        Document chunks:
        {chunks}

        Conversation so far:
        {history or "None"}

        User question: {question}"""

    elif prompt_type == "FirstQ":

        return f"""You are a PDF analysis assistant deciding whether you have enough context to answer.

        Given document chunks and a user question, choose ONE of two responses:

        OPTION A — You have enough information. Respond ONLY with this JSON:
        {{"need_more": false, "response": "<your full markdown answer here>"}}

        OPTION B — You need more context. Respond ONLY with this JSON:
        {{"need_more": true, "queries": ["specific search query 1", "specific search query 2"]}}

        Rules:
        - Output ONLY valid JSON. No preamble, no markdown fences, no explanation outside the JSON.
        - Use false/true (lowercase), not Python True/False.
        - Queries should be specific phrases likely to appear in the document, not paraphrases of the question.
        - Never invent facts. If the answer genuinely isn't findable, use Option A and say "I could not find this in the document."

        Document chunks:
        {chunks}

        Conversation so far:
        {history or "None"}

        User question: {question}"""

    elif prompt_type == "SecondQ":

        return f"""You are a precise PDF analysis assistant.

        You have been given additional document chunks to supplement your earlier retrieval. Answer the question using all provided chunks.
        Format your response in clean markdown (headings, bullet points, bold, code blocks where appropriate). Never wrap your full response in a code block.

        Rules:
        - Answer strictly from the chunks. Never invent facts, numbers, names, or dates.
        - For greetings or general conversational questions, respond normally.
        - If the answer is still not in the chunks, say: "I could not find this in the document."
        - Do not reference the chunks directly in your response.

        Document chunks:
        {chunks}

        Conversation so far:
        {history or "None"}

        User question: {question}"""
    
def format_chunks(ret_chunks):
    return "\n\n".join(
        f"[Page {c['page']}] {c['text']}" for c in ret_chunks
    )

def getReport(model,chunks_d):

    data = " ".join([c["text"] for c in chunks_d])

    prompt = f"""You are a document analyst. Synthesize the key themes, main arguments, and important information from the document excerpt below into a structured report.

    Format your report in clean markdown: use headings, bullet points, bold text, and code blocks where relevant. Do not wrap the entire response in a code block.

    Write professionally — do not reference the source text directly (avoid "the document says" or "in the provided text").

    Document content:
    {data}"""
    
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

            more_chunks = get_moreChunks(chunks, index, response,question)

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

def make_title(pdf_name,qs,model=None):

    prompt = f""""You are a PDF Analyser. User asked you a question regarding a PDF and 
    you have to suggest a proper chat title. Proper meaningfull and not too long. Only return title nothing else.
    
    PDF name: {pdf_name}
    User question: {qs}"""


    title = ask_AI("llama-3.3-70b-versatile",prompt,isStream=False)

    return title

def main():
    pass


if __name__ == "__main__":
    main()