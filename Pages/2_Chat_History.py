import streamlit as st
from supabase import create_client
from utils import db_management


def main():

    if "supabase" not in st.session_state:
            
        st.session_state.supabase = create_client(db_management.getSB_url(), db_management.get_SBAnon())

    if "user" in st.session_state:
        st.write(st.session_state.user)




if __name__ == "__main__":

    main()