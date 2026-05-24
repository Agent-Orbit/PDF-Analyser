import streamlit as st
from dotenv import load_dotenv
import os

def get_groqAPI():

    load_dotenv()
    try:
        return st.secrets["GROQ_API_KEY"]
    except:
        return os.getenv("GROQ_API_KEY")