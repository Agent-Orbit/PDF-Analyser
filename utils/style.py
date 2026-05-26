import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

            html, body, [class*="css"] {
                font-family: 'DM Mono', monospace;
            }

            h1, h2, h3 {
                font-family: 'Syne', sans-serif;
            }

            .stApp {
                background-color: #0d0d0d;
                color: #e8e3d8;
            }

            section[data-testid="stSidebar"] {
                background-color: #111111;
                border-right: 1px solid #2a2a2a;
            }

            .stChatMessage {
                background-color: #161616 !important;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                margin-bottom: 0.5rem;
            }

            .tag {
                display: inline-block;
                background: #c8ff00;
                color: #0d0d0d;
                font-family: 'Syne', sans-serif;
                font-weight: 700;
                font-size: 0.65rem;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                padding: 2px 10px;
                border-radius: 2px;
                margin-bottom: 0.5rem;
            }

            .model-badge {
                display: inline-block;
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                color: #888;
                font-size: 0.7rem;
                padding: 3px 10px;
                border-radius: 20px;
                font-family: 'DM Mono', monospace;
            }
        </style>
    """, unsafe_allow_html=True)