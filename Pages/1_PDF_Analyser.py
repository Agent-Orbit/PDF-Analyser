import streamlit as st
from rag import pdf_parser, embedder, retriever, llm, evaluations
from supabase import create_client
from utils import db_management
import math

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
        st.markdown("---")

        # Authentication

        if "supabase" not in st.session_state:
            st.session_state.supabase = create_client(db_management.getSB_url(), db_management.get_SBAnon())

        if not st.session_state.get("auth_done"):
            authLogic()
        
        # Add user name
        if st.session_state.get("auth_done"):

            if st.session_state.user is not None:
                name = st.session_state.user.user_metadata.get("full_name", st.session_state.user.email)
                st.markdown(f"### User: {name}")
            else:
                st.markdown("### Guest")
        
        st.write("")
        if st.button("Logout",width="content",key="logout23"):
            logout()

        st.markdown("---")
        st.markdown("### Upload Document")
        st.markdown('<span class="model-badge">⬡ groq llama-3.3-70b-versatile · API</span>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown('<span class="model-badge">⚙ Mode</span>', unsafe_allow_html=True)
        isBetter = st.toggle("Better Mode", value=False, help="Retrieves additional chunks if the first pass lacks enough context")
        if isBetter:
            st.caption("⚠ Uses 3-4x more API calls per question.")
        st.markdown("---")

        uploadedData = st.file_uploader("Drop a PDF", type=["pdf"], label_visibility="collapsed")

        st.session_state.isBetter = isBetter

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
                st.session_state.model = "llama-3.3-70b-versatile"
                

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

    if st.session_state.user is not None:
        res = st.session_state.supabase.table("sessions").insert({
            "user_id": st.session_state.user.id,
            "pdf_name": st.session_state.pdf.name,
            "report": report
        }).execute()
        st.session_state.session_id = res.data[0]["id"]


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
            if msg["role"] == "assistant":

                with st.expander("Sources"):

                    for c in msg["ret_chunks"]:

                        st.caption(f"Page {c['page']} · score {c['score']}")
                        st.markdown(f"> {c['text'][:250]}...")
                    st.markdown("---")
                
                    st.caption(f"Faithfulness: {msg['faithfulness_Score']}%")


    user_prompt = st.chat_input("Ask about your document...")

    if user_prompt:

        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                q_emb = embedder.embed_query(user_prompt)
                ret_chunks = retriever.get_topK_chunks(st.session_state.chunks, st.session_state.index, user_prompt,q_emb)
                if not ret_chunks:
                    st.warning("I couldn't find relevant information in this document.")
                    return

                response, st.session_state.llm_history = llm.getResponse(
                    st.session_state.model,
                    st.session_state.chunks,
                    ret_chunks,
                    st.session_state.index,
                    user_prompt,
                    history=st.session_state.llm_history,
                    isBetter=st.session_state.isBetter
                )

            placeholder = st.empty()
            full_response = ""

            for token in getStream(response):

                full_response += token
                placeholder.markdown(full_response)

            # eval metrics

            faithfulness_score = evaluations.get_faithfulnessScore(user_q=user_prompt,llm_ans=full_response,ret_chunks=ret_chunks)
            faith_score = None
            if ret_chunks:

                with st.expander("Sources"):

                    for c in ret_chunks:

                        st.caption(f"Page {c['page']} · score {c['score']}")
                        st.markdown(f"> {c['text'][:250]}...")

                    st.markdown("---")
                    faith_score = faithfulness_score["faithfulness"]
                    

                    if math.isnan(faith_score[0]):
                        st.caption("Faithfulness: unavailable")
                        faith_score = None
                    else:
                        faith_score = round(faith_score[0] * 100, 1)
                        st.caption(f"Faithfulness: {faith_score}%")
                    
                    
                        
            
            summary = llm.summarize_turn(st.session_state.model,user_prompt,full_response)
            st.session_state.llm_history = llm.appendHistory(summary,st.session_state.llm_history)
                


        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        st.session_state.chat_history.append({"role": "assistant", "content": full_response,"ret_chunks": ret_chunks,
                                              'faithfulness_Score': faith_score})

        

        # Updating Data base
        
        db_response = (
            st.session_state.supabase.table("messages")
            .select("history")
            .eq("session_id", st.session_state.session_id)
            .maybe_single()
            .execute()
        )

        if db_response is None:

            new_history = [
                {"role": "user", "content": user_prompt},
                {
                    "role": "assistant",
                    "content": full_response,
                    "faithfulness_Score": faith_score
                }
            ]

            st.session_state.supabase.table("messages").insert([
                {
                    "session_id": st.session_state.session_id,
                    "history": new_history
                }
            ]).execute()

        else:

            history = db_response.data["history"]

            history.append({
                "role": "user",
                "content": user_prompt
            })

            history.append({
                "role": "assistant",
                "content": full_response,
                "faithfulness_Score": faith_score
                })

            (
                st.session_state.supabase.table("messages")
                .update({"history": history})
                .eq("session_id", st.session_state.session_id)
                .execute()
            )

def getStream(response):

    for chunk in response:

            content = chunk.choices[0].delta.content or ""

            if content:
                yield content



def signup():

    st.markdown("## Username:")
    name = st.text_input("Input Username", placeholder="someone")

    st.markdown("## Email:")
    email = st.text_input("Input E-mail adress", placeholder="someone@xyz.com")
    st.markdown("## Password:")
    password = st.text_input("Input Password", type="password")
    st.write("")

    if st.button("Sign up"):

        with st.spinner("Signing you up..."):

            try:

                response = st.session_state.supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "full_name": name    
                        }
                    }
                    })

                st.success("Successfully Signed-in")
                if response:
                    st.session_state.user = response.user

                    if response.session:
                        st.session_state.supabase.auth.set_session(
                            response.session.access_token,
                            response.session.refresh_token
                        )
                    else:
                        st.info("Check your email to confirm your account.")

                    st.session_state.auth_done = True

            except Exception as e:
                st.error(e)


def log_in():

    st.markdown("## Email:")
    email = st.text_input("Input E-mail adress", placeholder="someone@xyz.com")
    st.markdown("## Password:")
    password = st.text_input("Input Password", type="password")
    st.write("")

    if st.button("Log in"):

        with st.spinner("Logging in..."):

            try:
                response = st.session_state.supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                st.success(f"Logged in!")
                if response:
                    st.session_state.user = response.user
                    st.session_state.supabase.auth.set_session(
                        response.session.access_token,
                        response.session.refresh_token
                    )
                    st.session_state.auth_done = True

            except Exception as e:
                st.error(f"{e}")

@st.dialog("User Authentication", dismissible=False)
def authLogic():

    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "choose"

    if st.session_state.auth_view == "choose":

        st.markdown("## Please sign up or log in")
        col1, col2 = st.columns(2)
        st.markdown("---")

        with col1:
            if st.button("Sign up", use_container_width=True, key="signup_main"):
                st.session_state.auth_view = "signup"
                st.rerun()

        with col2:
            if st.button("Log in", use_container_width=True, key="loginmain"):
                st.session_state.auth_view = "login"
                st.rerun()

        st.markdown("---")
        if st.button("Continue as Guest", key="guestcontinue"):
            st.session_state.user = None
            st.session_state.auth_done = True
            st.rerun()

    elif st.session_state.auth_view == "signup":
        signup()

    elif st.session_state.auth_view == "login":
        log_in()
    
    if "auth_done" in st.session_state:

        if st.session_state.auth_done:
            st.rerun()

def logout():

    try:
        st.session_state.supabase.auth.sign_out()
    except:
        pass

    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()



if __name__ == "__main__":
    main()