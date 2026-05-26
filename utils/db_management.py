from dotenv import load_dotenv
import os
import streamlit as st

def getSB_key():

    load_dotenv()

    try:
        return st.secrets["SB_PUBLISHABLE_KEY"]
    except:
        return os.getenv("SB_PUBLISHABLE_KEY")
    
def getSB_url():

    load_dotenv()

    try:
        return st.secrets["SB_URL"]
    except:
        return os.getenv("SB_URL")

def get_SBAnon():

    load_dotenv()
    try:
        return st.secrets["SB_ANON_KEY"]
    except:
        return os.getenv("SB_ANON_KEY")
    
HISTORY_KEYS = ["chat_id", "loaded_chat_id"]
ANALYSER_KEYS = ["pdf", "pdf_id", "model", "embeddings", "index", "chunks", "chat_history", "llm_history", "report", "session_id"]  

def clear_history_state():
    for key in HISTORY_KEYS:
        if key in st.session_state:
            del st.session_state[key]

def clear_analyser_state():
    for key in ANALYSER_KEYS:
        if key in st.session_state:
            del st.session_state[key]
