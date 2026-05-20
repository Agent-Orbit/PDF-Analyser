import streamlit as st
from rag import pdf_parser, embedder, retriever, llm


st.set_page_config(page_title="PDF Analyser", page_icon="📄", layout="wide")

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

        .stFileUploader {
            background-color: #161616;
            border: 1px dashed #3a3a3a;
            border-radius: 8px;
            padding: 1rem;
        }

        .stChatMessage {
            background-color: #161616 !important;
            border: 1px solid #2a2a2a;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }

        .stChatInputContainer {
            border-top: 1px solid #2a2a2a;
            background-color: #0d0d0d;
        }

        .stSpinner > div {
            border-top-color: #c8ff00 !important;
        }

        .stDivider {
            border-color: #2a2a2a;
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


def main():

    with st.sidebar:

        st.markdown('<div class="tag">PDF Analyser</div>', unsafe_allow_html=True)
        st.markdown("### Upload Document")
        st.markdown('<span class="model-badge">⬡ gemini-2.0-flash · API</span>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown('<span class="model-badge">⚙ Mode</span>', unsafe_allow_html=True)
        isBetter = st.toggle("Better Mode", value=False, help="Retrieves additional chunks if the first pass lacks enough context")
        st.markdown("---")

        uploadedData = st.file_uploader("Drop a PDF", type=["pdf"], label_visibility="collapsed")

        if uploadedData:

            st.success(f"📄 {uploadedData.name}")

            if "pdf_id" not in st.session_state:
                st.session_state.pdf_id = None

            if st.session_state.pdf_id is not None:
                if uploadedData.file_id != st.session_state.pdf_id:

                    for key in ["pdf", "pdf_id", "model", "embeddings", "index", "chunks", "chat_history", "llm_history"]:
                        st.session_state.pop(key, None)

            if "pdf" not in st.session_state:

                st.session_state.pdf = uploadedData
                st.session_state.pdf_id = uploadedData.file_id
                st.session_state.model = "gemini-2.0-flash"
                st.session_state.isBetter = isBetter

        st.markdown("---")

        if "chat_history" in st.session_state and st.session_state.chat_history:

            if st.button("🗑 Clear Chat", use_container_width=True):

                st.session_state.chat_history = []
                st.session_state.llm_history = []
                st.rerun()

    if "pdf" not in st.session_state:

        st.markdown("## PDF Analyser")
        st.markdown("Upload a PDF in the sidebar to get started.")
        return

    if "chunks" not in st.session_state:

        with st.spinner("Parsing document..."):
            st.session_state.chunks = pdf_parser.get_chunks(st.session_state.pdf)

        with st.spinner("Generating report..."):
            showReport()

    if "chunks" in st.session_state:
        chatAI()


def showReport():

    chunks = st.session_state.chunks
    chunks_sel = min(5, len(chunks))
    report = llm.getReport(st.session_state.model, chunks[:chunks_sel])
    st.session_state.report = report


def chatAI():

    if "embeddings" not in st.session_state:

        with st.spinner("Embedding document..."):
            st.session_state.embeddings = embedder.embed_chunks(st.session_state.chunks)
            st.session_state.index = retriever.build_index(st.session_state.embeddings)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "llm_history" not in st.session_state:
        st.session_state.llm_history = []

    if "report" in st.session_state:

        st.markdown('<div class="tag">AI Report</div>', unsafe_allow_html=True)

        with st.chat_message("assistant"):
            st.markdown(st.session_state.report)

        st.divider()

    st.markdown('<div class="tag">Chat</div>', unsafe_allow_html=True)

    for msg in st.session_state.chat_history:

        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_prompt = st.chat_input("Ask about your document...")

    if user_prompt:

        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                q_emb = embedder.embed_query(user_prompt)
                ret_chunks = retriever.get_topK_chunks(st.session_state.chunks, st.session_state.index, q_emb)

                response, st.session_state.llm_history = llm.getResponse(
                    st.session_state.model,
                    st.session_state.chunks,
                    ret_chunks,
                    st.session_state.index,
                    user_prompt,
                    history=st.session_state.llm_history,
                    isBetter=st.session_state.isBetter
                )

            st.markdown(response)

        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        st.session_state.chat_history.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()