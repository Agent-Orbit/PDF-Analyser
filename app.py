import streamlit as st

st.set_page_config(
    page_title="PDF Analyser",
    page_icon="📄",
    layout="wide"
)

pages = {
    "📄 PDF Tools": [
        st.Page(
            "Pages/1_PDF_Analyser.py",
            title="PDF Analyser",
            icon="📊"
        ),
    ]
}

pg = st.navigation(pages)
pg.run()