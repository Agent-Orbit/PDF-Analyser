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
