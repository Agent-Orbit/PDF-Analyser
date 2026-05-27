import streamlit as st
from supabase import create_client
from utils import db_management
from utils.style import apply_styles
import math

def main():

    apply_styles()

    if "analyser_active" in st.session_state:
        del st.session_state["analyser_active"]

    if "supabase" not in st.session_state:
        st.session_state.supabase = create_client(db_management.getSB_url(), db_management.get_SBAnon())

    if "user" in st.session_state:

        if st.session_state.user is None:
            return

        st.session_state.user_id = st.session_state.user.id

        if "chat_id" in st.session_state:
            showChat(st.session_state.chat_id)
        else:
            show_History()
    
    


def show_History():

    response = st.session_state.supabase.table("sessions").select("*").eq("user_id", st.session_state.user.id).order("created_at", desc=True).execute()

    if len(response.data) == 0:
        st.markdown("# No History yet.")

    else:

        for history in response.data:

            with st.container(border=True):

                st.caption(f"Title: {history['title']}")
                st.caption(f"PDF: {history['pdf_name']}")

                if st.button("Open Chat", key=f"{history['id']}_chatOpen"):
                    st.session_state.chat_id = history['id']
                    st.rerun()


def showChat(chatID):

    if st.button("← Back"):
        del st.session_state.chat_id
        if "loaded_chat_id" in st.session_state:
            del st.session_state.loaded_chat_id
        st.rerun()

    if st.session_state.get("loaded_chat_id") != chatID:

        response = st.session_state.supabase.table("sessions").select("report").eq("id", chatID).execute()
        st.session_state.history_report = response.data[0]['report']

        response = st.session_state.supabase.table("messages").select("history").eq("session_id", chatID).execute()

        if len(response.data) > 0:
            st.session_state.history_chat = response.data[0]['history']
        
        else:
            st.session_state.history_chat = []
        st.session_state.loaded_chat_id = chatID

    with st.chat_message("assistant"):
        st.markdown(st.session_state.history_report)

    for msg in st.session_state.history_chat:

        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            if msg["role"] == "assistant":
                with st.expander("Sources"):

                    for c in msg["ret_chunks"]:

                        st.caption(f"Page {c['page']} · score {c['score']}")
                        st.markdown(f"> {c['text'][:250]}...")
                    st.markdown("---")

                    score = msg.get('faithfulness_Score')
                    if score is None or (isinstance(score, float) and math.isnan(score)):
                        st.caption("Faithfulness: unavailable")
                    else:
                        st.caption(f"Faithfulness: {score}%")


if __name__ == "__main__":
    main()