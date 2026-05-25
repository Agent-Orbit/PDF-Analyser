import streamlit as st
from supabase import create_client
from utils import db_management


def main():

    if "supabase" not in st.session_state:
            
        st.session_state.supabase = create_client(db_management.getSB_url(), db_management.get_SBAnon())

    if "user" in st.session_state:
        st.session_state.user_id = st.session_state.user.id
        show_History()

def show_History():

    response = st.session_state.supabase.table("sessions").select("*").eq("user_id",st.session_state.user.id).execute()
    
    if response is None:
        st.markdown("# No History yet.")
    else:
        st.write(response)


if __name__ == "__main__":

    main()